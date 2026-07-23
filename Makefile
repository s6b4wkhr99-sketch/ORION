.PHONY: postgres-up postgres-down setup-2_5m setup-local migrate init-postgres worker backend frontend dev dev-daemon dev-stop dev-status dev-restart test-smoke test-e2e test-phase3 backup backup-release restore archive-sqlite cleanup-storage nightly-maintenance weekly-maintenance storage-audit validate-compose

# CURDIR — spaces in path break abspath/dir (e.g. "Website Project/...").
ROOT := $(CURDIR)/

postgres-up:
	@if command -v docker >/dev/null 2>&1 || [ -x /Applications/Docker.app/Contents/Resources/bin/docker ]; then \
		docker compose -f "$(ROOT)docker-compose.postgres.yml" up -d; \
	elif PATH="/opt/homebrew/opt/postgresql@16/bin:$$PATH" pg_isready -h 127.0.0.1 -p 5432 >/dev/null 2>&1; then \
		echo "PostgreSQL already running on 127.0.0.1:5432 (native — Docker not required)"; \
	else \
		echo "Docker not found. Starting native PostgreSQL via Homebrew..."; \
		bash "$(ROOT)scripts/setup_2_5m_postgres.sh"; \
	fi

postgres-down:
	@if command -v docker >/dev/null 2>&1 || [ -x /Applications/Docker.app/Contents/Resources/bin/docker ]; then \
		docker compose -f "$(ROOT)docker-compose.postgres.yml" down; \
	else \
		echo "Docker not installed — native PostgreSQL left running."; \
		echo "To stop Homebrew Postgres: brew services stop postgresql@16"; \
	fi

setup-2_5m:
	bash "$(ROOT)scripts/setup_2_5m_postgres.sh"

setup-local:
	bash "$(ROOT)scripts/setup_local.sh"

migrate:
	cd "$(ROOT)backend" && . .venv/bin/activate && alembic upgrade head

init-postgres:
	cd "$(ROOT)backend" && . .venv/bin/activate && python scripts/init_postgres.py

worker:
	bash "$(ROOT)scripts/start_worker.sh"

backend:
	cd "$(ROOT)backend" && . .venv/bin/activate && uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

backend-fast:
	cd "$(ROOT)backend" && . .venv/bin/activate && \
		SKIP_PHYSICAL_SCHEMA=true DASHBOARD_CACHE_INVALIDATE_ON_STARTUP=false \
		uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

backend-native:
	cd "$(ROOT)backend" && . .venv/bin/activate && \
		uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 2

frontend:
	cd "$(ROOT)frontend" && npm run dev

dev:
	bash "$(ROOT)scripts/dev.sh" start

dev-terminal:
	bash "$(ROOT)scripts/dev.sh" start

dev-daemon:
	bash "$(ROOT)scripts/dev_daemon.sh" start

dev-stop:
	bash "$(ROOT)scripts/dev.sh" stop

dev-status:
	bash "$(ROOT)scripts/dev.sh" status

dev-restart:
	bash "$(ROOT)scripts/dev.sh" restart

frontend-build:
	cd "$(ROOT)frontend" && npm run build

test-smoke:
	bash "$(ROOT)scripts/run_test_smoke.sh"

test-e2e:
	cd "$(ROOT)frontend" && npm run test:e2e

test-phase3:
	cd "$(ROOT)backend" && . .venv/bin/activate && DATABASE_URL=$${DATABASE_URL:-postgresql+psycopg2://cios:cios_dev_password@127.0.0.1:5432/cios} python tests/test_phase3_postgres.py

backup:
	bash "$(ROOT)scripts/backup_local.sh"

backup-release:
	bash "$(ROOT)scripts/backup_release.sh"

validate-compose:
	bash "$(ROOT)scripts/validate_compose_staging.sh"

restore:
	bash "$(ROOT)scripts/restore_local.sh" --latest --yes

archive-sqlite:
	bash "$(ROOT)scripts/archive_legacy_sqlite.sh"

cleanup-storage:
	cd "$(ROOT)backend" && . .venv/bin/activate && python scripts/cleanup_storage.py

nightly-maintenance:
	cd "$(ROOT)backend" && . .venv/bin/activate && python scripts/nightly_maintenance.py

weekly-maintenance:
	cd "$(ROOT)backend" && . .venv/bin/activate && python scripts/weekly_maintenance.py

storage-audit:
	cd "$(ROOT)backend" && . .venv/bin/activate && python scripts/storage_audit.py
