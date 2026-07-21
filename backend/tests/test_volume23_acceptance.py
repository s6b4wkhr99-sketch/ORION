"""Volume 23 — Project README acceptance tests."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.knowledge.registry import DOCUMENT_VOLUMES
from app.project_readme.registry import (
    BUSINESS_QUESTIONS,
    CORE_WORKFLOW,
    README_ACCEPTANCE_CRITERIA,
    README_VERSION,
    WHAT_CIOS_IS_NOT,
)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def run_tests():
    passed = 0
    readme_path = os.path.join(PROJECT_ROOT, "README.md")
    vol_path = os.path.join(PROJECT_ROOT, "docs", "23_Project_README.md")

    with open(readme_path, encoding="utf-8") as f:
        readme = f.read()

    assert "Customer Intelligence Operating System" in readme
    assert "CIOS is not a CRM" in readme
    assert "CIOS is not a Mass Email Provider" in readme
    for line in WHAT_CIOS_IS_NOT:
        assert line.replace(".", "") in readme.replace(".", "") or line in readme
    print("✓ Section 1 Project overview")
    passed += 1

    for question in BUSINESS_QUESTIONS:
        assert question.rstrip("?") in readme or question in readme
    print("✓ Section 2 Core business questions")
    passed += 1

    for step in CORE_WORKFLOW:
        assert step in readme
    assert "Auto Mapping Engine" in readme
    assert "Learning Database" in readme
    print("✓ Section 3 Core workflow")
    passed += 1

    assert "frontend/" in readme and "backend/" in readme and "docs/" in readme
    assert "pip install" in readme or "npm install" in readme
    print("✓ Repository structure and quick start")
    passed += 1

    assert "docs/README.md" in readme or "Volumes 01–24" in readme or "Volumes 01–23" in readme
    assert len(DOCUMENT_VOLUMES) >= 23
    assert any(v["volume"] == "23" for v in DOCUMENT_VOLUMES)
    print("✓ Documentation library indexed")
    passed += 1

    assert os.path.isfile(vol_path)
    with open(vol_path, encoding="utf-8") as f:
        vol_doc = f.read()
    assert README_VERSION.split()[0] == "Volume" or "Volume 23" in vol_doc
    print("✓ Volume 23 specification document on disk")
    passed += 1

    assert len(README_ACCEPTANCE_CRITERIA) == 6
    print("✓ Acceptance criteria registry")
    passed += 1

    print(f"\nVolume 23 Project README: {passed}/{passed} acceptance checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_tests())
