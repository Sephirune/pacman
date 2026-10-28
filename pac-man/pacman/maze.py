from dataclasses import dataclass


WALL_N, WALL_E, WALL_S, WALL_W = 1, 2, 4, 8
OFFSETS = {WALL_N: (0, -1), WALL_E: (1, 0),
           WALL_S: (0, 1), WALL_W: (-1, 0)}
OPPOSITE = {WALL_N: WALL_S, WALL_E: WALL_W,
            WALL_S: WALL_N, WALL_W: WALL_E}

class MazeError(Exception):
    """raised when a maze cannot be generated or is invalid"""


@dataclass
class MazeData():
    """Maze grid and helpers for the game."""

    width: int
    height: int
    grid: list[list[int]]


    def can_move(self, x, y, direction) -> bool:


    def is_blocked(self, x, y) -> bool:


    def corners(self) -> list[tuple[int, int]]:

    def spawn(self) -> tuple[int, int]:


def generate_maze(width: int, height: int, seed: int) -> MazeData: