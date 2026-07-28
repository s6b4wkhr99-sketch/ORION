# ORION DNA × Buyer Data — 적용 가능성 및 로드맵

**문서 유형:** 제품 기획 · 적용 가능성 검토 (사용자 승인 대기)  
**버전:** 0.1 (Saved Proposal)  
**작성일:** 2026-07-28  
**대상:** 경영진, 마케팅·전략, BI, 개발  
**관련 화면:** Mission Control — ORION DNA 위젯  
**관련 코드:** `executive_dashboard.py` (`_intelligence_radar`), `orion-dna-widget.tsx`, `purchase_dashboard.py`, `buyer_upload.py`

---

## 1. 요약 (한 줄)

> ORION DNA 6축에 “현재 구매자”를 **그대로 대체·합치기**는 데이터상 제한적(Prospect 매칭 ~1%)이지만, **Purchase DNA**를 나란히 두거나 매칭률 개선 후 **dual radar**로 비교하는 방식은 **충분히 적용 가능**하다.

**상태:** Phase 1 구현 **대기** — 사용자가 “기억해달라”고 요청하여 본 문서로 보존.

**사용자 결정 (2026-07-28):** Phase 3 **Dual radar (Prospect vs Buyer)** 는 캠페인 운영 중 **매칭률 30%+** 달성 이후 요청 예정. 지금은 착수하지 않음.

---

## 2. ORION DNA As-Is

| 항목 | 내용 |
|------|------|
| 데이터 소스 | Prospect 전체 — `CustomerIntelligence` (17단계 파이프라인) |
| 6축 | Purchase Power, Pain Index, Lifestyle, PRIZM Proxy, Ceragem Segment, Recommendation |
| 빌드 | `backend/app/campaign/executive_dashboard.py` → `_intelligence_radar()` |
| UI | `frontend/.../orion-dna-widget.tsx` — Mission Control `intelligence_radar` |
| 성숙도 | Prospect intelligence 기준 ~85% |

**핵심:** ORION DNA는 **예측·Prospect** 프로필이며, Purchase Intelligence(실구매)와 **목적이 다름**.

---

## 3. Buyer 데이터와 연결 고리

| 데이터 | 위치 | ORION DNA 관계 |
|--------|------|----------------|
| 실구매 row | `buyer_purchases` | SKU, state, email, channel |
| Prospect 매칭 | `matched_customer_id` | 있으면 → `CustomerIntelligence` 사용 가능 |
| GAP | Buyer Upload & GAP | SKU 분포·보정 (DNA와 별도) |
| Dedup | `source_row_key` (migration 0019) | 동일 row 재업로드만 skip |

### 3.1 로컬 DB 기준 스냅샷 (2026-07 검토)

| 지표 | 값 |
|------|-----|
| 구매 row | 5,289 |
| Prospect 매칭 row | 64 (**1.2%**) |
| 고유 구매 이메일 | 2,767 |
| 매칭된 고유 이메일 | **29 (1.0%)** |

→ 구매자 대부분은 Prospect DB에 없거나 이메일 미매칭. **6축 intelligence로 DNA “대체”는 현재 통계적으로 불가**에 가깝다.

---

## 4. 적용 방안 (우선순위)

### A. Dual-layer ORION DNA — Matched Buyers 오버레이

| | |
|--|--|
| **방법** | `matched_customer_id` → intelligence → `buildOrionDnaRadarFromCustomers()` (Recommendation Center 패턴) |
| **UX** | Prospect DNA(보라) + Actual Buyer DNA(초록) 이중 trace |
| **기술 난이도** | 낮음 |
| **데이터 적합성** | **낮음** (현재 ~29명) |
| **적용 시점** | Prospect–Buyer 이메일 매칭률 **30%+** 이후 |

### B. Purchase DNA — 별도 레이더 (**권장 · Phase 1**)

ORION DNA 6축과 **다른 축**, **100% 구매 데이터** 반영.

| 축 예시 | 계산 |
|---------|------|
| V-Series Share | V SKU 구매 비율 |
| M-Series Share | M SKU 구매 비율 |
| Brand Loyalty | purchases ÷ unique buyers (전국) |
| Product Trust | SKU×주 재구매 강도 |
| Shopify Share | 채널 비율 |
| Geographic Coverage | OTHER 제외 주 커버리지 |

| | |
|--|--|
| **기술 난이도** | 중간 — `purchase_dashboard` 확장 |
| **데이터 적합성** | **높음** (전체 buyer row) |
| **UX** | Mission Control ORION DNA: 탭 `Prospect` \| `Purchase` |
| **API** | `GET /dashboard/purchases` 확장 또는 `GET /dashboard/buyer-dna` |

### C. GAP 보정 — Recommendation 축만 calibrate

Buyer GAP reweighted SKU로 Recommendation 1축만 조정.

| | |
|--|--|
| **기술 난이도** | 중~高 |
| **데이터 적합성** | 중간 |
| **리스크** | 방법론·검증·설명 필요 |

### D. Buyer 이메일 Prospect 업로드 + 파이프라인

매칭률 상승 → A안 viable.

| | |
|--|--|
| **기술 난이도** | 중간 (업로드·파이프라인 已有) |
| **효과** | 매칭률 ↑ → dual radar 의미 ↑ |

---

## 5. 이미 있는 Purchase Intelligence (참고)

- Purchases by State (지도)
- Purchase Radar (Y: volume, X: switch / Product Trust)
- Brand Loyalty (지도 hover)
- Buyer Upload dedup (`source_row_key`)
- GAP 패널

**Gap:** Mission Control ORION DNA는 여전히 **Prospect-only**.

---

## 6. 권장 로드맵

| Phase | 내용 | 조건 |
|-------|------|------|
| **1** | Mission Control ORION DNA 토글 `Prospect` \| `Purchase` + Purchase DNA API/위젯 | **즉시 착수 가능** (사용자 승인 시) |
| **2** | 이메일 정규화·매칭률 KPI (`prospect_match_rate_pct`) Mission Control 표시 | 운영 개선 |
| **3** | Dual trace: Prospect vs Matched Buyers intelligence | **사용자 보류** — 캠페인 운영 중 매칭률 30%+ 달성 후 요청 |

---

## 7. 구현 시 주의

1. **Prospect DNA를 buyer-only로 대체하지 말 것** — 표본·방법론 왜곡.
2. Purchase DNA와 Prospect DNA **명칭·범례·툴팁** 분리 (`Purchases_by_State_and_Purchase_Radar_Plan.md`와 동일 원칙).
3. OTHER state (~35% buyer row) — Geographic Coverage 축 정의 시 정책 명시.
4. `matched_customer_id` dual radar는 **n 표본** 툴팁 필수.

---

## 8. 관련 문서

- `docs/Purchases_by_State_and_Purchase_Radar_Plan.md`
- `docs/17_Analytics_Executive_Intelligence.md`
- `docs/Other_Mac_Native_Troubleshooting.md` (v1.5.0, migrate 0019)

---

## 9. 결정 대기

- [ ] Phase 1 (Purchase DNA) 구현 승인
- [ ] Purchase DNA 6축 최종 확정
- [ ] Phase 2 일정 (매칭률 KPI)
- [x] Phase 3 (Dual radar) — **보류**: 캠페인 운영 중 매칭률 30%+ 이후 사용자 요청 시 착수
