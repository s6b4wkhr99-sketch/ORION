"""Volume 13 Section 17 — Background worker (async upload queue)."""

import logging
import os
import time

from app.acquisition.upload_queue import run_worker_cycle
from app.providers.export_queue import run_export_cycle
from app.database import SessionLocal
from app.devops.logging_config import configure_logging

configure_logging()
logger = logging.getLogger("cios.worker")


def main() -> None:
    interval = int(os.getenv("WORKER_POLL_SECONDS", "5"))
    logger.info("CIOS worker started poll_interval=%ss", interval)
    while True:
        db = SessionLocal()
        worked = False
        try:
            worked = run_worker_cycle(db)
            if run_export_cycle(db):
                worked = True
            if worked:
                logger.info("worker processed upload job")
            else:
                logger.debug("worker heartbeat status=idle")
        except Exception:
            logger.exception("worker cycle failed")
            db.rollback()
        finally:
            db.close()
        if not worked:
            time.sleep(interval)


if __name__ == "__main__":
    main()
