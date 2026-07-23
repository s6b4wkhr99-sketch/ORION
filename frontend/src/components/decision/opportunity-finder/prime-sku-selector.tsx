"use client";

import { PRODUCT_OPTIONS } from "@/lib/config";
import { promoStyleForCode, uniquePromoCodes } from "@/lib/promo-chip-styles";
import type { StandingPromotionRow } from "@/lib/standing-promotions";
import { cn } from "@/lib/utils";

type PrimeSkuSelectorProps = {
  mainSku: string;
  additionalSkus: string[];
  onMainChange: (sku: string) => void;
  onAdditionalChange: (skus: string[]) => void;
  bySku?: Array<{ product: string; customers: number; revenue: number }>;
  activePromotions?: StandingPromotionRow[];
};

export function PrimeSkuSelector({
  mainSku,
  additionalSkus,
  onMainChange,
  onAdditionalChange,
  bySku,
  activePromotions = [],
}: PrimeSkuSelectorProps) {
  const promoBySku = new Map(activePromotions.map((row) => [row.product, row]));
  const promoCodes = uniquePromoCodes(activePromotions.map((row) => row.promo_code));

  const toggleAdditional = (sku: string) => {
    if (sku === mainSku) return;
    if (additionalSkus.includes(sku)) {
      onAdditionalChange(additionalSkus.filter((code) => code !== sku));
    } else {
      onAdditionalChange([...additionalSkus, sku]);
    }
  };

  return (
    <section className="orion-widget p-5">
      <h2 className="text-base font-semibold text-gray-900">Prime SKU Selection</h2>
      <p className="mt-1 text-xs text-[var(--cios-secondary)]">
        Email campaigns require one Main SKU. Add supporting SKUs to evaluate combined DB potential.
      </p>

      {activePromotions.length ? (
        <div className="mt-3 flex flex-wrap items-center gap-3 text-[10px] text-[var(--cios-secondary)]">
          {activePromotions.map((row) => {
            const style = promoStyleForCode(row.promo_code, promoCodes);
            return (
              <span key={row.product} className="inline-flex items-center gap-1.5">
                <span className={cn("inline-block h-2.5 w-2.5 rounded-full border", style.legendDot)} />
                {row.product} · {row.promo_code}
                {row.default_promotion_pct != null ? ` (${row.default_promotion_pct}%)` : ""}
              </span>
            );
          })}
        </div>
      ) : null}

      <div className="mt-4">
        <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-[var(--cios-secondary)]">Main SKU (required)</p>
        <div className="flex flex-wrap gap-2">
          {PRODUCT_OPTIONS.map((sku) => (
            <SkuChip
              key={`main-${sku}`}
              label={sku}
              active={mainSku === sku}
              tone="main"
              promo={promoBySku.get(sku)}
              promoCodes={promoCodes}
              onClick={() => {
                onMainChange(sku);
                onAdditionalChange(additionalSkus.filter((code) => code !== sku));
              }}
            />
          ))}
        </div>
      </div>

      <div className="mt-5">
        <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-[var(--cios-secondary)]">Additional SKUs (multi)</p>
        <div className="flex flex-wrap gap-2">
          {PRODUCT_OPTIONS.filter((sku) => sku !== mainSku).map((sku) => (
            <SkuChip
              key={`add-${sku}`}
              label={sku}
              active={additionalSkus.includes(sku)}
              tone="add"
              promo={promoBySku.get(sku)}
              promoCodes={promoCodes}
              onClick={() => toggleAdditional(sku)}
            />
          ))}
        </div>
      </div>

      {bySku?.length ? (
        <div className="mt-5 overflow-x-auto">
          <table className="min-w-full text-xs">
            <thead>
              <tr className="border-b border-[var(--cios-border)] text-left text-[var(--cios-secondary)]">
                <th className="py-2 pr-3">SKU</th>
                <th className="py-2 pr-3">Promotion</th>
                <th className="py-2 pr-3">DB Customers</th>
                <th className="py-2">DB Revenue</th>
              </tr>
            </thead>
            <tbody>
              {bySku.map((row) => {
                const promo = promoBySku.get(row.product);
                return (
                  <tr key={row.product} className="border-b border-gray-100">
                    <td className="py-2 pr-3 font-medium text-gray-900">
                      {row.product}
                      {row.product === mainSku ? " · Main" : additionalSkus.includes(row.product) ? " · Add-on" : ""}
                    </td>
                    <td className="py-2 pr-3">
                      {promo ? (
                        <PromoBadge promo={promo} promoCodes={promoCodes} />
                      ) : (
                        "—"
                      )}
                    </td>
                    <td className="py-2 pr-3">{row.customers.toLocaleString()}</td>
                    <td className="py-2">${Math.round(row.revenue).toLocaleString()}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      ) : null}
    </section>
  );
}

function PromoBadge({ promo, promoCodes }: { promo: StandingPromotionRow; promoCodes: string[] }) {
  const style = promoStyleForCode(promo.promo_code, promoCodes);
  return (
    <span
      className={cn(
        "rounded-full border px-2 py-0.5 text-[10px] font-medium",
        style.border,
        style.bg,
        style.text,
      )}
    >
      {promo.promo_code}
      {promo.default_promotion_pct != null ? ` · ${promo.default_promotion_pct}%` : ""}
    </span>
  );
}

function SkuChip({
  label,
  active,
  tone,
  promo,
  promoCodes,
  onClick,
}: {
  label: string;
  active: boolean;
  tone: "main" | "add";
  promo?: StandingPromotionRow;
  promoCodes: string[];
  onClick: () => void;
}) {
  const hasPromo = Boolean(promo?.promo_code);
  const promoStyle = hasPromo ? promoStyleForCode(promo!.promo_code, promoCodes) : null;
  const promoLabel =
    promo?.promo_code && promo.default_promotion_pct != null
      ? `${promo.promo_code} · ${promo.default_promotion_pct}% off`
      : promo?.promo_code;

  return (
    <button
      type="button"
      onClick={onClick}
      title={promoLabel}
      className={cn(
        "rounded-full border px-3 py-1.5 text-xs font-medium transition-colors",
        active && tone === "main" && "border-indigo-600 bg-indigo-600 text-white",
        active && tone === "add" && "border-teal-600 bg-teal-50 text-teal-800",
        !active && hasPromo && promoStyle && cn(promoStyle.border, promoStyle.bg, promoStyle.text, "hover:opacity-90"),
        !active && !hasPromo && "border-gray-200 bg-white text-gray-700 hover:border-indigo-300",
        active && hasPromo && promoStyle && cn("ring-2 ring-offset-1", promoStyle.ring),
      )}
    >
      <span className="inline-flex items-center gap-1.5">
        {hasPromo && promoStyle ? (
          <span className={cn("h-1.5 w-1.5 rounded-full", active ? "bg-white/80" : promoStyle.dot)} />
        ) : null}
        {label}
      </span>
    </button>
  );
}
