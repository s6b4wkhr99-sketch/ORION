"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowRight, CheckCircle2, DollarSign, Package, Sparkles, Target, TrendingUp, Upload, Users } from "lucide-react";
import {
  CampaignFilterPanel,
  EMPTY_CAMPAIGN_FILTERS,
  useCampaignFilteredCustomers,
} from "@/components/campaign/campaign-filter-panel";
import { ExecutiveKpiRow } from "@/components/decision/mission-control/executive-kpi-row";
import { OrionDnaWidget, buildOrionDnaRadarFromCustomers } from "@/components/decision/mission-control/orion-dna-widget";
import { WidgetShell } from "@/components/decision/mission-control/widget-shell";
import {
  ConfidenceGauge,
  MessageRecommendation,
  ProductFitTreemap,
  PromotionStrategy,
} from "@/components/decision/recommendation-center/widgets";
import { SimpleBarChart } from "@/components/dashboard/simple-bar-chart";
import { PageSkeleton } from "@/components/ui/skeleton";
import { indexLevel } from "@/components/customer/customer-filters";
import { useFilters } from "@/contexts/filter-context";
import { api, type CustomerRow } from "@/lib/api";
import { formatCurrency, formatNumber, formatPercent } from "@/lib/utils";

function topMode<T>(items: T[], pick: (t: T) => string | null | undefined): string {
  const counts = new Map<string, number>();
  for (const item of items) {
    const v = pick(item);
    if (!v) continue;
    counts.set(v, (counts.get(v) ?? 0) + 1);
  }
  let best = "—";
  let max = 0;
  for (const [k, v] of counts) {
    if (v > max) {
      max = v;
      best = k;
    }
  }
  return best;
}

function messageCategory(direction: string): string {
  const d = direction.toLowerCase();
  if (d.includes("pain") || d.includes("relief")) return "Clinical Relief";
  if (d.includes("wellness") || d.includes("prevention")) return "Premium Wellness";
  if (d.includes("lifestyle") || d.includes("premium")) return "Lifestyle Upgrade";
  if (d.includes("aging")) return "Healthy Aging";
  return "Pain Management";
}

export default function RecommendationsPage() {
  const router = useRouter();
  const { selectedUploadId, dataRevision } = useFilters();
  const [customers, setCustomers] = useState<CustomerRow[]>([]);
  const [distribution, setDistribution] = useState<{ by_state: { state: string; count: number }[]; by_zip: { zip: string; count: number }[] } | null>(null);
  const [filters, setFilters] = useState(EMPTY_CAMPAIGN_FILTERS);
  const [promotion, setPromotion] = useState("percent");
  const [approved, setApproved] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api
      .getCustomers(selectedUploadId ?? undefined)
      .then((data) => {
        setCustomers(data.customers.items);
        setDistribution(data.distribution);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [selectedUploadId, dataRevision]);

  const filtered = useCampaignFilteredCustomers(customers, filters);

  const metrics = useMemo(() => {
    const expectedOrders = filtered.reduce((s, c) => s + (c.expected_conversion_rate ?? 0), 0);
    const expectedRevenue = filtered.reduce((s, c) => s + (c.expected_revenue ?? 0), 0);
    const leFrame = expectedRevenue * 0.15;
    const cost = expectedRevenue * 0.12;
    const roi = cost > 0 ? (expectedRevenue - cost) / cost : null;
    const conversion = filtered.length ? expectedOrders / filtered.length : 0;
    const confidence = Math.min(98, Math.round(68 + conversion * 1000 + Math.min(filtered.length / 5000, 20)));
    return { expectedOrders, expectedRevenue, leFrame, roi, conversion, confidence };
  }, [filtered]);

  const recommendation = useMemo(() => {
    const product = topMode(filtered, (c) => c.recommended_product);
    const message = topMode(filtered, (c) => c.message_direction);
    const segment = topMode(filtered, (c) => c.prizm_proxy_segment);
    const state = topMode(filtered, (c) => c.state);
    const category = messageCategory(message);
    return {
      product,
      message,
      segment,
      state,
      category,
      campaignType: filters.campaignTypes[0] ?? "Email",
      cta: "Schedule a Wellness Consultation",
      priority: topMode(filtered, (c) => indexLevel(c.campaign_priority)),
      headline: `Experience ${product} — Wellness engineered for your lifestyle`,
      supporting: `Target ${segment} audience in ${state} with ${message.toLowerCase()} messaging and promo code attribution.`,
      tone: category === "Clinical Relief" ? "Empathetic · Evidence-led" : "Premium · Aspirational",
    };
  }, [filtered, filters.campaignTypes]);

  const productFit = useMemo(() => {
    const map = new Map<string, { revenue: number; customers: number }>();
    for (const c of filtered) {
      const p = c.recommended_product ?? "Unknown";
      const cur = map.get(p) ?? { revenue: 0, customers: 0 };
      cur.revenue += c.expected_revenue ?? 0;
      cur.customers += 1;
      map.set(p, cur);
    }
    return [...map.entries()]
      .map(([product, v]) => ({ product, revenue: v.revenue, customers: v.customers }))
      .sort((a, b) => b.revenue - a.revenue)
      .slice(0, 6);
  }, [filtered]);

  const preview = useMemo(() => {
    const bySegment = new Map<string, number>();
    const byState = new Map<string, number>();
    for (const c of filtered) {
      if (c.prizm_proxy_segment) bySegment.set(c.prizm_proxy_segment, (bySegment.get(c.prizm_proxy_segment) ?? 0) + 1);
      if (c.state) byState.set(c.state, (byState.get(c.state) ?? 0) + 1);
    }
    return {
      bySegment: [...bySegment.entries()].map(([label, value]) => ({ label, value })).slice(0, 6),
      byState: [...byState.entries()].map(([label, value]) => ({ label, value })).slice(0, 8),
    };
  }, [filtered]);

  const dnaRadar = useMemo(() => buildOrionDnaRadarFromCustomers(filtered), [filtered]);

  const availableStates = useMemo(() => [...new Set(customers.map((c) => c.state).filter(Boolean) as string[])].sort(), [customers]);
  const availableZips = useMemo(() => [...new Set(customers.map((c) => c.zip).filter(Boolean) as string[])].sort(), [customers]);
  const availableCities = useMemo(() => (distribution?.by_zip ?? []).map((z) => z.zip).filter(Boolean), [distribution]);

  if (loading) return <PageSkeleton />;

  if (!customers.length) {
    return (
      <div className="orion-widget flex flex-col items-center justify-center p-16 text-center">
        <Upload className="mb-4 h-10 w-10 text-indigo-500" />
        <p className="text-lg text-gray-800">Upload customer data to generate campaign recommendations.</p>
        <Link href="/import" className="orion-btn-primary mt-6 px-4 py-2 text-sm">
          Go to Upload Center
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight text-gray-900">Recommendation Center</h1>
        <p className="mt-1 text-sm text-[var(--cios-secondary)]">
          What is the best campaign strategy for this opportunity? — Product, message, promotion, and executive approval.
        </p>
      </header>

      <section className="orion-widget overflow-hidden">
        <div className="flex flex-col gap-5 border-b border-[var(--cios-border)] bg-gradient-to-r from-indigo-50/60 to-white p-5 lg:flex-row lg:items-center">
          <div className="flex h-16 w-16 shrink-0 items-center justify-center rounded-2xl bg-white shadow-sm ring-1 ring-indigo-100">
            <Package className="h-8 w-8 text-indigo-500" />
          </div>
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-indigo-600" />
              <p className="text-xs font-semibold uppercase tracking-wide text-indigo-600">AI Recommendation Summary</p>
            </div>
            <h2 className="mt-1 text-xl font-semibold text-gray-900">
              Recommend {recommendation.product} to {recommendation.segment}
            </h2>
            <p className="mt-1 text-sm text-[var(--cios-secondary)]">
              {recommendation.state} · {recommendation.campaignType} · {formatNumber(filtered.length)} audience · {formatCurrency(metrics.expectedRevenue)} expected
            </p>
          </div>
          <ConfidenceGauge score={metrics.confidence} />
        </div>
      </section>

      <ExecutiveKpiRow
        items={[
          { label: "Expected Revenue", value: formatCurrency(metrics.expectedRevenue), icon: TrendingUp, accent: "purple" },
          { label: "Forecast Orders", value: formatNumber(Math.round(metrics.expectedOrders)), icon: Target, accent: "blue" },
          { label: "Audience Size", value: formatNumber(filtered.length), icon: Users, accent: "green" },
          { label: "Le Frame Incentive", value: formatCurrency(metrics.leFrame), icon: DollarSign, accent: "amber" },
          { label: "Predicted Conversion", value: formatPercent(metrics.conversion), icon: Sparkles, accent: "purple" },
        ]}
      />

      <CampaignFilterPanel
        filters={filters}
        onChange={setFilters}
        availableStates={availableStates}
        availableZips={availableZips}
        availableCities={availableCities}
      />

      <div className="grid gap-6 lg:grid-cols-2">
        <WidgetShell title="Product Fit" subtitle="Revenue-weighted product opportunity in audience">
          <ProductFitTreemap data={productFit} />
        </WidgetShell>
        <WidgetShell title="Recommendation DNA" subtitle="Why this audience is qualified">
          <OrionDnaWidget intelligenceRadar={dnaRadar} />
        </WidgetShell>
      </div>

      <WidgetShell title="Message Recommendation" subtitle="Communication strategy for this campaign">
        <MessageRecommendation
          category={recommendation.category}
          headline={recommendation.headline}
          supporting={recommendation.supporting}
          tone={recommendation.tone}
          conversion={metrics.conversion}
        />
      </WidgetShell>

      <WidgetShell title="Promotion Strategy" subtitle="Offer recommendation — promo code attribution ready">
        <PromotionStrategy selected={promotion} onChange={setPromotion} />
      </WidgetShell>

      <WidgetShell title="Expected Campaign Result" subtitle="Forecast envelope before executive approval">
        <div className="grid gap-6 lg:grid-cols-2">
          <dl className="grid gap-3 sm:grid-cols-2">
            <ResultItem label="Product" value={recommendation.product} />
            <ResultItem label="Audience" value={`${formatNumber(filtered.length)} customers`} />
            <ResultItem label="Message" value={recommendation.message} />
            <ResultItem label="Promotion" value={promotion === "percent" ? "10% Online Discount" : promotion} />
            <ResultItem label="Expected Revenue" value={formatCurrency(metrics.expectedRevenue)} />
            <ResultItem label="Campaign Risk" value={recommendation.priority === "High" ? "Low" : "Medium"} />
          </dl>
          <div className="space-y-4">
            <div>
              <p className="mb-2 text-sm font-medium text-gray-700">Audience by Segment</p>
              <SimpleBarChart data={preview.bySegment} color="#6366F1" />
            </div>
            <div>
              <p className="mb-2 text-sm font-medium text-gray-700">Audience by State</p>
              <SimpleBarChart data={preview.byState} color="#818CF8" />
            </div>
          </div>
        </div>
      </WidgetShell>

      <section className="orion-widget p-5">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <h2 className="text-base font-semibold text-gray-900">Recommendation Approval</h2>
            <p className="mt-1 text-sm text-[var(--cios-secondary)]">
              Executive approval is required before Audience Export per ORION workflow.
            </p>
            {approved && (
              <p className="mt-2 flex items-center gap-2 text-sm font-medium text-emerald-700">
                <CheckCircle2 className="h-4 w-4" />
                Recommendation approved — ready for export
              </p>
            )}
          </div>
          <div className="flex flex-wrap gap-3">
            <button
              type="button"
              disabled={approved || filtered.length === 0}
              onClick={() => setApproved(true)}
              className="rounded-xl bg-emerald-600 px-5 py-2.5 text-sm font-semibold text-white hover:opacity-90 disabled:opacity-50"
            >
              {approved ? "Approved ✓" : "Approve Recommendation"}
            </button>
            <button
              type="button"
              disabled={!approved}
              onClick={() => router.push("/export")}
              className="orion-btn-primary inline-flex items-center gap-2 px-5 py-2.5 text-sm font-semibold disabled:opacity-50"
            >
              Proceed to Audience Export
              <ArrowRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      </section>
    </div>
  );
}

function ResultItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl bg-slate-50 px-4 py-3">
      <dt className="text-xs text-[var(--cios-secondary)]">{label}</dt>
      <dd className="mt-1 text-sm font-semibold text-gray-900">{value}</dd>
    </div>
  );
}
