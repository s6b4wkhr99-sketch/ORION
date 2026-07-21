# Volume 25 — Git Workflow & Release Management

**Version:** 1.0 · **Status:** Final

Git workflow, branching strategy, release lifecycle, and version governance for Ceragem CIOS. Registry: `backend/app/git_workflow/registry.py`

**Dependencies:** Volume 13 Deployment & DevOps · Volume 24 Development Convention

---

## 1. Purpose

Every code contribution shall follow this workflow.

## 2. Git Strategy

Simplified GitFlow:

```text
main
│
develop
│
feature/*
release/*
hotfix/*
```

## 3. Branch Definitions

| Branch | Purpose | Key Rules |
|--------|---------|-----------|
| `main` | Production-ready code | Protected; merge from release/hotfix only |
| `develop` | Integration branch | Feature merges; always buildable |
| `feature/*` | Individual work | From develop → back to develop |
| `release/*` | Release prep | QA, docs, perf; no new features |
| `hotfix/*` | Emergency fixes | From main → main + develop |

## 4. Branch Protection

Protected: `main`, `develop` — PR required, code review, CI pass, no force push, no direct commits.

## 5. Commit Convention

Format: `type(scope): description`

Types: `feat`, `fix`, `refactor`, `docs`, `style`, `test`, `build`, `chore`, `perf`

## 6. Pull Request Rules

Every PR includes: Summary, Business Purpose, Related Specification, Affected Modules, Testing Result, Checklist.

## 7. Merge Strategy

**Squash and Merge** — clean history, one feature per commit, easier rollback.

## 8. Semantic Versioning

`Major.Minor.Patch` — major = breaking; minor = new features; patch = bug fixes.

## 9–10. Release Lifecycle & Tags

Feature Development → Develop → Release Branch → QA → Approval → Production → Tag → Maintenance

Production tags: `v1.0.0`, `v1.0.1`, `v1.1.0` (immutable).

## 11. Release Notes

Version, Release Date, Summary, Features, Bug Fixes, Database Changes, API Changes, Known Issues, Documentation Updates.

## 12. Rollback Strategy

Triggers: critical bug, outage, security issue, database corruption.

Process: identify release → checkout previous tag → deploy previous image → restore DB if needed → validate → incident report.

Rollback script: `deploy/scripts/rollback.sh`

## 13. Documentation Synchronization

Every merged feature updates: relevant Volume, metadata, API docs, database docs, README when applicable.

## 14–15. CI/CD

PR checks: build, lint, unit/integration tests, API validation, security scan.

Pipeline: Git Push → CI Build → Tests → Docker Image → QA → Approval → Production.

Workflow: `.github/workflows/cios-ci.yml`

## 16. Code Ownership

| Module | Owner |
|--------|-------|
| Upload | Backend Team |
| Intelligence | AI Team |
| Dashboard | Frontend Team |
| Campaign | Marketing Platform Team |
| Provider | Integration Team |
| Database | Database Team |
| Infrastructure | DevOps Team |

## 17. Repository Standards

`README.md`, `LICENSE`, `CHANGELOG.md`, `docs/`, `metadata/`, `deployment/` (implemented as `deploy/`), `.env.example`, `.gitignore`

## 18. Definition of Done

Code · tests · docs · metadata · API · QA · PR approval · merged to develop.

## API

- `GET /api/v1/git-workflow`
- `GET /api/v1/git-workflow/compliance`

## Tests

```bash
cd backend && python tests/test_volume25_acceptance.py
```
