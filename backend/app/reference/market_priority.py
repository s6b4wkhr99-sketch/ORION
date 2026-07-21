"""US massage-chair priority markets — shared by intelligence rules and dashboards."""

from __future__ import annotations

# Traditional Ceragem demand concentration (incl. DC with VA).
PRIORITY_MARKET_STATES: frozenset[str] = frozenset(
    {"CA", "TX", "FL", "NY", "NJ", "VA", "DC", "IL", "PA", "MA"}
)

# Legacy coastal reference — M10 eligibility is now nationwide (High PP + High/Mid income).
M10_PREMIUM_STATES: frozenset[str] = frozenset({"CA", "NY", "NJ", "VA", "DC"})

# Legacy Sun Belt reference — S4 promo expansion applies to all states when S4 promo is active.
S4_VALUE_STATES: frozenset[str] = frozenset({"FL", "TX"})


def normalize_customer_state(state: str | None) -> str | None:
    code = (state or "").strip().upper()
    if not code:
        return None
    if code == "DISTRICT OF COLUMBIA":
        return "DC"
    return code[:2] if len(code) > 2 else code
