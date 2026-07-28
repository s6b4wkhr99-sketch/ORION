# Purchases by State + Purchase Radar — 기획안 (지표 정의)

**문서 유형:** 제품 기획 · 지표 정의  
**버전:** 0.1 (Draft)  
**대상:** 경영진, 마케팅·전략, BI, 개발  
**데이터 소스:** `buyer_purchases` (Buyer Upload — 실구매 전용)  
**관련 화면:** Mission Control의 Opportunity by State / Opportunity Radar (**별도 모듈**, 혼동 금지)

---

## 1. 목적과 포지셔닝

### 1.1 왜 별도 화면인가

| Mission Control (Prospect) | Purchase Intelligence (Buyer) |
|----------------------------|-------------------------------|
| **Expected** Opportunity · TAR | **Actual** Purchases · 실적 |
| Intelligence Pipeline (PP, Pain, Lifestyle…) | 업로드된 **구매 사실** |
| “어디·누구에게 **캠페인**할까?” | “**이미** 어디서·무엇이 팔렸나?” |
| 260만 잠재고객 | 현재 ~5,289 구매 행 / ~2,767 고유 이메일 |

동일 UI 패턴(지도 + Radar)을 재사용하되, **제목·축·툴팁·KPI 명칭**은 반드시 **Actual / Purchase** 로 구분합니다.

### 1.2 비즈니스 질문

1. 어느 **주(State)** 에서 실제 구매가 집중되는가?
2. 주·SKU 조합에서 **어떤 제품**이 실적으로 강한가?
3. Shopify vs Legacy 등 **채널**별 구매 패턴은?
4. (선택) Prospect 대비 **실구매 GAP**은 어디서 발생하는가? — GAP은 보조 패널

### 1.3 권한·진입

- **메뉴 제안:** `Purchase Intelligence` 또는 Buyer Upload & GAP 하위 탭 `Overview`
- **RBAC:** `report_import` (Buyer Upload와 동일) 또는 신규 `purchase_intelligence`
- **Prospect Mission Control과 데이터 격리** — KPI 합산 없음

---

## 2. 데이터 범위 (As-Is)

### 2.1 집계 단위

| 엔티티 | 정의 |
|--------|------|
| **Purchase row** | `buyer_purchases` 1행 = 의자(chair) 구매 1건 (동일 이메일·동일 주문 다중 라인 가능) |
| **Unique buyer** | `DISTINCT email` (정규화된 이메일) |
| **State** | `buyer_purchases.state` — US 2-letter 또는 `OTHER` |
| **Product (SKU)** | `sku_token` → Master/Pause 표시명 매핑 (V4→Master S4 등) |
| **Channel** | `source_channel`: `shopify` \| `legacy` \| `generic` |

### 2.2 현재 보유 · 미보유

| 필드 | 상태 | Phase |
|------|------|-------|
| email, sku_token, state, product_raw, source_channel | ✅ 저장됨 | 1 |
| upload_id (배치 필터) | ✅ | 1 |
| matched_customer_id (Prospect 연결) | ✅ 64건 수준 | 1 (보조) |
| order_date / paid_at | ❌ DB 미저장 (원본 컬럼 존재 가능) | 2 |
| order_amount / revenue | ❌ DB 미저장 | 2 |
| zip_code | ❌ | 2 |
| Intelligence (PP, Pain, Opportunity Score) | ❌ Buyer 미적용 | — (본 화면에서 사용 안 함) |

### 2.3 기본 필터 (전 위젯 공통)

| 필터 | 옵션 | 기본값 |
|------|------|--------|
| **Buyer scope** | All buyer uploads · 단일 upload 배치 | All |
| **Channel** | All · Shopify · Legacy | All |
| **SKU family** | All · Master (V/S) · Pause (M) | All |
| **State quality** | Include OTHER · Exclude OTHER | Include (OTHER 별도 표시) |

---

## 3. KPI Row (상단 요약)

Mission Control KPI와 **명칭을 다르게** 정의합니다.

| KPI | 지표 ID | 정의 | 집계식 | 현재 DB 예시 |
|-----|---------|------|--------|--------------|
| **Total Purchases** | `purchase_row_count` | 의자 구매 **행** 수 | `COUNT(buyer_purchases.id)` | 5,289 |
| **Unique Buyers** | `unique_buyer_emails` | 고유 구매자 이메일 | `COUNT(DISTINCT email)` | 2,767 |
| **Top Purchase State** | `top_purchase_state` | 구매 **행** 수 최다 주 (`OTHER` 제외 옵션) | `ARGMAX(state, count)` | CA |
| **Top SKU (Actual)** | `top_sku_token` | 구매 행 수 최다 SKU | `ARGMAX(sku_token, count)` | V4 |
| **Shopify Share** | `shopify_purchase_pct` | Shopify 채널 구매 비율 | `shopify_rows / total_rows × 100` | ~69% |
| **Prospect Match Rate** | `prospect_match_rate_pct` | Buyer 이메일 중 Prospect 존재 비율 | `matched_emails / unique_emails × 100` | ~2.3% |

**표시하지 않을 KPI (Prospect 전용):** Expected Revenue, Predicted Conversion, Opportunity Customers, AI Confidence

---

## 4. Widget A — Purchases by State

### 4.1 역할

Mission Control **Opportunity by State**와 **동일 레이아웃**, **다른 의미**:  
주별 **실제 구매 분포** (예측 매출 아님).

### 4.2 제목·카피

| 요소 | 문구 |
|------|------|
| Title | **Purchases by State** |
| Subtitle | Actual chair purchases by geography (not expected revenue) |
| Legend | Purchase volume · Low → High |
| Link (선택) | View Purchase Detail → (주 drill-down 또는 Buyer GAP) |

### 4.3 지도 Choropleth — Primary Metric (택 1, UI 토글)

| Metric ID | 표시명 | 정의 | 색상 스케일 |
|-----------|--------|------|-------------|
| **`purchase_count`** (기본) | Purchase Count | 해당 주의 구매 **행** 수 | Min–Max 또는 quantile |
| **`unique_buyers`** | Unique Buyers | 해당 주의 고유 이메일 수 | 동일 |
| **`purchase_share_pct`** | Share of Purchases | `state_count / national_count × 100` | 0–100% |
| **`v_line_share_pct`** | V-Series Share | 해당 주 구매 중 `sku_token` ∈ {V4,V5,V6,V7,V9,S4} 비율 | 0–100% |

**OTHER 처리 (필수 UX):**

- 지도에는 **US 50+DC만** 색칠
- `OTHER`는 지도 **외부** “Unassigned location” 카드로 건수·비율 표시 (현재 ~35%)
- 필터 “Exclude OTHER” 시 분모·분자에서 제외하고 subtitle에 명시

### 4.4 Tooltip (주 hover)

```
{State Name} ({ST})
Purchases: {purchase_count} ({purchase_share_pct}% of total)
Unique buyers: {unique_buyers}
Top SKU: {top_sku_token} ({top_sku_count})
Channels: Shopify {n} · Legacy {n}
```

### 4.5 Drill-down (Phase 1.5)

- 주 클릭 → 우측 또는 하단 **State Purchase Detail**: SKU bar, channel split, sample `product_raw`

---

## 5. Widget B — Purchase Radar

### 5.1 역할

Opportunity Radar와 **동일 차트 타입**(Scatter/Bubble), **축 의미 전면 교체**:  
**Intelligence Opportunity Score 없음** — **실구매 볼륨·구조** 중심.

### 5.2 제목·카피

| 요소 | 문구 |
|------|------|
| Title | **Purchase Radar** |
| Subtitle | Y: Purchase volume score · X: switch axis (actual purchases, not intelligence) |
| Footer | Each bubble = one **State × Product** cell with purchase activity |

### 5.3 버블 단위 (Grain)

**1 bubble = 1 (state, product)** 쌍

- `state`: US code 또는 `OTHER` (OTHER는 지도와 동일 정책 — Radar에서 제외 또는 별도 “Unassigned” 점)
- `product`: `sku_token` → 표시명 (Master V9, Pause M6 …) — **Opportunity Radar와 동일 색상 범례** 재사용 가능

**최소 표시 임계:** `purchase_count >= 1` (Phase 1); 혼잡 시 `>= 3` 또는 Top N states

### 5.4 Y축 — Purchase Volume Score (고정)

| 항목 | 정의 |
|------|------|
| **Raw** | `purchase_count` (해당 state×product 구매 행 수) |
| **Display score (0–100)** | 코호트 내 **percentile rank** 또는 min-max normalize |

```
purchase_volume_score = percentile_rank(purchase_count within visible bubbles) × 100
```

| Tier (툴팁) | Percentile |
|-------------|------------|
| High | ≥ 67th |
| Medium | 34th – 66th |
| Low | < 34th |

> Opportunity Radar의 Y축(Intelligence Opportunity Score)과 **수식·데이터 소스 완전 분리**.

### 5.5 X축 — Switch Axis (탭 5종, Phase 1)

Mission Control과 **탭 UI 동형**, **지표만 교체**:

| Tab ID | Label | X Score (0–100) | 원천 · 계산 |
|--------|-------|-----------------|-------------|
| **`state_volume`** (기본) | State Purchase Index | 해당 **주 전체** 구매량의 national percentile | `percentile_rank( SUM(purchases) by state )` — 버블은 주 내 product이므로 **동일 주의 모든 버블이 같은 X** |
| **`sku_mix_v`** | V-Series Mix | 해당 state×product 셀에서 V계열 비중이 아니라, **해당 주**의 V-series purchase share | 주 단위: `V_purchases / all_purchases × 100` |
| **`sku_mix_m`** | M-Series Mix | Pause(M) 계열 구매 share (주 단위) | 동일 |
| **`channel_digital`** | Digital (Shopify) Share | 주 단위 Shopify 행 비율 × 100 | `shopify / (shopify+legacy+generic)` |
| **`buyer_density`** | Buyer Density | 주 단위 `unique_buyers / purchase_count` (repeat proxy) × scale | 0–100 normalize |

**Phase 2 X축 (데이터 확장 후):**

| Tab | 조건 |
|-----|------|
| **Purchase Era** | `paid_at` 저장 시 — 주별 최근 24개월 vs legacy 비율 |
| **Avg Order Value** | `order_amount` 저장 시 — 주×SKU 평균 금액 percentile |

### 5.6 버블 인코딩

| 채널 | 필드 |
|------|------|
| **Color** | Product (SKU) — `productColor()` 기존 범례 |
| **Size** | `purchase_count` (sqrt scale, min/max cap) |
| **Opacity** | `unique_buyers / purchase_count` (repeat buyers → 진하게, optional) |

### 5.7 Tooltip

```
{State} · {Product Label}
Purchases: {purchase_count}
Unique buyers: {unique_buyers}
Purchase volume score: {purchase_volume_score} (Y)
{Active X-axis label}: {x_score}
Share of national purchases: {national_share_pct}%
Channel: Shopify {n} · Legacy {n}
```

### 5.8 “Show all” / 필터

- SKU 범례 클릭 → product filter (Opportunity Radar 동작 동일)
- State multi-select (Top 10 by volume default + expand)

---

## 6. 보조 Widget (선택, Phase 1)

### 6.1 SKU Purchase Distribution (Bar)

- X: SKU (V4, V6, M6 …) · Y: purchase_count · % labels
- 필터 scope 반영

### 6.2 Channel Split (Donut)

- Shopify / Legacy / Generic — purchase_count

### 6.3 GAP Snapshot (링크만)

- “Compare to Prospect profile →” → 기존 **Buyer Upload & GAP** 리포트  
- 본 Overview에 GAP 수치 **중복 표시하지 않음** (목적 분리)

---

## 7. Prospect Intelligence와의 관계 (명시적 비적용)

| 항목 | Purchase Radar | Opportunity Radar |
|------|----------------|-------------------|
| Y축 | Purchase Volume Score | Intelligence Opportunity Score |
| X축 | State volume, SKU mix, Channel… | Lifestyle, PP, Pain, Digital, Brand |
| 데이터 | `buyer_purchases` | `customer_intelligence` + rollup |
| 매출 | ❌ (Phase 1) | Expected Revenue |
| 매칭 64건 Intelligence | **본 화면 미사용** | — |

**Matched buyer drill-down (별도 액션):**  
이메일 클릭 시 Prospect Intelligence 조회 — **예외적 64건만**, Radar 집계에는 포함하지 않음.

---

## 8. 데이터 품질 · 해석 가이드 (UI Disclaimer)

화면 하단 고정 1줄:

> Actual purchases from Buyer Upload. Does not include prospect forecasts. **{other_pct}%** of rows have unassigned state (OTHER). Intelligence scores are not applied to buyer records.

---

## 9. API · 집계 (개념 스키마, 구현 아님)

```
GET /api/v1/dashboard/purchases/executive
  ?upload_id=uuid|all
  &channel=shopify|legacy|all
  &exclude_other=true|false

Response:
  kpis: { purchase_row_count, unique_buyer_emails, top_purchase_state, ... }
  purchases_by_state: [{ state, purchase_count, unique_buyers, purchase_share_pct, top_sku, ... }]
  purchase_radar: [{
    state, product, sku_token,
    purchase_count, unique_buyers,
    purchase_volume_score,           // Y
    state_volume_score,              // X candidates
    v_series_share_score,
    m_series_share_score,
    shopify_share_score,
    buyer_density_score,
    national_share_pct,
    channel_breakdown: { shopify, legacy, generic }
  }]
  meta: { other_count, other_pct, buyer_upload_batches, as_of }
```

**캐시:** Buyer upload 완료 시 invalidate (Prospect dashboard cache와 **분리**).

---

## 10. Phase 로드맵

| Phase | 범위 |
|-------|------|
| **1** | KPI + Purchases by State (`purchase_count`) + Purchase Radar (Y volume, X state_volume / channel / SKU mix) |
| **1.5** | State drill-down, OTHER card, upload batch filter |
| **2** | Ingest `paid_at`, `order_amount`, `zip` → Era tab, AOV choropleth option, revenue-sized bubbles |
| **3** | Matched-buyer overlay (Prospect segment of **matched only**) — separate layer, not default |

---

## 11. 성공 기준 (기획)

1. 사용자가 **Expected vs Actual** 을 혼동하지 않는다 (명칭·subtitle·disclaimer).
2. CA·V4 등 **현재 CSV/XLSX에서 검증 가능한 패턴**이 지도·Radar에 재현된다.
3. OTHER 비율이 **항상 visible** — 잘못된 지역 전략 방지.
4. Prospect Mission Control **KPI·캐시·API에 영향 없음**.

---

## 12. 현재 데이터 sanity check (2026-07-28 기준)

| 검증 | 값 | 기획 반영 |
|------|-----|-----------|
| Total purchases | 5,289 | KPI · Radar population |
| Top state | CA (1,912) | Map peak |
| OTHER | 1,850 (35%) | Disclaimer + exclude filter |
| Top SKU | V4 (2,535) | Radar color dominance |
| Shopify share | 3,665 / 5,289 ≈ 69% | Channel tab · KPI |

---

**문서 위치:** `docs/Purchases_by_State_and_Purchase_Radar_Plan.md`  
**작성:** Le Frame / CIOS Product  
**상태:** Draft — 구현 전 검토용
