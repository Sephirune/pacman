from dataclasses import dataclass
from pacman.maze import MazeData, WALL_E, WALL_N, WALL_S, WALL_W, OFFSETS, OPPOSITE
from collections import deque

STOP = 0


@dataclass
class Entity:
    """Class that represents something that moves through the maze."""
    x: int
    y: int
    speed: float
    direction: int = STOP
    progress: float = 0.0

    def choose_direction(self, maze: MazeData) -> int:  # que quiere hacer el personaje?
        """Return the direction to take from the current cell."""

        raise NotImplementedError

    def _pick(self, maze: MazeData) -> int:  # es posible que haga eso?
        """Returns a possible direction, or STOP."""

        direction = self.choose_direction(maze)
        if direction != STOP and maze.can_move(self.x, self.y, direction):
            return direction
        else:
            return STOP

    def update(self, dt: float, maze: MazeData) -> None:
        """Advance ``dt`` seconds."""

        remaining_cells = self.speed * dt
        if self.direction == STOP:
            self.direction = self._pick(maze)
        while self.direction != STOP:
            needed = (1 - self.progress)
            if remaining_cells < needed:
                self.progress += remaining_cells
                return
            else:
                remaining_cells -= needed
                dx, dy = OFFSETS[self.direction]
                self.x += dx
                self.y += dy
                self.progress = 0.0
                self.direction = self._pick(maze)

    def reverse(self) -> None:
        """Turn around between two cells."""

        if self.direction == STOP or self.progress == 0.0:
            return

        dx, dy = OFFSETS[self.direction]
        self.x += dx
        self.y += dy
        self.progress = 1.0 - self.progress
        self.direction = OPPOSITE[self.direction]

    def exact_position(self) -> tuple[float, float]:
        """Return the position as floats, for drawing."""

        if self.direction == STOP:
            return (float(self.x), float(self.y))
        else:
            dx, dy = OFFSETS[self.direction]
            return (self.x + dx * self.progress, self.y + dy * self.progress)


@dataclass
class Player(Entity):
    """Class that represents the player. Moves and turns when it can."""

    queued: int = STOP

    def queue_direction(self, direction: int) -> None:
        """Remember the direction the player wants to take."""

        if direction in OFFSETS:
            self.queued = direction
        else:
            raise ValueError(f"Invalid direction: {direction}")

    def choose_direction(self, maze: MazeData) -> int:
        """Choose the direction to take from the current cell.
        Use the queued direction if possible, else keep going, else STOP.
        """

        if self.queued != STOP and maze.can_move(self.x,
                                                 self.y,
                                                 self.queued):
            new_direction = self.queued
            self.queued = STOP
            return new_direction
        if self.direction != STOP:
            return self.direction
        else:
            return STOP

    def update(self, dt: float, maze: MazeData) -> None:
        """Advance ``dt`` seconds, turning around first if requested."""

        if (self.direction != STOP
                and self.queued == OPPOSITE[self.direction]
                and self.progress > 0):
            self.reverse()
            self.queued = STOP

        super().update(dt, maze)
