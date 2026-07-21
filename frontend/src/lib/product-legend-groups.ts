import type { ProductTargetSummary } from "@/lib/product-visual";
import {
  STANDING_PROMO_DONOR_DERIVED_PRODUCTS,
  standingPromoCreditSkus,
  standingPromoDonorSkus,
} from "@/lib/standing-promo-legend";

/** Display-only legend groups — underlying API data stays per SKU. */
export const PAUSE_M6_GROUP_LABEL = "Pause M6 (M6s)";

export type ProductLegendGroup = {
  label: string;
  products: readonly string[];
  /** Brand color source when the group is selected on maps/charts. */
  colorProduct: string;
};

export const PRODUCT_LEGEND_GROUPS: readonly ProductLegendGroup[] = [
  {
    label: PAUSE_M6_GROUP_LABEL,
    products: ["Pause M6", "Pause M6s"],
    colorProduct: "Pause M6",
  },
] as const;

const GROUP_BY_LABEL = new Map(PRODUCT_LEGEND_GROUPS.map((group) => [group.label, group]));

const SKU_TO_GROUP = new Map<string, ProductLegendGroup>();
for (const group of PRODUCT_LEGEND_GROUPS) {
  for (const sku of group.products) {
    SKU_TO_GROUP.set(sku, group);
  }
}

const HIDDEN_SINGLE_LEGEND = new Set(
  PRODUCT_LEGEND_GROUPS.flatMap((group) => [...group.products]),
);

/** User-facing product name — M6/M6s SKUs render as the combined legend label. */
export function displayProductLabel(product: string | null | undefined): string {
  if (!product) return "—";
  return SKU_TO_GROUP.get(product)?.label ?? product;
}

/** Dedupe grouped SKUs when listing products on chart popovers. */
export function displayProductLegendLabels(products: string[]): string[] {
  const seen = new Set<string>();
  const out: string[] = [];
  for (const product of products) {
    const label = displayProductLabel(product);
    if (seen.has(label)) continue;
    seen.add(label);
    out.push(label);
  }
  return out;
}

/** Match chart/map row SKUs to the active legend — grouped SKUs only, no standing-promo donors. */
export function matchesLegendSelection(activeLegend: string | null | undefined, sku: string): boolean {
  if (!activeLegend) return true;
  const sources = sourceProductsForLegend(activeLegend) ?? [activeLegend];
  return sources.includes(sku);
}

type ScatterLegendRow = {
  product?: string | null;
  top_product?: string | null;
  revenue?: number;
  customers?: number;
  orders?: number;
};

function rowSku(row: ScatterLegendRow): string {
  return row.product ?? row.top_product ?? "";
}

/**
 * Filter scatter/radar points for an active legend.
 * Direct SKU rows win; standing-promo legends borrow donor geos to reach minCount.
 */
export function filterScatterPointsForLegend<T extends ScatterLegendRow>(
  points: T[],
  activeLegend: string | null | undefined,
  geoKey: (row: T) => string,
  minCount = 0,
): T[] {
  if (!activeLegend) return points;

  const sources = sourceProductsForLegend(activeLegend) ?? [activeLegend];
  const relabel = (row: T): T => ({ ...row, product: activeLegend, top_product: activeLegend });

  let direct = points.filter((row) => sources.includes(rowSku(row)));

  const usesDonorFill = (STANDING_PROMO_DONOR_DERIVED_PRODUCTS as readonly string[]).includes(activeLegend);
  if (usesDonorFill) {
    const seenGeos = new Set(direct.map(geoKey));
    const donors = new Set(standingPromoDonorSkus(activeLegend));
    const donorCandidates = points
      .filter((row) => donors.has(rowSku(row)) && !seenGeos.has(geoKey(row)))
      .sort((a, b) => Number(b.revenue ?? 0) - Number(a.revenue ?? 0));

    for (const row of donorCandidates) {
      if (minCount > 0 && direct.length >= minCount) break;
      direct = [...direct, relabel(row)];
      seenGeos.add(geoKey(row));
    }
  }

  if (direct.length > 0) return direct;

  if (!usesDonorFill) {
    return direct;
  }

  const donors = new Set(standingPromoDonorSkus(activeLegend));
  const donorRows = points.filter((row) => donors.has(rowSku(row)));
  const byGeo = new Map<string, T>();

  for (const row of donorRows) {
    const key = geoKey(row);
    const existing = byGeo.get(key);
    if (!existing) {
      byGeo.set(key, relabel(row));
      continue;
    }
    byGeo.set(key, {
      ...existing,
      product: activeLegend,
      top_product: activeLegend,
      revenue: Number(existing.revenue ?? 0) + Number(row.revenue ?? 0),
      customers: Number(existing.customers ?? 0) + Number(row.customers ?? 0),
      orders: Number(existing.orders ?? 0) + Number(row.orders ?? 0),
    });
  }

  const merged = [...byGeo.values()].sort((a, b) => Number(b.revenue ?? 0) - Number(a.revenue ?? 0));
  return minCount > 0 ? merged.slice(0, minCount) : merged;
}

/** Choropleth / metro map — direct SKU attribution only (no donor credit). */
export function directProductMetrics(
  revenueByProduct: Record<string, { expected_revenue?: number; target_customers?: number }>,
  activeLegend: string | null | undefined,
): { revenue: number; customers: number } {
  if (!activeLegend) {
    return { revenue: 0, customers: 0 };
  }
  const sources = sourceProductsForLegend(activeLegend) ?? [activeLegend];
  let revenue = 0;
  let customers = 0;
  for (const sku of sources) {
    const row = revenueByProduct[sku];
    revenue += Number(row?.expected_revenue ?? 0);
    customers += Number(row?.target_customers ?? 0);
  }
  return { revenue, customers };
}

/** ZIP choropleth — direct + backend geo-gated outreach (see zcta_choropleth). */
export function choroplethProductMetrics(
  revenueByProduct: Record<string, { expected_revenue?: number; target_customers?: number }>,
  activeLegend: string | null | undefined,
): { revenue: number; customers: number } {
  return directProductMetrics(revenueByProduct, activeLegend);
}

/** M-series legend rows — replaces individual SKUs that belong to a display group. */
export const M_SERIES_DISPLAY_LEGEND = ["Pause M10", PAUSE_M6_GROUP_LABEL, "Pause M4"] as const;

export function isGroupedLegendLabel(label: string | null | undefined): boolean {
  return Boolean(label && GROUP_BY_LABEL.has(label));
}

export function sourceProductsForLegend(label: string | null | undefined): string[] | null {
  if (!label) return null;
  const group = GROUP_BY_LABEL.get(label);
  if (group) return [...group.products];
  return [label];
}

export function colorProductForLegend(label: string | null | undefined): string | null {
  if (!label) return null;
  const group = GROUP_BY_LABEL.get(label) ?? SKU_TO_GROUP.get(label);
  return group?.colorProduct ?? label;
}

export function shouldHideSingleLegendProduct(product: string): boolean {
  return HIDDEN_SINGLE_LEGEND.has(product);
}

export function mergeProductMetrics(
  byProduct: Record<string, { expected_revenue?: number; target_customers?: number } | undefined>,
  products: string[],
): { revenue: number; customers: number } {
  let revenue = 0;
  let customers = 0;
  const credited = new Set<string>();
  for (const product of products) {
    for (const sku of standingPromoCreditSkus(product)) {
      if (credited.has(sku)) continue;
      credited.add(sku);
      const row = byProduct[sku];
      revenue += Number(row?.expected_revenue ?? 0);
      customers += Number(row?.target_customers ?? 0);
    }
  }
  return { revenue, customers };
}

export function mergeProductTargets(
  targets: ProductTargetSummary[] | undefined,
  products: string[],
  label?: string,
): ProductTargetSummary | undefined {
  const creditSkus = [...new Set(products.flatMap((product) => standingPromoCreditSkus(product)))];
  const rows = (targets ?? []).filter((row) => creditSkus.includes(row.product));
  if (!rows.length) return undefined;
  return {
    product: label ?? rows[0].product,
    expected_customers: rows.reduce((sum, row) => sum + row.expected_customers, 0),
    expected_revenue: rows.reduce((sum, row) => sum + row.expected_revenue, 0),
    expected_orders: rows.reduce((sum, row) => sum + row.expected_orders, 0),
  };
}

export function legendEntryHasData(dataProducts: Set<string>, label: string): boolean {
  const sources = sourceProductsForLegend(label) ?? [label];
  for (const product of sources) {
    if (standingPromoCreditSkus(product).some((sku) => dataProducts.has(sku))) {
      return true;
    }
  }
  return false;
}

/** Standing-promo SKUs whose legend totals include donor / outreach credit. */
export const STANDING_PROMO_LEGEND_PRODUCTS = ["Master V6", "Master V5", "Master S4", "Pause M10"] as const;

export function buildLegendTargetMap(
  productTargets: ProductTargetSummary[],
): Map<string, ProductTargetSummary> {
  const map = new Map<string, ProductTargetSummary>();
  for (const target of productTargets) {
    map.set(target.product, target);
  }
  for (const group of PRODUCT_LEGEND_GROUPS) {
    const merged = mergeProductTargets(productTargets, [...group.products], group.label);
    if (merged) map.set(group.label, merged);
  }
  for (const promo of STANDING_PROMO_LEGEND_PRODUCTS) {
    const merged = mergeProductTargets(productTargets, [promo]);
    if (merged) map.set(promo, merged);
  }
  return map;
}

export function mergeSellableProducts(
  rows: ProductTargetSummary[],
): ProductTargetSummary[] {
  const consumed = new Set<string>();
  const out: ProductTargetSummary[] = [];

  for (const group of PRODUCT_LEGEND_GROUPS) {
    const merged = mergeProductTargets(rows, [...group.products], group.label);
    if (merged && merged.expected_customers > 0) {
      out.push(merged);
      group.products.forEach((product) => consumed.add(product));
    }
  }

  for (const row of rows) {
    if (!consumed.has(row.product)) out.push(row);
  }

  return out.sort((a, b) => b.expected_revenue - a.expected_revenue);
}

export function mergeProductChartRows<T extends { product: string; revenue: number; customers: number }>(
  rows: T[],
): T[] {
  const consumed = new Set<string>();
  const out: T[] = [];

  for (const group of PRODUCT_LEGEND_GROUPS) {
    const matching = rows.filter((row) => group.products.includes(row.product));
    if (!matching.length) continue;
    out.push({
      ...matching[0],
      product: group.label,
      revenue: matching.reduce((sum, row) => sum + row.revenue, 0),
      customers: matching.reduce((sum, row) => sum + row.customers, 0),
    });
    group.products.forEach((product) => consumed.add(product));
  }

  for (const row of rows) {
    if (!consumed.has(row.product)) {
      out.push({ ...row, product: displayProductLabel(row.product) } as T);
    }
  }

  return out.sort((a, b) => b.revenue - a.revenue);
}
