# Volume 11 — Security, Permission & Governance

## Implementation

| Module | Purpose |
|--------|---------|
| `backend/app/security/roles.py` | Six approved system roles |
| `backend/app/security/permissions.py` | Section 5 permission matrix |
| `backend/app/security/password.py` | BCrypt + Section 13 password policy |
| `backend/app/security/audit.py` | Immutable `audit_log` table |
| `backend/app/security/upload_validation.py` | Filename + MIME validation |
| `backend/app/security/rate_limit.py` | API rate limiting |
| `backend/app/models/user.py` | User accounts with roles |
| `backend/app/models/intelligence_version.py` | Intelligence version history |

## Roles

System Administrator, Marketing Manager, Marketing Analyst, Data Administrator, Executive Viewer, Read Only

## Session

JWT Bearer token, 30-minute idle timeout (`jwt_expire_minutes=30`)

## Dev Credentials

| Email | Password | Role |
|-------|----------|------|
| user@company.com | Ceragem2026!Adm | System Administrator |
| manager@company.com | Ceragem2026!Mgr | Marketing Manager |
| analyst@company.com | Ceragem2026!Ana | Marketing Analyst |
| data@company.com | Ceragem2026!Dat | Data Administrator |

## Tests

```bash
cd backend && python tests/test_volume11_acceptance.py
```
