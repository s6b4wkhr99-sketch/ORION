"""Volume 18 Section 12 — Recommendation confidence scoring."""

CONFIDENCE_CATEGORIES = (
    ("Very High", 85),
    ("High", 70),
    ("Medium", 50),
    ("Low", 30),
    ("Unknown", 0),
)


def confidence_category(score: float | None) -> str:
    if score is None:
        return "Unknown"
    value = max(0.0, min(100.0, score))
    for name, threshold in CONFIDENCE_CATEGORIES:
        if value >= threshold:
            return name
    return "Unknown"


def base_confidence(priority_score: float, email_index: float) -> float:
    """Map rule priority (0–1) to 0–100 base confidence."""
    return round(min(100.0, (priority_score * 70) + (email_index * 30)), 2)


def adjust_confidence(base: float, learning_adjustment: float) -> float:
    """Learning Second — adjust within ±15 points without overriding rules."""
    return round(max(0.0, min(100.0, base + learning_adjustment)), 2)
