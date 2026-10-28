from dataclasses import dataclass
from typing import Any


MAX_ENTRIES = 10
MAX_NAME_LENGTH = 10


@dataclass
class ScoreEntry:
    name: str
    score: int


def validate_name(name: str) -> str:
    """Return the cleaned name or raise ValueError."""

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
    """Build valid entries from raw JSON data."""
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
    """Persistent top-10 table."""
    def __init__(self, path: str, max_entries: int = MAX_ENTRIES) -> None:
        pass

    def load(warnings):
        Si el fichero no existe, la lista queda vacía y no es un aviso: es la primera ejecución.
        Abre con with y encoding="utf-8", y captura OSError y UnicodeDecodeError.
        Captura json.JSONDecodeError: aviso y lista vacía. Piensa qué pasa con el fichero corrupto cuando luego se guarde: sobrescribirlo pierde lo que hubiera. Renombrarlo a .bak antes es una opción.
        Pasa lo leído por parse_entries, ordena de mayor a menor y recorta al máximo (el fichero puede venir con 500 entradas manipuladas)

    def add(name, score) -> bool:
        Valida el nombre y la puntuación (dejando que ValueError suba, o devolviendo False, lo que decidas).
        Inserta, reordena y recorta al máximo.
        Devuelve si la entrada ha quedado dentro de la tabla.

    def top() -> list[ScoreEntry]
        devuelve una copia, para que la UI no pueda alterar tu lista interna.

    def save(warnings) -> bool:
        Construye la lista de diccionarios a partir de las entradas.
        Escribe con with. Para ser robusto frente a un cierre a mitad de escritura, escribe en un fichero temporal en la misma carpeta y reemplázalo con os.replace. Es opcional, pero encaja con “robusto a errores de fichero”.
        Si salta OSError, aviso y devuelve False. Nunca debe propagar la excepción.