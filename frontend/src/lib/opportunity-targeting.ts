import type { CustomerRow } from "@/lib/api";
import { PRODUCT_OPTIONS } from "@/lib/config";

export type ExplorerTargetCriteria = {
  product: string;
  lifestyleMin: number;
  painMin: number;
  purchasePowerMin: number;
  state: string;
  goal: string;
};

export const EXPLORER_GOALS = ["Revenue", "Conversion", "Acquisition", "Premium Product", "Clinical Product"] as const;

export const PRODUCT_SERIES = {
  v: ["Master V9", "Master V7", "Master V6", "Master V5", "Master S4"],
  m: ["Pause M10", "Pause M6", "Pause M6s", "Pause M4"],
} as const;

/** Map legacy DB values to current catalog SSOT. */
export function normalizeProductCode(product: string | null | undefined): string {
  const code = (product ?? "").trim();
  if (code === "Pause S4" || code === "Master V4") return "Master S4";
  return code;
}

/** Intelligence indices are stored 0–1; UI sliders use 0–100. */
export function indexPercent(value: number | null | undefined): number {
  if (value == null) return 0;
  return value <= 1 ? value * 100 : value;
}

export function matchesProductFilter(product: string | null | undefined, selected: string): boolean {
  if (!selected) return true;
  const normalized = normalizeProductCode(product);
  if (selected === "V Series") {
    return PRODUCT_SERIES.v.includes(normalized as (typeof PRODUCT_SERIES.v)[number]);
  }
  if (selected === "M Series") {
    return PRODUCT_SERIES.m.includes(normalized as (typeof PRODUCT_SERIES.m)[number]);
  }
  return normalized === normalizeProductCode(selected);
}

export function filterCustomersByTarget(customers: CustomerRow[], criteria: ExplorerTargetCriteria): CustomerRow[] {
  return customers.filter((c) => {
    if (!matchesProductFilter(c.recommended_product, criteria.product)) return false;
    if (criteria.state && c.state !== criteria.state) return false;
    if (indexPercent(c.pain_index) < criteria.painMin) return false;
    if (indexPercent(c.purchase_power_index) < criteria.purchasePowerMin) return false;
    if (indexPercent(c.lifestyle_index) < criteria.lifestyleMin) return false;
    return true;
  });
}

export function sortCustomersByGoal(customers: CustomerRow[], goal: string): CustomerRow[] {
  const copy = [...customers];
  if (goal === "Conversion") return copy.sort((a, b) => (b.expected_conversion_rate ?? 0) - (a.expected_conversion_rate ?? 0));
  if (goal === "Acquisition") return copy.sort((a, b) => indexPercent(b.purchase_power_index) - indexPercent(a.purchase_power_index));
  if (goal === "Clinical Product") return copy.sort((a, b) => indexPercent(b.pain_index) - indexPercent(a.pain_index));
  if (goal === "Premium Product") return copy.sort((a, b) => indexPercent(b.purchase_power_index) - indexPercent(a.purchase_power_index));
  return copy.sort((a, b) => (b.expected_revenue ?? 0) - (a.expected_revenue ?? 0));
}

export function deriveCampaignMessage(criteria: ExplorerTargetCriteria): string {
  const product = criteria.product;
  if (product === "V Series" || product.startsWith("Master V") || product === "Master S4" || criteria.goal === "Clinical Product" || criteria.painMin >= 55) {
    return "Pain Relief + Therapeutic Value Message";
  }
  if (product === "M Series" || product.startsWith("Pause M") || criteria.lifestyleMin >= 55) {
    return "Sleep Restoration + Wellness Message";
  }
  if (criteria.purchasePowerMin >= 65 || criteria.goal === "Premium Product") {
    return "Premium Lifestyle + Consultation Message";
  }
  if (criteria.goal === "Acquisition") {
    return "Product Education + Financing Message";
  }
  return "Wellness Education + Value Message";
}

export function deriveRecommendedProduct(criteria: ExplorerTargetCriteria, matched: CustomerRow[]): string {
  if (criteria.product && criteria.product !== "V Series" && criteria.product !== "M Series") {
    return normalizeProductCode(criteria.product);
  }
  if (matched.length) {
    const counts = new Map<string, number>();
    for (const c of matched) {
      const p = normalizeProductCode(c.recommended_product ?? "Unknown");
      counts.set(p, (counts.get(p) ?? 0) + 1);
    }
    return [...counts.entries()].sort((a, b) => b[1] - a[1])[0]?.[0] ?? "Master V9";
  }
  if (criteria.painMin >= 50) return "Master V7";
  if (criteria.lifestyleMin >= 50 && criteria.painMin < 45) return "Pause M6";
  if (criteria.purchasePowerMin >= 60) return "Master V9";
  return "Master S4";
}

export function resolveOpportunityScore(
  backendScore: number | undefined,
  fallback: { revenue: number; maxRevenue: number; conversion: number },
): number {
  if (backendScore != null && backendScore > 0) return Math.round(backendScore);
  return Math.min(
    99,
    Math.round((fallback.revenue / Math.max(fallback.maxRevenue, 1)) * 55 + fallback.conversion * 10000 * 0.2),
  );
}

export const EXPLORER_PRODUCT_CHOICES = ["", "V Series", "M Series", ...PRODUCT_OPTIONS] as const;
