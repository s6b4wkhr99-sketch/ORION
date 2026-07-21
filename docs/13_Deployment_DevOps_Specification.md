# Volume 13 Section 21 — Operational Runbook

## Application Restart

```bash
docker compose restart backend frontend nginx
# Local dev:
./run_backend.sh   # terminal 1
./run_frontend.sh  # terminal 2
```

## Database Restart

```bash
docker compose restart postgres
docker compose exec backend alembic upgrade head
```

## Upload Failure Recovery

1. Check logs: `docker compose logs backend | grep upload`
2. Verify storage: `GET /api/v1/health` → `storage.status`
3. Clear partial upload via admin UI or `DELETE /api/v1/upload/{upload_id}`
4. Re-upload source file after fixing mapping/validation issues

## Campaign Recovery

1. Confirm campaign not in `completed`/`approved` immutable state
2. Review audit log: `GET /api/v1/audit/logs` (System Administrator)
3. Re-run forecast: `GET /api/v1/campaign/{id}/forecast`

## Export Recovery

1. Check export history: `GET /api/v1/export/history`
2. Regenerate: `POST /api/v1/export`
3. Download: `GET /api/v1/export/download/{export_id}`

## Rollback

```bash
deploy/scripts/rollback.sh <previous-image-tag>
```

Record rollback in release notes and audit trail.

## Backup Restore

```bash
# List backups
ls backend/backups/

# Restore SQLite (local)
cp backend/backups/<timestamp>/campaign_intelligence.db backend/campaign_intelligence.db

# Restore PostgreSQL
psql "$DATABASE_URL" < backend/backups/<timestamp>/database.sql
```

## Emergency Shutdown

```bash
docker compose down
# Preserve volumes: do not use -v unless data loss is acceptable
```

## Production Verification

After every deploy:

```bash
CIOS_BASE_URL=https://cios.company.com deploy/scripts/deploy_validate.sh
```

## Monitoring & Alerts (Section 13–14)

| Signal | Tooling |
|--------|---------|
| CPU / Memory / Disk | Docker stats, host monitoring |
| API response time | Request logs (`execution_ms`) |
| Auth failures | Audit log + 401 rate |
| Backup failure | Scheduler logs |

Alert channels: email (`ALERT_EMAIL`), Slack (`ALERT_SLACK_WEBHOOK`), webhook (`ALERT_WEBHOOK_URL`).

## Disaster Recovery (Section 16)

- **RPO:** 24 hours (daily backups)
- **RTO:** 4 hours (restore + validation)
- **Backup verification:** weekly restore to staging
- **DR validation:** monthly full recovery drill
