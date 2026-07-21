/** Ceragem Segmentation+ recommendation helpers — uses explicit product ladders. */

import { M_SERIES_PRODUCTS, V_SERIES_PRODUCTS } from "@/lib/config";
import {
  ceragemSegmentSortKey,
  ladderForCeragem,
  mergeLadderWithObserved,
} from "@/lib/product-ladders";
import { effectiveProductPrice } from "@/lib/effective-product-price";

const CERAGEM_TIER_SCORES: Record<string, number> = {
  "High+": 90,
  High: 90,
  "Mid-High+": 70,
  "Mid-High": 70,
  "Mid+": 58,
  Mid: 58,
  "Mid-Low+": 45,
  "Mid-Low": 45,
  "Low+": 25,
  Low: 25,
};

function parseCeragemTier(segment: string): string {
  const text = segment.trim();
  if (text.includes(" · ")) return text.split(" · ")[0]?.trim() ?? text;
  if (text.includes(" + ")) {
    const legacy = text.split(" + ")[0]?.trim() ?? text;
    if (legacy.endsWith("+")) return legacy;
    return `${legacy}+`;
  }
  if (text.endsWith("+")) return text;
  return `${text}+`;
}

export { ceragemSegmentSortKey };

export function sortCeragemSegments<T extends { segment: string }>(rows: T[]): T[] {
  return [...rows].sort((a, b) => {
    const [tierA, axisA, labelA] = ceragemSegmentSortKey(a.segment);
    const [tierB, axisB, labelB] = ceragemSegmentSortKey(b.segment);
    return tierA - tierB || axisA - axisB || labelA.localeCompare(labelB);
  });
}

export function ceragemSegmentScore(segment: string): number {
  const tier = parseCeragemTier(segment);
  return CERAGEM_TIER_SCORES[tier] ?? 50;
}

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

/** Ladder-first segment hover SKUs, filled to ensure V/M mix when needed. */
export function ensureSegmentRecommendationProducts(segment: string, products: string[] | undefined, limit = 6): string[] {
  const ladder = ladderForCeragem(segment);
  const ordered = mergeLadderWithObserved(ladder, products, limit);
  const score = ceragemSegmentScore(segment);
  const sellable = sellableForScore(score, limit * 2);
  const result: string[] = [...ordered];
  const seen = new Set(result);

  const appendFrom = (candidates: string[], series: "v" | "m", maxCount: number) => {
    let added = result.filter((p) => productSeries(p) === series).length;
    for (const product of candidates) {
      if (added >= maxCount || seen.has(product) || productSeries(product) !== series) continue;
      seen.add(product);
      result.push(product);
      added += 1;
    }
  };

  appendFrom([...ordered, ...(products ?? []), ...sellable], "v", 2);
  appendFrom([...ordered, ...(products ?? []), ...sellable], "m", 2);

  for (const product of [...(products ?? []), ...sellable]) {
    if (result.length >= limit || seen.has(product)) continue;
    seen.add(product);
    result.push(product);
  }

  return result.slice(0, limit);
}

export function splitSegmentProductsBySeries(products: string[]): { vSeries: string[]; mSeries: string[] } {
  const vSeries: string[] = [];
  const mSeries: string[] = [];
  for (const product of products) {
    const series = productSeries(product);
    if (series === "v" && !vSeries.includes(product)) vSeries.push(product);
    if (series === "m" && !mSeries.includes(product)) mSeries.push(product);
  }
  return { vSeries, mSeries };
}
