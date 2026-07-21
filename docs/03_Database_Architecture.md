# Volume 03 — Database Architecture

Version 1.0 — Approved

---

## Document Information

| Item | Value |
|------|-------|
| Document | Database Architecture |
| Version | 1.0 |
| Status | Approved |
| Project | Ceragem Customer Intelligence Operating System (CIOS) |
| Dependency | Volume 02 — Platform Architecture |

---

## 1. Purpose

Defines the logical database architecture for CIOS — entity relationships, data domains, and design principles before physical implementation (Volume 16).

---

## 2. Design Principles

| Principle | Description |
|-----------|-------------|
| Raw preservation | Original upload files and Datalogix categorical values are never altered |
| Separation of concerns | Customer data, intelligence, campaigns, and learning are distinct domains |
| Immutability | Upload history, audit logs, and learning records are append-only |
| Traceability | Every intelligence output links to rule versions and source data |
| Configuration-driven | Field mappings and provider templates stored in database, not hard-coded |

---

## 3. Data Domains

```
┌─────────────────┐   ┌──────────────────────┐   ┌─────────────────┐
│  Customer Data  │   │ Customer Intelligence │   │    Campaign     │
│  customers      │──►│ customer_intelligence │◄──│ campaign        │
│  raw_upload     │   │ recommendation        │   │ campaign_target │
│  upload_history │   └──────────────────────┘   │ campaign_report │
└─────────────────┘                             │ campaign_learning│
                                                └─────────────────┘
┌─────────────────┐   ┌──────────────────────┐   ┌─────────────────┐
│    Provider     │   │  Security & Audit    │   │     Export      │
│  provider       │   │  users, role         │   │  export_job     │
│  provider_map   │   │  permission          │   └─────────────────┘
└─────────────────┘   │  audit_log           │
                      └──────────────────────┘
```

---

## 4. Core Entities

### 4.1 Customer Domain

| Entity | Purpose |
|--------|---------|
| customer | Standardized customer profile (email PK, demographics, Datalogix) |
| upload_file (raw_upload) | Immutable raw upload metadata |
| upload_history | Processing audit trail per upload |

### 4.2 Intelligence Domain

| Entity | Purpose |
|--------|---------|
| customer_intelligence | Generated intelligence per customer (segments, indices, forecasts) |
| recommendation | Synced recommendation record with AI engine metadata |

### 4.3 Campaign Domain

| Entity | Purpose |
|--------|---------|
| campaign | Campaign definition, status, forecast |
| campaign_target | Audience linkage (customer ↔ campaign) |
| campaign_report | Normalized provider report summary |
| campaign_learning | Immutable learning record per completed campaign |

### 4.4 Integration Domain

| Entity | Purpose |
|--------|---------|
| provider | Provider master (Generic CSV, Mailchimp, Klaviyo, etc.) |
| provider_mapping | Export/import field mapping per provider |
| export_history (export_job) | Export job tracking |

### 4.5 Security Domain

| Entity | Purpose |
|--------|---------|
| user_account (users) | Authenticated users |
| role | Role definitions |
| permission | Module-level permissions |
| audit_log | Immutable system audit trail |

---

## 5. Reference Data

| Source | Purpose |
|--------|---------|
| ZIP Intelligence | Median income, population, regional characteristics |
| Datalogix codes | Categorical financial and household signals |
| Product catalog | Ceragem product definitions |
| Provider templates | Field mapping templates per ESP |

Loaded via `app.processing.seed` and configuration tables.

---

## 6. Relationships

```
customer 1──1 customer_intelligence
customer 1──* campaign_target *──1 campaign
campaign 1──* campaign_report
campaign 1──* campaign_learning
customer 1──1 recommendation
provider 1──* provider_mapping
```

Foreign keys and indexes defined in Volume 16 — Database ERD & Physical Schema.

---

## 7. Views & Analytics Layer

Logical analytics views (implemented physically in Volume 16):

| View | Purpose |
|------|---------|
| vw_customer_summary | Customer intelligence rollup |
| vw_campaign_summary | Campaign performance summary |
| vw_state_summary | State-level intelligence |
| vw_zip_summary | ZIP-level intelligence |
| vw_product_summary | Product performance |
| vw_roi_summary | ROI and Le Frame incentive |

Materialized views: `mv_campaign_forecast`, `mv_state_revenue`, `mv_product_performance`

---

## 8. Triggers

| Trigger | Purpose |
|---------|---------|
| trg_upload_history | Record upload completion |
| trg_intelligence_timestamp | Intelligence generation timestamp |
| trg_campaign_learning | Create learning on report import |
| trg_refresh_dashboard_views | Refresh materialized views |

---

## 9. Environment Strategy

| Environment | Database |
|-------------|----------|
| Development | SQLite (`backend/cios.db`) |
| Production | PostgreSQL 16 |
| Migrations | Alembic (`backend/alembic/`) |

Schema application: `app.schema.apply.apply_physical_schema()`

---

## 10. Dependencies

| Volume | Document |
|--------|----------|
| 09 | Field Mapping & Data Dictionary |
| 16 | Database ERD & Physical Schema |
| 10 | Business Rule Library |
