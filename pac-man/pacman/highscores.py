from dataclasses import dataclass, field
from typing import Any


MAX_ENTRIES = 10
MAX_NAME_LENGTH = 10


@dataclass
class ScoreEntry:
    name: str
    score: int


def validate_name(name) -> str:
    """Return the cleaned name or raise ValueError."""


def parse_entries(raw, warnings) -> list[ScoreEntry]:
    """Build valid entries from raw JSON data."""


class HighScores:
    """Persistent top-10 table."""
    def __init__(self, path: str, max_entries: int = MAX_ENTRIES) -> None:
