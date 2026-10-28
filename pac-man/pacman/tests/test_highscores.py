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