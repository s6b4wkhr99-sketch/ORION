"""Volume 11 Section 16 — Simple in-memory rate limiting."""

import time
from collections import defaultdict

from fastapi import HTTPException, Request

from app.config import settings


class RateLimiter:
    def __init__(self, max_requests: int = 120, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._hits: dict[str, list[float]] = defaultdict(list)

    def check(self, request: Request) -> None:
        key = request.client.host if request.client else "unknown"
        now = time.time()
        window_start = now - self.window_seconds
        hits = self._hits[key]
        # Drop expired timestamps in-place (cheaper than rebuilding every request).
        if len(hits) > self.max_requests:
            hits[:] = [t for t in hits if t >= window_start]
        else:
            i = 0
            for t in hits:
                if t >= window_start:
                    hits[i] = t
                    i += 1
            del hits[i:]
        if len(hits) >= self.max_requests:
            raise HTTPException(
                status_code=429,
                detail={"success": False, "message": "Rate limit exceeded"},
            )
        hits.append(now)


rate_limiter = RateLimiter(
    max_requests=settings.rate_limit_max_requests,
    window_seconds=settings.rate_limit_window_seconds,
)
