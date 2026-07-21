"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowLeft, Crosshair } from "lucide-react";
import { DonutChart } from "@/components/ui/donut-chart";
import { ExpectedRevenueInfo } from "@/components/ui/info-tooltip";
import { PageSkeleton } from "@/components/ui/skeleton";
import { useFilters } from "@/contexts/filter-context";
import { api, type ZipDashboard } from "@/lib/api";
import { marketIntelligenceHref } from "@/lib/market-intelligence";
import { mergeSellableProducts } from "@/lib/product-legend-groups";
import { formatCurrency, formatNumber } from "@/lib/utils";

type ZipDetailViewProps = {
  zipParam: string | null;
  stateParam: string | null;
};

export function ZipDetailView({ zipParam, stateParam }: ZipDetailViewProps) {
  const router = useRouter();
  const { selectedUploadId, dataRevision } = useFilters();
  const [data, setData] = useState<ZipDashboard | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api
      .getZipDashboard(selectedUploadId ?? undefined, zipParam ?? undefined)
      .then(setData)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [selectedUploadId, zipParam, dataRevision]);

  if (loading) return <PageSkeleton />;
  if (!data?.available_zips.length) {
    return (
      <p className="text-sm text-[var(--cios-secondary)]">
        Select a ZIP code from the ZIP Heatmap or search below once data is available.
      </p>
    );
  }

  const summary = data.summary;
  const sellableProducts = mergeSellableProducts(data.sellable_products ?? []);

  const backHref = marketIntelligenceHref({
    view: "metro",
    state: stateParam ?? summary.state ?? null,
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <button
          type="button"
          onClick={() => router.push(backHref)}
          className="inline-flex items-center gap-1.5 text-sm font-medium text-[var(--cios-primary)] hover:underline"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Metro Intelligence
        </button>
        <Link
          href={`/opportunities?zip=${encodeURIComponent(summary.zip ?? zipParam ?? "")}${stateParam ? `&state=${encodeURIComponent(stateParam)}` : ""}`}
          className="cios-btn inline-flex items-center gap-2 border border-[var(--cios-border)] bg-white px-3 py-1.5 text-sm font-medium text-gray-900 hover:bg-gray-50"
        >
          <Crosshair className="h-4 w-4 text-[var(--cios-primary)]" />
          Find product opportunities in this ZIP
        </Link>
      </div>

      <section className="cios-card p-5">
        <h2 className="mb-4 text-base font-semibold text-gray-900">Zip Intelligence</h2>
        <dl className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          <InfoItem label="ZIP" value={summary.zip ?? "—"} />
          <InfoItem label="City" value={summary.city || "—"} />
          <InfoItem
            label="Median Income"
            value={
              data.income_intelligence.median_income != null
                ? formatCurrency(data.income_intelligence.median_income)
                : "—"
            }
          />
          <InfoItem label="Top 50 Income ZIP" value={data.income_intelligence.top_50_income_zip ? "Yes" : "No"} />
          <InfoItem label="Target Customers" value={formatNumber(summary.target_customers)} />
          <InfoItem label="Expected Revenue" value={formatCurrency(summary.expected_revenue)} hint={<ExpectedRevenueInfo />} />
        </dl>
      </section>

      <section>
        <h2 className="mb-3 text-base font-semibold text-gray-900">Customer Intelligence</h2>
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <DonutCard title="PRIZM Distribution" data={data.customer_intelligence.prizm_distribution} />
          <DonutCard title="Ceragem Distribution" data={data.customer_intelligence.ceragem_distribution} />
          <DonutCard title="Purchase Power" data={data.customer_intelligence.purchase_power} />
          <DonutCard title="Pain Index" data={data.customer_intelligence.pain_index} />
        </div>
      </section>

      <section>
        <h2 className="mb-3 text-base font-semibold text-gray-900">Campaign Opportunity</h2>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {data.campaign_opportunity.map((o) => (
            <div key={o.type} className="cios-card p-4">
              <h3 className="font-semibold text-gray-900">{o.type}</h3>
              <p className="mt-1 text-2xl font-bold text-[var(--cios-primary)]">{formatNumber(o.score)}</p>
              <p className="mt-1 text-xs text-[var(--cios-secondary)]">{o.label}</p>
            </div>
          ))}
        </div>
      </section>

      {sellableProducts.length > 0 && (
        <section>
          <h2 className="mb-3 flex items-center gap-1.5 text-base font-semibold text-gray-900">
            Sellable Products
            <ExpectedRevenueInfo align="left" />
          </h2>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {sellableProducts.slice(0, 8).map((p) => (
              <div key={p.product} className="cios-card p-4">
                <p className="font-semibold text-gray-900">{p.product}</p>
                <p className="mt-1 text-xs text-[var(--cios-secondary)]">
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

function DonutCard({ title, data }: { title: string; data: Record<string, number> }) {
  return (
    <div className="cios-card flex flex-col items-center p-4">
      <p className="mb-3 text-center text-sm font-medium text-gray-900">{title}</p>
      <DonutChart data={data} title={title} legendPosition="bottom" />
    </div>
  );
}

function InfoItem({ label, value, hint }: { label: string; value: string; hint?: React.ReactNode }) {
  return (
    <div className="rounded-lg bg-gray-50 p-3">
      <dt className="flex items-center gap-1 text-xs text-[var(--cios-secondary)]">
        {label}
        {hint}
      </dt>
      <dd className="mt-1 text-sm font-medium text-gray-900">{value}</dd>
    </div>
  );
}
