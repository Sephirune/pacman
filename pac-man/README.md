*This project has been created as part of the 42 curriculum by aarogarc, guantino*

# Pac-Man

## Description

A Pac-Man clone written in Python 3.10+ with **pygame**. Mazes are generated
by the A-Maze-ing package assigned to us (`mazegenerator` 2.1.0), the game is
configured through a JSON file with comments, keeps a persistent top-10, has a
cheat mode for evaluation and is packaged as a standalone build for itch.io.

Game loop: **Main Menu → Start Game → Win or Lose → Enter name → Main Menu**.

Features:

- Main menu (Start Game, View Highscores, Instructions, Exit) with the top 10
  always visible on the side.
- At least 10 levels; level 1 uses the configured seed, the next ones are
  random mazes.
- Pacgums in every corridor (or a configured amount), super-pacgums and one
  ghost in each corner, player starting in the middle.
- Four ghosts with different personalities: Blinky chases, Pinky ambushes
  4 cells ahead, Inky is unpredictable, Clyde runs back to his corner when
  he gets close.
- Edible ghosts flee from the player, flash before turning back and, once
  eaten, return to their corner as eyes and respawn after 5 seconds.
- HUD with score, lives, level and remaining time; pause menu; game-over and
  victory screens with name entry.

## Instructions

Requirements: Python ≥ 3.10 and [uv](https://docs.astral.sh/uv/).

```sh
make install          # creates .venv, installs pygame + the maze package
make run              # = uv run python3 pac-man.py config.json
uv run python3 pac-man.py other_config.json
```

Other rules: `make debug` (pdb), `make test` (pytest), `make lint`,
`make lint-strict`, `make package` (standalone build), `make clean`,
`make fclean`.

### Controls

| Key | Action |
| --- | --- |
| Arrow keys / WASD | Move (WASD is read by key *position*, so ZQSD on AZERTY) |
| P / ESC | Pause and resume |
| ENTER / SPACE | Validate in menus |
| 1 | Cheat: invincibility on/off |
| 2 | Cheat: freeze ghosts on/off |
| 3 | Cheat: skip level (counts as cleared) |
| 4 | Cheat: +1 life |
| 5 | Cheat: double player speed on/off |

Active cheats are shown in green at the bottom right of the game screen.

### Packaging and itch.io

`make package` runs PyInstaller with `pac-man.spec` and produces
`dist/pac-man/` (executable + `config.json` + `PLAYING.txt`, the in-package
instructions) and `dist/pac-man.zip`. PyInstaller builds for the OS it runs
on, so build on the target OS (e.g. Linux at 42).

Uploading: create a project on itch.io (*Kind: Downloadable*, *Visibility:
Draft* or *Restricted*), upload `dist/pac-man.zip` and tick the matching
platform. Started without arguments, the packaged game reads the
`config.json` next to the executable; from a terminal you can still pass a
config file.

## Configuration

JSON file; lines whose first non-blank character is `#` are comments.
Missing or invalid values are replaced by a default or clamped into range,
with a `Warning:` on stderr. Unknown keys are ignored. Only a file that cannot
be read, a wrong extension or invalid JSON stops the program, with a one-line
error message (no traceback).

| Key | Default | Valid range | Meaning |
| --- | --- | --- | --- |
| `lives` | 3 | 1–99 | Starting lives |
| `seed` | 42 | 1–999999 | Seed of the first maze |
| `levels` | 10 × `{14, 10}` | width 14–60, height 10–50 | List of `{"width", "height"}`; padded with 14×10 levels up to 10 |
| `pacgum` | 0 | 0–3000 | Number of pacgums; 0 = one per free cell |
| `points_per_pacgum` | 10 | 0–99 | |
| `points_per_super_pacgum` | 50 | 0–150 | |
| `points_per_ghost` | 200 | 0–676767 | |
| `level_max_time` | 90 | 10–600 | Seconds per level |
| `highscore_filename` | `Billy_Mitchell_type_aaah.json` | non-empty string | Relative paths are relative to the config file |

When the time limit is reached the player loses a life, positions are reset
and the clock restarts; eaten pacgums stay eaten.

## Highscore

- Stored as a JSON list of `{"name", "score"}` in `highscore_filename`.
- Loaded when the game starts, saved after the player enters a name.
- Names: 1–10 characters, ASCII letters, digits and spaces (leading and
  trailing spaces are removed). Scores: non-negative integers.
- Only the top 10 is kept, sorted by score; on a tie the older entry stays
  above (stable sort).
- Robustness: a missing file means an empty table; invalid entries are
  skipped with a warning; a corrupt file is renamed to `<file>.bak` so it is
  not lost, and the game starts with an empty table. Saving writes
  `<file>.tmp` and then renames it, so a crash while writing never destroys
  the previous table.

Why: a JSON file is human-readable, easy to check during evaluation and
needs no extra dependency.

## Maze Generation

`pacman/maze.py` is the only module that talks to the package:

```python
gen = MazeGenerator(size=(width, height), perfect=False, seed=seed)
grid = gen.maze      # list of rows, one int per cell
```

Each cell is a 4-bit wall mask (N=1, E=2, S=4, W=8); 15 is a closed cell
(the "42" pattern drawn by the package in the middle). Our loader adapts to
that interface: it checks the grid size, cell values and that neighbouring
cells agree on shared walls, and turns any failure (import error, exception,
bad data) into a `MazeError`. `game.load_level` retries with a random seed
up to 3 times, then shows the error in the main menu instead of crashing.
`seed=0` makes the package pick a random maze, which we use for levels 2+.
`perfect=False` gives loops (no dead ends), as Pac-Man needs.

## Implementation

- **Movement**: entities live on cells (`x`, `y`) with a `progress` between
  0 and 1 toward the next cell. They only change direction on a cell, which
  keeps them aligned with corridors. The player buffers the last direction
  key until it becomes possible, and can turn back instantly.
- **Ghost AI**: each ghost computes a target cell according to its
  personality and, at each cell, takes the direction whose neighbour is
  closest to the target with a BFS distance (`MazeData.distances_from`).
  Ties are broken in the order N, W, S, E. Edible ghosts pick the neighbour
  farthest from the player; eaten ghosts head for their corner.
- **Game rules** (`pacman/game.py`) never import pygame: they can be tested
  without a window (`tests/test_game.py`). The UI reads the `Game` state and
  the list of `GameEvent`s it produces.
- **Rendering**: the maze is drawn once per level into an image; sprites
  (Pac-Man frames, ghosts, dots) are drawn once into images too. Each frame
  only copies images and text to the window. The tile size adapts to the
  maze so 14×10 up to 60×50 fit in the 1024×768 window.
- **MLX-equivalent functions only**: window creation, images and pixel
  drawing into them, copying images to the window, text output, keyboard /
  window events and a frame loop. The mapping is listed at the top of
  `pacman/ui/app.py`. No sound (MLX has none).

## General Software Architecture

```
pac-man.py            entry point: args, config, launches App, catches errors
pacman/
  config.py           load_config() -> GameConfig / LevelConfig
  maze.py             generate_maze() wraps mazegenerator -> MazeData
  level.py            build_level(): pacgums, super-pacgums, spawn points
  entities.py         Entity -> Player, Ghost (+ GhostStates, personalities)
  game.py             Game: rules, timers, cheats, levels, events; new_game()
  highscores.py       HighScores table, validate_name()
  ui/
    app.py            App: window, main loop, current Screen
    screens.py        MenuScreen, HighscoresScreen, InstructionsScreen,
                      GameScreen (with pause menu), EndScreen (name entry)
    renderer.py       GameRenderer: maze image, entities, HUD
    sprites.py        SpriteSet: pre-rendered images
    theme.py          colours, fonts, text helper
tests/                pytest suites (config, highscores, game rules)
pac-man.spec          PyInstaller spec used by `make package`
```

`App` owns one `Screen` at a time; a screen asks the app to `switch()` to
another. `GameScreen` owns a `Game` and a `GameRenderer`. `Game` owns a
`Level` (which owns a `MazeData`), a `Player` and four `Ghost`s, and reads
the `GameConfig`. Data flows one way: UI → commands on `Game` → UI reads
`Game` to draw.

## Project Management

See [`docs/project_management/`](docs/project_management/): team
organisation, timeline, risk analysis and acceptance test plan.

## Resources

- [pygame documentation](https://www.pygame.org/docs/)
- [The Pac-Man Dossier](https://www.gamedeveloper.com/design/the-pac-man-dossier)
  (Jamey Pittman) – ghost personalities and targeting
- [Understanding Pac-Man Ghost Behavior](https://gameinternals.com/understanding-pac-man-ghost-behavior)
- [PyInstaller manual](https://pyinstaller.org/en/stable/)
- [itch.io – uploading a game](https://itch.io/docs/creators/getting-started)
- [uv documentation](https://docs.astral.sh/uv/)

### AI usage

An AI assistant (Claude) was used to:

- write the pygame front-end (`pacman/ui/`), the new entry point and the
  PyInstaller packaging;
- review the core modules and fix integration issues (eaten ghosts never
  respawned, edible ghosts moved randomly instead of fleeing, an uncaught
  maze error when changing level, highscore methods that were private);
- write `tests/test_game.py`, the Makefile rules and a first draft of this
  README and of the project-management documents.

<!-- TODO: describe how you reviewed / tested the generated parts. -->
