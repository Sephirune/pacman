from dataclasses import dataclass
from typing import Any
import json
import os


MAX_ENTRIES = 10
MAX_NAME_LENGTH = 10


@dataclass(frozen=True)  # Clase inmutable
class ScoreEntry:
    """Highscore record. name must be valid
    and score a positive integer."""

    name: str
    score: int


def validate_name(name: str) -> str:
    """Return the cleaned name or raise ValueError.
    Strips whitespaces and checks that the result is not
    empty."""

    stripped: str = name.strip()

    if not stripped:
        raise ValueError("Empty string detected.")
    if len(stripped) > MAX_NAME_LENGTH:
        raise ValueError("Name too long!")

    for char in stripped:
        if not (char == " " or (char.isascii() and char.isalnum())): # No podemos usal alnum porque acepta las tildes, ñ, etc.
            raise ValueError(f"Invalid character detected: {char}")

    return stripped


def parse_entries(raw: Any, warnings: list[str]) -> list[ScoreEntry]:
    """Build valid entries from raw JSON data.
    Invalid items are skipped and reported."""

    if not isinstance(raw, list):
        warnings.append("raw is not a list.")
        return []
    if not raw:
        return []

    valid_entries: list[ScoreEntry] = []

    for element in raw:
        if isinstance(element, dict):
            name = element.get("name")
            if not isinstance(name, str):
                warnings.append(f"Name is not a string: {name}")
                continue

            try:
                valid_name = validate_name(name)
            except ValueError as e:
                warnings.append(f"Error validating name: {name}. Error: {e}")
                continue
            score = element.get("score")
            if not isinstance(score, int) or isinstance(score, bool) or score < 0:
                warnings.append(f"Invalid score detected: {score}")
                continue
            valid_entries.append(ScoreEntry(name=valid_name, score=score))
        else:
            warnings.append("Element is not a dict.")
            continue

    return valid_entries


class HighScores:
    """Persistent top-10 table. Entries are
    sorted by score. With equal scores, the older entry
    stays above the newer one."""

    def __init__(self, path: str, max_entries: int = MAX_ENTRIES) -> None:
        """Create an empty table linked to a file which will be readed
        by load."""

        self.path = path
        self.max_entries = max_entries
        self.entries: list[ScoreEntry] = []

    def _load(self, warnings: list[str]) -> None:
        """Load the table from disk. Missing files aren't errors
        (the first run starts with an empty table). Corrupt JSON files
        are moved to ''<path>.bak'' and the table starts empty."""

        if not self.path:
            return

        self.entries = []

        try:
            with open(self.path, encoding="utf-8") as f:
                loaded_json = json.load(f)
        except FileNotFoundError:
            return

        except (OSError, UnicodeDecodeError) as e:
            warnings.append(f"cannot read '{self.path}': {e}")
            return

        except json.JSONDecodeError as e:
            try:
                os.replace(self.path, self.path + ".bak")
                warnings.append(f"Corrupt json loaded. File moved to .bak to prevent errors: {e}")
            except OSError as backup_error:
                warnings.append(f"Error. Could not backup file: {backup_error}")
            return

        valid_json = parse_entries(loaded_json, warnings)
        self.entries = sorted(valid_json, key=lambda e: e.score, reverse=True)[:self.max_entries]

    def _add(self, name: str, score: int) -> bool:
        """Add a score keeping the table sorted and trimmed."""

        valid_name = validate_name(name)

        if not isinstance(score, int) or isinstance(score, bool) or score < 0:
            raise ValueError("Invalid score.")

        entry = ScoreEntry(valid_name, score)
        self.entries.append(entry)
        self.entries = sorted(self.entries, key=lambda e: e.score, reverse=True)[:self.max_entries]

        return any(e is entry for e in self.entries)

    def _top(self) -> list[ScoreEntry]:
        """Return a copy of the table. Best score wins."""

        return list(self.entries)

    def _save(self, warnings: list[str]) -> bool:
        """Write the table to disk. Writes to ''<path>.tmp'' first
        and then replaces the file so a failure never corrupts the
        previous file."""

        records: list[dict[str, Any]] = []
        tmp = self.path + ".tmp"
        for entry in self.entries:
            records.append({
                "name": entry.name,
                "score": entry.score
            })

        try:
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(records, f, indent=2)
            os.replace(tmp, self.path)
        except OSError as e:
            warnings.append(f"cannot save '{self.path}': {e}")
            try:
                os.remove(tmp)
            except OSError as remove_error:
                warnings.append(f"Error removing tmp: {remove_error}")
                pass
            return False

        return True
