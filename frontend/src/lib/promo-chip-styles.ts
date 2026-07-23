/** Shared promo-code color palette — used in Active Promotions, Prime SKU selector, etc. */
export type PromoChipStyle = {
  border: string;
  bg: string;
  text: string;
  dot: string;
  ring: string;
  legendDot: string;
  /** Left accent for list rows */
  rowAccent: string;
};

export const PROMO_CHIP_STYLES: PromoChipStyle[] = [
  {
    border: "border-amber-400",
    bg: "bg-amber-50",
    text: "text-amber-950",
    dot: "bg-amber-500",
    ring: "ring-amber-400",
    legendDot: "border-amber-400 bg-amber-50",
    rowAccent: "border-l-amber-500",
  },
  {
    border: "border-violet-400",
    bg: "bg-violet-50",
    text: "text-violet-950",
    dot: "bg-violet-500",
    ring: "ring-violet-400",
    legendDot: "border-violet-400 bg-violet-50",
    rowAccent: "border-l-violet-500",
  },
  {
    border: "border-emerald-400",
    bg: "bg-emerald-50",
    text: "text-emerald-950",
    dot: "bg-emerald-500",
    ring: "ring-emerald-400",
    legendDot: "border-emerald-400 bg-emerald-50",
    rowAccent: "border-l-emerald-500",
  },
  {
    border: "border-sky-400",
    bg: "bg-sky-50",
    text: "text-sky-950",
    dot: "bg-sky-500",
    ring: "ring-sky-400",
    legendDot: "border-sky-400 bg-sky-50",
    rowAccent: "border-l-sky-500",
  },
  {
    border: "border-rose-400",
    bg: "bg-rose-50",
    text: "text-rose-950",
    dot: "bg-rose-500",
    ring: "ring-rose-400",
    legendDot: "border-rose-400 bg-rose-50",
    rowAccent: "border-l-rose-500",
  },
];

export function uniquePromoCodes(codes: Iterable<string>): string[] {
  return [...new Set([...codes].filter(Boolean))];
}

export function promoStyleForCode(promoCode: string, promoCodes: string[]): PromoChipStyle {
  const idx = promoCodes.indexOf(promoCode);
  return PROMO_CHIP_STYLES[(idx >= 0 ? idx : 0) % PROMO_CHIP_STYLES.length];
}
