import pytest
from pacman.highscores import validate_name

@pytest.mark.parametrize("raw, expected", [
    ("Ana", "Ana"),
    ("  Ana  ", "Ana"),
    ("John Doe", "John Doe"),
    ("abcdefghij", "abcdefghij"),
    ("  abcdefghij  ", "abcdefghij"),
])
def test_valid_names(raw: str, expected: str) -> None:
    assert validate_name(raw) == expected


@pytest.mark.parametrize("raw", [
    "abcdefghijk", "", "   ", "ñandú", "a\tb", "ab;",
])
def test_invalid_names(raw: str) -> None:
    with pytest.raises(ValueError):
        validate_name(raw)


import json
from pathlib import Path

from pacman.highscores import HighScores


def test_load_valid_file_keeps_it(tmp_path: Path) -> None:
    path = tmp_path / "scores.json"
    path.write_text(json.dumps([{"name": "Ana", "score": 500},
                                {"name": "Bob", "score": 900}]))
    table = HighScores(str(path))
    warnings: list[str] = []
    table.load(warnings)
    assert [e.name for e in table.entries] == ["Bob", "Ana"]
    assert warnings == []
    assert path.exists()
    assert not (tmp_path / "scores.json.bak").exists()