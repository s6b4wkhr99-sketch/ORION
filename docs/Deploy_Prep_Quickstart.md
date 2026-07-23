# Deploy Prep Quickstart (Phase C)

**Version:** 1.1.2 · **Updated:** 2026-07-23

배포 전 점검·백업·CI·원격 저장소 설정을 위한 1페이지 가이드입니다.

---

## 1. 릴리스 백업 (iCloud / 오프라인)

```bash
bash scripts/backup_release.sh
# 또는 출력 폴더 지정:
bash scripts/backup_release.sh "$HOME/Library/Mobile Documents/com~apple~CloudDocs/CIOS-Backups"
```

현재 `VERSION` 기준으로 `git archive` ZIP을 생성합니다.

---

## 2. Git 원격 저장소 (Phase C-1)

로컬에 `origin`이 없으면 GitHub/GitLab URL을 등록합니다.

```bash
bash scripts/setup_remote.sh git@github.com:YOUR_ORG/cios.git
git push -u origin main --tags
```

`gh` CLI가 있으면 저장소 생성 후 push도 가능합니다.

---

## 3. 프로덕션 시크릿 (Phase C-2)

`deploy/env/production.env`에서 **반드시** 교체:

| 변수 | 설명 |
|------|------|
| `JWT_SECRET` | 강력한 랜덤 문자열 (로컬 dev 값 재사용 금지) |
| `POSTGRES_PASSWORD` / `DATABASE_URL` | 프로덕션 DB 자격 증명 |
| `CORS_ORIGINS` | 실제 프론트 도메인 |

생성 예:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(48))"
```

배포 후 `AUTH_REQUIRED=true` 및 관리자 비밀번호 변경을 확인하세요.

---

## 4. Docker Compose 스테이징 검증 (Phase C-4)

```bash
bash scripts/validate_compose_staging.sh
# 전체 스택 (선택):
docker compose --env-file deploy/env/staging.env up -d --build
CIOS_BASE_URL=http://127.0.0.1:8080 bash deploy/scripts/deploy_validate.sh
docker compose --env-file deploy/env/staging.env down
```

---

## 5. CI / QA 배포 (Phase C-3)

| 항목 | 상태 |
|------|------|
| GitHub Actions `smoke` job | `make test-smoke` (PR/push) |
| Full acceptance (`test` job) | 기존 Volume 12/13 |
| `deploy-qa` | **활성화 (v1.2.0)** — GitHub Environment `qa` + secrets 필요 |
| `make setup-data` | Census/ACS 대용량 파일 다운로드 |
| `make generate-secrets` | JWT/DB password 생성 |
| `make compose-staging-smoke` | Docker full stack 검증 |

로컬에서 CI와 동일 smoke:

```bash
make test-smoke
make test-e2e    # dev 서버 + Playwright
```

---

## 6. Upload cancel API (Volume 27 §16)

| Method | Path | 설명 |
|--------|------|------|
| `POST` | `/api/v1/upload/{upload_id}/cancel` | `pending` 업로드 취소 |
| UI | Upload Center → Recent Uploads | **Cancel** 버튼 (v1.1.3) |

`processing` / `completed` 상태는 취소 불가. Worker는 `cancelled` 항목을 건너뜁니다.

---

## 7. 관련 문서

| 문서 | 용도 |
|------|------|
| [Local_Operations_Quickstart.md](./Local_Operations_Quickstart.md) | 로컬 dev |
| [31_Development_Status_Report.md](./31_Development_Status_Report.md) | 전체 현황 |
| [27_Development_Completion_Specification.md](./27_Development_Completion_Specification.md) | As-Built |
