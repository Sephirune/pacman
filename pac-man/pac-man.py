import sys
from pacman.config import load_config, ConfigError


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python3 pac-man.py config.json", file=sys.stderr)
        return 1

    try:
        config = load_config(sys.argv[1])
    except ConfigError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    print(config)
    return 0


if __name__ == "__main__":
    sys.exit(main())
