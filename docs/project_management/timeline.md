# Timeline

| # | Milestone | Status |
| --- | --- | --- |
| 1 | Read subject, split work, set up repo | done |
| 2 | Config loader + tests | done |
| 3 | Maze package integration (`maze.py`, `level.py`) | done |
| 4 | Entities, movement, ghost AI | done |
| 5 | Game rules (`game.py`), highscores | done |
| 6 | pygame UI: menu, game view, HUD  done |
| 7 | Pause, game over / victory, name entry, cheats | done |
| 8 | Packaging (PyInstaller) + itch.io upload | upload |
| 9 | README, project-management docs | done |
| 10 | Acceptance tests, bug fixing, peer review | in progress |

```mermaid
gantt
    dateFormat  YYYY-MM-DD
    title Pac-Man
    section Core
    Config + maze          :done, c1, 5d
    Entities + rules       :done, c2, after c1, 7d
    section UI
    pygame screens         :done, u1, after c2, 5d
    section Delivery
    Packaging + docs       :active, d1, after u1, 3d
```
