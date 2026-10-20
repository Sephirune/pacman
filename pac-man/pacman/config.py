from dataclasses import dataclass, field
from typing import Any


class ConfigError(Exception):
    """Class used to control errors that crashes the program"""


@dataclass
class LevelConfig():
    width: int = 14
    height: int = 10


def return_levels() -> list[LevelConfig]:
    i = 0
    result = []
    while i < 10:
        levels = LevelConfig()
        result.append(levels)
        i += 1
    return result

@dataclass
class GameConfig():
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
        if key not in data:
            warnings.append("Warning: value not detected in data. Default'll be used")
            return default
        value = data[key]
        
        if not isinstance(value, int) or isinstance(value, bool):
            warnings.append(f"Warning: value content: {value} is not bool or int. Default'll be used: {default}")
            return default
        if value < lo:
            warnings.append(f"Warning: value size is too low: {value}. Lo will be used: {lo}")
            return lo
        if value > hi:
            warnings.append(f"Warning: value size is to high: {value}. Hi will be used: {hi}")
            return hi
        
        return value


def parse_levels(raw: dict[str, Any], warnings: list[str]) -> list[LevelConfig]:
    if not raw:
        warnings.append("Warning: no raw data detected.")


def load_config(path: str) -> GameConfig: ...       # orquesta todo """


""" print(strip_comments("#hola que tal"))
warnings: list[str] = []

result = get_int(
    data={"lives": 50},
    key="lives",
    default=3,
    lo=1,
    hi=99,
    warnings=warnings
)

print(result)
print(warnings) """

print(return_levels())