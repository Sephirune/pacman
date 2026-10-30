from dataclasses import dataclass


WALL_N, WALL_E, WALL_S, WALL_W = 1, 2, 4, 8
OFFSETS = {WALL_N: (0, -1), WALL_E: (1, 0),
           WALL_S: (0, 1), WALL_W: (-1, 0)}
OPPOSITE = {WALL_N: WALL_S, WALL_E: WALL_W,
            WALL_S: WALL_N, WALL_W: WALL_E}

MIN_WIDTH = 14
MIN_HEIGHT = 10

class MazeError(Exception):
    """raised when a maze cannot be generated or is invalid"""


@dataclass
class MazeData():
    """Maze grid and helpers for the game."""

    width: int
    height: int
    grid: list[list[int]]


    def can_move(self, x, y, direction) -> bool:
        for i in OFFSETS.keys():
            if direction[i] not in OFFSETS:
                raise ValueError()
            if self.is_blocked(x, y):
                return False
        return True
            


    def is_blocked(self, x, y) -> bool:
        if x not in self.grid or y not in self.grid:
            return True
        return False

    def corners(self) -> list[tuple[int, int]]:
        return [
            (0, 0),
            (self.width - 1, 0),
            (0, self.height - 1),
            (self.width - 1, self.height - 1)
        ]

    def spawn(self) -> tuple[int, int]:
        centre = (self.width // 2, self.height // 2)
        if not self.is_blocked(centre.__getattribute__(self.width), centre.__getattribute__(self.height)):
            return centre
        else:
            
        return ...
        

def generate_maze(width: int, height: int, seed: int) -> MazeData:
    if not isinstance(width, int) or not isinstance(height, int):
        raise MazeError(f"Error: invalid dimensions for {width}, {height}")
    return ...