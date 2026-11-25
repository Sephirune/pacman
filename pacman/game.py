from dataclasses import dataclass, field
from enum import Enum
from random import Random

from pacman.config import GameConfig
from pacman.entities import (Ghost, GhostPersonality, GhostStates, Player,
                             STOP)
from pacman.level import Level, build_level
from pacman.maze import MazeError, generate_maze

SCARED_DURATION = 8.0
EATEN_RESPAWN = 5.0    # seconds until an eaten ghost respawns
READY_DURATION = 2.0   # pause at level start / after a death
PLAYER_SPEED = 5.0
GHOST_SPEED = 4.5


class GameState(Enum):
    PLAYING = 1
    PAUSED = 2
    GAME_OVER = 3
    VICTORY = 4
    ERROR = 5


class LevelLoadError(Exception):
    """Raised when a level cannot be generated."""


def load_level(config: GameConfig, index: int, rng: Random) -> Level:
    """Generate level ``index``. Level 1 uses the configured seed, the
    others use seed 0, which makes the maze package pick a random maze."""

    level_cfg = config.levels[index]
    seed = config.seed if index == 0 else 0
    try:
        maze = generate_maze(level_cfg.width, level_cfg.height, seed=seed)
        return build_level(maze, config.pacgum, rng)
    except (MazeError, ValueError) as e:
        raise LevelLoadError(f"cannot generate level {index + 1}: {e}") \
            from e


@dataclass
class Game:
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

    @property
    def level_number(self) -> int:
        """Level shown in the HUD (1-based)."""

        return min(self.level_index + 1, len(self.config.levels))

    @property
    def time_left(self) -> float:
        """Seconds left before the level time limit."""

        return max(0.0, self.config.level_max_time - self.time_elapsed)

    @property
    def is_over(self) -> bool:
        """True when the game ended (won, lost or broken)."""

        return self.state in (GameState.GAME_OVER, GameState.VICTORY,
                              GameState.ERROR)

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
        if self.lives <= 0:
            self.lives = 0
            self.state = GameState.GAME_OVER
        else:
            self._respawn()

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

        self._next_level()

    def _update_ghosts(self, dt: float) -> None:
        """Move ghosts. Eaten ghosts go back to their corner and
        reappear there after EATEN_RESPAWN seconds."""

        maze = self.level.maze
        for i, ghost in enumerate(self.ghosts):
            if ghost.state == GhostStates.EATEN:
                self.eaten_timers[i] -= dt
                if self.eaten_timers[i] <= 0:
                    del self.eaten_timers[i]
                    ghost.x, ghost.y = ghost.corner
                    ghost.direction = STOP
                    ghost.progress = 0.0
                    ghost.state = GhostStates.CHASING
                    continue
                if (ghost.x, ghost.y) == ghost.corner:
                    ghost.direction = STOP  # wait in its corner
                    ghost.progress = 0.0
                    continue
            if self.cheat_freeze:
                continue
            if ghost.state == GhostStates.SCARED:
                ghost.target = (self.player.x, self.player.y)  # to flee
            elif ghost.state == GhostStates.CHASING:
                ghost.update_target(self.player, maze, self.time_elapsed)
            ghost.update(dt, maze)

    def update(self, dt: float) -> None:
        """Advance the game by dt seconds."""

        if self.state != GameState.PLAYING:
            return

        # skip cheat
        if self.cheat_skip:
            self.cheat_skip = False
            self._skip_level()
            return

        # "READY!" pause: nothing moves, clock stopped
        if self.ready_timer > 0:
            self.ready_timer -= dt
            return

        # move characters
        maze = self.level.maze
        self.player.update(dt * self.cheat_speed, maze)
        self._update_ghosts(dt)

        # pacgum
        player_pos = (self.player.x, self.player.y)
        if player_pos in self.level.pacgums:
            self.level.pacgums.discard(player_pos)
            self.score += self.config.points_per_pacgum

        # super-pacgum
        if player_pos in self.level.super_pacgums:
            self.level.super_pacgums.discard(player_pos)
            self.score += self.config.points_per_super_pacgum
            self.scared_timer = SCARED_DURATION
            for ghost in self.ghosts:
                if ghost.state == GhostStates.CHASING:
                    ghost.state = GhostStates.SCARED

        # scared timer countdown
        if self.scared_timer > 0:
            self.scared_timer -= dt
            if self.scared_timer <= 0:
                for ghost in self.ghosts:
                    if ghost.state == GhostStates.SCARED:
                        ghost.state = GhostStates.CHASING

        # player-ghost collisions
        px, py = self.player.exact_position()
        for i, ghost in enumerate(self.ghosts):
            gx, gy = ghost.exact_position()
            if abs(gx - px) < 0.5 and abs(gy - py) < 0.5:
                if ghost.state == GhostStates.SCARED:
                    ghost.state = GhostStates.EATEN
                    self.eaten_timers[i] = EATEN_RESPAWN
                    self.score += self.config.points_per_ghost
                elif (ghost.state == GhostStates.CHASING and not
                      self.cheat_invincible):
                    self._lose_life()
                    return

        # level cleared
        if not self.level.pacgums:
            self._next_level()
            return

        # time limit: lose a life and restart the clock
        self.time_elapsed += dt
        if self.time_elapsed >= self.config.level_max_time:
            self.time_elapsed = 0.0
            self._lose_life()


def new_game(config: GameConfig) -> Game:
    """Build a Game from a loaded config (moved from pac-man.py).
    Raises LevelLoadError if the first maze cannot be generated."""

    rng = Random()
    level = load_level(config, 0, rng)
    player = Player(x=level.player_start[0], y=level.player_start[1],
                    speed=PLAYER_SPEED)
    personalities = [
        GhostPersonality.BLINKY,
        GhostPersonality.PINKY,
        GhostPersonality.INKY,
        GhostPersonality.CLYDE,
    ]
    ghosts = []
    for i in range(len(level.ghost_starts)):
        start = level.ghost_starts[i]
        ghosts.append(Ghost(
            x=start[0], y=start[1],
            speed=GHOST_SPEED,
            state=GhostStates.CHASING,
            corner=start,
            target=level.player_start,
            personality=personalities[i],
            rng=Random(),
        ))
    return Game(level_index=0, player=player, ghosts=ghosts, level=level,
                config=config, rng=rng, lives=config.lives)
