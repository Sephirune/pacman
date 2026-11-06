from dataclasses import dataclass
from collections import deque


WALL_N, WALL_E, WALL_S, WALL_W = 1, 2, 4, 8
OFFSETS = {WALL_N: (0, -1), WALL_E: (1, 0),
           WALL_S: (0, 1), WALL_W: (-1, 0)}
OPPOSITE = {WALL_N: WALL_S, WALL_E: WALL_W,
            WALL_S: WALL_N, WALL_W: WALL_E}

MIN_WIDTH = 14
MIN_HEIGHT = 10
BLOCKED = 15


class MazeError(Exception):
    """raised when a maze cannot be generated or is invalid"""


@dataclass
class MazeData():
    """Maze grid and helpers for the game."""

    width: int
    height: int
    grid: list[list[int]]

    def can_move(self, x: int, y: int, direction: int) -> bool:
        """Checks if a step in a direction is possible."""

        if direction not in OFFSETS:
            raise ValueError(f"Invalid direction detected: {direction}")
        if self.is_blocked(x, y):
            return False

        dx, dy = OFFSETS[direction]
        dest = (x + dx, y + dy)
        dest_x, dest_y = dest
        if self.is_blocked(dest_x, dest_y):
            return False

        if (self.grid[y][x] & direction) != 0:
            return False

        return True

    def is_blocked(self, x: int, y: int) -> bool:
        """Checks if a cell is blocked or outside the maze."""

        if not (0 <= x < self.width and 0 <= y < self.height): # Lo de fuera del grid esta bloqueado
            return True
        return self.grid[y][x] == BLOCKED  # Dentro, la celda esta bloqueada si vale 15

    def corners(self) -> list[tuple[int, int]]:
        """Return the four corners of the maze as (x, y) tuples."""

        return [
            (0, 0),
            (self.width - 1, 0),
            (0, self.height - 1),
            (self.width - 1, self.height - 1)
        ]

    def validate_wall_consistency(self) -> bool:
        """Ensure adjacent cells agree on shared walls."""

        for y in range(self.height):
            for x in range(self.width):
                for direction, (dx, dy) in OFFSETS.items():
                    nx, ny = x + dx, y + dy

                    if not (0 <= nx < self.width and 0 <= ny < self.height):  # si esta fuera se salta
                        continue
                    wall_here = bool(self.grid[y][x] & direction)

                    wall_neighbor = bool(  # pared opuesta
                        self.grid[ny][nx] & OPPOSITE[direction]
                    )

                    if wall_here != wall_neighbor:  # si no coinciden
                        return False
        return True

    def spawn(self) -> tuple[int, int]:
        """Return the cell where the player starts."""

        centre = (self.width // 2, self.height // 2)
        cx, cy = centre

        if not self.is_blocked(cx, cy):
            return centre
        else:
            free: list[tuple[int, int]] = []
            for y in range(self.height):
                for x in range(self.width):
                    if not self.is_blocked(x, y):
                        free.append((x, y))
            if not free:
                raise MazeError("No free cells available.")
            return min(free, key=lambda cell: (
                abs(cell[0] - cx) + abs(cell[1] - cy),
                cell[1],
                cell[0]
                ))

    def distances_from(self, x: int, y: int) -> dict[tuple[int, int], int]:
        """Returns the distance that must be walked until
        a valid cell using BFS."""

        if self.is_blocked(x, y):
            return {}

        distances: dict[tuple[int, int]] = {(x, y): 0}
        queue: deque[tuple[int, int]] = deque(distances)

        while queue:
            col, row = queue.popleft()
            for direction, (drow, dcol) in OFFSETS.items():
                if self.can_move(row, col, direction):
                    nrow = row + drow
                    ncol = col + dcol

                    if not (0 <= nrow < self.height and
                            0 <= ncol < self.width):
                        continue

                    neighbour = (ncol, nrow)
                    if neighbour not in distances:
                        distances[neighbour] = distances[(col, row)] + 1
                        queue.append(neighbour)

        return distances


def _is_int(value: object) -> bool:
    """Return True for integers, excluding booleans."""

    return isinstance(value, int) and not isinstance(value, bool)


def generate_maze(width: int, height: int, seed: int) -> MazeData:
    """Generate a maze with the assigned A-Maze-ing package."""

    if not _is_int(width) or not _is_int(height) or not _is_int(seed):
        raise MazeError(f"Invalid dimensions for {width}, {height}")

    if width < MIN_WIDTH or height < MIN_HEIGHT:
        raise MazeError(
            f"Invalid parameters: {width} {height}."
            f"At least {MIN_WIDTH}x{MIN_HEIGHT}.")

    if seed < 0:
        raise MazeError(f"Seed must not be a negative integer: {seed}")

    try:
        from mazegenerator import MazeGenerator
    except ImportError as e:
        raise MazeError(f"Maze generation failed: {e}") from e

    try:
        gen = MazeGenerator(size=(width, height), perfect=False, seed=seed)
        grid: list[list[int]] = [list(row) for row in gen.maze]
    except Exception as e:
        raise MazeError(f"{e}") from e

    if len(grid) != height:
        raise MazeError(
            f"Generated grid height error: {len(grid)} instead of {height}.")

    for row_idx, row in enumerate(grid):
        if len(row) != width:
            raise MazeError(
                f"row {row_idx} has {len(row)} cells instead of {width}")

    for y in range(height):
        for x in range(width):
            cell = grid[y][x]
            if not _is_int(cell) or not (0 <= cell <= 15):
                raise MazeError(f"Invalid cell value: ({x}, {y}) {cell}.")

    maze_data = MazeData(width, height, grid)
    if not maze_data.validate_wall_consistency():
        raise MazeError("Generated maze has inconsistent walls.")

    return maze_data
