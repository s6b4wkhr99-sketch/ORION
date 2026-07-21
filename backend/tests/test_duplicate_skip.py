"""Email duplicate rows are skipped on upload; Datalogix refreshed on duplicate when enabled."""

import json
import os
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.acquisition.upload import process_upload, save_upload_file
from app.database import SessionLocal
from app.models.customer import Customer, CustomerDatalogix, CustomerIntelligence


def run_tests() -> int:
    tag = uuid.uuid4().hex[:8]
    emails = {
        "a": f"dup-skip-{tag}-a@test.com",
        "b": f"dup-skip-{tag}-b@test.com",
        "c": f"dup-skip-{tag}-c@test.com",
        "d": f"dup-skip-{tag}-d@test.com",
    }
    db = SessionLocal()
    try:
        csv1 = f"Email,State,ZIP Code\n{emails['a']},CT,06801\n{emails['b']},CT,06802\n"
        upload1 = process_upload(db, save_upload_file(csv1.encode(), "dup1.csv"), "dup1.csv")
        assert json.loads(upload1.summary_json)["rows_processed"] == 2

        csv2 = (
            "Email,State,ZIP Code\n"
            f"{emails['a']},CT,06801\n"
            f"{emails['b']},CT,06802\n"
            f"{emails['c']},CT,06803\n"
            f"{emails['a']},CT,06801\n"
        )
        upload2 = process_upload(db, save_upload_file(csv2.encode(), "dup2.csv"), "dup2.csv")
        summary = json.loads(upload2.summary_json)
        assert summary["rows_processed"] == 1, summary
        assert summary["duplicates_skipped"] == 3, summary
        assert summary.get("duplicates_updated", 0) == 0

        csv3 = (
            "Email,Datalogix - Net Worth Indicator,Datalogix - Gender\n"
            f"{emails['a']},Y,F\n"
            f"{emails['d']},Z,M\n"
        )
        upload3 = process_upload(db, save_upload_file(csv3.encode(), "dup3.csv"), "dup3.csv")
        summary3 = json.loads(upload3.summary_json)
        assert summary3["rows_processed"] == 1, summary3
        assert summary3["duplicates_skipped"] == 1, summary3
        assert summary3["duplicates_updated"] == 1, summary3

        dlx = (
            db.query(CustomerDatalogix)
            .join(Customer)
            .filter(Customer.email == emails["a"])
            .first()
        )
        assert dlx is not None
        assert dlx.net_worth == "Y"
        assert dlx.gender == "F"

        count = db.query(Customer).filter(Customer.email.in_(emails.values())).count()
        assert count == 4
    finally:
        db.close()

    print("PASS: duplicate emails skipped (in-file + existing DB)")
    print("PASS: Datalogix refreshed on duplicate re-upload")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_tests())
