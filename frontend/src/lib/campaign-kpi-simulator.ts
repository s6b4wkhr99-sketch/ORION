import type { ExecutiveSummary, MetroDashboardRow, StateDashboard } from "@/lib/api";
import type { FinderSearchCriteria } from "@/components/decision/opportunity-finder/search-builder";
import { deriveCampaignMessage, type ExplorerTargetCriteria } from "@/lib/opportunity-targeting";

export type IntelligenceLayer = "mission" | "market" | "metro";

export type LayerSignal = {
  layer: IntelligenceLayer;
  label: string;
  href: string;
  customers: number | null;
  revenue: number | null;
  conversion: number | null;
  orders: number | null;
  opportunityScore: number | null;
  topProduct: string | null;
  geoLabel: string | null;
  active: boolean;
};

export type CampaignKpiTargets = {
  customers: number;
  revenue: number;
  conversion: number;
  orders: number;
  roi: number | null;
};

export type SimulatedCampaignPlan = {
  signals: LayerSignal[];
  baseline: CampaignKpiTargets;
  targets: CampaignKpiTargets;
  intelligenceWeight: { mission: number; market: number; metro: number };
  campaignMessage: string;
  recommendedProduct: string | null;
  confidence: number;
  geoScope: string;
};

function pct(value: number | null | undefined): number {
  if (value == null || Number.isNaN(value)) return 0;
  return value > 1 ? value / 100 : value;
}

function toExplorerCriteria(criteria: FinderSearchCriteria): ExplorerTargetCriteria {
  return {
    product: criteria.product,
    state: criteria.state,
    painMin: criteria.minPainIndex,
    purchasePowerMin: criteria.minPurchasePower,
    lifestyleMin: criteria.minLifestyle,
    goal: criteria.goal,
  };
}

function productRevenueShare(executive: ExecutiveSummary, product: string): number {
  if (!product) return 1;
  const rows = executive.product_ranking ?? executive.product_distribution ?? [];
  const total = rows.reduce((sum, row) => sum + (row.revenue ?? 0), 0) || 1;
  const match = rows.find((row) => row.product === product);
  return match ? (match.revenue ?? 0) / total : 0.12;
}

function stateRevenueShare(executive: ExecutiveSummary, state: string): number {
  if (!state) return 1;
  const rows = executive.revenue_by_state ?? executive.state_performance ?? [];
  const total = rows.reduce((sum, row) => sum + (row.revenue ?? 0), 0) || 1;
  const match = rows.find((row) => row.state === state);
  return match ? (match.revenue ?? 0) / total : 0.08;
}

function filterScale(criteria: FinderSearchCriteria): number {
  const lifestyle = 1 - criteria.minLifestyle / 220;
  const pain = 1 - criteria.minPainIndex / 220;
  const pp = 1 - criteria.minPurchasePower / 220;
  return Math.max(0.18, Math.min(1, lifestyle * pain * pp));
}

export function buildMissionSignal(executive: ExecutiveSummary, criteria: FinderSearchCriteria): LayerSignal {
  const productShare = productRevenueShare(executive, criteria.product);
  const scale = filterScale(criteria);
  const customers = Math.round((executive.targetable_customers ?? executive.total_customers ?? 0) * productShare * scale);
  const revenue = Math.round((executive.expected_revenue ?? 0) * productShare * scale);
  const conversion = pct(executive.predicted_conversion_rate ?? executive.expected_conversion ?? executive.conversion_rate);
  const orders = Math.round(customers * conversion);
  const topState =
    executive.top_opportunity_state ??
    executive.top_performing_state ??
    executive.state_performance?.[0]?.state ??
    null;

  return {
    layer: "mission",
    label: "Mission Control",
    href: "/mission-control",
    customers,
    revenue,
    conversion,
    orders,
    opportunityScore: executive.commercial_intelligence?.commercial_health_score ?? null,
    topProduct:
      criteria.product ||
      executive.top_product_opportunity ||
      executive.commercial_intelligence?.highest_opportunity_sku?.product ||
      null,
    geoLabel: topState ? `National · top ${topState}` : "National executive scope",
    active: true,
  };
}

export function buildMarketSignal(
  executive: ExecutiveSummary,
  state: StateDashboard | null,
  criteria: FinderSearchCriteria,
): LayerSignal {
  const active = Boolean(criteria.state && state);
  if (!active || !state) {
    return {
      layer: "market",
      label: "Market Intelligence",
      href: criteria.state ? `/market-intelligence?state=${encodeURIComponent(criteria.state)}` : "/market-intelligence",
      customers: null,
      revenue: null,
      conversion: null,
      orders: null,
      opportunityScore: null,
      topProduct: null,
      geoLabel: criteria.state ? `${criteria.state} (loading…)` : "Select a state",
      active: false,
    };
  }

  const productRow = criteria.product
    ? state.product_opportunity?.find((row) => row.product === criteria.product)
    : state.product_opportunity?.[0];
  const scale = filterScale(criteria);
  const customers = Math.round((productRow?.expected_customers ?? state.kpis.target_customers ?? 0) * scale);
  const revenue = Math.round((productRow?.expected_revenue ?? state.kpis.expected_revenue ?? 0) * scale);
  const conversion = pct(productRow?.expected_orders && customers ? productRow.expected_orders / customers : state.kpis.average_conversion);
  const orders = Math.round(customers * conversion);

  return {
    layer: "market",
    label: "Market Intelligence",
    href: `/market-intelligence?state=${encodeURIComponent(criteria.state)}`,
    customers,
    revenue,
    conversion,
    orders,
    opportunityScore: state.opportunity_score ?? state.geo_intelligence?.opportunity_score ?? null,
    topProduct: productRow?.product ?? state.sellable_products?.[0]?.product ?? criteria.product ?? null,
    geoLabel: `${criteria.state} state view`,
    active: true,
  };
}

export function buildMetroSignal(
  metro: MetroDashboardRow | null,
  criteria: FinderSearchCriteria,
): LayerSignal {
  const active = Boolean(criteria.metroCbsa && metro);
  if (!active || !metro) {
    return {
      layer: "metro",
      label: "Metro Intelligence",
      href: criteria.metroCbsa ? `/metro-intelligence?cbsa=${encodeURIComponent(criteria.metroCbsa)}` : "/metro-intelligence",
      customers: null,
      revenue: null,
      conversion: null,
      orders: null,
      opportunityScore: null,
      topProduct: null,
      geoLabel: criteria.metroCbsa ? "Metro selected" : "Optional metro drill-down",
      active: false,
    };
  }

  const productRow = criteria.product
    ? metro.sellable_products?.find((row) => row.product === criteria.product)
    : metro.sellable_products?.[0];
  const scale = filterScale(criteria);
  const customers = Math.round((productRow?.expected_customers ?? metro.target_customers ?? 0) * scale);
  const revenue = Math.round((productRow?.expected_revenue ?? metro.expected_revenue ?? 0) * scale);
  const conversion = pct(productRow?.expected_orders && customers ? productRow.expected_orders / customers : metro.conversion);
  const orders = Math.round(customers * conversion);

  return {
    layer: "metro",
    label: "Metro Intelligence",
    href: `/metro-intelligence?cbsa=${encodeURIComponent(metro.cbsa_code)}`,
    customers,
    revenue,
    conversion,
    orders,
    opportunityScore: metro.opportunity_score ?? null,
    topProduct: productRow?.product ?? metro.top_product ?? criteria.product ?? null,
    geoLabel: metro.cbsa_name,
    active: true,
  };
}

export function blendSignals(signals: LayerSignal[]): { baseline: CampaignKpiTargets; weights: SimulatedCampaignPlan["intelligenceWeight"] } {
  const active = signals.filter((signal) => signal.active && signal.customers != null);
  if (!active.length) {
    return {
      baseline: { customers: 0, revenue: 0, conversion: 0, orders: 0, roi: null },
      weights: { mission: 1, market: 0, metro: 0 },
    };
  }

  const weights =
    active.length === 3
      ? { mission: 0.2, market: 0.35, metro: 0.45 }
      : active.some((s) => s.layer === "metro") && active.some((s) => s.layer === "market")
        ? { mission: 0.25, market: 0.35, metro: 0.4 }
        : active.some((s) => s.layer === "metro")
          ? { mission: 0.3, market: 0, metro: 0.7 }
          : active.some((s) => s.layer === "market")
            ? { mission: 0.35, market: 0.65, metro: 0 }
            : { mission: 1, market: 0, metro: 0 };

  const weightFor = (layer: IntelligenceLayer) => weights[layer];
  const sumW = active.reduce((sum, signal) => sum + weightFor(signal.layer), 0) || 1;

  const customers = Math.round(
    active.reduce((sum, signal) => sum + (signal.customers ?? 0) * weightFor(signal.layer), 0) / sumW,
  );
  const revenue = Math.round(
    active.reduce((sum, signal) => sum + (signal.revenue ?? 0) * weightFor(signal.layer), 0) / sumW,
  );
  const conversion =
    active.reduce((sum, signal) => sum + (signal.conversion ?? 0) * weightFor(signal.layer), 0) / sumW;
  const orders = Math.round(customers * conversion);

  return {
    baseline: { customers, revenue, conversion, orders, roi: null },
    weights,
  };
}

export function simulateCampaignPlan(args: {
  executive: ExecutiveSummary;
  state: StateDashboard | null;
  metro: MetroDashboardRow | null;
  criteria: FinderSearchCriteria;
  targetAdjustPct?: number;
}): SimulatedCampaignPlan {
  const { executive, state, metro, criteria, targetAdjustPct = 100 } = args;
  const signals = [
    buildMissionSignal(executive, criteria),
    buildMarketSignal(executive, state, criteria),
    buildMetroSignal(metro, criteria),
  ];
  const { baseline, weights } = blendSignals(signals);
  const adjust = Math.max(0.5, Math.min(1.5, targetAdjustPct / 100));

  const targets: CampaignKpiTargets = {
    customers: Math.round(baseline.customers * adjust),
    revenue: Math.round(baseline.revenue * adjust),
    conversion: Math.min(0.35, baseline.conversion * adjust),
    orders: Math.round(baseline.customers * adjust * Math.min(0.35, baseline.conversion * adjust)),
    roi: executive.campaign_roi ?? state?.kpis.campaign_roi ?? null,
  };

  const radar = executive.intelligence_radar ?? [];
  const confidence = radar.length ? radar.reduce((sum, row) => sum + row.score, 0) / radar.length : 72;

  const geoParts = ["United States"];
  if (criteria.state) geoParts.push(criteria.state);
  if (metro?.cbsa_name) geoParts.push(metro.cbsa_name);

  const recommendedProduct =
    signals.find((s) => s.layer === "metro" && s.active)?.topProduct ??
    signals.find((s) => s.layer === "market" && s.active)?.topProduct ??
    signals.find((s) => s.layer === "mission")?.topProduct ??
    criteria.product ??
    null;

  return {
    signals,
    baseline,
    targets,
    intelligenceWeight: weights,
    campaignMessage: deriveCampaignMessage(toExplorerCriteria(criteria)),
    recommendedProduct,
    confidence,
    geoScope: geoParts.join(" → "),
  };
}
