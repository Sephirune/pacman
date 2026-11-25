# Risk analysis

| Risk | Prob. | Impact | Mitigation |
| --- | --- | --- | --- |
| The assigned maze package fails or returns bad data | Medium | High | `generate_maze` validates size, values and wall consistency and raises `MazeError`; `load_level` retries 3 times with a random seed; the error is shown in the menu, never a traceback |
| The package is reinstalled / changed during evaluation | Medium | Medium | We only use the public constructor and `.maze`; the wheel is referenced from `pyproject.toml` and reinstalled with `make install` |
| Config modified during evaluation with bad values | High | High | Every key is validated and clamped with a warning; unknown keys ignored; tests cover wrong types, ranges and broken JSON |
| Corrupt or unwritable highscore file | Medium | Medium | Corrupt file moved to `.bak`; atomic save through `.tmp`; save errors displayed in the menu |
| Unhandled exception = project "non-functional" | Low | Critical | Expected errors handled where they happen; last-resort handler in `pac-man.py` prints a one-line error |
| Graphics library refused (not MLX-like) | Low | High | Only window, images, blit, text, events and loop are used; mapping documented in `pacman/ui/app.py` |
| Large mazes (60×50) too slow or too small | Medium | Medium | Tile size adapts to the maze; maze drawn once per level; measured ~11 ms per frame at 60×50 |
| Packaged build missing files (fonts, wheel) | Medium | High | `make package` tested by launching the build; default pygame font is collected by the PyInstaller hook |
| Recode request during the defense | High | Medium | Rules isolated in `game.py`, constants at the top of each module, both team members able to explain each module |
| Team member unavailable | Low | Medium | Interface contract documented in `team_organization.md`; tests let one person change the other's part safely |
