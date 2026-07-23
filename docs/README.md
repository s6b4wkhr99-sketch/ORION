# Ceragem CIOS / Le Frame — Specification Index

**Active development baseline:** Le Frame (Volumes 01–28 in this folder)  
**ORION platform blueprint:** Deferred — see [`../../../ORION Project/ORION/`](../../../ORION%20Project/ORION/) (v1.0 COMPLETE)

Cursor and developers must follow the documents applicable to the **current development phase**.

---

## Le Frame — Active Development (Current)

| Volume | Document | Title |
|--------|----------|-------|
| 20 | [20_Le_Frame_Customer_Intelligence_Methodology.md](./20_Le_Frame_Customer_Intelligence_Methodology.md) | **Le Frame Customer Intelligence Methodology** |
| 01–19, 21–28 | See table below | CIOS Volumes (as-built + operational) |

> **Policy:** ORION implementation is **deferred**. Do not begin ORION Sprint 0.1 or ORION architecture migration unless explicitly re-authorized.  
> **Reference only:** ORION v1.0 blueprint lives in [`../../../ORION Project/ORION/README.md`](../../../ORION%20Project/ORION/README.md).

---

## ORION Enterprise Blueprint (Reference — Deferred)

All ORION specifications live in **[`../../../ORION Project/ORION/`](../../../ORION%20Project/ORION/)**:

| Item | Path |
|------|------|
| Project root | [ORION Project/README.md](../../../ORION%20Project/README.md) |
| Master index | [ORION/README.md](../../../ORION%20Project/ORION/README.md) |
| Constitution | [ORION/00_ORION_Constitution.md](../../../ORION%20Project/ORION/00_ORION_Constitution.md) |
| Volumes 01–09 | [ORION Project/ORION/](../../../ORION%20Project/ORION/) |
| Sprint 0.1 WBS | [ORION/Sprint_0.1_WBS.md](../../../ORION%20Project/ORION/Sprint_0.1_WBS.md) |
| ADRs | [ORION/adr/](../../../ORION%20Project/ORION/adr/) |

**ORION Documentation v1.0:** COMPLETE (Le Frame ©) — Adoption & Certification Vol 09 FINAL.

---

## Documentation Library (Volumes 01–28) — Le Frame / CIOS

| Volume | Document | Title |
|--------|----------|-------|
| 01 | [01_Executive_Proposal.md](./01_Executive_Proposal.md) | Executive Proposal |
| 02 | [02_Platform_Architecture.md](./02_Platform_Architecture.md) | Platform Architecture |
| 03 | [03_Database_Architecture.md](./03_Database_Architecture.md) | Database Architecture |
| 04 | [04_Intelligence_Engine.md](./04_Intelligence_Engine.md) | Intelligence Engine |
| 05 | [05_UX_UI_Specification.md](./05_UX_UI_Specification.md) | UX/UI Specification |
| 06 | [06_Campaign_Operating_System.md](./06_Campaign_Operating_System.md) | Campaign Operating System |
| 07 | [07_API_Specification.md](./07_API_Specification.md) | API Specification |
| 08 | [08_Cursor_Development_Guide.md](./08_Cursor_Development_Guide.md) | Cursor Development Guide |
| 09 | [09_Field_Mapping_Data_Dictionary.md](./09_Field_Mapping_Data_Dictionary.md) | Field Mapping & Data Dictionary |
| 10 | [10_Business_Rule_Library.md](./10_Business_Rule_Library.md) | Business Rule Library |
| 11 | [11_Security_Permission_Governance.md](./11_Security_Permission_Governance.md) | Security, Permission & Governance |
| 12 | [12_Testing_QA_Specification.md](./12_Testing_QA_Specification.md) | Testing & QA |
| 13 | [13_Deployment_DevOps_Specification.md](./13_Deployment_DevOps_Specification.md) | Deployment & DevOps |
| 14 | [14_System_Administration_Operations_Manual.md](./14_System_Administration_Operations_Manual.md) | System Administration & Operations |
| 15 | [15_Provider_Integration_Specification.md](./15_Provider_Integration_Specification.md) | Provider Integration |
| 16 | [16_Database_ERD_Physical_Schema.md](./16_Database_ERD_Physical_Schema.md) | Database ERD & Physical Schema |
| 17 | [17_Analytics_Executive_Intelligence.md](./17_Analytics_Executive_Intelligence.md) | Analytics & Executive Intelligence |
| 18 | [18_AI_Intelligence_Recommendation_Engine.md](./18_AI_Intelligence_Recommendation_Engine.md) | AI Intelligence & Recommendation Engine |
| 19 | [19_Intelligence_Calculation_Framework.md](./19_Intelligence_Calculation_Framework.md) | Intelligence Calculation Framework |
| 20 | [20_Le_Frame_Customer_Intelligence_Methodology.md](./20_Le_Frame_Customer_Intelligence_Methodology.md) | Le Frame Customer Intelligence Methodology |
| 21 | [21_Master_Index_Cross_Reference_Knowledge_Governance.md](./21_Master_Index_Cross_Reference_Knowledge_Governance.md) | Master Index & Knowledge Governance |
| 22 | [22_Reference_Data_Library.md](./22_Reference_Data_Library.md) | Reference Data Library |
| 23 | [23_Project_README.md](./23_Project_README.md) | Project README |
| 24 | [24_Development_Convention.md](./24_Development_Convention.md) | Development Convention |
| 25 | [25_Git_Workflow_Release_Management.md](./25_Git_Workflow_Release_Management.md) | Git Workflow & Release Management |
| 26 | [26_CIOS_Design_Principles.md](./26_CIOS_Design_Principles.md) | CIOS Design Principles |
| 27 | [27_Development_Completion_Specification.md](./27_Development_Completion_Specification.md) | Development Completion Specification (As-Built) |
| 28.1 | [28.1_Hybrid_Operations_Plan.md](./28.1_Hybrid_Operations_Plan.md) | Hybrid Operations Plan |
| 29 | [29_Intelligence_Modeling_Guide.md](./29_Intelligence_Modeling_Guide.md) | **Intelligence Modeling Guide (재구축 기준 · Mission Control 매핑)** |
| 30 | [30_Intelligence_Logic_and_Formulas.md](./30_Intelligence_Logic_and_Formulas.md) | **Intelligence Logic & Formulas (로직·수식·도표 상세)** |
| 31 | [31_Development_Status_Report.md](./31_Development_Status_Report.md) | **Development Status Report (개발 현황 · v1.1.0)** |

> **Live README:** Repository root [`README.md`](../README.md)  
> **Local ops:** [Local_Operations_Quickstart.md](./Local_Operations_Quickstart.md) · **Current status:** Volume 31 (v1.1.0)  
> **As-Built:** Volume 27 (v1.0.1) · **Intelligence rebuild baseline:** Volume 29 · **Formulas reference:** Volume 30  
> **Operations:** Volume 28.1

## API Base URL

```
/api/v1
```

## Response Envelope

```json
{ "success": true, "data": {} }
{ "success": false, "message": "Error message" }
```

## Run Tests

```bash
cd backend && source .venv/bin/activate && python tests/run_acceptance.py
```
