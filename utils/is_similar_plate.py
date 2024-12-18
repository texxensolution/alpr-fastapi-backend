from rapidfuzz.distance import Levenshtein


def is_similar_plate(
    plate1: str,
    plate2: str,
    max_distance: int = 1
) -> bool:
    distance = Levenshtein.distance(plate1, plate2)

    return distance <= max_distance