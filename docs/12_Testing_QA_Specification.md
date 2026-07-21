# Volume 12 — Testing & Quality Assurance

## Run Tests

```bash
# Full regression (Volume 12 + all acceptance suites)
cd backend && python tests/run_acceptance.py

# Volume 12 QA catalog only
cd backend && python tests/test_volume12_qa.py
```

## Structure

| Path | Purpose |
|------|---------|
| `tests/qa_catalog.py` | TEST-* ID registry with spec traceability |
| `tests/qa_helpers.py` | Shared fixtures, data generators, timers |
| `tests/test_volume12_qa.py` | Sections 5–14 test cases |
| `tests/run_acceptance.py` | Regression runner + report |

## Test Categories (Section 3)

Upload, Mapping, Datalogix, Intelligence, Campaign, Dashboard, API, Security, Performance, Regression

## Test Data (Section 16)

Generated programmatically in `qa_helpers.py`:

- Small: 1–100 rows (default unit/integration)
- Medium: 200 rows (performance smoke in QA env)
- Large/Stress: reserved for staging environment

## Exit Criteria (Section 18)

Run `python tests/run_acceptance.py` — all suites must pass before release.

## UI Tests

Dashboard/API verification covers Section 10 server-side; frontend E2E reserved for staging with Playwright (not in MVP automated suite).
