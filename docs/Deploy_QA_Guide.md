# Deploy QA Guide (v1.2.0)

**Updated:** 2026-07-23

QA 환경 배포 절차 및 GitHub Actions 설정입니다.

---

## 1. 사전 준비 (QA 서버)

```bash
# 서버에 Docker + Docker Compose
sudo mkdir -p /opt/orion
sudo chown $USER /opt/orion
git clone git@github.com:s6b4wkhr99-sketch/ORION.git /opt/orion
cd /opt/orion
make setup-data          # Census/ACS 대용량 파일 (Git 미포함)
bash scripts/generate_secrets.sh   # JWT + DB password 생성
# deploy/env/qa.env 에 시크릿 반영
bash scripts/validate_deploy_env.sh deploy/env/qa.env qa
bash deploy/scripts/deploy_qa.sh
```

---

## 2. GitHub Secrets (Environment: `qa`)

Repository → **Settings → Environments → New environment: `qa`**

| Secret | 설명 |
|--------|------|
| `QA_HOST` | QA 서버 IP 또는 hostname |
| `QA_SSH_USER` | SSH 사용자 (예: `ubuntu`) |
| `QA_SSH_KEY` | Private key (PEM 전체) |
| `QA_APP_DIR` | (선택) 앱 경로, 기본 `/opt/orion` |
| `QA_PUBLIC_URL` | (선택) 외부 검증 URL, 예: `https://qa.orion.example.com` |

---

## 3. GitHub Actions 배포

**Actions → Deploy QA → Run workflow**

또는 `main` push 후 수동 트리거.

Workflow:
1. `validate-config` — compose + qa.env 검증
2. `deploy-qa` — SSH로 서버에서 `deploy_qa.sh` 실행

---

## 4. 수동 QA 배포 (서버에서)

```bash
cd /opt/orion
git pull origin main
export CIOS_BASE_URL=http://127.0.0.1:8080
bash deploy/scripts/deploy_qa.sh
```

---

## 5. Staging Docker smoke (로컬/CI)

```bash
make validate-compose              # config only
make compose-staging-smoke         # full up → validate → down (Docker 필요)
```

---

## 6. 프로덕션 시크릿

```bash
make generate-secrets
bash scripts/validate_deploy_env.sh deploy/env/production.env production
```

`production` profile은 placeholder가 있으면 **exit 1**.

---

## 관련 문서

- [Deploy_Prep_Quickstart.md](./Deploy_Prep_Quickstart.md)
- [Local_Operations_Quickstart.md](./Local_Operations_Quickstart.md)
