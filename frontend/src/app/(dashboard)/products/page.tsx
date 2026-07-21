"use client";

import { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { HorizontalBarChart } from "@/components/dashboard/horizontal-bar-chart";
import { SimpleBarChart } from "@/components/dashboard/simple-bar-chart";
import { DataTable } from "@/components/ui/data-table";
import { EmptyState } from "@/components/ui/empty-state";
import { MockupKpiCard } from "@/components/mockup/mockup-kpi-card";
import { ExpectedRevenueInfo } from "@/components/ui/info-tooltip";
import { PageHeader } from "@/components/mockup/page-header";
import { PageSkeleton } from "@/components/ui/skeleton";
import { useFilters } from "@/contexts/filter-context";
import { api, type ProductDashboard } from "@/lib/api";
import { PRODUCT_OPTIONS } from "@/lib/config";
import { formatCurrency, formatNumber, formatPercent } from "@/lib/utils";

export default function ProductsPage() {
  return (
    <Suspense fallback={<PageSkeleton />}>
      <ProductsPageContent />
    </Suspense>
  );
}

function ProductsPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { selectedUploadId, dataRevision } = useFilters();
  const [data, setData] = useState<ProductDashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const productParam = searchParams.get("product");

  useEffect(() => {
    setLoading(true);
    api
      .getProductDashboard(selectedUploadId ?? undefined, productParam ?? undefined)
      .then(setData)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [selectedUploadId, productParam, dataRevision]);

  if (loading) return <PageSkeleton />;

  if (!data) {
    return (
      <EmptyState
        title="No product intelligence data yet."
        description="Upload customer data to analyze product opportunities."
        action={
          <Link href="/import" className="cios-btn bg-[var(--cios-primary)] px-4 py-2 text-white hover:opacity-90">
            Go to Upload Center
          </Link>
        }
      />
    );
  }

  const kpis = data.kpis;

  return (
    <div className="space-y-6">
      <PageHeader subtitle="Product-centric business intelligence — identify the optimal audience for each Ceragem product." />

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
        {data.products.slice(0, 5).map((p) => (
          <button
            key={p}
            type="button"
            onClick={() => router.push(`/products?product=${encodeURIComponent(p)}`)}
            className={`cios-card p-4 text-left hover:shadow-md ${
              data.selected_product === p ? "ring-2 ring-[var(--cios-primary)]" : ""
            }`}
          >
            <p className="text-sm font-medium text-gray-900">{p}</p>
            <p className="mt-2 text-xs text-[var(--cios-secondary)]">
              {data.selected_product === p ? formatCurrency(data.kpis.expected_revenue) : "Select to analyze"}
            </p>
          </button>
        ))}
      </div>

      <section className="cios-card p-5">
        <h2 className="mb-3 text-base font-semibold text-gray-900">Product Selector</h2>
        <div className="flex flex-wrap gap-2">
          {PRODUCT_OPTIONS.map((p) => (
            <button
              key={p}
              type="button"
              onClick={() => router.push(`/products?product=${encodeURIComponent(p)}`)}
              className={`rounded-full px-4 py-2 text-sm font-medium ${
                data.selected_product === p
                  ? "bg-[var(--cios-primary)] text-white"
                  : "border border-[var(--cios-border)] bg-white text-gray-700 hover:bg-gray-50"
              }`}
            >
              {p}
            </button>
          ))}
        </div>
      </section>

      <section>
        <h2 className="mb-3 text-base font-semibold text-gray-900">Product KPI</h2>
        <div className="grid grid-cols-2 gap-3 lg:grid-cols-5">
          <MockupKpiCard label="Expected Customers" value={formatNumber(kpis.expected_customers)} showSparkline={false} />
          <MockupKpiCard label="Expected Orders" value={formatNumber(Math.round(kpis.expected_orders))} showSparkline={false} />
          <MockupKpiCard label="Expected Revenue" value={formatCurrency(kpis.expected_revenue)} showSparkline={false} hint={<ExpectedRevenueInfo />} />
          <MockupKpiCard label="Campaign Count" value={formatNumber(kpis.campaign_count)} showSparkline={false} />
          <MockupKpiCard label="Average Conversion" value={formatPercent(kpis.average_conversion)} showSparkline={false} />
        </div>
      </section>

      <div className="grid gap-6 lg:grid-cols-2">
        <section className="cios-card p-5">
          <h2 className="mb-4 text-base font-semibold text-gray-900">Best States</h2>
          <HorizontalBarChart
            data={data.best_states.map((s) => ({ label: s.state, value: s.revenue }))}
            valueFormatter={(v) => formatCurrency(v)}
          />
          <p className="mt-2 text-xs text-[var(--cios-secondary)]">Click state in table below to open State Dashboard</p>
          <div className="mt-3 flex flex-wrap gap-2">
            {data.best_states.slice(0, 5).map((s) => (
              <button
                key={s.state}
                type="button"
                onClick={() => router.push(`/market-intelligence?state=${encodeURIComponent(s.state)}`)}
                className="cios-btn border border-[var(--cios-border)] bg-white px-3 py-1 text-xs hover:bg-gray-50"
              >
                {s.state} · {formatCurrency(s.revenue)}
              </button>
            ))}
          </div>
        </section>
        <section className="cios-card p-5">
          <h2 className="mb-4 text-base font-semibold text-gray-900">Best ZIPs</h2>
          <SimpleBarChart
            data={data.best_zips.map((z) => ({ label: z.zip, value: z.revenue }))}
            valueFormatter={(v) => formatCurrency(v)}
            color="#5B9BD5"
          />
          <div className="mt-3 flex flex-wrap gap-2">
            {data.best_zips.slice(0, 5).map((z) => (
              <button
                key={z.zip}
                type="button"
                onClick={() => router.push(`/market-intelligence?view=zip&zip=${z.zip}`)}
                className="cios-btn border border-[var(--cios-border)] bg-white px-3 py-1 text-xs hover:bg-gray-50"
              >
                {z.zip} · {formatCurrency(z.revenue)}
              </button>
            ))}
          </div>
        </section>
      </div>

      <section>
        <h2 className="mb-3 text-base font-semibold text-gray-900">Segment Opportunity</h2>
        <DataTable
          rows={data.segment_matrix}
          rowKey={(r) => `${r.ceragem_segment}-${r.prizm_segment}`}
          columns={[
            { key: "ceragem_segment", header: "Ceragem Segment", getValue: (r) => r.ceragem_segment, filterable: true },
            { key: "prizm_segment", header: "PRIZM Proxy Segment", getValue: (r) => r.prizm_segment, filterable: true },
            { key: "target_customers", header: "Target Customers", getValue: (r) => r.target_customers },
            { key: "expected_revenue", header: "Expected Revenue", getValue: (r) => r.expected_revenue, render: (r) => formatCurrency(r.expected_revenue) },
            { key: "campaign_priority", header: "Campaign Priority", getValue: (r) => r.campaign_priority, filterable: true },
          ]}
        />
      </section>

      <section>
        <h2 className="mb-3 text-base font-semibold text-gray-900">Campaign Performance</h2>
        <DataTable
          rows={data.campaign_performance}
          rowKey={(r) => r.campaign_id}
          onRowClick={() => router.push("/campaigns")}
          emptyMessage="No campaign performance for this product yet. Import a campaign report."
          columns={[
            { key: "campaign", header: "Campaign", getValue: (r) => r.campaign },
            { key: "revenue", header: "Revenue", getValue: (r) => r.revenue, render: (r) => formatCurrency(r.revenue) },
            { key: "conversion", header: "Conversion", getValue: (r) => r.conversion ?? 0, render: (r) => (r.conversion != null ? formatNumber(r.conversion) : "—") },
            { key: "roi", header: "ROI", getValue: (r) => r.roi ?? 0, render: (r) => (r.roi != null ? formatPercent(r.roi) : "—") },
            { key: "ctr", header: "CTR", getValue: (r) => r.ctr ?? 0, render: (r) => formatPercent(r.ctr) },
            { key: "status", header: "Status", getValue: (r) => r.status ?? "—", filterable: true },
          ]}
        />
      </section>
    </div>
  );
}
