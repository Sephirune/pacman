from pathlib import Path
from typing import Any

import pytest

from config import (ConfigError, LevelConfig, get_int, load_config,
                    parse_levels, strip_comments)


def write(tmp_path: Path, name: str, content: str) -> str:
    """Create a file inside tmp_path and return its path."""
    file = tmp_path / name
    file.write_text(content, encoding="utf-8")
    return str(file)


def test_strip_comments() -> None:
    text = '# comentario\n{"a": 1}\n  # otro'
    assert strip_comments(text) == '\n{"a": 1}\n'


@pytest.mark.parametrize("data, expected, n_warnings", [
    ({"lives": 5}, 5, 0),
    ({"lives": True}, 3, 1),
    ({"lives": "tres"}, 3, 1),
    ({"lives": 500}, 99, 1),
    ({"lives": 0}, 1, 1),
    ({}, 3, 1),
])
def test_get_int(data: dict[str, Any], expected: int,
                 n_warnings: int) -> None:
    warnings: list[str] = []
    assert get_int(data, "lives", 3, 1, 99, warnings) == expected
    assert len(warnings) == n_warnings


def test_parse_levels_clamps_and_fills() -> None:
    warnings: list[str] = []
    raw = [{"width": 21, "height": 15}, {"width": 99, "height": 12}, "hola"]
    levels = parse_levels(raw, warnings)
    assert levels[0] == LevelConfig(width=21, height=15)
    assert levels[1] == LevelConfig(width=60, height=12)
    assert len(levels) == 10
    assert len(warnings) == 2


def test_parse_levels_without_data() -> None:
    warnings: list[str] = []
    levels = parse_levels(None, warnings)
    assert len(levels) == 10
    assert len(warnings) == 1


def test_missing_file(tmp_path: Path) -> None:
    with pytest.raises(ConfigError):
        load_config(str(tmp_path / "nope.json"))


def test_wrong_extension(tmp_path: Path) -> None:
    with pytest.raises(ConfigError):
        load_config(write(tmp_path, "c.txt", "{}"))


def test_broken_json(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="line 1"):
        load_config(write(tmp_path, "c.json", "{ not json"))


def test_root_is_list(tmp_path: Path) -> None:
    with pytest.raises(ConfigError):
        load_config(write(tmp_path, "c.json", "[1, 2]"))


def test_valid_config_with_comments(tmp_path: Path) -> None:
    content = '# comentario\n{"lives": 5, "seed": 7, "foo": 1}\n'
    cfg = load_config(write(tmp_path, "c.json", content))
    assert cfg.lives == 5
    assert cfg.seed == 7
    assert cfg.points_per_ghost == 200


def test_warnings_go_to_stderr(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    load_config(write(tmp_path, "c.json", '{"lives": "tres"}'))
    assert "lives" in capsys.readouterr().err