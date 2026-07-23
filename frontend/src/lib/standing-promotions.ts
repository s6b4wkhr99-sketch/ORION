/** Active promotions — loaded from API (`active_promotions`); codes and % are runtime-variable. */
export const STANDING_PROMOTION_ORDER = [
  "Master V6",
  "Master V5",
  "Master S4",
  "Pause M10",
  "Pause M6s",
] as const;

/** Bump when Promotion Coverage KPI logic changes — used in executive cache keys + stale detection. */
export const PROMOTION_COVERAGE_CACHE_VERSION = "conservative-v1";

const STANDING_PROMOTION_SET = new Set<string>(STANDING_PROMOTION_ORDER);

export type StandingPromotionRow = {
  product: string;
  promo_code: string;
  max_promotion: number;
  default_promotion_pct: number | null;
  selling_price: number;
  status: string;
};

/** Map legacy Pause S4 API rows to Master S4 (same product). */
export function normalizeStandingPromoProduct(product: string | null | undefined): string {
  const code = (product ?? "").trim();
  if (code === "Pause S4" || code === "Master V4") return "Master S4";
  return code;
}

export function normalizeActivePromotions(rows: StandingPromotionRow[]): StandingPromotionRow[] {
  const merged = new Map<string, StandingPromotionRow>();
  for (const row of rows) {
    const product = normalizeStandingPromoProduct(row.product);
    if (!product || product === "Pause S4") continue;
    merged.set(product, { ...row, product });
  }
  return filterStandingPromotions([...merged.values()]);
}

export type PromotionCoverageRow = {
  product?: string | null;
  promo_code: string;
  customers: number;
  coverage_pct: number;
  projected?: boolean;
  primary_direct?: number;
  direct?: number;
  up_convert?: number;
  down_convert?: number;
  segment_in?: number;
  afford_own?: number;
  unreachable?: number;
  kpi_basis?: string;
  promotion_coverage_version?: string;
};

export function normalizePromotionCoverage(rows: PromotionCoverageRow[]): PromotionCoverageRow[] {
  const productRows = rows.filter((row) => row.product);
  const unassignedRows = rows.filter((row) => !row.product);
  const merged = new Map<string, PromotionCoverageRow>();
  for (const row of productRows) {
    const product = normalizeStandingPromoProduct(row.product);
    const prev = merged.get(product);
    if (!prev) {
      merged.set(product, { ...row, product });
      continue;
    }
    merged.set(product, {
      ...prev,
      promo_code: prev.promo_code || row.promo_code,
      customers: prev.customers + row.customers,
      coverage_pct: Math.round((prev.coverage_pct + row.coverage_pct) * 10) / 10,
      projected: prev.projected || row.projected,
      primary_direct: (prev.primary_direct ?? 0) + (row.primary_direct ?? 0),
      direct: (prev.direct ?? 0) + (row.direct ?? 0),
      up_convert: (prev.up_convert ?? 0) + (row.up_convert ?? 0),
      down_convert: (prev.down_convert ?? 0) + (row.down_convert ?? 0),
      segment_in: (prev.segment_in ?? 0) + (row.segment_in ?? 0),
      kpi_basis: prev.kpi_basis || row.kpi_basis,
    });
  }
  const standingRows = STANDING_PROMOTION_ORDER.flatMap((product) => {
    const row = merged.get(product);
    return row ? [row] : [];
  });
  const unassigned = unassignedRows.reduce<PromotionCoverageRow | null>((acc, row) => {
    if (!acc) {
      return { ...row, product: null };
    }
    return {
      ...acc,
      customers: acc.customers + row.customers,
      coverage_pct: Math.round((acc.coverage_pct + row.coverage_pct) * 10) / 10,
      afford_own: (acc.afford_own ?? 0) + (row.afford_own ?? 0),
      unreachable: (acc.unreachable ?? 0) + (row.unreachable ?? 0),
    };
  }, null);
  return unassigned ? [...standingRows, unassigned] : standingRows;
}

/** True when a cached executive payload still reflects pre-conservative coverage logic. */
export function isStalePromotionCoverageCache(
  commercial: { promotion_coverage?: PromotionCoverageRow[]; promotion_coverage_version?: string } | null | undefined,
): boolean {
  if (!commercial?.promotion_coverage?.length) return false;
  return commercial.promotion_coverage_version !== PROMOTION_COVERAGE_CACHE_VERSION;
}

export function filterStandingPromotions(rows: StandingPromotionRow[]): StandingPromotionRow[] {
  const byProduct = new Map(rows.map((row) => [row.product, row]));
  return STANDING_PROMOTION_ORDER.flatMap((product) => {
    const row = byProduct.get(product);
    return row ? [row] : [];
  });
}

export function isStandingPromotionProduct(product: string): boolean {
  return STANDING_PROMOTION_SET.has(product);
}

export function activePromotionMap(rows: StandingPromotionRow[]): Map<string, StandingPromotionRow> {
  return new Map(normalizeActivePromotions(rows).map((row) => [row.product, row]));
}

export type CommercialSkuHighlight = {
  product: string | null;
  net_profit_pct: number | null;
  net_profit: number | null;
  recommended_promotion?: number | null;
  promotion_pct?: number | null;
  promo_code?: string | null;
  standing_promotion?: boolean;
  standing_promotion_margin_pct?: number | null;
};

export type CommercialSkuKpiRow = CommercialSkuHighlight & {
  product: string;
};

export function resolveBestStandingPromoSku(data: {
  best_standing_promo_sku?: CommercialSkuHighlight | null;
  highest_margin_sku?: CommercialSkuHighlight | null;
  sku_commercial_kpis?: CommercialSkuKpiRow[];
  active_promotions?: StandingPromotionRow[];
}): CommercialSkuHighlight | null {
  if (data.best_standing_promo_sku?.product) {
    return data.best_standing_promo_sku;
  }

  const anchorMargin = data.highest_margin_sku?.net_profit_pct ?? null;
  const promotedKpis = (data.sku_commercial_kpis ?? []).filter((row) => isStandingPromotionProduct(row.product));
  if (promotedKpis.length) {
    const best =
      anchorMargin != null
        ? [...promotedKpis].sort(
            (a, b) =>
              Math.abs((a.net_profit_pct ?? 0) - anchorMargin) -
              Math.abs((b.net_profit_pct ?? 0) - anchorMargin),
          )[0]
        : [...promotedKpis].sort(
            (a, b) => (b.net_profit_pct ?? Number.NEGATIVE_INFINITY) - (a.net_profit_pct ?? Number.NEGATIVE_INFINITY),
          )[0];
    return {
      product: best.product,
      net_profit_pct: best.net_profit_pct ?? null,
      net_profit: best.net_profit ?? null,
      recommended_promotion: best.recommended_promotion ?? null,
      promotion_pct: best.promotion_pct ?? null,
      promo_code: best.promo_code ?? null,
      standing_promotion: Boolean(best.promo_code),
    };
  }

  const promos = filterStandingPromotions(data.active_promotions ?? []);
  const first = promos[0];
  if (!first) return null;

  return {
    product: first.product,
    net_profit_pct: null,
    net_profit: null,
    promotion_pct: first.default_promotion_pct != null ? first.default_promotion_pct / 100 : null,
    standing_promotion_margin_pct: first.default_promotion_pct != null ? first.default_promotion_pct / 100 : null,
    promo_code: first.promo_code,
    standing_promotion: true,
  };
}
