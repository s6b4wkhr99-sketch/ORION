#!/usr/bin/env python3
"""Volume 28.1 Phase C — storage audit report only."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.database import SessionLocal
from app.ops.maintenance import build_storage_audit, write_storage_audit_report


def main() -> int:
    db = SessionLocal()
    try:
        report_path = write_storage_audit_report(db)
        report = build_storage_audit(db)
    finally:
        db.close()
    print(json.dumps({"report_path": str(report_path), "summary": report}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
