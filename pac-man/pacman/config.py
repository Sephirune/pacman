from dataclasses import dataclass, field


@dataclass
class ConfigError(Exception):
    """Class used to control errors that crashes the program"""


@dataclass
class LevelConfig():
    width: int = 14
    height: int = 10


@dataclass
class GameConfig():
    levels: int = field(default_factory=list[LevelConfig])
    highscore_filename: str = "Billy Mitchell type aaah"
    lives: int = 3
    pacgum: int = 42
    points_per_pacgum: int = 10
    points_per_super_pacgum: int = 50
    points_per_ghost: int = 200
    seed: int = 42
    level_max_time: int = 90


def strip_comments(text: str) -> list[str]:
    stripped: str = str.splitlines(text)

    empty: str = ""
    for line in stripped:
        result = []
        if line.lstrip().startswith("#"):
            result.append(empty)
        result.append(stripped)

    new_text: str = "\n".join(result)

    return new_text


""" def get_int(data, key, default, lo, hi, warnings) -> int:
    try:
        with open(data, encoding="utf-8") as content:
            if key not in data:
                print("Warning: data not detected in key. Default'll be used")
                return default
            readed = content.read()
            if readed is not bool or readed is not int:
                print("Warning: readed content is not bool or int. Default'll be used")
                return default
            if readed < lo:
                print("Warning: readed size is too low. Lo will be used")
                return lo
            if readed > hi:
                print("Warning: readed size is to high. Hi will be used")
                return hi """


def parse_levels(raw, warnings) -> list[LevelConfig]: ...


def load_config(path: str) -> GameConfig: ...       # orquesta todo


print(strip_comments("#hola que tal"))