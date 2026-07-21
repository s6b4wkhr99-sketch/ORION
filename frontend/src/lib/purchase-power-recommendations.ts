/** Purchase Power band recommendation helpers — mirrors backend series-mix rules. */

import { M_SERIES_PRODUCTS, V_SERIES_PRODUCTS } from "@/lib/config";

export const PURCHASE_POWER_BAND_SCORES: Record<string, number> = {
  "$150K+": 85,
  "$100K–$150K": 68,
  "$75K–$100K": 52,
  "$50K–$75K": 38,
  "<$50K": 25,
};

import { effectiveProductPrice } from "@/lib/effective-product-price";

function productSeries(product: string): "v" | "m" | "other" {
  if (product.startsWith("Master V") || product === "Master S4") return "v";
  if (product.startsWith("Pause M")) return "m";
  return "other";
}

function priceAccessibilityFit(product: string, purchasePowerScore: number): number {
  const price = effectiveProductPrice(product);
  if (purchasePowerScore < 38) {
    if (price <= 4200) return 9;
    if (price <= 5500) return 6;
    if (price <= 6500) return 2;
    return -5;
  }
  if (purchasePowerScore < 58) {
    if (price >= 4200 && price <= 7000) return 5;
    if (price <= 5500) return 4;
    return 0;
  }
  if (price >= 9000) return 8;
  if (price >= 7500) return 5;
  return 1;
}

function sellableForScore(score: number, limit = 12): string[] {
  const active = [...V_SERIES_PRODUCTS, ...M_SERIES_PRODUCTS];
  return [...active]
    .map((product) => ({ product, fit: priceAccessibilityFit(product, score) }))
    .filter((row) => row.fit > 0)
    .sort((a, b) => b.fit - a.fit)
    .map((row) => row.product)
    .slice(0, limit);
}

/** Ensure at least 2 V-series and 2 M-series picks (band recommendations + price accessibility). */
export function ensureBandRecommendationProducts(band: string, products: string[] | undefined, limit = 6): string[] {
  const score = PURCHASE_POWER_BAND_SCORES[band] ?? 50;
  const topRecommended = products ?? [];
  const sellable = sellableForScore(score, limit * 2);
  const result: string[] = [];
  const seen = new Set<string>();

  const appendFrom = (candidates: string[], series: "v" | "m", maxCount: number) => {
    let added = 0;
    for (const product of candidates) {
      if (added >= maxCount || seen.has(product) || productSeries(product) !== series) continue;
      seen.add(product);
      result.push(product);
      added += 1;
    }
    return added;
  };

  const vRec = topRecommended.filter((p) => productSeries(p) === "v");
  const mRec = topRecommended.filter((p) => productSeries(p) === "m");
  const vSell = sellable.filter((p) => productSeries(p) === "v");
  const mSell = sellable.filter((p) => productSeries(p) === "m");

  let vAdded = appendFrom(vRec, "v", 2);
  if (vAdded < 2) vAdded += appendFrom(vSell, "v", 2 - vAdded);

  let mAdded = appendFrom(mRec, "m", 2);
  if (mAdded < 2) mAdded += appendFrom(mSell, "m", 2 - mAdded);

  for (const product of [...topRecommended, ...sellable]) {
    if (result.length >= limit || seen.has(product)) continue;
    seen.add(product);
    result.push(product);
  }

  return result.slice(0, limit);
}

export function splitBandProductsBySeries(products: string[]): { vSeries: string[]; mSeries: string[] } {
  const vSeries: string[] = [];
  const mSeries: string[] = [];
  for (const product of products) {
    const series = productSeries(product);
    if (series === "v" && !vSeries.includes(product)) vSeries.push(product);
    if (series === "m" && !mSeries.includes(product)) mSeries.push(product);
  }
  return { vSeries, mSeries };
}
