import { GAP_SKU_DISPLAY_ORDER } from "@/lib/buyer-gap-order";
import { productColor } from "@/lib/product-visual";

/** Actual purchase SKU tokens → catalog product (for colors only). */
export const PURCHASE_SKU_TO_PRODUCT: Record<string, string> = {
  V4: "Master S4",
  S4: "Master S4",
  V5: "Master V5",
  V6: "Master V6",
  V7: "Master V7",
  V9: "Master V9",
  M2: "Pause M2",
  M4: "Pause M4",
  M6: "Pause M6",
  M6S: "Pause M6s",
  M10: "Pause M10",
};

const V_SERIES_SKUS = new Set(["V9", "V7", "V6", "V5", "V4", "S4"]);

export function purchaseSkuColor(sku: string | null | undefined): string {
  if (!sku) return productColor(null);
  const product = PURCHASE_SKU_TO_PRODUCT[sku.toUpperCase()];
  return productColor(product ?? sku);
}

export function purchaseSkuLegendOrder(skus: Iterable<string>): string[] {
  const seen = new Set([...skus].map((sku) => sku.toUpperCase()));
  const ordered = GAP_SKU_DISPLAY_ORDER.filter((sku) => seen.has(sku));
  for (const sku of seen) {
    if (!ordered.includes(sku)) ordered.push(sku);
  }
  return ordered;
}

export function purchaseSkuBelongsToVSeries(sku: string): boolean {
  return V_SERIES_SKUS.has(sku.toUpperCase());
}

/** User-facing legend / tooltip label from actual purchase SKU token. */
export function purchaseSkuLegendLabel(sku: string): string {
  const token = sku.toUpperCase();
  if (token === "S4") return "Master S4";
  if (token.startsWith("V")) return `Master ${token}`;
  if (token === "M6S") return "Pause M6s";
  if (token.startsWith("M")) return `Pause ${token}`;
  return token;
}

export function purchaseSkuProductLabel(sku: string): string {
  return purchaseSkuLegendLabel(sku);
}
