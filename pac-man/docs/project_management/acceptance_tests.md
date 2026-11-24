# Acceptance test plan

Automated tests: `make test` (config, highscores, game rules).
Manual tests below are run with `make run` unless stated otherwise.

## Command line and configuration

| # | Test | Expected | Result |
| --- | --- | --- | --- |
| C1 | `python3 pac-man.py` | Usage message, exit 1 | OK |
| C2 | Two arguments | Usage message, exit 1 | OK |
| C3 | Missing file | `Error: Cannot read ...`, exit 1 | OK |
| C4 | Non `.json` file | `Error: Invalid path extension.` | OK |
| C5 | Broken JSON | `Error: Invalid JSON at line L, column C` | OK |
| C6 | Wrong types, out-of-range values, unknown keys | Warnings, game starts with defaults / clamped values | OK |
| C7 | `# comments` anywhere | Ignored | OK |
| C8 | Fewer than 10 levels | Padded to 10, HUD shows `LEVEL 1/10` | OK |
| C9 | Level 60×50 and 14×10 | Whole maze visible, playable | OK |

## Gameplay

| # | Test | Expected | Result |
| --- | --- | --- | --- |
| G1 | Start game | Level 1 maze from seed, Pac-Man in the middle, 4 ghosts in corners, READY! | OK |
| G2 | Arrows and WASD | Moves only along corridors | OK |
| G3 | Eat pacgum / super-pacgum | Score +X / +Y, ghosts turn blue and flee | OK |
| G4 | Eat blue ghost | +Z, eyes go home, ghost back after 5 s | OK |
| G5 | Touched by ghost | −1 life, everyone back to start | OK |
| G6 | Lose all lives | GAME OVER, then name entry | OK |
| G7 | Eat all pacgums | Next level, random maze, score and lives kept | OK |
| G8 | Timer reaches 0 | −1 life, timer restarts | OK |
| G9 | Clear last level | YOU WIN!, congratulations screen, name entry | OK |
| G10 | P / ESC | Pause menu: Resume, Main Menu | OK |
| G11 | Window loses focus | Game pauses | OK |
| G12 | Cheats 1–5 | Invincible / freeze / skip / +1 life / speed, shown in HUD | OK |

## Highscores

| # | Test | Expected | Result |
| --- | --- | --- | --- |
| H1 | No highscore file | Empty table, no error | OK |
| H2 | Enter `Bob 42` | Saved, highlighted in the menu top 10 | OK |
| H3 | Name with `ñ`, `;`, >10 chars | Rejected at typing / validation | OK |
| H4 | Corrupt file | Moved to `.bak`, warning, empty table | OK |
| H5 | 11th score lower than all | "did not reach the top 10" message | OK |

## Packaging

| # | Test | Expected | Result |
| --- | --- | --- | --- |
| P1 | `make package` | `dist/pac-man/` and `dist/pac-man.zip` | OK (Linux) |
| P2 | Launch the built executable without arguments | Uses bundled `config.json` | OK (Linux) |
| P3 | Download from itch.io and play | Works | TODO |

## Bugs found and fixed during integration

| Bug | Fix |
| --- | --- |
| Eaten ghosts stayed "eyes" forever | Respawn timer (5 s) in `Game` |
| Edible ghosts moved randomly instead of fleeing | `Ghost.choose_direction` picks the cell farthest from the player |
| `MazeError` when loading level 2+ crashed the game | `load_level` retries, then `GameState.ERROR` shown in the menu |
| Time limit skipped to the next level (win by waiting) | Time-out now costs a life |
| Level complete + time limit could both trigger in one frame | Early returns in `Game.update` |
| Several ghosts could hit the player in the same frame | Collision loop stops after a life is lost |
| Highscore methods private (`_load`, ...) while tests use `load` | Public API `load/add/top/save` |
| JSON error message `line1` instead of `line 1` | Fixed format string |
| Makefile `run` pointed to a missing `src` module | `run` launches `pac-man.py config.json` |
