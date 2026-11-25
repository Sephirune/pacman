# Team organisation

## Split of the work

The project was cut along the boundary between game rules and display, so
both halves could be developed and tested independently.

| Area | Modules | Owner |
| --- | --- | --- |
| Configuration parsing | `pacman/config.py`, `tests/test_config.py` |  |
| Maze integration, levels | `pacman/maze.py`, `pacman/level.py` |  |
| Entities and ghost AI | `pacman/entities.py` |  |
| Game rules | `pacman/game.py` |  (initial) /  (integration) |
| Highscores | `pacman/highscores.py`, `tests/test_highscores.py` |  |
| pygame UI (menus, HUD, screens, sprites) | `pacman/ui/` |  |
| Packaging, Makefile, pyproject | `pac-man.spec`, `Makefile`, `pyproject.toml` |  |
| Documentation | `README.md`, `docs/` |  |

## Interface contract between the two halves

- The UI only uses `new_game(config)`, `Game.update(dt)`, the cheat / pause
  methods and the public fields of `Game`, `Player`, `Ghost`, `Level`.
- `Game` never imports pygame. What happened during a frame is reported
  through `Game.pop_events()`.
- `HighScores.load / add / top / save` is the only highscore API used by
  the UI.

## Decisions

| Decision | Reason |
| --- | --- |
| pygame as graphics library | Available with pip; we only use functions that have an MLX equivalent (see `pacman/ui/app.py`) |
| Highscores in a JSON file | Readable during evaluation, no dependency |
| Time limit = lose a life and restart the clock | Advancing to the next level on time-out would let a player win by waiting |
| Cheats on keys 1–5, always available | The reviewer can test every feature without reading code |
| uv + `pyproject.toml` | Reproducible install of pygame and of the assigned wheel |
