"""Datalogix categorical code interpretation."""

STRONG_CODES = {"X", "Y"}
WEAK_CODES = {"Z", "U", "0", ""}


def normalize_code(value) -> str:
    if value is None:
        return ""
    text = str(value).strip().upper()
    if text in ("NAN", "NONE", "NULL", "NA"):
        return ""
    return text


def income_signal_strength(code: str) -> float:
    """Datalogix estimated-income code → 0–1 purchase signal."""
    normalized = normalize_code(code)
    ranked = {
        "X": 1.0,
        "H": 0.82,
        "I": 0.76,
        "G": 0.70,
        "K": 0.64,
        "J": 0.58,
        "F": 0.52,
        "E": 0.46,
        "Y": 0.72,
        "U": 0.35,
        "Z": 0.10,
    }
    if normalized in ranked:
        return ranked[normalized]
    return signal_strength(normalized)


def signal_strength(code: str) -> float:
    code = normalize_code(code)
    if code == "X":
        return 1.0
    if code == "Y":
        return 0.7
    if code == "U":
        return 0.35
    if code == "Z":
        return 0.1
    return 0.0


def is_strong(code: str) -> bool:
    return normalize_code(code) in STRONG_CODES


def is_numeric_income(value) -> bool:
    if value is None:
        return False
    try:
        float(str(value).replace(",", "").replace("$", ""))
        return True
    except ValueError:
        return False


def parse_numeric(value) -> float | None:
    if value is None:
        return None
    try:
        return float(str(value).replace(",", "").replace("$", ""))
    except ValueError:
        return None


def is_categorical_code(value) -> bool:
    """Principle D-002: X/Y/Z/U are proprietary categories, never numeric."""
    if value is None:
        return False
    return normalize_code(value) in {"X", "Y", "Z", "U"}


def is_numeric_value(value) -> bool:
    if value is None or is_categorical_code(value):
        return False
    try:
        float(str(value).replace(",", "").replace("$", "").replace("%", "").strip())
        return True
    except ValueError:
        return False
