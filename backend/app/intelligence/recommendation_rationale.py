"""Structured product recommendation rationale for customer analysis."""

from __future__ import annotations

from typing import Any

from app.intelligence.product_ladders import resolve_active_ladder
from app.intelligence.recommendation_rules import RecommendationInputs
from app.intelligence.types import IntelligenceContext

SLEEP_SEGMENT_LABELS: dict[str, str] = {
    "none": "해당 없음",
    "metro_sleep_deprived": "수면 부족 대도시 (Innerbody)",
    "metro_plus_prizm_sleep_affinity": "수면 부족 대도시 + PRIZM 복합",
    "simple_life_sleep_stress": "Simple Life · 경제적 수면 스트레스",
    "caregiver_fatigue": "돌봄 피로 · 수면 저하",
    "midlife_rest_gap": "중간 통증 + 휴식 니즈",
    "economic_sleep_burden": "저소득 · 수면 스트레스",
    "blended_sleep_affinity": "복합 수면 취약 신호",
    "prizm_sleep_affinity": "PRIZM 수면 친화 세그먼트",
    "sleep_affinity": "수면 취약 신호",
    "high_sleep_affinity": "높은 수면 취약도",
    "moderate_sleep_affinity": "중간 수면 취약도",
}


def _pct(value: float | None) -> float:
    if value is None:
        return 0.0
    return round(float(value) * 100, 1)


def _infer_selection_rule(inputs: RecommendationInputs) -> str:
    ladder, source = resolve_active_ladder(
        ceragem_segment=inputs.ceragem_segment,
        prizm_segment=inputs.prizm_segment,
        pain_index_category=inputs.pain_index_category,
        premium_zip=inputs.premium_zip,
    )
    head = " → ".join(ladder[:3])
    if source == "ceragem":
        return f"Ceragem 래더 ({inputs.ceragem_segment}) 우선 — {head}"
    return f"PRIZM 래더 ({inputs.prizm_segment or 'Unknown'}) 우선 — {head}"


def _adjustment_notes(product_result: dict[str, Any]) -> list[dict[str, str]]:
    notes: list[dict[str, str]] = []
    price_adj = product_result.get("price_resistance_adjustment") or {}
    if price_adj.get("adjusted"):
        notes.append(
            {
                "type": "price_resistance",
                "label": "가격 저항 조정",
                "detail": f"{price_adj.get('original_product')} → {price_adj.get('adjusted_product')} ({price_adj.get('adjustment_reason')})",
            }
        )
    sleep_adj = product_result.get("sleep_deprivation_adjustment") or {}
    if sleep_adj.get("adjusted"):
        notes.append(
            {
                "type": "sleep_affinity",
                "label": "수면 취약도 M Series 가산",
                "detail": f"{sleep_adj.get('original_product')} → {sleep_adj.get('adjusted_product')} ({sleep_adj.get('adjustment_reason')})",
            }
        )
    return notes


def _brand_familiarity_detail(ctx: IntelligenceContext) -> str:
    zip_intel = ctx.zip_intelligence or {}
    parts = [f"Brand geo boost: {float(zip_intel.get('brand_geo_boost') or 0):.2f}"]
    if zip_intel.get("asian_relative_index"):
        parts.append(
            f"Asian {zip_intel.get('asian_population_pct')}% "
            f"({zip_intel.get('asian_relative_index')}x vs 5.9%)"
        )
    if zip_intel.get("korean_metro_match"):
        parts.append(f"한인 metro: {zip_intel.get('korean_metro_label')}")
    elif zip_intel.get("korean_state_match"):
        parts.append("한인 주별 TOP10")
    return " · ".join(parts)


def build_recommendation_rationale(ctx: IntelligenceContext, rule_result: dict[str, Any]) -> dict[str, Any]:
    """Explain product selection using intelligence factors and rule trace."""
    inputs = build_recommendation_inputs_from_ctx(ctx)
    zip_intel = ctx.zip_intelligence or {}
    product_result = rule_result.get("product") or {}

    sleep_segment = str(zip_intel.get("sleep_segment") or inputs.sleep_segment or "none")
    sleep_tier = str(zip_intel.get("sleep_deprivation_tier") or inputs.sleep_deprivation_tier or "none")
    sleep_boost = float(zip_intel.get("sleep_geo_boost") or inputs.sleep_geo_boost or 0.0)

    factors = [
        {
            "key": "purchase_power",
            "label": "잠정 구매력",
            "level": ctx.purchase_power_category or "Low",
            "score": _pct(ctx.purchase_power_index),
            "detail": f"Ceragem {ctx.ceragem_segment or '—'} · ZIP income {zip_intel.get('income_tier', 'Unknown')}",
        },
        {
            "key": "pain_index",
            "label": "Pain Index",
            "level": ctx.pain_index_category or "Low",
            "score": _pct(ctx.pain_index),
            "detail": "FDA Class 2 치료 니즈 — High일 때 V Series 우선",
        },
        {
            "key": "lifestyle",
            "label": "라이프스타일",
            "level": ctx.lifestyle_category or "Low",
            "score": _pct(ctx.lifestyle_index),
            "detail": f"PRIZM {ctx.prizm_proxy_segment or 'Unknown'}",
        },
        {
            "key": "digital_engagement",
            "label": "온라인 구매력",
            "level": _digital_level(ctx.email_response_index),
            "score": _pct(ctx.email_response_index),
            "detail": f"Metro digital tier: {zip_intel.get('digital_metro_tier', 'other')}",
        },
        {
            "key": "brand_familiarity",
            "label": "브랜드 인지도",
            "level": _brand_level(ctx.brand_familiarity_index),
            "score": _pct(ctx.brand_familiarity_index),
            "detail": _brand_familiarity_detail(ctx),
        },
        {
            "key": "sleep_affinity",
            "label": "수면 장애 신호",
            "level": "High" if sleep_boost >= 0.24 else "Medium" if sleep_boost >= 0.14 else "Low",
            "score": round(sleep_boost * 100, 1),
            "detail": SLEEP_SEGMENT_LABELS.get(sleep_segment, sleep_segment),
        },
    ]

    adjustments = _adjustment_notes(product_result)
    selection_rule = _infer_selection_rule(inputs)
    summary_parts = [
        f"추천 제품 {ctx.recommended_product}",
        f"기준 룰: {selection_rule}",
    ]
    if adjustments:
        summary_parts.append(f"조정 {len(adjustments)}건 적용")
    if sleep_boost >= 0.14:
        summary_parts.append(f"수면 신호 {SLEEP_SEGMENT_LABELS.get(sleep_segment, sleep_segment)}")

    return {
        "recommended_product": ctx.recommended_product,
        "selection_rule": selection_rule,
        "ceragem_segment": ctx.ceragem_segment,
        "prizm_proxy_segment": ctx.prizm_proxy_segment,
        "campaign_strategy": ctx.campaign_strategy,
        "message_direction": ctx.message_direction,
        "factors": factors,
        "adjustments": adjustments,
        "sleep_segment": sleep_segment,
        "sleep_segment_label": SLEEP_SEGMENT_LABELS.get(sleep_segment, sleep_segment),
        "sleep_deprivation_tier": sleep_tier,
        "summary": " · ".join(summary_parts),
    }


def build_recommendation_inputs_from_ctx(ctx: IntelligenceContext) -> RecommendationInputs:
    from app.intelligence.recommendation_rules import build_recommendation_inputs

    return build_recommendation_inputs(ctx)


def _digital_level(value: float | None) -> str:
    score = float(value or 0)
    if score >= 0.55:
        return "High"
    if score >= 0.25:
        return "Medium"
    return "Low"


def _brand_level(value: float | None) -> str:
    score = float(value or 0)
    if score >= 0.45:
        return "High"
    if score >= 0.18:
        return "Medium"
    return "Low"


def rationale_from_framework_summary(summary: dict | None) -> dict | None:
    if not summary:
        return None
    stored = summary.get("recommendation_rationale")
    if stored:
        return stored
    rec = (summary.get("categories") or {}).get("recommendation") or {}
    if isinstance(rec, dict) and rec.get("rationale"):
        return rec["rationale"]
    return None


def rationale_from_intelligence_row(intel, customer) -> dict | None:
    """Rebuild or load rationale for API responses when full trace is not loaded."""
    import json

    if getattr(intel, "framework_summary_json", None):
        try:
            summary = json.loads(intel.framework_summary_json)
            stored = rationale_from_framework_summary(summary)
            if stored:
                return stored
        except json.JSONDecodeError:
            pass

    sleep_segment = "none"
    sleep_boost = 0.0
    income_tier = "Unknown"
    if getattr(intel, "framework_summary_json", None):
        try:
            summary = json.loads(intel.framework_summary_json)
            sleep_cat = (summary.get("categories") or {}).get("sleep_affinity") or {}
            sleep_segment = str(sleep_cat.get("sleep_segment") or "none")
            sleep_boost = float(sleep_cat.get("sleep_geo_boost") or 0.0)
        except json.JSONDecodeError:
            pass

    ctx = IntelligenceContext(
        customer={"state": getattr(customer, "state", None), "zip": getattr(customer, "zip", None), "city": getattr(customer, "city", None)},
        prizm_proxy_segment=intel.prizm_proxy_segment,
        ceragem_segment=intel.ceragem_segment,
        message_direction=intel.message_direction,
        purchase_power_index=intel.purchase_power_index or 0,
        purchase_power_category=_index_level(intel.purchase_power_index),
        pain_index=intel.pain_index or 0,
        pain_index_category=_index_level(intel.pain_index),
        lifestyle_index=intel.lifestyle_index or 0,
        lifestyle_category=_index_level(intel.lifestyle_index),
        email_response_index=intel.email_response_index or 0,
        brand_familiarity_index=intel.brand_familiarity_index or 0,
        recommended_product=intel.recommended_product,
        campaign_strategy=None,
        zip_intelligence={"income_tier": income_tier, "sleep_segment": sleep_segment, "sleep_geo_boost": sleep_boost},
    )
    rule_result = {
        "product": {
            "recommended_product": intel.recommended_product,
            "price_resistance_adjustment": {"adjusted": False},
            "sleep_deprivation_adjustment": {"adjusted": False},
        }
    }
    return build_recommendation_rationale(ctx, rule_result)


def _index_level(value: float | None) -> str:
    if value is None:
        return "Low"
    if value >= 0.75:
        return "High"
    if value >= 0.45:
        return "Medium"
    return "Low"
