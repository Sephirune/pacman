from pacman.entities import Ghost, Player, GhostStates, STOP
from pacman.config import GameConfig
from dataclasses import dataclass
from pacman.maze import MazeData, generate_maze
from pacman.level import Level, build_level
from enum import Enum
from random import Random

SCARED_DURATION = 8.0


class GameState(Enum):
    PLAYING = 1
    PAUSED = 2
    GAME_OVER = 3
    VICTORY = 4


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
    state: GameState = GameState.PLAYING
    cheat_invincible: bool = False
    cheat_freeze: bool = False
    cheat_speed: float = 1.0
    cheat_skip: bool = False

    def _respawn(self) -> None:
        """Reset player and ghosts to their starting positions."""

        self.player.x, self.player.y = self.level.player_start
        self.player.direction = STOP
        self.player.progress = 0.0
        for ghost, start in zip(self.ghosts, self.level.ghost_starts):
            ghost.x, ghost.y = start
            ghost.direction = STOP
            ghost.progress = 0.0
            ghost.state = GhostStates.CHASING

    def _next_level(self) -> None:
        """Load the next level or end the game if there are none left."""

        self.level_index += 1
        if self.level_index >= len(self.config.levels):
            self.state = GameState.VICTORY
            return
        level_cfg = self.config.levels[self.level_index]
        maze = generate_maze(level_cfg.width, level_cfg.height,
                             seed=0)
        self.level = build_level(maze, self.config.pacgum, self.rng)
        self.time_elapsed = 0.0
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

    def update(self, dt: float, maze: MazeData) -> None:
        """Advance the game by dt seconds."""

        if self.state != GameState.PLAYING:
            return

        # Checkeo del skip
        if self.cheat_skip:
            self.cheat_skip = False
            self._skip_level()
            return

        # mover personajes
        self.player.update(dt, maze)
        for ghost in self.ghosts:
            if self.cheat_freeze:
                continue
            ghost.update_target(self.player, maze, self.time_elapsed)
            ghost.update(dt, maze)

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

        # bajar timer de asustados
        if self.scared_timer > 0:
            self.scared_timer -= dt
            if self.scared_timer <= 0:
                for ghost in self.ghosts:
                    if ghost.state == GhostStates.SCARED:
                        ghost.state = GhostStates.CHASING

        # colisiones jugador-fantasma
        px, py = self.player.exact_position()
        for ghost in self.ghosts:
            gx, gy = ghost.exact_position()
            if abs(gx - px) < 0.5 and abs(gy - py) < 0.5:
                if ghost.state == GhostStates.SCARED:
                    ghost.state = GhostStates.EATEN
                    self.score += self.config.points_per_ghost
                elif (ghost.state == GhostStates.CHASING and not
                      self.cheat_invincible):
                    self.lives -= 1
                    if self.lives <= 0:
                        self.state = GameState.GAME_OVER
                    else:
                        self._respawn()

        # tiempo límite
        self.time_elapsed += dt
        if self.time_elapsed >= self.config.level_max_time:
            self._next_level()

        # victoria de nivel
        if not self.level.pacgums:
            self._next_level()
