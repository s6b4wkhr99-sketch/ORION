#!/usr/bin/env python3
"""Volume 28.1 Phase A/C — purge expired exports, temp files, and old upload archives."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.database import SessionLocal
from app.ops.maintenance import (
    cleanup_exports,
    cleanup_old_upload_archives,
    cleanup_temp_directories,
)


def main() -> int:
    db = SessionLocal()
    try:
        jobs, files = cleanup_exports(db)
    finally:
        db.close()

    temp_removed = cleanup_temp_directories()
    archive_removed = cleanup_old_upload_archives()

    print(
        "cleanup complete "
        f"exports_removed={jobs} export_files_removed={files} "
        f"temp_files_removed={temp_removed} upload_archives_removed={archive_removed}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
