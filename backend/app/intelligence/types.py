"""CIOS Intelligence Engine — Rule Library (Volume 04)."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class RuleTrace:
    rule_id: str
    name: str
    input: dict[str, Any]
    output: dict[str, Any]
    explanation: str
    business_rule_id: str | None = None


@dataclass
class IntelligenceContext:
    """Mutable context passed through the fixed execution pipeline."""

    customer: dict[str, Any] = field(default_factory=dict)
    datalogix_raw: dict[str, Any] = field(default_factory=dict)
    datalogix_signals: dict[str, Any] = field(default_factory=dict)
    datalogix_intermediate: dict[str, Any] = field(default_factory=dict)
    zip_ref: dict[str, Any] | None = None
    zip_intelligence: dict[str, Any] = field(default_factory=dict)
    email_valid: bool = False
    trace: list[RuleTrace] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    prizm_proxy_segment: str | None = None
    ceragem_segment: str | None = None
    message_direction: str | None = None
    purchase_power_index: float = 0.0
    purchase_power_category: str | None = None
    pain_index: float = 0.0
    pain_index_category: str | None = None
    lifestyle_index: float = 0.0
    lifestyle_category: str | None = None
    email_response_index: float = 0.0
    brand_familiarity_index: float = 0.0
    recommendation_rationale: dict[str, Any] = field(default_factory=dict)
    recommended_product: str | None = None
    campaign_strategy: str | None = None
    campaign_priority: float = 0.0
    campaign_priority_category: str | None = None
    expected_conversion: float = 0.0
    baseline_conversion: float = 0.0
    promo_uplift: float = 0.0
    baseline_revenue: float = 0.0
    expected_orders: float = 0.0
    expected_revenue: float = 0.0
    le_frame_incentive: float = 0.0
    price_resistance_score: float = 0.0
    recommended_promotion: float = 0.0
    promo_code: str | None = None
    commercial_version: str | None = None
    commercial_kpis: dict[str, Any] = field(default_factory=dict)
    framework: dict[str, Any] = field(default_factory=dict)
    calculation_version: str | None = None
    engine_version: str | None = None

    def add_trace(self, rule_id: str, name: str, inp: dict, out: dict, explanation: str) -> None:
        from app.rules.library import resolve_business_rule_id

        self.trace.append(
            RuleTrace(
                rule_id,
                name,
                inp,
                out,
                explanation,
                business_rule_id=resolve_business_rule_id(rule_id),
            )
        )

    def to_intelligence_dict(self) -> dict[str, Any]:
        return {
            "prizm_proxy_segment": self.prizm_proxy_segment,
            "ceragem_segment": self.ceragem_segment,
            "message_direction": self.message_direction,
            "purchase_power_index": self.purchase_power_index,
            "purchase_power": self.purchase_power_category,
            "pain_index": self.pain_index,
            "pain_index_level": self.pain_index_category,
            "lifestyle_index": self.lifestyle_index,
            "lifestyle": self.lifestyle_category,
            "email_responsiveness_index": self.email_response_index,
            "brand_familiarity_index": self.brand_familiarity_index,
            "recommendation_rationale": self.recommendation_rationale,
            "recommended_product": self.recommended_product,
            "campaign_strategy": self.campaign_strategy,
            "expected_conversion_rate": self.expected_conversion,
            "baseline_conversion": self.baseline_conversion,
            "promo_uplift": self.promo_uplift,
            "baseline_revenue": self.baseline_revenue,
            "expected_orders": self.expected_orders,
            "expected_revenue": self.expected_revenue,
            "le_frame_incentive": self.le_frame_incentive,
            "price_resistance_score": self.price_resistance_score,
            "recommended_promotion": self.recommended_promotion,
            "promo_code": self.promo_code,
            "commercial_version": self.commercial_version,
            "commercial_kpis": self.commercial_kpis,
            "campaign_priority_score": self.campaign_priority,
            "campaign_priority": self.campaign_priority_category,
            "calculation_version": self.calculation_version,
            "engine_version": self.engine_version,
            "framework": self.framework,
            "rule_trace": [
                {
                    "rule_id": t.rule_id,
                    "business_rule_id": t.business_rule_id,
                    "name": t.name,
                    "explanation": t.explanation,
                    "input": t.input,
                    "output": t.output,
                }
                for t in self.trace
            ],
        }
