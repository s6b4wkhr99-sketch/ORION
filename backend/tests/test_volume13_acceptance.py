"""Volume 13 Section 22 — Deployment & DevOps acceptance tests."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pathlib import Path

from fastapi.testclient import TestClient

from app.config import settings
from app.database import Base, SessionLocal, engine
from app.main import app
from app.processing.seed import seed_configuration
from app.security.users import seed_users

ROOT = Path(__file__).resolve().parents[2]


def _reset():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    seed_configuration(db)
    seed_users(db)
    db.close()


def run_tests():
    _reset()
    client = TestClient(app)
    passed = 0

    # DEVOPS-003 — configuration via environment (defaults present)
    assert settings.database_url
    assert settings.jwt_secret
    assert settings.upload_dir
    assert settings.export_path
    assert settings.log_level
    print("✓ DEVOPS-003 Runtime configuration via settings")
    passed += 1

    # Section 11 — Health endpoint
    r = client.get("/api/v1/health")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["success"] is True
    data = body["data"]
    assert "application" in data
    assert "database" in data
    assert data["database"]["status"] == "up"
    assert "storage" in data
    assert data["storage"]["status"] == "up"
    assert "version" in data
    assert data["version"] == settings.app_version
    assert "timestamp" in data
    print("✓ GET /api/v1/health — application, database, storage, version, timestamp")
    passed += 1

    # Section 19 — semantic versioning
    parts = settings.app_version.split(".")
    assert len(parts) == 3 and all(p.isdigit() for p in parts)
    print("✓ Section 19 Semantic versioning")
    passed += 1

    # Section 17 — Alembic migration present
    versions = ROOT / "backend" / "alembic" / "versions"
    assert (ROOT / "backend" / "alembic.ini").is_file()
    assert any(versions.glob("*.py"))
    print("✓ Section 17 Alembic migration tooling")
    passed += 1

    # Section 6 — Container artifacts
    assert (ROOT / "backend" / "Dockerfile").is_file()
    assert (ROOT / "frontend" / "Dockerfile").is_file()
    assert (ROOT / "docker-compose.yml").is_file()
    assert (ROOT / "docker" / "nginx" / "nginx.conf").is_file()
    print("✓ Section 6–7 Docker & Nginx container strategy")
    passed += 1

    # Section 8 — Environment templates
    for env in ("development", "qa", "staging", "production"):
        assert (ROOT / "deploy" / "env" / f"{env}.env").is_file()
    assert (ROOT / ".env.example").is_file()
    print("✓ Section 4 & 8 Environment definitions and templates")
    passed += 1

    # Section 9 — CI/CD pipeline definition
    assert (ROOT / ".github" / "workflows" / "cios-ci.yml").is_file()
    print("✓ Section 9 CI/CD pipeline (GitHub Actions)")
    passed += 1

    # Section 10 — Deployment validation script
    script = ROOT / "deploy" / "scripts" / "deploy_validate.sh"
    assert script.is_file()
    print("✓ Section 10 Deployment validation script")
    passed += 1

    # Section 15 — Backup script
    assert (ROOT / "backend" / "scripts" / "backup.sh").is_file()
    print("✓ Section 15 Backup strategy script")
    passed += 1

    # Section 21 — Runbook documented
    assert (ROOT / "docs" / "13_Deployment_DevOps_Specification.md").is_file()
    print("✓ Section 21 Operational runbook")
    passed += 1

    # Section 12 — Request logging middleware registered
    middleware_names = [m.cls.__name__ for m in app.user_middleware if hasattr(m, "cls")]
    assert "RequestLoggingMiddleware" in middleware_names
    print("✓ Section 12 Structured request logging")
    passed += 1

    print(f"\nVolume 13 DevOps: {passed}/{passed} acceptance checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_tests())
