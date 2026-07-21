"""Volume 13 Section 12 — Structured application logging."""

import logging
import sys
import time
from datetime import datetime

from app.config import settings
from app.utils.timezone import app_timezone


class CiosFormatter(logging.Formatter):
    _defaults = ("request_id", "user_id", "cios_module", "execution_ms")

    def format(self, record: logging.LogRecord) -> str:
        for key in self._defaults:
            if not hasattr(record, key):
                setattr(record, key, "-")
        return super().format(record)


def _est_log_time(secs: float | None = None) -> time.struct_time:
    when = datetime.fromtimestamp(secs if secs is not None else time.time(), tz=app_timezone())
    return when.timetuple()


def configure_logging() -> None:
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    root = logging.getLogger()
    if root.handlers:
        root.setLevel(level)
        return
    handler = logging.StreamHandler(sys.stdout)
    formatter = CiosFormatter(
        "%(asctime)s %(levelname)s %(name)s "
        "request_id=%(request_id)s user_id=%(user_id)s cios_module=%(cios_module)s "
        "execution_ms=%(execution_ms)s %(message)s"
    )
    formatter.converter = _est_log_time
    handler.setFormatter(formatter)
    root.addHandler(handler)
    root.setLevel(level)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
