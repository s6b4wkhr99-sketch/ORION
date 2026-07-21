# Volume 14 — System Administration & Operations Manual

Operational procedures for running Ceragem CIOS after deployment. See also [Volume 13 Deployment & DevOps](./13_Deployment_DevOps_Specification.md).

## Administrator Dashboard

**UI:** Settings → Open Administrator Dashboard (`/admin`)  
**API:** `GET /api/v1/admin/dashboard` (System Administrator only)

Displays: system status, CPU/memory, database, storage, API health, running campaigns, upload queue, scheduled jobs, notification center, operational metrics.

## Daily Operations (Section 2)

| Activity | How |
|----------|-----|
| System health | `GET /api/v1/health` or Admin Dashboard |
| Upload queue | Admin Dashboard → Upload Queue |
| Campaign status | Admin Dashboard → Running Campaigns |
| Dashboard health | `GET /api/v1/dashboard/executive` |
| API health | Admin Dashboard → API Health |
| Backup verification | Admin Dashboard → Backup status |
| Audit log review | `GET /api/v1/audit/logs` |

**Automated checklist:** `GET /api/v1/admin/checklists/daily`

### Daily Checklist (Section 4)

- Application running
- Database running
- File storage available
- Backup completed
- Dashboard updated
- Campaign jobs completed
- Scheduler running
- No critical alerts

## End-of-Day Checklist (Section 26)

`GET /api/v1/admin/checklists/end-of-day`

- Upload queue empty
- Campaign jobs completed
- Reports imported
- Dashboards updated
- Learning records generated
- Backup completed
- Audit logs recorded
- No critical alerts

## Weekly Operations (Section 5)

- Customer upload review — Upload Center / audit history
- Duplicate customer review — upload summary `duplicates_updated`
- Field mapping verification — Settings → Mapping version
- Campaign performance — Campaign Performance dashboards
- Forecast accuracy — Learning insights
- Learning database — `GET /api/v1/learning/insights`
- Storage cleanup — review `uploads/` and backups (90-day retention)
- Audit review — `GET /api/v1/audit/logs`

## Monthly Operations (Section 6)

- Database optimization — `VACUUM ANALYZE` (PostgreSQL, maintenance window)
- Index maintenance — DBA review
- Backup restore test — staging environment (Volume 13 DR)
- Performance benchmark — Volume 12 performance tests on staging
- Campaign trend analysis — ROI Center
- Rule version review — Settings → Rule Version (read-only in production)
- Provider mapping review — `GET /api/v1/admin/providers`
- Security review — Volume 11 RBAC audit

## Customer Upload Operations (Sections 7–8)

```
Receive file → Verify format → Upload → Validate mapping → Review validation
→ Generate intelligence → Verify customer count → Archive original file
```

Verify: customer count, duplicates, invalid emails, ZIP/state validation, Datalogix columns, PRIZM, recommendations, dashboard refresh.

## Campaign Operations (Sections 9–10)

Lifecycle: Planning → Forecast → Approval → Export → Execution → Import Results → Analysis → Learning

Administrator: monitor export, verify import, confirm dashboard refresh, archive campaign.

Report import: receive provider report → upload → validate → normalize → store → update dashboards → learning record.

## Intelligence Operations (Section 11)

Verify PRIZM proxy, Ceragem segment, purchase power, pain index, lifestyle, recommendation, campaign priority, expected revenue. **No manual editing permitted.**

## Dashboard Operations (Section 12)

Daily verify: Executive, Customer, Campaign, State, ZIP, ROI, Product dashboards — charts, tables, filters, exports, API response.

## User Administration (Section 13)

| Action | API |
|--------|-----|
| Create user | `POST /api/v1/admin/users` |
| Disable user | `POST /api/v1/admin/users/{email}/disable` |
| Reset password | `POST /api/v1/admin/users/{email}/reset-password` |
| Assign role | `PUT /api/v1/admin/users/{email}/role` |
| Activate user | `POST /api/v1/admin/users/{email}/activate` |
| Unlock account | `POST /api/v1/admin/users/{email}/unlock` |
| List users | `GET /api/v1/admin/users` |

Every action writes an immutable audit log entry.

## Roles (Section 14)

System Administrator, Marketing Manager, Marketing Analyst, Data Administrator, Executive Viewer, Read Only.

Role changes require System Administrator approval.

## Rule Administration (Section 15)

Business rules are **read-only** in production. Changes require business approval, version update, regression testing, and deployment approval.

## Provider Administration (Section 16)

Supported: Generic CSV, Klaviyo, Mailchimp, HubSpot, Attentive, Salesforce Marketing Cloud.

Periodically verify export templates, field mapping, import mapping, and provider compatibility.

## Database Administration (Section 17)

| Frequency | Task |
|-----------|------|
| Daily | Database health (`/api/v1/health`) |
| Weekly | Index review |
| Monthly | Vacuum/analyze (maintenance window) |
| Quarterly | Capacity planning |

Maintenance must not interrupt active production campaigns.

## Backup Administration (Section 18)

Daily: database, uploads, campaign reports, learning database (`backend/scripts/backup.sh`).

Weekly: backup integrity check. Monthly: restore test.

## Incident Management (Section 19)

| Severity | Examples |
|----------|----------|
| Critical | Database down, application down, auth failure, export failure |
| High | Business function unavailable |
| Medium | Limited function |
| Low | Cosmetic |

Critical incidents require immediate escalation (see Section 24).

## Operational KPIs (Section 25)

| Metric | Target |
|--------|--------|
| Platform availability | 99.9% |
| Dashboard response | < 2 seconds |
| Upload processing | < 15 seconds |
| Forecast generation | < 3 seconds |
| Export generation | < 10 seconds |
| Critical incident response | < 30 minutes |

Live samples: `GET /api/v1/admin/metrics`

## Maintenance Window (Section 21)

Preferred: **Sunday 02:00–05:00**. Production changes only during approved windows unless emergency authorized.

## Change Management (Section 22)

Every change: Change ID, requestor, approver, reason, risk assessment, rollback plan, deployment time, verification result.

## Support Escalation (Section 24)

Marketing Operations → System Administrator → Development Team → Product Owner → Executive Review

## Run Tests

```bash
cd backend && python tests/test_volume14_acceptance.py
cd backend && python tests/run_acceptance.py
```
