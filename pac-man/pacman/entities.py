from dataclasses import dataclass
from pacman.maze import MazeData, WALL_E, WALL_N, WALL_S, WALL_W, OFFSETS, OPPOSITE

STOP = 0


@dataclass
class Move:
    """Class that represents something that moves through the maze."""
    x: int
    y: int
    speed: float
    direction: int = STOP
    progress: float = 0.0

    def choose_direction(self, maze: MazeData) -> int:
        """Return the direction to take from the current cell."""

    def _pick(self, maze: MazeData) -> int:
        """Returns a possible direction, or STOP."""
        if self.choose_direction(maze) != STOP and maze.can_move(self.x, self.y, self.d):
            return self.choose_direction()

    def update(self, dt: float, maze: MazeData) -> None:
        """Advance ``dt`` seconds."""

    def reverse(self) -> None:
        """Turn around between two cells."""

    def exact_position(self) -> tuple[float, float]:
        """Return the position as floats, for drawing."""


@dataclass
class Player(Move):
    """Class that represents the player. Moves and turns when it can."""
    queued: int = STOP

    def queue_direction(self, direction: int) -> None:
        """Remember the direction the player wants to take."""

    def choose_direction(self, maze: MazeData) -> int:
        return super().choose_direction()

    def update(self, dt: float, maze: MazeData):
        return super().update(maze)
    