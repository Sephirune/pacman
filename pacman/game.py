"""Game rules: one running game, independent from any graphics library."""

from dataclasses import dataclass, field
from enum import Enum
from random import Random

from pacman.config import GameConfig
from pacman.entities import (Ghost, GhostPersonality, GhostStates, Player,
                             STOP)
from pacman.level import Level, build_level
from pacman.maze import MazeError, generate_maze

SCARED_DURATION = 8.0      # segundos que los fantasmas son comestibles
EATEN_RESPAWN = 5.0        # segundos hasta que un fantasma comido reaparece
READY_DURATION = 2.0       # pausa "READY!" al empezar nivel / tras morir
PLAYER_SPEED = 5.0         # celdas por segundo
GHOST_SPEED = 4.5
GHOST_SPEED_PER_LEVEL = 0.1
GHOST_MAX_SPEED = 5.2
SCARED_SPEED_FACTOR = 0.55
EATEN_SPEED_FACTOR = 2.0
CHEAT_SPEED_FACTOR = 2.0
MAZE_RETRIES = 3

PERSONALITIES = [
    GhostPersonality.BLINKY,
    GhostPersonality.PINKY,
    GhostPersonality.INKY,
    GhostPersonality.CLYDE,
]


class GameState(Enum):
    """Global state of a running game."""

    PLAYING = 1
    PAUSED = 2
    GAME_OVER = 3
    VICTORY = 4
    ERROR = 5


class GameEvent(Enum):
    """Things that happened during an update, for the UI (sounds, text)."""

    PACGUM = 1
    SUPER_PACGUM = 2
    GHOST_EATEN = 3
    LIFE_LOST = 4
    TIME_UP = 5
    LEVEL_COMPLETE = 6
    GAME_OVER = 7
    VICTORY = 8


class LevelLoadError(Exception):
    """Raised when a level cannot be generated."""


def load_level(config: GameConfig, index: int, rng: Random) -> Level:
    """Generate the maze of level ``index`` and place pacgums.

    The first level uses the configured seed; the next ones use seed 0,
    which makes the A-Maze-ing package pick a random maze.
    """

    level_cfg = config.levels[index]
    seed = config.seed if index == 0 else 0
    last_error: Exception | None = None
    for _ in range(MAZE_RETRIES):
        try:
            maze = generate_maze(level_cfg.width, level_cfg.height, seed=seed)
            return build_level(maze, config.pacgum, rng)
        except (MazeError, ValueError) as e:
            last_error = e
            seed = 0  # reintenta con un laberinto aleatorio
    raise LevelLoadError(
        f"cannot generate level {index + 1}: {last_error}")


def make_ghosts(level: Level) -> list[Ghost]:
    """Create one ghost per corner, each with its own personality."""

    ghosts: list[Ghost] = []
    for i, start in enumerate(level.ghost_starts):
        ghosts.append(Ghost(
            x=start[0], y=start[1],
            speed=GHOST_SPEED,
            state=GhostStates.CHASING,
            corner=start,
            target=level.player_start,
            personality=PERSONALITIES[i % len(PERSONALITIES)],
            rng=Random(),
        ))
    return ghosts


@dataclass
class Game:
    """A running game: score, lives, current level and all entities."""

    level_index: int
    player: Player
    ghosts: list[Ghost]
    level: Level
    config: GameConfig
    rng: Random
    score: int = 0
    lives: int = 3
    time_elapsed: float = 0.0
    scared_timer: float = 0.0
    ready_timer: float = READY_DURATION
    state: GameState = GameState.PLAYING
    error_message: str = ""
    cheat_invincible: bool = False
    cheat_freeze: bool = False
    cheat_speed: float = 1.0
    cheat_skip: bool = False
    eaten_timers: dict[int, float] = field(default_factory=dict)
    events: list[GameEvent] = field(default_factory=list)

    # ------------------------------------------------------------------
    # Info for the HUD
    # ------------------------------------------------------------------
    @property
    def level_number(self) -> int:
        """Human readable level number (1-based, capped to the max)."""

        return min(self.level_index + 1, len(self.config.levels))

    @property
    def level_count(self) -> int:
        """Total number of levels."""

        return len(self.config.levels)

    @property
    def time_left(self) -> float:
        """Seconds left before the level time limit."""

        return max(0.0, self.config.level_max_time - self.time_elapsed)

    @property
    def is_over(self) -> bool:
        """True when the game ended (won, lost or broken)."""

        return self.state in (GameState.GAME_OVER, GameState.VICTORY,
                              GameState.ERROR)

    # ------------------------------------------------------------------
    # Level handling
    # ------------------------------------------------------------------
    def _respawn(self) -> None:
        """Reset player and ghosts to their starting positions."""

        self.player.x, self.player.y = self.level.player_start
        self.player.direction = STOP
        self.player.queued = STOP
        self.player.progress = 0.0
        for ghost, start in zip(self.ghosts, self.level.ghost_starts):
            ghost.x, ghost.y = start
            ghost.corner = start
            ghost.direction = STOP
            ghost.progress = 0.0
            ghost.state = GhostStates.CHASING
            ghost.last_target_change = -1e9
        self.scared_timer = 0.0
        self.eaten_timers.clear()
        self.ready_timer = READY_DURATION

    def _next_level(self) -> None:
        """Load the next level or end the game if there are none left."""

        self.level_index += 1
        if self.level_index >= len(self.config.levels):
            self.state = GameState.VICTORY
            self.events.append(GameEvent.VICTORY)
            return
        try:
            self.level = load_level(self.config, self.level_index, self.rng)
        except LevelLoadError as e:
            self.state = GameState.ERROR
            self.error_message = str(e)
            return
        self.time_elapsed = 0.0
        self._respawn()

    def _lose_life(self) -> None:
        """Remove a life and respawn, or end the game."""

        self.lives -= 1
        self.events.append(GameEvent.LIFE_LOST)
        if self.lives <= 0:
            self.lives = 0
            self.state = GameState.GAME_OVER
            self.events.append(GameEvent.GAME_OVER)
        else:
            self._respawn()

    # ------------------------------------------------------------------
    # Commands from the UI
    # ------------------------------------------------------------------
    def pause(self) -> None:
        """Pause the game."""

        if self.state == GameState.PLAYING:
            self.state = GameState.PAUSED

    def resume(self) -> None:
        """Resume the game."""

        if self.state == GameState.PAUSED:
            self.state = GameState.PLAYING

    def _skip_level(self) -> None:
        """Cheat to skip current level."""

        self.events.append(GameEvent.LEVEL_COMPLETE)
        self._next_level()

    def cheat_add_life(self) -> None:
        """Cheat: give one extra life."""

        self.lives += 1

    def toggle_cheat_speed(self) -> None:
        """Cheat: switch between normal and double player speed."""

        self.cheat_speed = 1.0 if self.cheat_speed != 1.0 \
            else CHEAT_SPEED_FACTOR

    def pop_events(self) -> list[GameEvent]:
        """Return and clear the events produced since the last call."""

        events = self.events
        self.events = []
        return events

    # ------------------------------------------------------------------
    # Main update
    # ------------------------------------------------------------------
    def _ghost_speed(self, ghost: Ghost) -> float:
        """Speed of a ghost depending on its state and the level."""

        base = min(GHOST_SPEED + GHOST_SPEED_PER_LEVEL * self.level_index,
                   GHOST_MAX_SPEED)
        if ghost.state == GhostStates.SCARED:
            return base * SCARED_SPEED_FACTOR
        if ghost.state == GhostStates.EATEN:
            return base * EATEN_SPEED_FACTOR
        return base

    def _update_ghosts(self, dt: float) -> None:
        """Move ghosts and handle the eaten -> respawn timers."""

        maze = self.level.maze
        for i, ghost in enumerate(self.ghosts):
            if ghost.state == GhostStates.EATEN:
                self.eaten_timers[i] = self.eaten_timers.get(i, 0.0) - dt
                if self.eaten_timers[i] <= 0:
                    # Reaparece en su esquina
                    del self.eaten_timers[i]
                    ghost.x, ghost.y = ghost.corner
                    ghost.direction = STOP
                    ghost.progress = 0.0
                    ghost.state = GhostStates.CHASING
                    continue
                if (ghost.x, ghost.y) == ghost.corner:
                    ghost.direction = STOP  # espera en su esquina
                    ghost.progress = 0.0
                    continue
            if self.cheat_freeze:
                continue
            if ghost.state == GhostStates.SCARED:
                ghost.target = (self.player.x, self.player.y)
            elif ghost.state == GhostStates.CHASING:
                ghost.update_target(self.player, maze, self.time_elapsed)
            ghost.speed = self._ghost_speed(ghost)
            ghost.update(dt, maze)

    def _eat(self) -> None:
        """Eat the pacgum / super-pacgum under the player."""

        player_pos = (self.player.x, self.player.y)
        if player_pos in self.level.pacgums:
            self.level.pacgums.discard(player_pos)
            self.score += self.config.points_per_pacgum
            self.events.append(GameEvent.PACGUM)

        if player_pos in self.level.super_pacgums:
            self.level.super_pacgums.discard(player_pos)
            self.score += self.config.points_per_super_pacgum
            self.scared_timer = SCARED_DURATION
            self.events.append(GameEvent.SUPER_PACGUM)
            for ghost in self.ghosts:
                if ghost.state == GhostStates.CHASING:
                    ghost.state = GhostStates.SCARED
                    ghost.reverse()

    def _collisions(self) -> None:
        """Player / ghost collisions."""

        px, py = self.player.exact_position()
        for i, ghost in enumerate(self.ghosts):
            gx, gy = ghost.exact_position()
            if abs(gx - px) >= 0.5 or abs(gy - py) >= 0.5:
                continue
            if ghost.state == GhostStates.SCARED:
                ghost.state = GhostStates.EATEN
                self.eaten_timers[i] = EATEN_RESPAWN
                self.score += self.config.points_per_ghost
                self.events.append(GameEvent.GHOST_EATEN)
            elif (ghost.state == GhostStates.CHASING
                  and not self.cheat_invincible):
                self._lose_life()
                return

    def update(self, dt: float) -> None:
        """Advance the game by dt seconds."""

        if self.state != GameState.PLAYING:
            return

        if self.cheat_skip:
            self.cheat_skip = False
            self._skip_level()
            return

        # Pausa "READY!" sin mover nada ni contar tiempo
        if self.ready_timer > 0:
            self.ready_timer -= dt
            return

        maze = self.level.maze
        self.player.update(dt * self.cheat_speed, maze)
        self._update_ghosts(dt)
        self._eat()

        if self.scared_timer > 0:
            self.scared_timer -= dt
            if self.scared_timer <= 0:
                for ghost in self.ghosts:
                    if ghost.state == GhostStates.SCARED:
                        ghost.state = GhostStates.CHASING

        self._collisions()
        if self.state != GameState.PLAYING or self.ready_timer > 0:
            return

        if not self.level.pacgums:
            self.events.append(GameEvent.LEVEL_COMPLETE)
            self._next_level()
            return

        # Tiempo agotado: se pierde una vida y el reloj vuelve a empezar
        # (los pacgums ya comidos no vuelven).
        self.time_elapsed += dt
        if self.time_elapsed >= self.config.level_max_time:
            self.events.append(GameEvent.TIME_UP)
            self.time_elapsed = 0.0
            self._lose_life()


def new_game(config: GameConfig) -> Game:
    """Build a fresh Game (level 1) from a loaded config.

    Raises LevelLoadError if the first maze cannot be generated.
    """

    rng = Random()
    level = load_level(config, 0, rng)
    player = Player(x=level.player_start[0], y=level.player_start[1],
                    speed=PLAYER_SPEED)
    return Game(
        level_index=0,
        player=player,
        ghosts=make_ghosts(level),
        level=level,
        config=config,
        rng=rng,
        lives=config.lives,
    )
