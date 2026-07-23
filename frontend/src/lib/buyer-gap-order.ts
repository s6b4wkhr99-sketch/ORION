/** Ceragem chair SKU display order for buyer GAP reports (V-line then M-line). */
export const GAP_SKU_DISPLAY_ORDER = [
  "V9",
  "V7",
  "V6",
  "V5",
  "V4",
  "S4",
  "M10",
  "M6",
  "M6S",
  "M2",
  "M4",
] as const;

const GAP_SKU_RANK = new Map<string, number>(
  GAP_SKU_DISPLAY_ORDER.map((sku, index) => [sku, index]),
);

export function sortGapSkuEntries<T>(entries: [string, T][]): [string, T][] {
  return [...entries].sort((a, b) => {
    const rankA = GAP_SKU_RANK.get(a[0].toUpperCase()) ?? 999;
    const rankB = GAP_SKU_RANK.get(b[0].toUpperCase()) ?? 999;
    if (rankA !== rankB) return rankA - rankB;
    return a[0].localeCompare(b[0]);
  });
}
