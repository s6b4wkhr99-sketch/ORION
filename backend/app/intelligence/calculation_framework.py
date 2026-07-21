"""Volume 19 — Standardized intelligence calculation framework."""

from __future__ import annotations

import time
import uuid
from typing import Any

from app.ai_engine.confidence import confidence_category
from app.intelligence.framework_constants import (
    CALCULATION_VERSION,
    CATEGORY_BUSINESS_RULES,
    CERAGEM_V19_MAP,
    COMPOSITE_RULE_IDS,
    INTELLIGENCE_CATEGORIES,
    INTELLIGENCE_ENGINE_VERSION,
    PRIORITY_TO_GRADE,
    RULE_VERSION_DEFAULT,
)
from app.intelligence.types import IntelligenceContext, RuleTrace


def normalize_score(value: float | None, *, from_proxy: bool = False) -> float:
    """Section 17 — clamp intelligence scores to 0–100."""
    if value is None:
        return 0.0
    if from_proxy and value <= 1.0:
        return round(max(0.0, min(100.0, value * 100)), 2)
    return round(max(0.0, min(100.0, value)), 2)


def _trace_output(ctx: IntelligenceContext, rule_id: str) -> dict[str, Any]:
    for trace in ctx.trace:
        if trace.rule_id == rule_id:
            return trace.output or {}
    return {}


def _trace_for_category(ctx: IntelligenceContext, category: str) -> RuleTrace | None:
    rule_id = COMPOSITE_RULE_IDS.get(category)
    if not rule_id:
        return None
    for trace in ctx.trace:
        if trace.rule_id == rule_id:
            return trace
    return None


def _data_completeness(ctx: IntelligenceContext) -> float:
    signals = [
        bool(ctx.zip_intelligence),
        bool(ctx.datalogix_intermediate),
        bool(ctx.prizm_proxy_segment and ctx.prizm_proxy_segment != "Unknown"),
        bool(ctx.customer.get("email")),
        bool(ctx.customer.get("zip")),
    ]
    return sum(signals) / len(signals)


def category_confidence(composite: float | None, completeness: float, *, has_level: bool = True) -> float:
    """Section 13 — per-category confidence 0–100."""
    base = (composite or 0.5) * 70 if composite is not None else 35.0
    coverage = completeness * 25
    level_bonus = 5.0 if has_level else 0.0
    return normalize_score(base + coverage + level_bonus)


def build_explanation(
    *,
    category: str,
    level: str,
    primary_factors: list[str],
    secondary_factors: list[str],
    supporting_rules: list[str],
    confidence: float,
    calculation_version: str = CALCULATION_VERSION,
) -> dict[str, Any]:
    """Section 16 — explainability envelope."""
    return {
        "category": category,
        "level": level,
        "primary_factors": primary_factors,
        "secondary_factors": secondary_factors,
        "supporting_rules": supporting_rules,
        "confidence": confidence,
        "confidence_category": confidence_category(confidence),
        "calculation_version": calculation_version,
        "business_rule_id": CATEGORY_BUSINESS_RULES.get(category),
    }


def _purchase_power_framework(ctx: IntelligenceContext, completeness: float) -> dict[str, Any]:
    trace = _trace_for_category(ctx, "purchase_power")
    composite = _trace_output(ctx, "Rule-054").get("composite_score")
    if composite is None:
        composite = ctx.purchase_power_index
        score = normalize_score(composite, from_proxy=True)
    else:
        score = normalize_score(composite)
    level = ctx.purchase_power_category or "Low"
    confidence = category_confidence(composite, completeness)
    primary = []
    if ctx.zip_intelligence.get("premium_zip_indicator"):
        primary.append("Top 50 Income ZIP")
    if ctx.datalogix_intermediate.get("estimated_income_numeric"):
        primary.append("Estimated Income")
    if ctx.datalogix_intermediate.get("net_worth_strength", 0) > 0.3:
        primary.append("Net Worth Indicator")
    secondary = []
    if ctx.datalogix_signals.get("retail_card"):
        secondary.append("Retail Card Activity")
    if ctx.datalogix_signals.get("bank_card"):
        secondary.append("Bank Card Activity")
    if ctx.datalogix_intermediate.get("residential_stability", 0) > 0.3:
        secondary.append("Length of Residence")
    rules = [t.business_rule_id or t.rule_id for t in ctx.trace if t.rule_id.startswith("Rule-05")]
    return {
        "score": score,
        "level": level,
        "confidence": confidence,
        "explanation": build_explanation(
            category="purchase_power",
            level=level,
            primary_factors=primary or ["Geographic purchasing context"],
            secondary_factors=secondary,
            supporting_rules=[r for r in rules if r][:5],
            confidence=confidence,
        ),
        "trace": trace.output if trace else {},
    }


def _pain_index_framework(ctx: IntelligenceContext, completeness: float) -> dict[str, Any]:
    composite = _trace_output(ctx, "Rule-059").get("composite_score")
    level = ctx.pain_index_category or "Low"
    score = normalize_score(composite if composite is not None else ctx.pain_index, from_proxy=composite is None)
    confidence = category_confidence(composite, completeness)
    primary = []
    if ctx.datalogix_raw.get("age_range") or ctx.datalogix_raw.get("generation"):
        primary.append("Age / Generation")
    if ctx.prizm_proxy_segment in {"Aging in Place", "Caregiving Households"}:
        primary.append("Lifestyle segment alignment")
    secondary = ["Household composition", "Residence stability"]
    rules = [t.business_rule_id or t.rule_id for t in ctx.trace if t.rule_id.startswith("Rule-05") and int(t.rule_id.split("-")[1]) >= 55]
    return {
        "score": score,
        "level": level,
        "confidence": confidence,
        "explanation": build_explanation(
            category="pain_index",
            level=level,
            primary_factors=primary or ["Age and household signals"],
            secondary_factors=secondary,
            supporting_rules=[r for r in rules if r][:5],
            confidence=confidence,
        ),
    }


def _lifestyle_framework(ctx: IntelligenceContext, completeness: float) -> dict[str, Any]:
    composite = _trace_output(ctx, "Rule-064").get("composite_score")
    level = ctx.lifestyle_category or "Low"
    score = normalize_score(composite if composite is not None else ctx.lifestyle_index, from_proxy=composite is None)
    confidence = category_confidence(composite, completeness)
    primary = []
    if ctx.prizm_proxy_segment:
        primary.append(f"PRIZM Proxy: {ctx.prizm_proxy_segment}")
    if ctx.zip_intelligence.get("geographic_purchasing_context", 0) > 0.3:
        primary.append("ZIP Intelligence")
    secondary = ["Digital activity", "Retail activity", "Household stability"]
    rules = [t.business_rule_id or t.rule_id for t in ctx.trace if t.rule_id.startswith("Rule-06")]
    return {
        "score": score,
        "level": level,
        "confidence": confidence,
        "explanation": build_explanation(
            category="lifestyle",
            level=level,
            primary_factors=primary or ["Wellness orientation signals"],
            secondary_factors=secondary,
            supporting_rules=[r for r in rules if r][:5],
            confidence=confidence,
        ),
    }


def _prizm_framework(ctx: IntelligenceContext, completeness: float) -> dict[str, Any]:
    segment = ctx.prizm_proxy_segment or "Unknown"
    known = segment != "Unknown"
    score = normalize_score(0.85 if known else 0.2, from_proxy=True)
    confidence = category_confidence(0.85 if known else 0.2, completeness, has_level=known)
    primary = ["ZIP Intelligence", "Purchase readiness"]
    if ctx.datalogix_intermediate.get("digital_engagement", 0) > 0.3:
        primary.append("Digital Activity")
    rules = [t.business_rule_id or t.rule_id for t in ctx.trace if t.rule_id.startswith("Rule-02")]
    return {
        "score": score,
        "level": segment,
        "confidence": confidence,
        "explanation": build_explanation(
            category="prizm_proxy",
            level=segment,
            primary_factors=primary,
            secondary_factors=["Household", "Age", "Generation"],
            supporting_rules=[r for r in rules if r][:5],
            confidence=confidence,
        ),
    }


def _ceragem_framework(ctx: IntelligenceContext, completeness: float) -> dict[str, Any]:
    segment_v04 = ctx.ceragem_segment or "Unknown"
    segment_v19 = CERAGEM_V19_MAP.get(segment_v04, "Unknown")
    tier = segment_v04.split("+")[0].strip() if "+" in segment_v04 else "Low"
    tier_scores = {"High": 0.9, "Mid-High": 0.7, "Mid-Low": 0.45, "Low": 0.25}
    composite = tier_scores.get(tier, 0.3)
    score = normalize_score(composite, from_proxy=True)
    confidence = category_confidence(composite, completeness)
    rules = [t.business_rule_id or t.rule_id for t in ctx.trace if t.rule_id.startswith("Rule-03")]
    return {
        "score": score,
        "level": segment_v19,
        "level_v04": segment_v04,
        "confidence": confidence,
        "explanation": build_explanation(
            category="ceragem_segment",
            level=segment_v19,
            primary_factors=[
                f"Purchase Power: {ctx.purchase_power_category}",
                f"Pain Index: {ctx.pain_index_category}",
                f"Lifestyle: {ctx.lifestyle_category}",
            ],
            secondary_factors=[f"PRIZM: {ctx.prizm_proxy_segment}"],
            supporting_rules=[r for r in rules if r][:5],
            confidence=confidence,
        ),
    }


def _digital_engagement_framework(ctx: IntelligenceContext, completeness: float) -> dict[str, Any]:
    score = normalize_score(ctx.email_response_index, from_proxy=True)
    level = "High" if (ctx.email_response_index or 0) >= 0.55 else "Medium" if (ctx.email_response_index or 0) >= 0.25 else "Low"
    confidence = category_confidence(ctx.email_response_index, completeness)
    metro_tier = ctx.zip_intelligence.get("digital_metro_tier", "other")
    return {
        "score": score,
        "level": level,
        "confidence": confidence,
        "explanation": build_explanation(
            category="digital_engagement",
            level=level,
            primary_factors=[f"Metro digital tier: {metro_tier}"],
            secondary_factors=["Email responsiveness", "Online purchase signals"],
            supporting_rules=["RULE-DIG-001"],
            confidence=confidence,
        ),
    }


def _brand_familiarity_framework(ctx: IntelligenceContext, completeness: float) -> dict[str, Any]:
    score = normalize_score(ctx.brand_familiarity_index, from_proxy=True)
    level = "High" if (ctx.brand_familiarity_index or 0) >= 0.45 else "Medium" if (ctx.brand_familiarity_index or 0) >= 0.18 else "Low"
    confidence = category_confidence(ctx.brand_familiarity_index, completeness)
    geo_boost = float(ctx.zip_intelligence.get("brand_geo_boost") or 0)
    asian_idx = float(ctx.zip_intelligence.get("asian_relative_index") or 0)
    korean_label = ctx.zip_intelligence.get("korean_metro_label") or ""
    primary = [f"Brand geo boost: {geo_boost:.2f}"]
    if asian_idx >= 1.5:
        primary.append(f"Asian density {asian_idx}x national 5.9%")
    if korean_label:
        primary.append(f"Korean metro: {korean_label}")
    if ctx.customer.get("state") in {"TX", "PA"}:
        primary.append(f"State corridor: {ctx.customer.get('state')}")
    return {
        "score": score,
        "level": level,
        "confidence": confidence,
        "explanation": build_explanation(
            category="brand_familiarity",
            level=level,
            primary_factors=primary,
            secondary_factors=["Korean/Chinese diaspora enclave match", "ACS 2022 Korean metro tier"],
            supporting_rules=["RULE-BRD-001"],
            confidence=confidence,
        ),
    }


def _sleep_affinity_framework(ctx: IntelligenceContext, completeness: float) -> dict[str, Any]:
    zip_intel = ctx.zip_intelligence or {}
    sleep_boost = float(zip_intel.get("sleep_geo_boost") or 0.0)
    sleep_segment = str(zip_intel.get("sleep_segment") or "none")
    score = normalize_score(min(1.0, sleep_boost * 2.5), from_proxy=True)
    level = "High" if sleep_boost >= 0.24 else "Medium" if sleep_boost >= 0.14 else "Low"
    confidence = category_confidence(sleep_boost, completeness, has_level=sleep_segment != "none")
    return {
        "score": score,
        "level": level,
        "sleep_segment": sleep_segment,
        "sleep_geo_boost": sleep_boost,
        "confidence": confidence,
        "explanation": build_explanation(
            category="sleep_affinity",
            level=level,
            primary_factors=[f"Sleep segment: {sleep_segment}"],
            secondary_factors=["Innerbody metro tier", "PRIZM rest signals"],
            supporting_rules=["RULE-SLP-001"],
            confidence=confidence,
        ),
    }


def _recommendation_framework(ctx: IntelligenceContext, completeness: float) -> dict[str, Any]:
    composite = _trace_output(ctx, "Rule-066").get("composite_score")
    score = normalize_score(ctx.campaign_priority, from_proxy=True)
    confidence = category_confidence(composite, completeness)
    rationale = getattr(ctx, "recommendation_rationale", None) or {}
    factor_labels = [f["label"] for f in rationale.get("factors", []) if isinstance(f, dict)]
    return {
        "score": score,
        "recommended_product": ctx.recommended_product,
        "recommended_campaign": ctx.campaign_strategy,
        "recommended_message": ctx.message_direction,
        "campaign_priority": ctx.campaign_priority_category,
        "confidence": confidence,
        "rationale": rationale,
        "selection_rule": rationale.get("selection_rule"),
        "rationale_summary": rationale.get("summary"),
        "explanation": build_explanation(
            category="recommendation",
            level=ctx.campaign_priority_category or "Low",
            primary_factors=[
                f"Product: {ctx.recommended_product}",
                f"Strategy: {ctx.campaign_strategy}",
                *( [f"Rule: {rationale['selection_rule']}"] if rationale.get("selection_rule") else [] ),
            ],
            secondary_factors=factor_labels or [f"Message: {ctx.message_direction}"],
            supporting_rules=["RULE-REC-001", "RULE-REC-002", "RULE-REC-003", "RULE-SLP-001"],
            confidence=confidence,
        ),
    }


def _revenue_framework(ctx: IntelligenceContext, completeness: float) -> dict[str, Any]:
    revenue = ctx.expected_revenue or 0
    score = normalize_score(min(100.0, revenue / 100.0))
    confidence = category_confidence(ctx.expected_conversion, completeness)
    return {
        "score": score,
        "expected_revenue": round(revenue, 2),
        "revenue_range": {"low": round(revenue * 0.85, 2), "high": round(revenue * 1.15, 2)},
        "confidence": confidence,
        "explanation": build_explanation(
            category="revenue",
            level="forecast",
            primary_factors=[f"Product: {ctx.recommended_product}", f"Purchase Power: {ctx.purchase_power_category}"],
            secondary_factors=["Conservative conversion tier"],
            supporting_rules=["RULE-FOR-002", "RULE-FOR-003"],
            confidence=confidence,
        ),
    }


def _conversion_framework(ctx: IntelligenceContext, completeness: float) -> dict[str, Any]:
    rate = ctx.expected_conversion or 0
    score = normalize_score(min(100.0, rate * 10000))
    confidence = category_confidence(rate * 10, completeness)
    return {
        "score": score,
        "expected_conversion": round(rate, 6),
        "expected_orders": round(ctx.expected_orders, 4),
        "confidence": confidence,
        "explanation": build_explanation(
            category="conversion",
            level="probability",
            primary_factors=[f"Ceragem tier: {ctx.ceragem_segment}"],
            secondary_factors=[f"State: {ctx.customer.get('state')}", f"ZIP: {ctx.customer.get('zip')}"],
            supporting_rules=["RULE-FOR-004"],
            confidence=confidence,
        ),
    }


def _campaign_priority_framework(ctx: IntelligenceContext, completeness: float) -> dict[str, Any]:
    label = ctx.campaign_priority_category or "Low"
    grade = PRIORITY_TO_GRADE.get(label, "D")
    score = normalize_score(ctx.campaign_priority, from_proxy=True)
    confidence = category_confidence(_trace_output(ctx, "Rule-066").get("composite_score"), completeness)
    return {
        "score": score,
        "priority_level": label,
        "priority_grade": grade,
        "confidence": confidence,
        "explanation": build_explanation(
            category="campaign_priority",
            level=grade,
            primary_factors=[
                f"Revenue opportunity: {ctx.expected_revenue}",
                f"Conversion: {ctx.expected_conversion}",
            ],
            secondary_factors=[f"Recommendation confidence: {confidence}"],
            supporting_rules=["RULE-CAM-001"],
            confidence=confidence,
        ),
    }


def build_intelligence_audit(
    ctx: IntelligenceContext,
    *,
    calculation_id: uuid.UUID | None = None,
    execution_ms: float | None = None,
    generated_by: str = "intelligence_pipeline",
) -> dict[str, Any]:
    """Section 18 — intelligence calculation audit record."""
    return {
        "calculation_id": str(calculation_id or uuid.uuid4()),
        "customer_id": str(ctx.customer.get("customer_id") or ""),
        "timestamp": None,
        "rule_version": RULE_VERSION_DEFAULT,
        "calculation_version": CALCULATION_VERSION,
        "engine_version": INTELLIGENCE_ENGINE_VERSION,
        "generated_by": generated_by,
        "execution_time_ms": execution_ms,
        "confidence_summary": {
            cat: (ctx.framework.get(cat, {}) if hasattr(ctx, "framework") else {}).get("confidence")
            for cat in INTELLIGENCE_CATEGORIES
            if hasattr(ctx, "framework")
        },
        "errors": list(ctx.errors),
    }


def apply_calculation_framework(
    ctx: IntelligenceContext,
    *,
    generated_by: str = "intelligence_pipeline",
    execution_ms: float | None = None,
) -> dict[str, Any]:
    """
    Volume 19 post-pipeline pass — normalize scores, attach confidence & explainability.
    Deterministic: same ctx state → same framework output.
    """
    started = time.perf_counter()
    completeness = _data_completeness(ctx)

    categories = {
        "purchase_power": _purchase_power_framework(ctx, completeness),
        "pain_index": _pain_index_framework(ctx, completeness),
        "lifestyle": _lifestyle_framework(ctx, completeness),
        "digital_engagement": _digital_engagement_framework(ctx, completeness),
        "brand_familiarity": _brand_familiarity_framework(ctx, completeness),
        "sleep_affinity": _sleep_affinity_framework(ctx, completeness),
        "prizm_proxy": _prizm_framework(ctx, completeness),
        "ceragem_segment": _ceragem_framework(ctx, completeness),
        "recommendation": _recommendation_framework(ctx, completeness),
        "revenue": _revenue_framework(ctx, completeness),
        "conversion": _conversion_framework(ctx, completeness),
        "campaign_priority": _campaign_priority_framework(ctx, completeness),
    }

    calc_id = uuid.uuid4()
    elapsed = execution_ms if execution_ms is not None else round((time.perf_counter() - started) * 1000, 2)

    framework = {
        "calculation_id": str(calc_id),
        "calculation_version": CALCULATION_VERSION,
        "engine_version": INTELLIGENCE_ENGINE_VERSION,
        "rule_version": RULE_VERSION_DEFAULT,
        "generated_by": generated_by,
        "execution_time_ms": elapsed,
        "categories": categories,
    }
    audit = {
        "calculation_id": str(calc_id),
        "customer_id": str(ctx.customer.get("customer_id") or ""),
        "rule_version": RULE_VERSION_DEFAULT,
        "calculation_version": CALCULATION_VERSION,
        "engine_version": INTELLIGENCE_ENGINE_VERSION,
        "generated_by": generated_by,
        "execution_time_ms": elapsed,
        "confidence_summary": {cat: categories[cat].get("confidence") for cat in categories},
        "errors": list(ctx.errors),
    }
    framework["audit"] = audit

    ctx.framework = framework
    ctx.calculation_version = CALCULATION_VERSION
    ctx.engine_version = INTELLIGENCE_ENGINE_VERSION
    return framework


def framework_from_intelligence_row(intel, *, trace: list | None = None, db: Session | None = None) -> dict[str, Any] | None:
    """Rehydrate framework JSON stored on CustomerIntelligence or intelligence_trace."""
    import json

    from app.intelligence.trace_storage import load_framework_for_row

    if db is not None:
        loaded = load_framework_for_row(db, intel)
        if loaded:
            return loaded

    if getattr(intel, "framework_summary_json", None):
        try:
            return json.loads(intel.framework_summary_json)
        except json.JSONDecodeError:
            pass
    if getattr(intel, "framework_json", None):
        try:
            return json.loads(intel.framework_json)
        except json.JSONDecodeError:
            pass
    return None
