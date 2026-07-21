"use client";

import { formatCurrency, formatNumber, formatPercent } from "@/lib/utils";
import type { CommercialIntelligenceSummary } from "@/lib/api";
import { filterStandingPromotions, normalizeActivePromotions, normalizePromotionCoverage, resolveBestStandingPromoSku } from "@/lib/standing-promotions";
import { WidgetShell } from "./widget-shell";

type Props = {
  data: CommercialIntelligenceSummary;
};

function HealthGauge({ score }: { score: number }) {
  const color = score >= 80 ? "#22C55E" : score >= 60 ? "#3B82F6" : "#F59E0B";
  return (
    <div className="flex flex-col items-center justify-center gap-2">
      <div
        className="flex h-24 w-24 items-center justify-center rounded-full border-8 text-2xl font-bold text-gray-900"
        style={{ borderColor: color }}
      >
        {Math.round(score)}
      </div>
      <p className="text-xs text-[var(--cios-secondary)]">Commercial Health</p>
    </div>
  );
}

function promoContext(highlight: CommercialIntelligenceSummary["highest_margin_sku"] | undefined): string {
  if (!highlight?.product) return "";
  if (highlight.standing_promotion && highlight.promotion_pct != null) {
    return `${Math.round(highlight.promotion_pct * 100)}% standing promo`;
  }
  return "No standing promo";
}

function bestPromotedMargin(highlight: CommercialIntelligenceSummary["highest_margin_sku"] | undefined): string {
  if (highlight?.net_profit_pct != null) {
    return formatPercent(highlight.net_profit_pct);
  }
  return "—";
}

export function CommercialIntelligencePanel({ data }: Props) {
  const promos = normalizeActivePromotions(data.active_promotions ?? []);
  const bestPromotedSku = resolveBestStandingPromoSku(data);
  const coverage = normalizePromotionCoverage(data.promotion_coverage ?? []);

  return (
    <div className="grid gap-6 lg:grid-cols-3">
      <WidgetShell fill title="Active Promotions" subtitle="Standing promotion offers by SKU">
        <div className="flex h-full min-h-0 flex-col gap-2 overflow-auto">
          {promos.length === 0 ? (
            <p className="text-sm text-[var(--cios-secondary)]">No active promotion codes configured.</p>
          ) : (
            promos.map((row) => (
              <div key={row.product} className="flex items-center justify-between rounded-lg bg-gray-50 px-3 py-2 text-sm">
                <div>
                  <p className="font-medium text-gray-900">{row.product}</p>
                  <p className="text-xs text-[var(--cios-secondary)]">
                    {row.default_promotion_pct != null ? `${row.default_promotion_pct}% Off` : "Promotion"}
                    {row.max_promotion > 0 ? ` · Max ${formatCurrency(row.max_promotion)}` : ""}
                  </p>
                </div>
                <span className="rounded-full bg-indigo-100 px-2.5 py-1 text-xs font-semibold text-indigo-700">
                  {row.promo_code}
                </span>
              </div>
            ))
          )}
        </div>
      </WidgetShell>

      <WidgetShell
        fill
        title="Commercial KPI Highlights"
        subtitle="Net Margin/Total Address Revenue reflect standing promos"
      >
        <div className="grid h-full gap-4 sm:grid-cols-2">
          <div className="rounded-lg border border-[var(--cios-border)] p-3">
            <p className="text-xs font-medium uppercase tracking-wide text-[var(--cios-secondary)]">Highest Margin</p>
            <p className="mt-1 text-lg font-semibold text-gray-900">{data.highest_margin_sku?.product ?? "—"}</p>
            <p className="text-sm text-gray-600">
              {data.highest_margin_sku?.net_profit_pct != null
                ? formatPercent(data.highest_margin_sku.net_profit_pct)
                : "—"}{" "}
              net margin
            </p>
            <p className="text-[11px] text-[var(--cios-secondary)]">{promoContext(data.highest_margin_sku)}</p>
          </div>
          <div className="rounded-lg border border-[var(--cios-border)] p-3">
            <p className="text-xs font-medium uppercase tracking-wide text-[var(--cios-secondary)]">Best Promoted SKU</p>
            <p className="mt-1 text-lg font-semibold text-gray-900">{bestPromotedSku?.product ?? "—"}</p>
            <p className="text-sm text-gray-600">{bestPromotedMargin(bestPromotedSku ?? undefined)} net margin</p>
          </div>
          <div className="rounded-lg border border-[var(--cios-border)] p-3 sm:col-span-2">
            <p className="text-xs font-medium uppercase tracking-wide text-[var(--cios-secondary)]">Highest Opportunity</p>
            <p className="mt-1 text-lg font-semibold text-gray-900">{data.highest_opportunity_sku?.product ?? "—"}</p>
            <p className="text-sm text-gray-600">
              {data.highest_opportunity_sku?.expected_revenue != null
                ? formatCurrency(data.highest_opportunity_sku.expected_revenue)
                : "—"}{" "}
              expected
              {data.highest_opportunity_sku?.customer_share_pct != null
                ? ` · ${data.highest_opportunity_sku.customer_share_pct}% of addressable customers`
                : data.highest_opportunity_sku?.revenue_share_pct != null
                  ? ` · ${data.highest_opportunity_sku.revenue_share_pct}% revenue share`
                  : ""}
            </p>
          </div>
          <div className="flex items-center justify-center sm:col-span-2">
            <HealthGauge score={data.commercial_health_score ?? 0} />
          </div>
        </div>
      </WidgetShell>

      <WidgetShell
        fill
        title="Promotion Coverage"
        subtitle="Post-promo price addressable reach (% of targetable customers)"
      >
        <div className="flex h-full min-h-0 flex-col gap-5">
          {(coverage.length ? coverage : [{ promo_code: "—", customers: 0, coverage_pct: 0 }]).map((row) => {
            const convertParts: string[] = [];
            if ((row.up_convert ?? 0) > 0) convertParts.push(`↑${formatNumber(row.up_convert ?? 0)} up`);
            if ((row.down_convert ?? 0) > 0) convertParts.push(`↓${formatNumber(row.down_convert ?? 0)} down`);
            if ((row.direct ?? 0) > 0 && (row.up_convert ?? 0) + (row.down_convert ?? 0) > 0) {
              convertParts.unshift(`${formatNumber(row.direct ?? 0)} direct`);
            }
            return (
              <div key={row.product ?? row.promo_code} className="space-y-1">
                <div className="flex justify-between text-sm">
                  <span className="font-medium text-gray-800">
                    {row.product ? `${row.product} · ${row.promo_code}` : row.promo_code}
                  </span>
                  <span className="text-[var(--cios-secondary)]">
                    {formatNumber(row.customers)} · {row.coverage_pct}%
                  </span>
                </div>
                {convertParts.length > 0 ? (
                  <p className="text-[11px] text-[var(--cios-secondary)]">{convertParts.join(" · ")}</p>
                ) : null}
                <div className="h-2 overflow-hidden rounded-full bg-gray-100">
                  <div className="h-full rounded-full bg-indigo-500" style={{ width: `${Math.min(100, row.coverage_pct)}%` }} />
                </div>
              </div>
            );
          })}
        </div>
      </WidgetShell>
    </div>
  );
}
