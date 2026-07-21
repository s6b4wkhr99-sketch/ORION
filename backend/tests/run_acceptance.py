"""Volume 12 Section 14 — Full regression test runner with report."""

import os
import subprocess
import sys
from datetime import datetime, timezone

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Volume 12 QA suite first, then volume-specific acceptance suites
REGRESSION_SUITES = [
    "test_phase3_postgres.py",
    "test_phase2_async_upload.py",
    "test_phase1_scale.py",
    "test_volume26_acceptance.py",
    "test_volume25_acceptance.py",
    "test_volume24_acceptance.py",
    "test_volume23_acceptance.py",
    "test_volume22_acceptance.py",
    "test_rfc001_acceptance.py",
    "test_volume21_acceptance.py",
    "test_volume20_acceptance.py",
    "test_volume19_acceptance.py",
    "test_volume18_acceptance.py",
    "test_volume17_acceptance.py",
    "test_volume16_acceptance.py",
    "test_volume15_acceptance.py",
    "test_volume14_acceptance.py",
    "test_volume13_acceptance.py",
    "test_volume12_qa.py",
    "test_volume11_acceptance.py",
    "test_volume10_acceptance.py",
    "test_volume09_acceptance.py",
    "test_volume08_acceptance.py",
    "test_api_v1.py",
    "test_executive_dashboard.py",
    "test_upload_profile.py",
    "test_duplicate_skip.py",
    "test_campaign_volume06.py",
]


def main() -> int:
    os.chdir(BACKEND)
    failed: list[str] = []
    passed: list[str] = []
    started = datetime.now(timezone.utc)

    print("=" * 60)
    print("CIOS Regression Test Suite — Volumes 12–26")
    print(f"Started: {started.isoformat()}")
    print("=" * 60)

    for name in REGRESSION_SUITES:
        path = os.path.join(os.path.dirname(__file__), name)
        if not os.path.isfile(path):
            print(f"\nSKIP {name} (not found)")
            continue
        print(f"\n=== {name} ===")
        result = subprocess.run([sys.executable, path], cwd=BACKEND)
        if result.returncode != 0:
            failed.append(name)
        else:
            passed.append(name)

    finished = datetime.now(timezone.utc)
    print("\n" + "=" * 60)
    print("REGRESSION REPORT")
    print("=" * 60)
    print(f"Passed: {len(passed)}/{len(passed) + len(failed)} suites")
    for name in passed:
        print(f"  ✓ {name}")
    for name in failed:
        print(f"  ✗ {name}")
    print(f"Duration: {(finished - started).total_seconds():.1f}s")

    if failed:
        print(f"\nFAILED suites: {', '.join(failed)}")
        return 1
    print("\nAll regression suites passed — release criteria met.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
