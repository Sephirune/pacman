"""Entry point: python3 pac-man.py config.json"""

import os
import sys

from pacman.config import ConfigError, load_config

USAGE = "Usage: python3 pac-man.py config.json"


def config_path_from_args(argv: list[str]) -> str | None:
    """Return the config path given on the command line.

    The packaged build (PyInstaller) is started by double-click, without
    arguments: in that case only, the ``config.json`` next to the
    executable is used.
    """

    if len(argv) == 2:
        return argv[1]
    if len(argv) == 1 and getattr(sys, "frozen", False):
        return os.path.join(os.path.dirname(sys.executable), "config.json")
    return None


def main() -> int:
    """Load the config and run the game. Returns the exit status."""

    path = config_path_from_args(sys.argv)
    if path is None:
        print(USAGE, file=sys.stderr)
        return 1

    try:
        config = load_config(path)
    except ConfigError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    # pygame is imported here so usage/config errors are shown without
    # opening a window and without pygame's welcome message.
    os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
    try:
        import pygame
        from pacman.ui.app import App
    except ImportError as e:
        print(f"Error: missing dependency ({e}). Run 'make install'.",
              file=sys.stderr)
        return 1

    try:
        App(config, path).run()
    except pygame.error as e:
        print(f"Error: graphics problem: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 130
    except Exception as e:  # last resort: never show a traceback
        print(f"Error: unexpected problem: {type(e).__name__}: {e}",
              file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
