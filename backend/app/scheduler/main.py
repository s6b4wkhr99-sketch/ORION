"""Volume 13 Section 15 — Scheduled backup and maintenance tasks."""

import logging
import os
import subprocess
import time
from datetime import datetime, timezone

from app.devops.logging_config import configure_logging

configure_logging()
logger = logging.getLogger("cios.scheduler")


def run_backup() -> None:
    script = os.getenv("BACKUP_SCRIPT", "/app/scripts/backup.sh")
    if not os.path.isfile(script):
        logger.warning("Backup script not found: %s", script)
        return
    logger.info("Starting scheduled backup")
    subprocess.run(["bash", script], check=False)


def main() -> None:
    hour = int(os.getenv("BACKUP_HOUR_UTC", "2"))
    logger.info("CIOS scheduler started backup_hour_utc=%s", hour)
    last_run_day: str | None = None
    while True:
        now = datetime.now(timezone.utc)
        day_key = now.strftime("%Y-%m-%d")
        if now.hour == hour and day_key != last_run_day:
            run_backup()
            last_run_day = day_key
        time.sleep(60)


if __name__ == "__main__":
    main()
