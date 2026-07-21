"use client";

import { Suspense, useEffect, useState, type ReactNode } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { Sparkles } from "lucide-react";
import { AudienceDistributionPanel } from "@/components/campaign/audience-distribution-panel";
import { CampaignTimeline } from "@/components/campaign/campaign-timeline";
import { DataTable } from "@/components/ui/data-table";
import { EmptyState } from "@/components/ui/empty-state";
import { GroupedBarChart } from "@/components/ui/grouped-bar-chart";
import { KpiCard } from "@/components/ui/kpi-card";
import { ExpectedRevenueInfo } from "@/components/ui/info-tooltip";
import { PageSkeleton } from "@/components/ui/skeleton";
import { useToast } from "@/components/ui/toast";
import { api, type CampaignDetail } from "@/lib/api";
import { formatCurrency, formatNumber, formatPercent } from "@/lib/utils";

export default function CampaignDetailPage() {
  return (
    <Suspense fallback={<PageSkeleton />}>
      <CampaignDetailContent />
    </Suspense>
  );
}

function CampaignDetailContent() {
  const params = useParams();
  const router = useRouter();
  const { toast } = useToast();
  const campaignId = decodeURIComponent(String(params.campaignId ?? ""));
  const [data, setData] = useState<CampaignDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [filterNote, setFilterNote] = useState<string | null>(null);

  useEffect(() => {
    if (!campaignId) return;
    setLoading(true);
    api
      .getCampaignDetail(campaignId)
      .then(setData)
      .catch(() => setData(null))
      .finally(() => setLoading(false));
  }, [campaignId]);

  if (loading) return <PageSkeleton />;

  if (!data) {
    return (
      <EmptyState
        title="Campaign not found."
        description={`No campaign with ID ${campaignId}.`}
        action={
          <Link href="/campaigns" className="cios-btn bg-[var(--cios-primary)] px-4 py-2 text-white hover:opacity-90">
            Back to Campaign Performance
          </Link>
        }
      />
    );
  }

  const h = data.header;
  const k = data.kpis;

  const formatGrouped = (v: number, metric: string) => {
    if (metric === "Revenue") return formatCurrency(v);
    if (metric === "Conversion" || metric === "Forecast Accuracy") return `${v}%`;
    return formatNumber(v);
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm text-[var(--cios-secondary)]">Operational view — planning, execution, forecast, performance, and learning.</p>
        <Link href="/campaigns" className="text-sm text-[var(--cios-primary)] hover:underline">
          ← Campaign Performance
        </Link>
      </div>

      <section className="cios-card p-5">
        <h2 className="mb-4 text-base font-semibold text-gray-900">Campaign Header</h2>
        <dl className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
          <HeaderItem label="Campaign Name" value={h.campaign_name} />
          <HeaderItem label="Campaign ID" value={h.campaign_id} />
          <HeaderItem label="Campaign Type" value={h.campaign_type} />
          <HeaderItem label="Campaign Owner" value={h.campaign_owner} />
          <HeaderItem label="Campaign Status" value={h.campaign_status} />
          <HeaderItem label="Provider" value={h.provider} />
          <HeaderItem
            label="Campaign Period"
            value={
              h.campaign_period.start && h.campaign_period.end
                ? `${h.campaign_period.start.slice(0, 10)} — ${h.campaign_period.end.slice(0, 10)}`
                : "—"
            }
          />
          <HeaderItem label="Budget" value={h.budget != null ? formatCurrency(h.budget) : "—"} />
          <HeaderItem label="Forecast Version" value={h.forecast_version} />
          <HeaderItem label="Rule Version" value={h.rule_version} />
        </dl>
      </section>

      <section>
        <h2 className="mb-3 text-base font-semibold text-gray-900">KPI Cards</h2>
        <div className="grid grid-cols-2 gap-3 lg:grid-cols-4 xl:grid-cols-7">
          <KpiCard label="Target Customers" value={formatNumber(k.target_customers)} />
          <KpiCard label="Sent" value={formatNumber(k.sent)} />
          <KpiCard label="Delivered" value={formatNumber(k.delivered)} />
          <KpiCard label="Opened" value={formatNumber(k.opened)} />
          <KpiCard label="Clicked" value={formatNumber(k.clicked)} />
          <KpiCard label="Unique Click" value={formatNumber(k.unique_click)} />
          <KpiCard label="Expected Orders" value={formatNumber(Math.round(k.expected_orders))} />
          <KpiCard label="Actual Orders" value={formatNumber(Math.round(k.actual_orders))} />
          <KpiCard label="Expected Revenue" value={formatCurrency(k.expected_revenue)} hint={<ExpectedRevenueInfo />} />
          <KpiCard label="Actual Revenue" value={formatCurrency(k.actual_revenue)} />
          <KpiCard label="Forecast Accuracy" value={k.forecast_accuracy != null ? formatPercent(k.forecast_accuracy) : "—"} />
          <KpiCard label="Campaign ROI" value={k.campaign_roi != null ? formatPercent(k.campaign_roi) : "—"} />
          <KpiCard label="Le Frame Incentive" value={formatCurrency(k.le_frame_incentive)} />
        </div>
      </section>

      <div className="grid gap-6 lg:grid-cols-2">
        <section className="cios-card p-5">
          <h2 className="mb-4 text-base font-semibold text-gray-900">Forecast</h2>
          <dl className="grid gap-2 text-sm sm:grid-cols-2">
            <ForecastItem label="Expected Customers" value={formatNumber(Number(data.forecast.expected_customers ?? k.target_customers))} />
            <ForecastItem label="Expected Orders" value={formatNumber(Math.round(k.expected_orders))} />
            <ForecastItem label="Expected Revenue" value={formatCurrency(k.expected_revenue)} hint={<ExpectedRevenueInfo />} />
            <ForecastItem label="Expected ROI" value={data.forecast.expected_roi != null ? formatPercent(Number(data.forecast.expected_roi)) : "—"} />
            <ForecastItem label="Forecast Confidence" value={data.forecast.forecast_confidence != null ? formatPercent(Number(data.forecast.forecast_confidence)) : "—"} />
            <ForecastItem label="Le Frame Incentive" value={formatCurrency(Number(data.forecast.le_frame_incentive ?? k.le_frame_incentive))} />
          </dl>
        </section>
        <section className="cios-card p-5">
          <h2 className="mb-4 text-base font-semibold text-gray-900">Actual Performance</h2>
          <GroupedBarChart data={data.forecast_vs_actual} valueFormatter={formatGrouped} />
        </section>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <AudienceDistributionPanel
          data={data.audience_distribution}
          onFilter={(dim, val) => {
            setFilterNote(`${dim}: ${val}`);
            toast("success", `Dashboard filtered by ${dim} = ${val}`);
          }}
        />
        <section className="cios-card p-5">
          <h2 className="mb-4 text-base font-semibold text-gray-900">Product Distribution</h2>
          <div className="grid gap-3 sm:grid-cols-2">
            {data.product_distribution.map((p) => (
              <div key={p.product} className="rounded-lg border border-[var(--cios-border)] p-3">
                <h3 className="font-semibold text-gray-900">{p.product}</h3>
                <dl className="mt-2 space-y-1 text-xs">
                  <Row label="Target Customers" value={formatNumber(p.target_customers)} />
                  <Row label="Expected Orders" value={formatNumber(Math.round(p.expected_orders))} />
                  <Row label="Actual Orders" value={formatNumber(Math.round(p.actual_orders))} />
                  <Row label="Expected Revenue" value={formatCurrency(p.expected_revenue)} hint={<ExpectedRevenueInfo align="left" />} />
                  <Row label="Actual Revenue" value={formatCurrency(p.actual_revenue)} />
                  <Row label="Conversion" value={p.conversion != null ? formatPercent(p.conversion) : "—"} />
                </dl>
              </div>
            ))}
          </div>
        </section>
      </div>
      {filterNote && <p className="text-xs text-[var(--cios-secondary)]">Active filter: {filterNote}</p>}

      <div className="grid gap-6 lg:grid-cols-2">
        <section>
          <h2 className="mb-3 text-base font-semibold text-gray-900">State Performance</h2>
          <DataTable
            rows={data.state_performance}
            rowKey={(r) => r.state}
            onRowClick={(r) => router.push(`/market-intelligence?state=${encodeURIComponent(r.state)}`)}
            columns={[
              { key: "state", header: "State", getValue: (r) => r.state },
              { key: "target_customers", header: "Target Customers", getValue: (r) => r.target_customers },
              { key: "sent", header: "Sent", getValue: (r) => r.sent },
              { key: "ctr", header: "CTR", getValue: (r) => r.ctr ?? 0, render: (r) => formatPercent(r.ctr) },
              { key: "conversion", header: "Conversion", getValue: (r) => r.conversion ?? 0, render: (r) => (r.conversion != null ? formatNumber(r.conversion) : "—") },
              { key: "revenue", header: "Revenue", getValue: (r) => r.revenue, render: (r) => formatCurrency(r.revenue) },
              { key: "forecast_accuracy", header: "Forecast Accuracy", getValue: (r) => r.forecast_accuracy ?? 0, render: (r) => formatPercent(r.forecast_accuracy) },
              { key: "campaign_priority", header: "Campaign Priority", getValue: (r) => r.campaign_priority, filterable: true },
            ]}
          />
        </section>
        <section>
          <h2 className="mb-3 text-base font-semibold text-gray-900">ZIP Opportunity</h2>
          <DataTable
            rows={data.zip_opportunity}
            rowKey={(r) => r.zip}
            onRowClick={(r) => router.push(`/market-intelligence?view=zip&zip=${encodeURIComponent(r.zip)}`)}
            columns={[
              { key: "zip", header: "ZIP", getValue: (r) => r.zip },
              { key: "city", header: "City", getValue: (r) => r.city },
              { key: "customers", header: "Customers", getValue: (r) => r.customers },
              { key: "purchase_power", header: "Purchase Power", getValue: (r) => r.purchase_power, filterable: true },
              { key: "recommended_product", header: "Recommended Product", getValue: (r) => r.recommended_product ?? "—" },
              { key: "expected_revenue", header: "Expected Revenue", getValue: (r) => r.expected_revenue, render: (r) => formatCurrency(r.expected_revenue) },
              { key: "actual_revenue", header: "Actual Revenue", getValue: (r) => r.actual_revenue, render: (r) => formatCurrency(r.actual_revenue) },
              { key: "campaign_priority", header: "Campaign Priority", getValue: (r) => r.campaign_priority, filterable: true },
            ]}
          />
        </section>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <section className="cios-card p-5">
          <h2 className="mb-4 text-base font-semibold text-gray-900">Campaign Timeline</h2>
          <CampaignTimeline events={data.timeline} />
        </section>
        <section className="cios-card p-5">
          <div className="mb-4 flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-[var(--cios-primary)]" />
            <h2 className="text-base font-semibold text-gray-900">Learning Summary</h2>
          </div>
          <dl className="space-y-3 text-sm">
            <LearningRow label="Top Performing Segment" value={data.learning_summary.top_performing_segment ?? "—"} />
            <LearningRow label="Top Product" value={data.learning_summary.top_product ?? "—"} />
            <LearningRow label="Highest Conversion State" value={data.learning_summary.highest_conversion_state ?? "—"} />
            <LearningRow label="Highest Revenue ZIP" value={data.learning_summary.highest_revenue_zip ?? "—"} />
            <LearningRow label="Best Message Direction" value={data.learning_summary.best_message_direction ?? "—"} />
          </dl>
          <p className="mt-4 rounded-lg bg-[var(--cios-primary-light)] p-3 text-sm text-gray-900">
            {data.learning_summary.recommendation_for_next_campaign}
          </p>
          <button
            type="button"
            className="cios-btn mt-4 bg-[var(--cios-primary)] px-4 py-2 text-white hover:opacity-90"
            onClick={() => router.push("/campaign-center")}
          >
            Create Follow-up Campaign
          </button>
        </section>
      </div>
    </div>
  );
}

function HeaderItem({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-xs text-[var(--cios-secondary)]">{label}</dt>
      <dd className="mt-1 text-sm font-medium text-gray-900">{value}</dd>
    </div>
  );
}

function ForecastItem({ label, value, hint }: { label: string; value: string; hint?: ReactNode }) {
  return (
    <div className="flex justify-between gap-2 border-b border-gray-100 py-1">
      <dt className="flex items-center gap-1 text-[var(--cios-secondary)]">{label}{hint}</dt>
      <dd className="font-medium text-gray-900">{value}</dd>
    </div>
  );
}

function Row({ label, value, hint }: { label: string; value: string; hint?: ReactNode }) {
  return (
    <div className="flex justify-between gap-2">
      <dt className="flex items-center gap-1 text-[var(--cios-secondary)]">{label}{hint}</dt>
      <dd className="font-medium">{value}</dd>
    </div>
  );
}

function LearningRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between gap-4">
      <dt className="text-[var(--cios-secondary)]">{label}</dt>
      <dd className="font-medium text-gray-900">{value}</dd>
    </div>
  );
}
