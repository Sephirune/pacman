# Timeline

Replace the TODO dates with the real ones; the "Actual" column is the
progress tracking compared to the plan.

| # | Milestone | Planned | Actual | Status |
| --- | --- | --- | --- | --- |
| 1 | Read subject, split work, set up repo | TODO | TODO | done |
| 2 | Config loader + tests | TODO | TODO | done |
| 3 | Maze package integration (`maze.py`, `level.py`) | TODO | TODO | done |
| 4 | Entities, movement, ghost AI | TODO | TODO | done |
| 5 | Game rules (`game.py`), highscores | TODO | TODO | done |
| 6 | pygame UI: menu, game view, HUD | TODO | TODO | done |
| 7 | Pause, game over / victory, name entry, cheats | TODO | TODO | done |
| 8 | Packaging (PyInstaller) + itch.io upload | TODO | TODO | TODO upload |
| 9 | README, project-management docs | TODO | TODO | done |
| 10 | Acceptance tests, bug fixing, peer review | TODO | TODO | in progress |

```mermaid
gantt
    dateFormat  YYYY-MM-DD
    title Pac-Man
    section Core
    Config + maze          :done, c1, TODO, 5d
    Entities + rules       :done, c2, after c1, 7d
    section UI
    pygame screens         :done, u1, after c2, 5d
    section Delivery
    Packaging + docs       :active, d1, after u1, 3d
```
