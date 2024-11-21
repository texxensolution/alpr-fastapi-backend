import re

def normalize_plate(plate: str) -> str:
    return re.sub(r'[^A-Za-z0-9]', '', plate).upper().strip()


