# Volume 07 — API Specification

Base path: `/api/v1`

Implementation: `backend/app/api/v1/router.py`

Schemas: `backend/app/schemas/`

Services: `backend/app/api/services/`

Response envelope:

```json
{ "success": true, "data": {} }
{ "success": false, "message": "Error message" }
```

Authentication: JWT via `POST /api/v1/auth/login`. Default dev credentials in `README.md`.

Legacy `/api/*` routes in `backend/app/api/router.py` remain for backward compatibility.
