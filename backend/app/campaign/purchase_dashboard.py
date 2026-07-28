"""Purchase Intelligence dashboard — actual buyer_purchases aggregates (not prospect forecasts)."""

from __future__ import annotations

from collections import defaultdict

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.buyer import BuyerPurchase

US_STATES = frozenset(
    {
        "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", "HI", "ID", "IL", "IN", "IA",
        "KS", "KY", "LA", "ME", "MD", "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
        "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", "SD", "TN", "TX", "UT", "VT",
        "VA", "WA", "WV", "WI", "WY", "DC",
    }
)

SKU_TO_PRODUCT: dict[str, str] = {
    "V4": "Master S4",
    "V5": "Master V5",
    "V6": "Master V6",
    "V7": "Master V7",
    "V9": "Master V9",
    "S4": "Master S4",
    "M2": "Pause M2",
    "M4": "Pause M4",
    "M6": "Pause M6",
    "M6S": "Pause M6s",
    "M10": "Pause M10",
}

V_TOKENS = frozenset({"V4", "V5", "V6", "V7", "V9", "S4"})
M_TOKENS = frozenset({"M2", "M4", "M6", "M6S", "M10"})

RADAR_TOP_STATES_PER_SKU = 15


def _percentile_map(values: dict[str, float]) -> dict[str, float]:
    if not values:
        return {}
    items = sorted(values.items(), key=lambda x: (x[1], x[0]))
    if len(items) == 1:
        return {items[0][0]: 50.0}
    out: dict[str, float] = {}
    last = len(items) - 1
    for i, (key, _) in enumerate(items):
        out[key] = round(100 * i / last, 1)
    return out


def _product_label(sku_token: str | None) -> str:
    token = (sku_token or "").upper()
    return SKU_TO_PRODUCT.get(token, token or "Unknown")


def get_purchase_dashboard(db: Session) -> dict:
    rows = db.query(BuyerPurchase).all()
    if not rows:
        return {
            "kpis": {
                "purchase_row_count": 0,
                "unique_buyer_emails": 0,
                "top_purchase_state": None,
                "top_sku_token": None,
                "shopify_purchase_pct": 0,
                "prospect_match_rate_pct": 0,
            },
            "purchases_by_state": [],
            "purchase_radar": [],
            "meta": {
                "other_count": 0,
                "other_pct": 0,
                "buyer_upload_batches": 0,
                "disclaimer": "No buyer purchase data uploaded yet.",
            },
        }

    total_rows = len(rows)
    emails = {r.email.lower().strip() for r in rows if r.email}
    matched_emails = {r.email.lower().strip() for r in rows if r.matched_customer_id and r.email}

    by_state: dict[str, dict] = defaultdict(
        lambda: {
            "purchase_count": 0,
            "unique_emails": set(),
            "shopify": 0,
            "legacy": 0,
            "generic": 0,
            "v_count": 0,
            "m_count": 0,
            "sku_counts": defaultdict(int),
        }
    )
    other_count = 0
    shopify_total = 0

    for row in rows:
        state = (row.state or "OTHER").upper()
        if state not in US_STATES:
            state = "OTHER"
        if state == "OTHER":
            other_count += 1

        bucket = by_state[state]
        bucket["purchase_count"] += 1
        if row.email:
            bucket["unique_emails"].add(row.email.lower().strip())

        channel = (row.source_channel or "generic").lower()
        if channel == "shopify":
            bucket["shopify"] += 1
            shopify_total += 1
        elif channel == "legacy":
            bucket["legacy"] += 1
        else:
            bucket["generic"] += 1

        token = (row.sku_token or "").upper()
        if token in V_TOKENS:
            bucket["v_count"] += 1
        if token in M_TOKENS:
            bucket["m_count"] += 1
        if token:
            bucket["sku_counts"][token] += 1

    map_states = {s: d for s, d in by_state.items() if s in US_STATES and s != "OTHER"}
    state_totals = {s: d["purchase_count"] for s, d in map_states.items()}
    state_volume_scores = _percentile_map({s: float(v) for s, v in state_totals.items()})

    purchases_by_state: list[dict] = []
    for state, bucket in sorted(map_states.items(), key=lambda x: -x[1]["purchase_count"]):
        count = bucket["purchase_count"]
        top_sku = max(bucket["sku_counts"].items(), key=lambda x: x[1])[0] if bucket["sku_counts"] else None
        purchases_by_state.append(
            {
                "state": state,
                "purchase_count": count,
                "unique_buyers": len(bucket["unique_emails"]),
                "purchase_share_pct": round(100 * count / total_rows, 2),
                "top_sku_token": top_sku,
                "shopify_count": bucket["shopify"],
                "legacy_count": bucket["legacy"],
            }
        )

    top_state = purchases_by_state[0]["state"] if purchases_by_state else None
    sku_global: dict[str, int] = defaultdict(int)
    for row in rows:
        if row.sku_token:
            sku_global[row.sku_token.upper()] += 1
    top_sku = max(sku_global.items(), key=lambda x: x[1])[0] if sku_global else None

    # State × SKU cells for radar (exclude OTHER) — actual purchase tokens, not catalog product merge.
    cells: dict[tuple[str, str], dict] = {}
    cell_emails: dict[tuple[str, str], set] = defaultdict(set)
    for row in rows:
        state = (row.state or "OTHER").upper()
        if state not in US_STATES:
            continue
        token = (row.sku_token or "").upper()
        if not token:
            continue
        key = (state, token)
        if key not in cells:
            cells[key] = {"purchase_count": 0, "shopify": 0}
        cells[key]["purchase_count"] += 1
        if (row.source_channel or "").lower() == "shopify":
            cells[key]["shopify"] += 1
        if row.email:
            cell_emails[key].add(row.email.lower().strip())

    cell_counts = {f"{s}|{t}": float(c["purchase_count"]) for (s, t), c in cells.items()}
    volume_scores = _percentile_map(cell_counts)

    state_axis: dict[str, dict] = {}
    for state, bucket in map_states.items():
        count = bucket["purchase_count"]
        uniq = len(bucket["unique_emails"])
        state_axis[state] = {
            "state_volume_score": state_volume_scores.get(state, 50.0),
            "buyer_density_score": round(100 * uniq / max(count, 1), 1),
        }

    purchase_radar: list[dict] = []
    by_sku: dict[str, list[dict]] = defaultdict(list)
    for (state, sku_token), cell in cells.items():
        count = cell["purchase_count"]
        cell_id = f"{state}|{sku_token}"
        product = _product_label(sku_token)
        uniq = len(cell_emails[(state, sku_token)])
        axis = state_axis.get(state, {})
        by_sku[sku_token].append(
            {
                "id": cell_id,
                "label": f"{state} · {sku_token}",
                "state": state,
                "sku_token": sku_token,
                "product": product,
                "purchase_count": count,
                "unique_buyers": uniq,
                "purchase_volume_score": volume_scores.get(cell_id, 50.0),
                "state_volume_score": axis.get("state_volume_score", 50.0),
                "buyer_density_score": min(100.0, axis.get("buyer_density_score", 0)),
                "national_share_pct": round(100 * count / total_rows, 2),
                "revenue": float(count),
                "customers": uniq,
            }
        )

    active_skus = sorted(by_sku.keys())
    for sku_token in active_skus:
        ranked = sorted(by_sku[sku_token], key=lambda row: -int(row["purchase_count"]))
        purchase_radar.extend(ranked[:RADAR_TOP_STATES_PER_SKU])

    purchase_radar.sort(key=lambda row: -int(row["purchase_count"]))

    return {
        "kpis": {
            "purchase_row_count": total_rows,
            "unique_buyer_emails": len(emails),
            "top_purchase_state": top_state,
            "top_sku_token": top_sku,
            "shopify_purchase_pct": round(100 * shopify_total / max(total_rows, 1), 1),
            "prospect_match_rate_pct": round(100 * len(matched_emails) / max(len(emails), 1), 2),
        },
        "purchases_by_state": purchases_by_state,
        "purchase_radar": purchase_radar,
        "meta": {
            "other_count": other_count,
            "other_pct": round(100 * other_count / max(total_rows, 1), 1),
            "buyer_upload_batches": db.query(func.count(func.distinct(BuyerPurchase.upload_id))).scalar() or 0,
            "disclaimer": (
                "Actual purchases from Buyer Upload — not prospect forecasts. "
                f"{round(100 * other_count / max(total_rows, 1), 1)}% of rows have unassigned state (OTHER)."
            ),
        },
    }
