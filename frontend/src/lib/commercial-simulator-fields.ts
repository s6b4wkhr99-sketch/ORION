import type { StandingPromotionRow } from "@/lib/standing-promotions";

export function catalogPriceForSku(
  sku: string,
  standingPromoBySku: Map<string, StandingPromotionRow>,
  catalogPrices: Map<string, number>,
): number {
  return standingPromoBySku.get(sku)?.selling_price ?? catalogPrices.get(sku) ?? 0;
}

function splitCountAcross(count: number, slots: number): number[] {
  if (slots <= 0) return [];
  const base = Math.floor(count / slots);
  const remainder = count - base * slots;
  return Array.from({ length: slots }, (_, idx) => base + (idx < remainder ? 1 : 0));
}

function buildSkuTargetMixFromPromoCodes(
  selectedSkus: string[],
  audiencePromoCodeMix: { promo_code: string; count: number }[],
  standingPromoBySku: Map<string, StandingPromotionRow>,
): { sku: string; count: number }[] | undefined {
  if (!audiencePromoCodeMix.length || selectedSkus.length === 0) return undefined;

  const promoCounts = new Map(audiencePromoCodeMix.map((row) => [row.promo_code, row.count]));
  const skusByPromo = new Map<string, string[]>();

  for (const sku of selectedSkus) {
    const promoCode = standingPromoBySku.get(sku)?.promo_code?.trim();
    if (!promoCode) continue;
    const group = skusByPromo.get(promoCode) ?? [];
    group.push(sku);
    skusByPromo.set(promoCode, group);
  }

  const result: { sku: string; count: number }[] = [];
  for (const [promoCode, skus] of skusByPromo) {
    const total = promoCounts.get(promoCode) ?? 0;
    if (total <= 0) continue;
    const split = splitCountAcross(total, skus.length);
    skus.forEach((sku, idx) => {
      const count = split[idx] ?? 0;
      if (count > 0) result.push({ sku, count });
    });
  }

  return result.length ? result : undefined;
}

export function buildSkuTargetMix(
  selectedSkus: string[],
  audienceSkuMix?: { sku: string; count: number }[],
  opts?: {
    audiencePromoCodeMix?: { promo_code: string; count: number }[];
    standingPromoBySku?: Map<string, StandingPromotionRow>;
  },
): { sku: string; count: number }[] | undefined {
  if (audienceSkuMix?.length) {
    const mixMap = new Map(audienceSkuMix.map((row) => [row.sku, row.count]));
    const mix = selectedSkus
      .map((sku) => ({ sku, count: mixMap.get(sku) ?? 0 }))
      .filter((row) => row.count > 0);
    if (mix.length) return mix;
  }

  if (opts?.audiencePromoCodeMix?.length && opts.standingPromoBySku) {
    return buildSkuTargetMixFromPromoCodes(selectedSkus, opts.audiencePromoCodeMix, opts.standingPromoBySku);
  }

  return undefined;
}

export function skuTargetMixUsesPromoCodes(
  selectedSkus: string[],
  audienceSkuMix?: { sku: string; count: number }[],
  audiencePromoCodeMix?: { promo_code: string; count: number }[],
): boolean {
  if (audienceSkuMix?.length) {
    const mixMap = new Map(audienceSkuMix.map((row) => [row.sku, row.count]));
    if (selectedSkus.some((sku) => (mixMap.get(sku) ?? 0) > 0)) return false;
  }
  return Boolean(audiencePromoCodeMix?.length);
}

export function computeAverageSellingPrice(opts: {
  mainSku: string;
  additionalSkus: string[];
  standingPromoBySku: Map<string, StandingPromotionRow>;
  catalogPrices: Map<string, number>;
  audienceSkuMix?: { sku: string; count: number }[];
  audiencePromoCodeMix?: { promo_code: string; count: number }[];
  audienceAvgSellingPrice?: number | null;
}): number {
  const {
    mainSku,
    additionalSkus,
    standingPromoBySku,
    catalogPrices,
    audienceSkuMix,
    audiencePromoCodeMix,
    audienceAvgSellingPrice,
  } = opts;
  const selectedSkus = [mainSku, ...additionalSkus];

  if (audienceSkuMix?.length) {
    let weighted = 0;
    let total = 0;
    for (const row of audienceSkuMix) {
      if (!selectedSkus.includes(row.sku)) continue;
      const price = catalogPriceForSku(row.sku, standingPromoBySku, catalogPrices);
      if (price > 0 && row.count > 0) {
        weighted += price * row.count;
        total += row.count;
      }
    }
    if (total > 0) return Math.round((weighted / total) * 100) / 100;
  }

  const promoMixTargets = buildSkuTargetMixFromPromoCodes(
    selectedSkus,
    audiencePromoCodeMix ?? [],
    standingPromoBySku,
  );
  if (promoMixTargets?.length) {
    let weighted = 0;
    let total = 0;
    for (const row of promoMixTargets) {
      const price = catalogPriceForSku(row.sku, standingPromoBySku, catalogPrices);
      if (price > 0 && row.count > 0) {
        weighted += price * row.count;
        total += row.count;
      }
    }
    if (total > 0) return Math.round((weighted / total) * 100) / 100;
  }

  if (audienceAvgSellingPrice != null && audienceAvgSellingPrice > 0 && selectedSkus.length === 1) {
    return audienceAvgSellingPrice;
  }

  const prices = selectedSkus
    .map((sku) => catalogPriceForSku(sku, standingPromoBySku, catalogPrices))
    .filter((price) => price > 0);
  if (!prices.length) return 0;
  return Math.round((prices.reduce((sum, price) => sum + price, 0) / prices.length) * 100) / 100;
}

export function formatSkuPromoCodes(opts: {
  mainSku: string;
  additionalSkus: string[];
  standingPromoBySku: Map<string, StandingPromotionRow>;
  audienceProduct?: string | null;
  audiencePromoCode?: string | null;
}): string {
  const { mainSku, additionalSkus, standingPromoBySku, audienceProduct, audiencePromoCode } = opts;
  return [mainSku, ...additionalSkus]
    .map((sku) => {
      const standingCode = standingPromoBySku.get(sku)?.promo_code;
      const code = standingCode ?? (sku === audienceProduct ? audiencePromoCode : null);
      return code ? `${sku} · ${code}` : sku;
    })
    .join(" · ");
}

export function resolveSingleSkuPromoCode(opts: {
  mainSku: string;
  standingPromoBySku: Map<string, StandingPromotionRow>;
  audienceProduct?: string | null;
  audiencePromoCode?: string | null;
}): string | undefined {
  const { mainSku, standingPromoBySku, audienceProduct, audiencePromoCode } = opts;
  const standingCode = standingPromoBySku.get(mainSku)?.promo_code;
  const code = standingCode ?? (mainSku === audienceProduct ? audiencePromoCode : null);
  return code?.trim() || undefined;
}

export function describeStandingPromo(
  sku: string,
  standingPromoBySku: Map<string, StandingPromotionRow>,
  catalogPrices: Map<string, number>,
): string {
  const promo = standingPromoBySku.get(sku);
  const selling = catalogPriceForSku(sku, standingPromoBySku, catalogPrices);
  if (!promo?.promo_code) {
    return selling > 0 ? `No standing promo · catalog ${formatMoney(selling)}` : "No standing promo";
  }
  const parts = [promo.promo_code];
  if (promo.default_promotion_pct != null) parts.push(`${promo.default_promotion_pct}%`);
  if (promo.max_promotion) parts.push(`max ${formatMoney(promo.max_promotion)}`);
  if (selling > 0) parts.push(formatMoney(selling));
  return parts.join(" · ");
}

export function resolveLayeredPromotionForSku(
  sku: string,
  standingPromoBySku: Map<string, StandingPromotionRow>,
  additionalPct: number,
  additionalMax: number,
) {
  const standing = standingPromoBySku.get(sku);
  const basePct = standing?.default_promotion_pct != null ? standing.default_promotion_pct / 100 : 0;
  const baseMax = standing?.max_promotion ?? 0;
  return {
    basePct,
    baseMax,
    totalPct: basePct + additionalPct,
    totalMax: baseMax + additionalMax,
  };
}

export function parseAdditionalPromoInputs(additionalPct: string, additionalMax: string) {
  const hasPct = additionalPct.trim() !== "";
  const hasMax = additionalMax.trim() !== "";
  if (!hasPct && !hasMax) return {};
  const payload: { additionalPromotionPct?: number; additionalPromotionMax?: number } = {};
  if (hasPct) payload.additionalPromotionPct = Number(additionalPct);
  if (hasMax) payload.additionalPromotionMax = Number(additionalMax);
  return payload;
}

function formatMoney(amount: number): string {
  return `$${amount.toLocaleString("en-US", { maximumFractionDigits: 0 })}`;
}
