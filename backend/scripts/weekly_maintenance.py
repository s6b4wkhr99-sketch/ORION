#!/usr/bin/env python3
"""Volume 28.1 Phase C — weekly maintenance (REINDEX + storage audit)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.database import SessionLocal
from app.devops.logging_config import configure_logging
from app.ops.maintenance import run_weekly_maintenance

configure_logging()


def main() -> int:
    db = SessionLocal()
    try:
        result = run_weekly_maintenance(db)
    finally:
        db.close()
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
