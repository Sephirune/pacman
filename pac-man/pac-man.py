import sys
import random
from pacman.config import load_config, ConfigError
from pacman.maze import generate_maze
from pacman.level import build_level
from pacman.entities import Player, Ghost, GhostStates, GhostPersonality, STOP
from pacman.game import Game


def build_game(config) -> Game:
    """Build a Game from a loaded config."""

    rng = random.Random()
    level_cfg = config.levels[0]
    maze = generate_maze(level_cfg.width, level_cfg.height, seed=config.seed)
    level = build_level(maze, config.pacgum, rng)

    player = Player(
        x=level.player_start[0],
        y=level.player_start[1],
        speed=5.0,
    )

    ghosts = []
    personalities = [
        GhostPersonality.BLINKY,
        GhostPersonality.PINKY,
        GhostPersonality.INKY,
        GhostPersonality.CLYDE,
    ]

    for i in range(len(level.ghost_starts)):
        start = level.ghost_starts[i]
        personality = personalities[i]
        ghost = Ghost(
            x=start[0], y=start[1],
            speed=4.5,
            state=GhostStates.CHASING,
            corner=start,
            target=level.player_start,
            personality=personality,
            rng=random.Random(),
        )
        ghosts.append(ghost)

    return Game(
        level_index=0,
        player=player,
        ghosts=ghosts,
        level=level,
        config=config,
        rng=rng,
        lives=config.lives,
    )


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python3 pac-man.py config.json", file=sys.stderr)
        return 1

    try:
        config = load_config(sys.argv[1])
    except ConfigError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    game = build_game(config)
    return 0


if __name__ == "__main__":
    sys.exit(main())
