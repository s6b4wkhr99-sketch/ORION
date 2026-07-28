# Ceragem CIOS / ORION — 시스템 소개서

**문서 유형:** 고객·의사결정자용 시스템 소개  
**버전:** 1.0 · **작성 기준:** Commercial Intelligence `2026.07`  
**대상 독자:** 경영진, 마케팅·전략 담당자, 캠페인 운영자, BI·분석팀  
**방법론:** Le Frame Customer Intelligence Methodology (Volume 20)

---

## 1. 이 문서의 목적

본 문서는 Ceragem **CIOS**(Customer Intelligence Operating System) — 프론트엔드 브랜드명 **ORION** — 을 **처음 도입하거나 의사결정에 활용하려는 고객**이 다음을 충분히 이해할 수 있도록 작성되었습니다.

- **왜** 이 시스템이 만들어졌는가 (개발 의도)
- **어떤 준비 과정**을 거쳐 Intelligence가 생성되는가
- **Intelligence는 어떤 로직**으로 구성되는가
- **어떤 Reference Data**를 근거로 분석하는가
- **일반 CRM·BI와 무엇이 다른가** (분별력)
- **대시보드의 숫자와 추천을 어떻게 해석**해야 하는가

> CIOS는 CRM이 아니며, 이메일 발송 플랫폼(ESP)도 아닙니다.  
> **고객 데이터를 “구매 가능성·수익·우선순위”로 변환하는 의사결정 운영체제**입니다.

---

## 2. 개발 의도와 목적

### 2.1 핵심 질문

Le Frame 방법론과 CIOS는 고려 기간이 긴(high-consideration) 웰니스·테라피 제품(마사지 체어, Pause M 라인 등) 마케팅에서 반복되는 질문에 답하기 위해 설계되었습니다.

| 질문 | CIOS의 답 |
|------|-----------|
| 누가 가장 구매할 가능성이 높은가? | Ceragem Segment, Purchase Power, Pain Index, Campaign Priority |
| 어느 주·ZIP을 우선해야 하는가? | State/ZIP Opportunity Score, Market·Metro Intelligence |
| 어떤 제품·메시지 방향인가? | Intelligence SKU, Message Direction, PRIZM Proxy |
| 예상 전환율·매출·인센티브는? | Baseline Conversion, Promo Uplift, Expected Revenue, Le Frame Incentive |
| 다음에 어떤 캠페인을 실행해야 하는가? | Mission Control, Opportunity Finder, AI Recommendation (규칙 우선) |

### 2.2 전통적 도구와의 역할 구분

| 도구 | 주로 답하는 것 |
|------|----------------|
| **CRM** | 고객은 **누구**인가 (연락처·이력 관리) |
| **이메일/ESP** | **누구에게** 메시지를 보냈는가 (발송·오픈율) |
| **일반 BI** | 과거 지표를 **어떻게** 집계·시각화할 것인가 |
| **CIOS / ORION** | **누구·왜·언제·어디·무엇으로·얼마의 매출**을 기대할 수 있는가 |

### 2.3 설계 철학 (Le Frame)

> *고객은 올바른 제품, 올바른 메시지, 올바른 타이밍이 올바른 고객과 만날 때 구매한다.*

CIOS는 이 철학을 **결정론적(deterministic) 규칙**과 **설명 가능한(explainable) Intelligence**로 구현합니다. 동일한 입력 데이터는 동일한 Intelligence 결과를 생성하며, 각 점수·추천에는 근거 규칙(Rule ID)과 신뢰도(confidence)가 함께 기록됩니다.

### 2.4 시스템 헌법 (23 Design Principles)

모든 기능은 Volume 26의 설계 원칙을 따릅니다. 의사결정자가 특히 알아두어야 할 원칙은 다음과 같습니다.

| 원칙 | 의미 (고객 관점) |
|------|------------------|
| Customer Intelligence First | 운영 편의보다 **구매 Intelligence**가 우선 |
| Business Rules Before AI | AI는 보조; **비즈니스 규칙이 최종 판단** |
| Recommendation Must Be Explainable | 모든 추천은 **What / Why / Rule / Confidence** 제공 |
| Deterministic Processing | 같은 데이터 → **같은 결과** (재현 가능) |
| Dashboards Are Intelligence Systems | 리포트가 아니라 **“다음에 무엇을 할 것인가”**에 답 |
| Geography Is Business Intelligence | ZIP·주는 주소가 아니라 **기회 지표** |
| High-Consideration Product Strategy | 신뢰·교육·상담 주기를 반영한 전략 |

---

## 3. 시스템 준비 과정 — 데이터에서 의사결정까지

CIOS를 “켜서 바로 쓰는 도구”가 아니라 **데이터 준비 → Intelligence 생성 → 집계·캐시 → 의사결정 UI**의 파이프라인으로 이해하는 것이 중요합니다.

### 3.1 전체 흐름

```
[1] Reference Data 준비 (Census, ACS, SKU, 세그먼트 마스터)
         ↓
[2] 고객 데이터 업로드 (Excel/CSV)
         ↓
[3] 자동 필드 매핑 (RFC-001 — 수동 매핑 없이 표준화)
         ↓
[4] 17단계 Intelligence Pipeline (고객 1명당 1회 계산)
         ↓
[5] CustomerIntelligence 저장 + UploadRollup 집계
         ↓
[6] Mission Control / Market Intelligence / Opportunity Finder
         ↓
[7] (선택) Audience Export → ESP → 캠페인 실행 → Learning
```

### 3.2 Phase A — 플랫폼·Reference Data 준비

| 단계 | 내용 | 고객이 알아야 할 점 |
|------|------|---------------------|
| 환경 구성 | PostgreSQL, 마이그레이션, RDL(Reference Data Library) 시드 | Intelligence의 **기준값·임계치·SKU**는 코드가 아닌 **Reference Table**에서 관리 |
| 지리 Reference | Census ZCTA(2020), ACS 2022 5년 추정치(B19013 소득) | ZIP별 **중위소득·프리미엄 ZIP** 판단의 공식 근거 |
| Metro Reference | CBSA Top 50 Metro, ZCTA↔CBSA 교차 | Metro Intelligence·히트맵의 **행정 구역 기준** |
| 상품 Reference | Master V/M/S 시리즈 SKU, MSRP, Standing Promo | **Intelligence SKU**와 **실제 Promo Outreach SKU** 구분의 기준 |

> Reference Data는 Git에 포함되지 않는 대용량 지리 파일(약 90MB+)은 `make setup-data`로 별도 확보합니다.

### 3.3 Phase B — 고객 데이터 수집·표준화

**Upload Center**를 통해 Excel/CSV를 업로드하면:

1. **헤더 자동 감지** — 컬럼명 변형을 alias 사전으로 해석  
2. **RFC-001 Auto Mapping** — Le Frame 표준 필드 사전에 자동 매핑  
3. **검증·표준화** — 이메일, ZIP, State, Datalogix 코드 등 정규화  
4. **Customer + CustomerDatalogix** 테이블 저장  

**중요:** Datalogix X/Y/Z/U 코드는 **범주형 문자열로 보존**됩니다. 숫자로 강제 변환하지 않으며, 이는 Purchase Power·PRIZM Proxy 규칙의 정확도를 보장합니다.

### 3.4 Phase C — Intelligence Pipeline (17단계)

업로드된 각 고객 행(row)에 대해 아래 순서로 Intelligence가 계산됩니다.  
구현: `backend/app/intelligence/pipeline.py` · 상세: Volume 29, 30

| # | 엔진 | 출력 예 |
|---|------|---------|
| 1 | Normalization | 내부 표준 필드 |
| 2 | Datalogix Engine | X/Y/Z/U 행동·인구통계 신호 |
| 3 | ZIP Intelligence | 소득·인구·프리미엄 ZIP·주 검증 |
| 4 | Geo Market | Metro tier, Brand enclave, Digital boost |
| 5 | Income Proxy | 상업 전처리 소득 프록시 |
| 6 | PRIZM Proxy | 9개 라이프스타일 클러스터 |
| 7 | Purchase Power | High / Medium / Low |
| 8 | Pain Index | 치료·통증 니즈 |
| 9 | Lifestyle | 웰니스 지향성 |
| 10 | Ceragem Segment | 5-tier (High+ ~ Low+) |
| 11 | Message Direction | Email / DM / Nurture 전략 |
| 12 | Sleep Segment | 수면 박탈 세그먼트 |
| 13–15 | Commercial Pre/Post | SKU, Standing Promo, 실효 가격 |
| 14 | Recommendation | Intelligence SKU + rationale |
| 16 | Forecast | baseline_conversion, promo_uplift, revenue |
| 17 | Framework v19 | 0–100 점수, Priority A–D, audit JSON |

결과는 **CustomerIntelligence** 테이블에 저장되며, 업로드 단위로 **UploadRollup** (주·ZIP·세그먼트·SKU별)이 사전 집계됩니다.

### 3.5 Phase D — 대시보드·의사결정

집계된 Intelligence는 Mission Control 등 UI로 제공됩니다. 대규모 데이터(260만+ 고객)에서는 **Rollup-first + Dashboard Cache** 아키텍처로 응답 속도를 확보합니다.  
캐시는 업로드·재계산 시 자동 무효화됩니다.

---

## 4. Intelligence 구성 로직

### 4.1 Intelligence 피라미드 (7 Layers)

Le Frame 방법론은 7개 Intelligence Layer로 구성됩니다. 각 Layer는 CIOS 모듈에 1:1 매핑됩니다.

| Layer | 명칭 | CIOS 모듈 | 비즈니스 가치 |
|-------|------|-----------|---------------|
| 1 | Raw Customer Data | Upload / Acquisition | 신뢰할 수 있는 입력 |
| 2 | Geographic Intelligence | ZIP Engine, Geo Market | **어디서** 기회가 있는가 |
| 3 | Behavioral Intelligence | Datalogix Engine | **누구**가 반응할 가능성이 있는가 |
| 4 | Commercial Intelligence | Calculation Framework, Commercial Engine | **무엇을·얼마에** 제안할 것인가 |
| 5 | Campaign Intelligence | Campaign Analytics | 캠페인 설계·실행 Intelligence |
| 6 | Executive Intelligence | Executive Dashboard | **경영 의사결정** KPI |
| 7 | Continuous Learning | Campaign Learning | 실행 결과 → 미래 Intelligence 개선 |

### 4.2 핵심 Intelligence 지표 — 의미와 해석

#### Purchase Power (구매력)

- **질문:** Ceragem 가격대 제품을 **감당할 수 있는가?**
- **입력:** Datalogix 소득·순자산·주택가치, ZIP 중위소득, Brand Familiarity
- **출력:** High / Medium / Low
- **의사결정:** High → Master V9/V7 등 프리미엄 SKU; Low → Pause M / Nurture 중심

#### Pain Index (통증·치료 니즈)

- **질문:** **치료적 필요**가 얼마나 높은가?
- **입력:** Datalogix 연령·세대, Chronic Pain Geo Reference, Ceragem Segment 교차
- **의사결정:** Pain High + PP High → Master V 치료 내러티브·DM 우선

#### Lifestyle Index (라이프스타일)

- **질문:** **웰니스·활동적 생활** 지향인가?
- **의사결정:** Lifestyle High → Pause M, 웰니스 메시지 적합

#### PRIZM Proxy (라이프스타일 클러스터)

- **주의:** Nielsen PRIZM 라이선스 데이터가 **아닙니다**.  
  Le Frame **내부 프록시 모델**로, Datalogix + ZIP + 규칙(025–033)에서 9개 세그먼트를 도출합니다.
- **세그먼트 예:** Established Elite, Wellness Seekers, Aging in Place, Caregiving Households 등
- **의사결정:** 메시지 톤·채널·교육 vs 프로모션 강도 힌트

#### Ceragem Segment (5-tier)

- **Le Frame 고유 세그먼트:** Purchase Power + Pain + Lifestyle **복합**
- **티어:** High+ · Mid+ · Mid · Low+ · Low (웰니스/통증 지수 조합)
- **의사결정:** High+ = 최우선 타겟; Low = 장기 Nurture

#### Digital Engagement & Brand Familiarity

- **Digital:** Datalogix 온라인 접근·리테일 카드 등 → 이메일/디지털 캠페인 적합도
- **Brand Familiarity:** Korean metro tier, Asian density geo → **브랜드·커뮤니티 친숙도** (Ceragem 시장 특화)

### 4.3 Intelligence SKU vs Promo Outreach SKU

의사결정자가 **반드시 구분**해야 하는 개념입니다.

| 구분 | 정의 | 예 |
|------|------|-----|
| **Intelligence SKU** | 규칙 엔진이 **적합하다고 판단한** 제품 | Pause M6s (추천) |
| **Promo Outreach SKU** | Standing Promo(SAVE20/30)가 적용되는 **실제 아웃리치 SKU** | Pause M6 + SAVE20 |

Intelligence는 “이 고객에게 어떤 제품군이 맞는가”를 말하고, Outreach SKU는 “현재 프로모션 정책 하에 실제로 어떤 SKU로 접촉하는가”를 말합니다.

### 4.4 Opportunity Score (기회 점수)

주(State)·ZIP·레이더 차트에서 **우선순위 랭킹**에 사용됩니다.

**State/Radar 혼합 (개념):**

```
Intelligence Blend = 0.22×Pain + 0.20×PP + 0.18×Lifestyle + 0.20×Brand + 0.20×Digital
Opportunity Score = Blend×55% + Revenue Share×25% + Conversion×15% + Product Fit (최대 18)
```

ZIP 변형은 가중치가 다릅니다(PP 24%, Priority 18% 등).  
구현: `backend/app/campaign/opportunity_score.py`

> **참고:** Opportunity Radar의 X축 spread는 **표시용**이며, Opportunity Score(Y) 계산값 자체는 변경하지 않습니다.

### 4.5 Forecast (매출·전환 예측)

| 지표 | 의미 |
|------|------|
| **Baseline Conversion** | 프로모션 없이 예상되는 전환율 |
| **Promo Uplift** | Standing Promo 적용 시 추가 전환 |
| **Predicted Conversion** | Baseline + Promo Uplift |
| **Expected Revenue** | 예측 주문 × 실효 고객 결제가 |
| **Le Frame Incentive** | Expected Revenue × 15% (Rule FOR-003) |

모든 Forecast는 **결정론적 규칙**이며, Volume 10 Business Rule Library에 수식이 정의되어 있습니다.

### 4.6 AI Recommendation — 규칙 우선 구조

Volume 18 AI Engine은 다음 순서로 동작합니다.

```
1. Mandatory Business Rules (필수 규칙 — AI가 override 불가)
2. Learning Layer (과거 캠페인 결과 가중)
3. AI Rank (보조적 순위 제안)
```

**고객 관점:** AI Confidence가 “Very High”여도, **규칙 위반 추천은 시스템이 허용하지 않습니다.**

---

## 5. Reference Data — 소스와 활용

Reference Data는 “분석의 재료”가 아니라 **판단의 기준(기준선)** 입니다. CIOS Reference Data Library(RDL)는 중앙 관리·버전 관리됩니다.

### 5.1 지리·인구 Reference

| 소스 | 원본 | CIOS 저장·활용 | 활용 Intelligence |
|------|------|----------------|---------------------|
| **Census ZCTA 2020** | `cb_2020_us_zcta520_500k` shapefile | `backend/data/geo/`, GeoJSON by state | Market/Metro choropleth, ZCTA→CBSA |
| **ACS 2022 5yr B19013** | Census ACS Table B19013 | `zip_intelligence.median_income` | Purchase Power, Premium ZIP Top 50 |
| **ACS Geography** | `acs2022_5yr_geography.dat` | ZIP income import linkage | ZIP Intelligence 정합 |
| **CBSA Top 50 Metro** | `cbsa_reference.py` | Metro rollups | Metro Intelligence |
| **Brand Familiarity Geo** | Korean metro tier, Asian density | Geo Market Signals | Brand Familiarity, Opportunity Score |
| **Chronic Pain Geo** | City/state pain tiers | Pain Index geo boost | Pain Index |

**활용 화면:** Market Intelligence (주별), Metro Intelligence (CBSA·ZIP 히트맵)

### 5.2 고객 행동 Reference (업로드 데이터)

| 소스 | 처리 원칙 | 활용 |
|------|-----------|------|
| **Datalogix X/Y/Z/U** | 범주형 **문자열 보존** (숫자 변환 금지) | PP, PRIZM Proxy, Digital, Lifestyle |
| **Email / ZIP / State** | 표준화·검증 | Targetable 판단, Geo Intelligence |
| **Buyer Upload & GAP** | (선택) 실구매 보정 | Forecast Accuracy, Learning |

### 5.3 Intelligence·상품 Reference (RDL 내부)

| Domain | 예시 | API |
|--------|------|-----|
| Product | Master V9/V7/V6/V5, Pause M10/M6/M6s/M4, S4 | `GET /api/v1/reference/products` |
| Intelligence Masters | PP/Pain/Lifestyle/Ceragem/PRIZM/Priority | `GET /api/v1/reference/segments` |
| Geographic | state_master, zip_master | `GET /api/v1/reference/geographic` |
| Campaign | campaign_type, message_type | Reference tables |
| Provider | Klaviyo, Mailchimp, HubSpot, Attentive, SFMC | `GET /api/v1/reference/providers` |

**거버넌스:** Reference 변경 시 Business Review → Architecture Review → Approval → Version Increment → Documentation Update (Volume 22)

### 5.4 Business Rule Library

모든 Intelligence 로직은 Rule ID로 추적됩니다.

| Prefix | 영역 | 예 |
|--------|------|-----|
| UP / VAL / MAP | Upload·Validation·Mapping | RFC-001 |
| ZIP / PRZ | Geographic, PRIZM | ZIP-001, PRZ-025 |
| PUR / PAI / LIF | Purchase Power, Pain, Lifestyle | PUR-010 |
| SEG / REC | Ceragem Segment, Recommendation | SEG-040 |
| CAM / FOR | Campaign, Forecast | FOR-003 (Le Frame 15%) |
| LRN | Learning | LRN-001 |

상세: Volume 10 · 구현: `backend/app/rules/library.py`

---

## 6. 의사결정 워크플로우 — 화면별 역할

프론트엔드 브랜드 **ORION**의 주요 메뉴와 **의사결정 목적**입니다.

### 6.1 Mission Control (`/mission-control`)

**역할:** 경영진·전략 담당자의 **Command Center**

| 위젯 | 의사결정 질문 |
|------|---------------|
| KPI Row | 전체 Expected Revenue, Targetable Customers, Predicted Conversion은? |
| Commercial Intelligence | Standing Promo 커버리지, 최고 마진 SKU는? |
| Opportunity by State | **어느 주**에 집중 투자할 것인가? |
| Opportunity Radar | Pain vs Revenue 관계에서 **이상치 기회**는? |
| Today's Top Opportunity | **오늘** 실행할 최우선 1건은? |
| Ceragem Distribution | 세그먼트 믹스가 전략과 맞는가? |
| Revenue Funnel | Opportunity → Engaged → Convert → Orders 단계별 규모는? |
| Recent Opportunities | ZIP/City 단위 Top 6 기회 |
| Intelligence Score Distribution | High/Medium/Low 고객 밴드 |
| ORION DNA | Pain, Lifestyle, PP, Digital, Brand, Recommendation **6축 프로필** |

### 6.2 Market Intelligence (`/market-intelligence`)

**역할:** **전국·주(State) 단위** 기회 개요 및 Deep Dive  
ZIP choropleth, 주별 KPI, Opportunity Score 맵

### 6.3 Metro Intelligence (`/metro-intelligence`)

**역할:** **CBSA(Metro) 단위** 분석 — Top 50 Metro  
ZIP-level heatmap, Metro 내 ZIP 상세

### 6.4 Opportunity Finder (`/opportunities`)

**역할:** **캠페인 시뮬레이션** — SKU·주·세그먼트 필터 → Phase 1/2 Forecast  
“이 조건으로 캠페인하면 얼마나 나올 것인가?”에 답

### 6.5 Administration & Export

| 기능 | 의사결정 연계 |
|------|---------------|
| Upload Center | 새 데이터 → Intelligence 재생성 |
| SKU Catalog | 상품·프로모션 Reference 관리 |
| Audience Export | Intelligence 기반 **ESP 타겟 리스트** 출력 |
| Commercial Simulator | Forecast What-if |
| User Management | RBAC — 메뉴·Export 권한 |

---

## 7. 분별력 — CIOS를 적용할 때 기대할 수 있는 것

### 7.1 일반 BI / CRM 대비

| 일반 도구 | CIOS / ORION |
|-----------|--------------|
| 과거 실적 리포트 | **다음 액션** 추천 |
| 오픈율·클릭율 중심 | **구매 Intelligence** 중심 |
| 블랙박스 ML 세그먼트 | **Rule ID + factor + confidence** 설명 |
| 수동 필드 매핑 | **RFC-001 자동 매핑** |
| 단일 제품 푸시 | **High-consideration** 주기·Nurture 반영 |
| Revenue = List × Price | **Baseline + Promo Uplift** 분리, 실효 결제가 |
| CRM = 고객 관리 | **Intelligence OS** = 의사결정 OS |

### 7.2 Ceragem·Le Frame 특화 분별력

1. **Ceragem 5-tier Segment** — PP + Pain + Lifestyle 복합 (범용 RFM 아님)  
2. **PRIZM Proxy + Datalogix + Brand Familiarity** — 한인·웰니스 시장 corridor 반영  
3. **Intelligence SKU ≠ Outreach SKU** — 프로모션 정책과 추천의 분리  
4. **Geography as Opportunity** — ZIP/State를 **매출 기회 지표**로 모델링  
5. **Le Frame 15% Incentive** — Expected Revenue 기반 인센티브 Forecast 내장  
6. **Learning Loop** — 캠페인 Report Import → 미래 가중치 (과거 Intelligence는 불변)

### 7.3 신뢰할 수 있는 의사결정을 위한 체크리스트

의사결정 전 아래를 확인하십시오.

- [ ] **데이터 최신성:** 마지막 Upload 일시, Intelligence 재계산(`commercial_version`)  
- [ ] **Targetable 범위:** 이메일 보유 고객만 캠페인 Reachable  
- [ ] **Confidence 레벨:** AI Confidence Moderate/Low 시 규칙 근거(`framework_json`) 확인  
- [ ] **Promo 정책:** Standing Promo 변경 시 Commercial 재계산 필요  
- [ ] **지리 Reference:** `make setup-data` 미실행 시 ZIP income·choropleth 제한  
- [ ] **Rollup vs Raw:** 대시보드는 Rollup-first; 고객 단위 drill-down은 별도 API

---

## 8. 주요 KPI 해석 가이드 (Mission Control)

| KPI | 필드 | 해석 |
|-----|------|------|
| Expected Revenue | `expected_revenue` | Intelligence Forecast 합산 **예상 매출** |
| Opportunity Customers | `targetable_customers` | 이메일 보유 **도달 가능** 고객 수 |
| Predicted Conversion | `predicted_conversion_rate` | Baseline + Promo Uplift **집계 전환율** |
| Top Opportunity State | `top_opportunity_state` | Opportunity Score **최상위 주** |
| AI Confidence | intelligence_radar 파생 | Very High / High / Moderate / Low |
| Revenue Funnel | UI stages | Opportunity → Engaged(28.3%) → Likely(7.9%) → Orders |

**Intelligence Score Distribution:** High(80–100) / Medium(50–79) / Low(0–49) 고객 비율 — **캠페인 난이도·Nurture 비중** 판단에 활용

---

## 9. 지속적 개선 (Learning Loop)

```
Customer Upload → Intelligence → Recommendation → Campaign → Export
       ↑                                              ↓
       └──────── Learning ← Campaign Report Import ←┘
```

- **Learning은 미래 Intelligence를 개선**합니다.  
- **과거 Intelligence 기록은 수정하지 않습니다** (Principle 11).  
- Forecast Accuracy = Actual ÷ Expected — 경영진 KPI로 추적 (Volume 17)

---

## 10. 시스템 성숙도 및 범위 (현재)

| 항목 | 상태 |
|------|------|
| Local Native Pilot | 운영 가능 (~260만 고객 DB 검증) |
| Intelligence Pipeline 17단계 | 구현 완료 |
| Mission Control / Market / Metro / Opportunity Finder | 구현 완료 |
| Campaign OS (Learning, Report Import) | 구현 — 배포 시 `SHOW_CAMPAIGN_MODULES`로 노출 제어 |
| ORION Enterprise Blueprint | **별도 로드맵** — 현재 제품은 CIOS + ORION UX |
| Production Deploy | CI/CD·Deploy Guide 준비 (Volume Deploy Production Guide) |

---

## 11. 관련 문서 (심화 참조)

| 문서 | Volume | 주제 |
|------|--------|------|
| Executive Proposal | 01 | 비즈니스 케이스 |
| Platform Architecture | 02 | 모듈·데이터 흐름 |
| Intelligence Engine | 04 | 엔진 개요 |
| Business Rule Library | 10 | Rule ID·수식 |
| AI Recommendation Engine | 18 | Rule-first AI |
| Calculation Framework | 19 | 점수·confidence·audit |
| **Le Frame Methodology** | **20** | **7 Layer 방법론 (핵심)** |
| Reference Data Library | 22 | RDL 도메인 |
| Design Principles | 26 | 23 헌법 원칙 |
| Development Completion Spec | 27 | As-Built 기능 |
| **Intelligence Modeling Guide** | **29** | **Pipeline + Mission Control 매핑** |
| **Intelligence Logic & Formulas** | **30** | **로직·수식 1:1** |
| Local Operations Quickstart | — | 일상 운영 |
| Other Mac Operations Guide | — | 다른 Mac 설치 |

**API로 방법론 조회:** `GET /api/v1/methodology` · `GET /api/v1/knowledge`

---

## 12. 요약 — 의사결정자를 위한 한 페이지

**CIOS / ORION**은 Ceragem 고객 데이터를 **설명 가능한 구매 Intelligence**로 변환하고, **어디·누구·무엇·얼마**의 캠페인 결정을 지원하는 **Campaign Decision Intelligence** 플랫폼입니다.

- **준비:** Reference Data(Census·ACS·SKU) + 고객 Upload → 17단계 Pipeline  
- **로직:** Le Frame 7 Layer, Rule-first, Deterministic, Explainable  
- **Reference:** Census ZCTA/ACS, Datalogix, PRIZM Proxy, Ceragem 5-tier, Commercial Catalog  
- **분별력:** CRM/BI/ESP가 아닌 **의사결정 OS** — Geography·High-consideration·Promo 분리  
- **활용:** Mission Control에서 KPI 확인 → Market/Metro/Opportunity Finder에서 실행 설계 → Export

> 본 시스템의 숫자와 추천은 **“정답”이 아니라 규칙·데이터·버전에 기반한 Intelligence**입니다.  
> 중요한 경영 결정 전에는 **Confidence, Rule 근거, 데이터 최신성**을 함께 검토하십시오.

---

**문의 · 방법론:** Le Frame Inc.  
**문서 위치:** `docs/CIOS_System_Introduction.md`  
**Copyright © Le Frame Inc. All Rights Reserved.**
