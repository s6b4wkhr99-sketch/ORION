"use client";

import { useEffect, useState } from "react";
import { formatCurrency, formatNumber, formatPercent } from "@/lib/utils";
import { api, type CommercialIntelligenceSummary } from "@/lib/api";
import {
  normalizeActivePromotions,
  normalizePromotionCoverage,
  PROMOTION_COVERAGE_CACHE_VERSION,
  resolveBestStandingPromoSku,
  type PromotionCoverageRow,
} from "@/lib/standing-promotions";
import { promoStyleForCode, uniquePromoCodes } from "@/lib/promo-chip-styles";
import { cn } from "@/lib/utils";
import { WidgetShell } from "./widget-shell";

type Props = {
  data: CommercialIntelligenceSummary;
  uploadId?: string | null;
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

function PromoCodeBadge({
  code,
  promoCodes,
  size = "md",
}: {
  code: string;
  promoCodes: string[];
  size?: "sm" | "md";
}) {
  const style = promoStyleForCode(code, promoCodes);
  return (
    <span
      className={cn(
        "rounded-full border font-semibold",
        size === "sm" ? "px-1.5 py-0.5 text-[10px]" : "px-2.5 py-1 text-xs",
        style.border,
        style.bg,
        style.text,
      )}
    >
      {code}
    </span>
  );
}

export function CommercialIntelligencePanel({ data, uploadId }: Props) {
  const promos = normalizeActivePromotions(data.active_promotions ?? []);
  const bestPromotedSku = resolveBestStandingPromoSku(data);
  const [coverage, setCoverage] = useState<PromotionCoverageRow[]>(() =>
    normalizePromotionCoverage(data.promotion_coverage ?? []),
  );
  const [coverageError, setCoverageError] = useState<string | null>(null);
  const promoCodes = uniquePromoCodes([
    ...promos.map((row) => row.promo_code),
    ...coverage.filter((row) => row.product).map((row) => row.promo_code),
  ]);

  useEffect(() => {
    let cancelled = false;
    setCoverageError(null);

    api
      .getPromotionCoverage(uploadId ?? undefined)
      .then((snapshot) => {
        if (cancelled) return;
        if (snapshot.promotion_coverage_version !== PROMOTION_COVERAGE_CACHE_VERSION) {
          setCoverageError("Promotion coverage version mismatch — refresh the page.");
          return;
        }
        setCoverage(normalizePromotionCoverage(snapshot.promotion_coverage ?? []));
      })
      .catch((error) => {
        if (cancelled) return;
        setCoverageError(error instanceof Error ? error.message : "Failed to load promotion coverage");
        setCoverage(normalizePromotionCoverage(data.promotion_coverage ?? []));
      });

    return () => {
      cancelled = true;
    };
  }, [uploadId, data.promotion_coverage]);

  return (
    <div className="grid gap-6 lg:grid-cols-3">
      <WidgetShell fill title="Active Promotions" subtitle="Standing promotion offers by SKU">
        <div className="flex h-full min-h-0 flex-col gap-2 overflow-auto">
          {promos.length === 0 ? (
            <p className="text-sm text-[var(--cios-secondary)]">No active promotion codes configured.</p>
          ) : (
            promos.map((row) => (
              <div
                key={row.product}
                className="flex items-center justify-between rounded-lg bg-gray-50 px-3 py-2 text-sm"
              >
                <div>
                  <p className="font-medium text-gray-900">{row.product}</p>
                  <p className="text-xs text-[var(--cios-secondary)]">
                    {row.default_promotion_pct != null ? `${row.default_promotion_pct}% Off` : "Promotion"}
                    {row.max_promotion > 0 ? ` · Max ${formatCurrency(row.max_promotion)}` : ""}
                  </p>
                </div>
                <PromoCodeBadge code={row.promo_code} promoCodes={promoCodes} />
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
        subtitle="Conservative promo reach"
      >
        <div className="flex h-full min-h-0 flex-col gap-5">
          {coverageError ? (
            <p className="rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-900">{coverageError}</p>
          ) : null}
          {(coverage.length ? coverage : [{ promo_code: "—", customers: 0, coverage_pct: 0, product: null }]).map((row) => {
            const convertParts: string[] = [];
            if ((row.direct ?? 0) > 0 && (row.direct ?? 0) !== row.customers) {
              convertParts.push(`${formatNumber(row.direct ?? 0)} direct`);
            }
            if ((row.up_convert ?? 0) > 0) convertParts.push(`↑${formatNumber(row.up_convert ?? 0)} up`);
            if ((row.down_convert ?? 0) > 0) convertParts.push(`↓${formatNumber(row.down_convert ?? 0)} down`);
            if ((row.segment_in ?? 0) > 0) convertParts.push(`◎${formatNumber(row.segment_in ?? 0)} segment`);
            if ((row.afford_own ?? 0) > 0) {
              convertParts.push(`${formatNumber(row.afford_own ?? 0)} afford own tier`);
            }
            if ((row.unreachable ?? 0) > 0) {
              convertParts.push(`${formatNumber(row.unreachable ?? 0)} unreachable`);
            }
            const isUnassigned = !row.product;
            return (
              <div key={row.product ?? "unassigned"} className="space-y-1">
                <div className="flex justify-between gap-2 text-sm">
                  <span className="inline-flex min-w-0 flex-wrap items-center gap-1.5 font-medium text-gray-800">
                    {isUnassigned ? (
                      row.kpi_basis === "conservative_unassigned"
                        ? "Unassigned · no promo reach"
                        : row.promo_code
                    ) : (
                      <>
                        <span>{row.product}</span>
                        <span className="text-[var(--cios-secondary)]">·</span>
                        <PromoCodeBadge code={row.promo_code} promoCodes={promoCodes} size="sm" />
                      </>
                    )}
                  </span>
                  <span className="shrink-0 text-[var(--cios-secondary)]">
                    {row.product
                      ? `${formatNumber(row.customers)} reach · ${row.coverage_pct}%`
                      : `${formatNumber(row.customers)} · ${row.coverage_pct}%`}
                  </span>
                </div>
                {convertParts.length > 0 ? (
                  <p className="text-[11px] text-[var(--cios-secondary)]">
                    Composition: {convertParts.join(" · ")}
                  </p>
                ) : null}
                <div className="h-2 overflow-hidden rounded-full bg-gray-100">
                  <div
                    className={`h-full rounded-full ${row.product ? "bg-indigo-500" : "bg-gray-400"}`}
                    style={{ width: `${Math.min(100, row.coverage_pct)}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </WidgetShell>
    </div>
  );
}
