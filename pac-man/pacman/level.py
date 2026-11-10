from dataclasses import dataclass
from random import Random

from pacman.maze import MazeData, MazeError


@dataclass
class Level:
    """State of one level: pacgums, super-pacgums and starting positions."""

    maze: MazeData
    pacgums: set[tuple[int, int]]
    super_pacgums: set[tuple[int, int]]
    player_start: tuple[int, int]
    ghost_starts: list[tuple[int, int]]


def build_level(maze: MazeData, pacgum_count: int, rng: Random) -> Level:
    """Build a level from a generated maze."""

    if pacgum_count < 0:
        raise ValueError(f"pacgum_count must not be negative: {pacgum_count}")

    corners = maze.corners()
    if any(maze.is_blocked(x, y) for x, y in corners):
        raise MazeError("A corner of the maze is blocked.")

    spawn = maze.spawn()
    excluded = set(corners) | {spawn}

    candidates = []
    for y in range(maze.height):
        for x in range(maze.width):
            if not maze.is_blocked(x, y) and (x, y) not in excluded:
                candidates.append((x, y))

    if pacgum_count == 0 or pacgum_count >= len(candidates):
        chosen = candidates
    else:
        chosen = rng.sample(candidates, pacgum_count)

    return Level(
        maze=maze,
        pacgums=set(chosen),
        super_pacgums=set(corners),
        player_start=spawn,
        ghost_starts=list(corners),
    )
