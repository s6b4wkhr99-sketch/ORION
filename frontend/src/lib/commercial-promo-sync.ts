/** Sync additional promotion % (decimal) ↔ $ using catalog selling price. */

export function additionalPromoDollarsFromPct(pctDecimal: number, sellingPrice: number): number {
  if (!Number.isFinite(pctDecimal) || !Number.isFinite(sellingPrice) || sellingPrice <= 0) return 0;
  return Math.round(pctDecimal * sellingPrice * 100) / 100;
}

export function formatAdditionalPromoDollars(amount: number): string {
  if (!Number.isFinite(amount)) return "";
  return amount.toFixed(2);
}

export function formatAdditionalPromoPct(pctDecimal: number): string {
  if (!Number.isFinite(pctDecimal)) return "";
  if (pctDecimal >= 0.01) return pctDecimal.toFixed(4).replace(/(\.\d*?[1-9])0+$/, "$1");
  return pctDecimal.toFixed(6).replace(/(\.\d*?[1-9])0+$/, "$1").replace(/\.0+$/, "");
}

export function additionalPromoPctFromDollars(amount: number, sellingPrice: number): number {
  if (!Number.isFinite(amount) || !Number.isFinite(sellingPrice) || sellingPrice <= 0) return 0;
  return Math.round((amount / sellingPrice) * 10000) / 10000;
}

export function resolveTotalPromotionOverrides(opts: {
  basePctDecimal: number;
  baseMaxPromotion: number;
  additionalPct: string;
  additionalMax: string;
  sellingPrice: number;
}): { promotionPct?: number; maxPromotion?: number } {
  const { basePctDecimal, baseMaxPromotion, additionalPct, additionalMax, sellingPrice } = opts;
  const hasPct = additionalPct.trim() !== "";
  const hasMax = additionalMax.trim() !== "";
  if (!hasPct && !hasMax) return {};

  const addPctNum = hasPct ? Number(additionalPct) : additionalPromoPctFromDollars(Number(additionalMax), sellingPrice);
  const addMaxNum = hasMax
    ? Number(additionalMax)
    : additionalPromoDollarsFromPct(Number(additionalPct), sellingPrice);

  if (!Number.isFinite(addPctNum) && !Number.isFinite(addMaxNum)) return {};

  const totalPct = basePctDecimal + (Number.isFinite(addPctNum) ? addPctNum : 0);
  const totalMax = baseMaxPromotion + (Number.isFinite(addMaxNum) ? addMaxNum : 0);
  return { promotionPct: totalPct, maxPromotion: totalMax };
}
