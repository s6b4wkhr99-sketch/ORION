# Deploy Production Guide (v1.3.0)

**Updated:** 2026-07-23

프로덕션 배포 절차입니다. **수동 확인(`DEPLOY`)** 이 필요합니다.

---

## 1. 사전 checklist

- [ ] `make generate-secrets` → `deploy/env/production.env` 반영
- [ ] `bash scripts/validate_deploy_env.sh deploy/env/production.env production` 통과
- [ ] `make setup-data` (서버에서 Census/ACS 파일)
- [ ] DNS / TLS / 방화벽 설정 완료
- [ ] QA에서 `deploy_validate.sh` 통과 이력

---

## 2. GitHub Secrets (Environment: `production`)

| Secret | 설명 |
|--------|------|
| `PROD_HOST` | 프로덕션 서버 hostname |
| `PROD_SSH_USER` | SSH 사용자 |
| `PROD_SSH_KEY` | Private key (PEM) |
| `PROD_APP_DIR` | (선택) 기본 `/opt/orion` |

---

## 3. GitHub Actions 배포

**Actions → Deploy Production → Run workflow**

| Input | 값 |
|-------|-----|
| `base_url` | 프로덕션 URL (예: `https://cios.company.com`) |
| `confirm` | **`DEPLOY`** (대문자 필수) |

Steps:
1. production env placeholder 검증
2. SSH → `deploy_production.sh`
3. `deploy_validate.sh` 외부 URL 검증

---

## 4. 수동 프로덕션 배포

```bash
cd /opt/orion
git pull origin main
make setup-data
export CIOS_BASE_URL=https://cios.company.com
bash deploy/scripts/deploy_production.sh
```

---

## 5. CI 파이프라인 (v1.3.0)

| Job | 내용 |
|-----|------|
| smoke | SQLite auth/RBAC/cancel |
| postgres-acceptance | PG migrate + Phase 3 |
| e2e | Playwright 5 tests |
| test | Volume 12–26 regression |
| docker-build | push 시 이미지 빌드 |

---

## 관련 문서

- [Deploy_QA_Guide.md](./Deploy_QA_Guide.md)
- [Deploy_Prep_Quickstart.md](./Deploy_Prep_Quickstart.md)
