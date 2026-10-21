from dataclasses import dataclass, field
from typing import Any
import os
import json


wlo = 14
whi = 60
hlo = 10
hhi = 50

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
        warnings.append("value not detected in data. Default'll be used")
        return default
    value = data[key]

    if not isinstance(value, int) or isinstance(value, bool):
        warnings.append(f"value content: {value} is not bool or int. Default'll be used: {default}")
        return default
    if value < lo:
        warnings.append(f"value size is too low: {value}. Lo will be used: {lo}")
        return lo
    if value > hi:
        warnings.append(f"value size is to high: {value}. Hi will be used: {hi}")
        return hi

    return value


def get_str(data: dict[str, Any], key: str, default: int, warnings: list[str]) -> str:
    if key not in data:
        warnings.append("value not detected in data. Default'll be used")
        return default
    value = data[key]

    if not isinstance(value, str):
        warnings.append("value is not a string. Default'll be used")
        return default

    if not value or value.strip() == "":
        warnings.append("empty string detected. Default'll be used.")
        return default

    return value


def parse_levels(raw: Any, warnings: list[str]) -> list[LevelConfig]:
    if not isinstance(raw, list) or not raw:
        warnings.append("no raw data detected.")
        return list[LevelConfig]

    level_list: list[LevelConfig] = []
    for element in raw:
        if element is isinstance(element, dict):
            level_list.append(get_int(element, "width", wlo, wlo, whi, warnings))
            level_list.append(get_int(element, "height", hlo, hlo, hhi, warnings))
        else:
            warnings.append("invalid level format.")
            continue

    if len(level_list) < 10:
        i = 0
        while i < 10:
            level_list.append(list[LevelConfig])
            i += 1

    return level_list


def load_config(path: str) -> GameConfig:
    if not path.endswith(".json"):
        raise ConfigError("Invalid path extension.")

    try:
        with open(path, encoding="utf-8") as data:
            info = data.read()
            if not info or not path or not os.access(path, os.R_OK):
                raise OSError("invalid file access.")
            strip_comments(info)
    except ConfigError as e:
        print(f"Error: {e}")

    try:
        loaded_json = json.loads(info)
    except ConfigError as e:
        print(f"Error: line:{e.lineno}, col: {e.colno}")

    if loaded_json is not isinstance(loaded_json, dict):
        raise ConfigError("invalid json file.")

    warnings: list[str] = []
            

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
print(warnings)

print(return_levels()) """