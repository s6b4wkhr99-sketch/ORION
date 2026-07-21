"use client";

import type { MarketSizing, StateDashboard } from "@/lib/api";
import { formatCurrency, formatNumber, formatPercent } from "@/lib/utils";
import { SegmentDonutPanel } from "@/components/ui/segment-donut-panel";
import { MockupKpiCard } from "@/components/mockup/mockup-kpi-card";
import { ExpectedRevenueInfo } from "@/components/ui/info-tooltip";

type MarketDetailPanelsProps = {
  title: string;
  kpis: {
    target_customers: number;
    expected_revenue: number;
    average_conversion: number;
  };
  opportunityScore?: number | null;
  demographics?: StateDashboard["demographics"];
  geo?: StateDashboard["geo_intelligence"];
  marketSizing?: MarketSizing;
  segmentDistribution?: StateDashboard["segment_distribution"];
  sellableProducts?: StateDashboard["sellable_products"];
};

export function MarketDetailPanels({
  title,
  kpis,
  opportunityScore,
  demographics,
  geo,
  marketSizing,
  segmentDistribution,
  sellableProducts,
}: MarketDetailPanelsProps) {
  return (
    <div className="space-y-6">
      <section>
        <h2 className="mb-3 text-base font-semibold text-gray-900">{title}</h2>
        <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
          <MockupKpiCard label="Prospect Customers (SAM)" value={formatNumber(kpis.target_customers)} showSparkline={false} />
          <MockupKpiCard label="Expected Revenue" value={formatCurrency(kpis.expected_revenue)} showSparkline={false} hint={<ExpectedRevenueInfo />} />
          <MockupKpiCard label="Expected Conversion" value={formatPercent(kpis.average_conversion)} showSparkline={false} />
          <MockupKpiCard
            label="Opportunity Score"
            value={(() => {
              const score = opportunityScore ?? geo?.opportunity_score;
              return score != null ? String(Math.round(score)) : "—";
            })()}
            showSparkline={false}
          />
        </div>
      </section>

      {marketSizing && (
        <section className="cios-card p-5">
          <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-[var(--cios-secondary)]">TAM / TOM Analysis</h3>
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            <Metric label="TAM Households" value={formatNumber(marketSizing.tam_households)} />
            <Metric label="TAM Revenue Potential" value={formatCurrency(marketSizing.tam_revenue_potential)} highlight />
            <Metric label="TOM Households" value={formatNumber(marketSizing.tom_households)} />
            <Metric label="TOM Revenue Potential" value={formatCurrency(marketSizing.tom_revenue_potential)} highlight />
            <Metric label="SAM (Owned Prospects)" value={formatNumber(marketSizing.sam_customers)} />
            <Metric label="Penetration vs TOM" value={formatPercent(marketSizing.penetration_pct)} />
            <Metric label="Ceragem Fit Rate" value={formatPercent(marketSizing.ceragem_fit_rate)} />
            <Metric label="Avg Order Value" value={formatCurrency(marketSizing.avg_order_value)} />
          </div>
        </section>
      )}

      {demographics && (
        <section className="cios-card p-5">
          <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-[var(--cios-secondary)]">Demographics</h3>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <Metric
              label="Population"
              value={demographics.population != null ? formatNumber(demographics.population) : "—"}
            />
            <Metric
              label="Median Household Income"
              value={demographics.median_household_income != null ? formatCurrency(demographics.median_household_income) : "—"}
            />
            <Metric
              label="Asian Population %"
              value={demographics.asian_population_pct != null ? `${demographics.asian_population_pct}%` : "—"}
            />
            <Metric
              label="Asian Density Index"
              value={demographics.asian_relative_index != null ? `${demographics.asian_relative_index}× US avg` : "—"}
            />
          </div>
        </section>
      )}

      {geo && (
        <section className="cios-card p-5">
          <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-[var(--cios-secondary)]">Geo Intelligence</h3>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            <TierMetric label="Lifestyle" score={geo.lifestyle_score} tier={geo.lifestyle_tier} />
            <TierMetric label="Purchase Power" score={geo.purchase_power_score} tier={geo.purchase_power_tier} />
            <TierMetric label="Pain Index" score={geo.pain_index_score} tier={geo.pain_index_tier} />
            <TierMetric label="Brand Familiarity" score={geo.brand_score} tier={geo.brand_familiarity_tier} />
            <TierMetric label="Digital Engagement" score={geo.digital_score} tier={geo.digital_engagement_tier} />
            {geo.brand_enclave_pct != null && (
              <Metric label="Brand Enclave %" value={`${geo.brand_enclave_pct}%`} />
            )}
          </div>
        </section>
      )}

      {segmentDistribution && (
        <section>
          <h3 className="mb-3 text-base font-semibold text-gray-900">Prospect Segmentation</h3>
          <SegmentDonutPanel data={segmentDistribution} />
        </section>
      )}

      {sellableProducts && sellableProducts.length > 0 && (
        <section>
          <h3 className="mb-3 text-base font-semibold text-gray-900">Sellable Products</h3>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {sellableProducts.slice(0, 8).map((p) => (
              <div key={p.product} className="cios-card p-4">
                <p className="font-semibold text-gray-900">{p.product}</p>
                <p className="mt-2 text-sm text-[var(--cios-secondary)]">
                  {formatNumber(p.expected_customers)} customers · {formatCurrency(p.expected_revenue)}
                </p>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}

function Metric({ label, value, highlight }: { label: string; value: string; highlight?: boolean }) {
  return (
    <div className="rounded-lg bg-gray-50 p-3">
      <p className="text-xs text-[var(--cios-secondary)]">{label}</p>
      <p className={`mt-1 text-sm font-semibold ${highlight ? "text-[var(--cios-primary)]" : "text-gray-900"}`}>{value}</p>
    </div>
  );
}

function TierMetric({ label, score, tier }: { label: string; score?: number; tier?: string }) {
  return (
    <div className="rounded-lg border border-[var(--cios-border)] p-3">
      <p className="text-xs font-medium text-[var(--cios-secondary)]">{label}</p>
      <p className="mt-1 text-lg font-bold text-gray-900">{score != null ? Math.round(score) : "—"}</p>
      <p className="text-xs text-[var(--cios-primary)]">{tier ?? "—"}</p>
    </div>
  );
}
