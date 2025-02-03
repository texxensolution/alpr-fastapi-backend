import re
from rapidfuzz.distance import Levenshtein


def normalize_plate(plate: str) -> str:
    return re.sub(r'[^A-Za-z0-9]', '', plate).upper().strip()

def is_similar_plate(
    plate1: str,
    plate2: str,
    max_distance: int = 1
) -> bool:
    distance = Levenshtein.distance(plate1, plate2)

    return distance <= max_distance