from dataclasses import dataclass, field
from typing import Any
import json
import sys


# Valores para los métodos numéricos
wlo = 14
whi = 60
hlo = 10
hhi = 50
lo_live = 1
hi_live = 99
def_pacgum = 42
lo_pacgum = 0
hi_pacgum = 99
lo_sppacgum = 0
hi_sppacgum = 150
lo_ghost = 0
hi_ghost = 676767
lo_seed = 1
hi_seed = 999999
lo_lvl = 10
lo_lvl_time = 10
hi_lvl_time = 600


class ConfigError(Exception):
    """Class used to control errors that crashes the program"""


@dataclass
class LevelConfig():
    """Size of one level."""

    width: int = 14
    height: int = 10


def fill_levels(levels: list[LevelConfig]) -> list[LevelConfig]:
    """Complete a level list up to the minimum number of levels.
    Default levels are appended in place until the list
    has at least 10 levels."""

    while len(levels) < lo_lvl:
        levels.append(LevelConfig())
    return levels


def return_levels() -> list[LevelConfig]:
    """Returns a new list with the default levels."""

    return fill_levels([])


@dataclass
class GameConfig():
    """All the game parameters, with their default values."""

    levels: list[LevelConfig] = field(default_factory=return_levels)
    highscore_filename: str = "Billy_Mitchell_type_aaah.json"
    lives: int = 3
    pacgum: int = 42
    points_per_pacgum: int = 10
    points_per_super_pacgum: int = 50
    points_per_ghost: int = 200
    seed: int = 42
    level_max_time: int = 90


def strip_comments(text: str) -> str:
    """Blank out the comment lines of a JSON text.
    A line whose first non-blank character is ``#`` is replaced by an
    empty line. Lines are not removed, so the line numbers reported
    by the JSON parser match the original file."""

    stripped: list[str] = text.splitlines()

    result: list[str] = []
    for line in stripped:
        if line.lstrip().startswith("#"):
            result.append("")
        else:
            result.append(line)

    new_text: str = "\n".join(result)

    return new_text


def get_int(data: dict[str, Any], key: str, default: int, lo: int, hi: int, warnings: list[str]) -> int:
    """Read an integer from ``data`` and clamp it to a valid range."""

    if key not in data:
        warnings.append(f"value not detected in data: {key}. Default'll be used")
        return default
    value = data[key]

    if not isinstance(value, int) or isinstance(value, bool):
        warnings.append(f"value content: {key} is not bool or int. Default'll be used: {default}")
        return default
    if value < lo:
        warnings.append(f"value size is too low: {key}. Lo will be used: {lo}")
        return lo
    if value > hi:
        warnings.append(f"value size is to high: {key}. Hi will be used: {hi}")
        return hi

    return value


def get_str(data: dict[str, Any], key: str, default: str, warnings: list[str]) -> str:
    """Read a non-empty string from ``data``. If the key is missing,
    ''default'' is returned."""
    if key not in data:
        warnings.append(f"value not detected in data: {key}. Default'll be used")
        return default
    value = data[key]

    if not isinstance(value, str):
        warnings.append(f"value is not a string: {key}. Default'll be used")
        return default

    if not value or value.strip() == "":
        warnings.append(f"empty string detected: {key}. Default'll be used.")
        return default

    return value


def parse_levels(raw: Any, warnings: list[str]) -> list[LevelConfig]:
    """Build the level list from the raw ``levels`` value. The result
    always has at least 10 levels."""

    if not isinstance(raw, list) or not raw:
        warnings.append("'levels' is missing or not a non-empty list.")
        return return_levels()  # Si no hay datos, devuelve niveles

    level_list: list[LevelConfig] = []

    for element in raw:        
        if isinstance(element, dict):    
            w = get_int(element, "width", wlo, wlo, whi, warnings)
            h = get_int(element, "height", hlo, hlo, hhi, warnings)

            new_level = LevelConfig(width=w, height=h)
            level_list.append(new_level)
        else:
            warnings.append("invalid level format.")
            continue

    return fill_levels(level_list)


def load_config(path: str) -> GameConfig:
    """Load and validate the game configuration file."""

    if not path.endswith(".json"):
        raise ConfigError("Invalid path extension.")

    try:
        with open(path, encoding="utf-8") as data:
            info = data.read()
    except (OSError, UnicodeDecodeError) as e:
        raise ConfigError(f"Cannot read '{path}': {e}") from e
    stripped_info = strip_comments(info)

    try:
        loaded_json = json.loads(stripped_info)
    except json.JSONDecodeError as e:
        raise ConfigError(f"Invalid JSON at line {e.lineno}, column {e.colno}: {e.msg}") from e

    if not isinstance(loaded_json, dict):
        raise ConfigError("invalid json file.")

    warnings: list[str] = []
    defaults = GameConfig()
    lives = get_int(loaded_json, "lives", defaults.lives, lo_live, hi_live,
                    warnings)
    pacgum = get_int(loaded_json, "pacgum", defaults.pacgum, def_pacgum,
                     def_pacgum, warnings)
    points_per_pacgum = get_int(loaded_json, "points_per_pacgum",
                                defaults.points_per_pacgum,
                                lo_pacgum, hi_pacgum, warnings)
    points_per_super_pacgum = get_int(loaded_json, "points_per_super_pacgum",
                                      defaults.points_per_super_pacgum,
                                      lo_sppacgum, hi_sppacgum, warnings)
    points_per_ghost = get_int(loaded_json, "points_per_ghost",
                               defaults.points_per_ghost,
                               lo_ghost, hi_ghost, warnings)
    seed = get_int(loaded_json, "seed", defaults.seed, lo_seed,
                   hi_seed, warnings)
    levels = parse_levels(loaded_json.get("levels"), warnings)
    level_max_time = get_int(loaded_json, "level_max_time",
                             defaults.level_max_time,
                             lo_lvl_time, hi_lvl_time, warnings)
    highscore_filename = get_str(loaded_json, "highscore_filename",
                                 defaults.highscore_filename, warnings)
    for warning in warnings:
        print(f"Warning: {warning}", file=sys.stderr)

    return GameConfig(levels=levels,
                      highscore_filename=highscore_filename,
                      lives=lives,
                      pacgum=pacgum,
                      points_per_pacgum=points_per_pacgum,
                      points_per_super_pacgum=points_per_super_pacgum,
                      points_per_ghost=points_per_ghost,
                      seed=seed,
                      level_max_time=level_max_time)
