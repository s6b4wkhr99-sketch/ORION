"""Volume 14 Section 20 — In-memory operational timing samples."""

from collections import defaultdict, deque
from threading import Lock

_lock = Lock()
_samples: dict[str, deque[float]] = defaultdict(lambda: deque(maxlen=200))

KPI_TARGETS = {
    "platformAvailability": 99.9,
    "dashboardResponseMs": 2000,
    "uploadProcessingMs": 15000,
    "forecastGenerationMs": 3000,
    "exportGenerationMs": 10000,
    "criticalIncidentResponseMinutes": 30,
}


def record_timing(category: str, duration_ms: float) -> None:
    with _lock:
        _samples[category].append(duration_ms)


def _percentile(values: list[float], pct: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    idx = min(len(ordered) - 1, int(len(ordered) * pct))
    return round(ordered[idx], 2)


def timing_summary(category: str) -> dict:
    with _lock:
        values = list(_samples[category])
    return {
        "count": len(values),
        "avgMs": round(sum(values) / len(values), 2) if values else None,
        "p95Ms": _percentile(values, 0.95),
        "lastMs": values[-1] if values else None,
    }


def operational_metrics() -> dict:
    return {
        "targets": KPI_TARGETS,
        "uploadTime": timing_summary("upload"),
        "forecastTime": timing_summary("forecast"),
        "dashboardLoadTime": timing_summary("dashboard"),
        "exportTime": timing_summary("export"),
        "importTime": timing_summary("import"),
        "apiResponseTime": timing_summary("api"),
        "databaseResponseTime": timing_summary("database"),
        "campaignCompletionTime": timing_summary("campaign"),
    }
