"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { MapPin, Sparkles, Target, TrendingUp, Users } from "lucide-react";
import { CommercialIntelligencePanel } from "@/components/decision/mission-control/commercial-intelligence-panel";
import { ExecutiveKpiRow } from "@/components/decision/mission-control/executive-kpi-row";
import { ExpectedRevenueInfo } from "@/components/ui/info-tooltip";
import { IntelligenceScoreDistribution } from "@/components/decision/mission-control/intelligence-score-distribution";
import { type OpportunityRadarPoint } from "@/components/decision/mission-control/opportunity-radar";
import { MissionControlOpportunitySection } from "@/components/decision/mission-control/mission-control-opportunity-section";
import { MissionControlPurchaseSection } from "@/components/decision/mission-control/mission-control-purchase-section";
import { OrionDnaWidget } from "@/components/decision/mission-control/orion-dna-widget";
import { CeragemDistributionWidget, type CeragemSegmentBand } from "@/components/decision/mission-control/ceragem-distribution-widget";
import { sortCeragemSegments } from "@/lib/ceragem-segment-recommendations";
import { RecentOpportunitiesTable, type RecentOpportunityRow } from "@/components/decision/mission-control/recent-opportunities";
import { RevenueFunnelWidget } from "@/components/decision/mission-control/revenue-funnel-widget";
import { TodaysTopOpportunity } from "@/components/decision/mission-control/todays-top-opportunity";
import { WidgetShell } from "@/components/decision/mission-control/widget-shell";
import { PageSkeleton } from "@/components/ui/skeleton";
import { LazyWhenVisible } from "@/components/ui/lazy-when-visible";
import { useFilters } from "@/contexts/filter-context";
import { api, type ExecutiveDashboardRadarOpportunity, type ExecutiveDashboardStatePerformance, type ExecutiveSummary } from "@/lib/api";
import { dashboardCacheKey, readDashboardCache, writeDashboardCache } from "@/lib/dashboard-cache";
import { isStalePromotionCoverageCache, PROMOTION_COVERAGE_CACHE_VERSION } from "@/lib/standing-promotions";
import { resolveOpportunityScore } from "@/lib/opportunity-targeting";
import { formatCurrency, formatNumber, formatPercent, resolvePredictedConversionRate } from "@/lib/utils";

function avgRadarScore(radar: { score: number }[] | undefined): number {
  if (!radar?.length) return 0;
  return radar.reduce((s, r) => s + r.score, 0) / radar.length;
}

function formatTrend(current: number, previous: number, label = "vs previous period"): { text: string; up: boolean } | undefined {
  if (!previous || previous <= 0) return undefined;
  if (previous < current * 0.05 && current > 1000) return undefined;
  const pct = ((current - previous) / previous) * 100;
  const up = pct >= 0;
  return { text: `${up ? "↑" : "↓"} ${Math.abs(pct).toFixed(1)}% ${label}`, up };
}

function confidenceLabel(score: number): string {
  if (score >= 90) return "Very High";
  if (score >= 75) return "High";
  if (score >= 60) return "Moderate";
  return "Low";
}

function buildCeragemDistribution(data: ExecutiveSummary): CeragemSegmentBand[] {
  const distribution = data.ceragem_distribution ?? [];
  if (distribution.length) {
    return sortCeragemSegments(
      distribution.map((row) => ({
        segment: row.segment,
        count: row.customers,
        pct: row.pct,
        revenue: row.revenue,
        products: row.products ?? [],
      })),
    );
  }

  const segments = data.segment_performance ?? [];
  if (!segments.length) return [];

  const total = segments.reduce((s, seg) => s + seg.customers, 0) || 1;
  return sortCeragemSegments(
    segments.map((seg) => ({
      segment: seg.segment,
      count: seg.customers,
      pct: Math.round((seg.customers / total) * 100),
      revenue: seg.revenue,
    })),
  );
}

function mapRadarOpportunity(row: ExecutiveDashboardRadarOpportunity): OpportunityRadarPoint {
  return {
    id: row.id,
    label: row.label,
    state: row.state,
    product: row.product,
    opportunityScore: Math.round(row.opportunity_score ?? 0),
    lifestyleScore: row.lifestyle_score ?? 50,
    purchasePowerScore: row.purchase_power_score ?? 50,
    purchasePowerTier: row.purchase_power_tier,
    painIndexScore: row.pain_index_score ?? 50,
    lifestyleTier: row.lifestyle_tier,
    digitalScore: row.digital_score ?? 45,
    digitalTier: row.digital_engagement_tier,
    brandScore: row.brand_score ?? 45,
    brandTier: row.brand_familiarity_tier,
    customers: row.customers,
    revenue: row.revenue,
  };
}

function buildRadarPoints(data: ExecutiveSummary, topProduct: string | null): OpportunityRadarPoint[] {
  if (data.radar_opportunities?.length) {
    return data.radar_opportunities.map(mapRadarOpportunity);
  }

  const states = data.state_performance ?? data.revenue_by_state.map((s) => ({ ...s, customers: 0, conversion: 0, orders: 0 }));
  const maxRev = Math.max(...states.map((s) => s.revenue), 1);
  const maxCustomers = Math.max(
    ...states.map((s) => ("customers" in s && typeof s.customers === "number" ? s.customers : Math.round(s.revenue / 8))),
    1,
  );
  return states
    .filter((s) => s.revenue > 0)
    .sort((a, b) => {
      const scoreA = (a as ExecutiveDashboardStatePerformance).opportunity_score ?? 0;
      const scoreB = (b as ExecutiveDashboardStatePerformance).opportunity_score ?? 0;
      return scoreB - scoreA || b.revenue - a.revenue;
    })
    .slice(0, 10)
    .map((s, i) => {
      const customers = "customers" in s && typeof s.customers === "number" ? s.customers : Math.round(s.revenue / 8);
      const conversion = "conversion" in s && typeof s.conversion === "number" ? s.conversion : 0.03;
      const perf = s as ExecutiveDashboardStatePerformance;
      const lifestyleScore =
        perf.lifestyle_score ?? Math.min(95, Math.round(55 + (s.revenue / maxRev) * 40));
      const purchasePowerScore =
        perf.purchase_power_score ?? perf.purchase_power_index_score ?? Math.min(95, Math.round(45 + (customers / maxCustomers) * 50));
      const painIndexScore = perf.pain_index_score ?? Math.min(90, Math.round(25 + conversion * 120));
      const digitalScore = perf.digital_score ?? Math.min(90, Math.round(30 + conversion * 100));
      const brandScore = perf.brand_score ?? Math.min(90, Math.round(28 + (s.revenue / maxRev) * 30));
      const product = perf.top_product ?? data.product_ranking?.[i % (data.product_ranking.length || 1)]?.product ?? topProduct ?? "—";
      return {
        id: `state-${s.state}`,
        label: s.state,
        state: s.state,
        product,
        opportunityScore: resolveOpportunityScore(perf.opportunity_score, {
          revenue: s.revenue,
          maxRevenue: maxRev,
          conversion,
        }),
        lifestyleScore,
        purchasePowerScore,
        purchasePowerTier: perf.purchase_power_tier,
        lifestyleTier: perf.lifestyle_tier,
        painIndexScore,
        digitalScore,
        digitalTier: perf.digital_engagement_tier,
        brandScore,
        brandTier: perf.brand_familiarity_tier,
        customers,
        revenue: s.revenue,
      };
    });
}

function buildRecentOpportunities(data: ExecutiveSummary, topProduct: string | null): RecentOpportunityRow[] {
  const zips = data.top_zips ?? [];
  if (zips.length) {
    const maxRevenue = Math.max(...zips.map((row) => row.revenue), 1);
    return [...zips]
      .sort((a, b) => {
        const scoreA =
          a.opportunity_score ??
          resolveOpportunityScore(undefined, { revenue: a.revenue, maxRevenue, conversion: a.conversion });
        const scoreB =
          b.opportunity_score ??
          resolveOpportunityScore(undefined, { revenue: b.revenue, maxRevenue, conversion: b.conversion });
        return scoreB - scoreA || b.revenue - a.revenue;
      })
      .slice(0, 6)
      .map((z, i) => ({
        rank: i + 1,
        state: z.state,
        city: z.city ?? null,
        zip: z.zip,
        opportunityScore: Math.round(
          z.opportunity_score ??
            resolveOpportunityScore(undefined, {
              revenue: z.revenue,
              maxRevenue,
              conversion: z.conversion,
            }),
        ),
        customers: z.customers ?? (Math.round(z.orders * 20) || Math.round(z.revenue / 8)),
        predictedConversion: z.conversion,
        baselineConversion: z.baseline_conversion ?? z.conversion,
        promoUplift: z.promo_uplift ?? 0,
        expectedRevenue: z.revenue,
        recommendedProduct: z.intelligence_product ?? "—",
        promoProduct: z.promo_outreach_product ?? z.top_product ?? "—",
      }));
  }
  const states = [...(data.state_performance ?? data.revenue_by_state)].sort(
    (a, b) =>
      ((b as ExecutiveDashboardStatePerformance).opportunity_score ?? 0) -
      ((a as ExecutiveDashboardStatePerformance).opportunity_score ?? 0),
  );
  return states.slice(0, 6).map((s, i) => ({
    rank: i + 1,
    state: s.state,
    zip: null,
    opportunityScore: Math.round((s as ExecutiveDashboardStatePerformance).opportunity_score ?? Math.min(99, 90 - i * 4)),
    customers: "customers" in s ? (s.customers as number) : 0,
    predictedConversion: "conversion" in s ? (s.conversion as number) : resolvePredictedConversionRate(data),
    baselineConversion: data.baseline_conversion_rate ?? resolvePredictedConversionRate(data),
    promoUplift: data.promo_uplift_rate ?? 0,
    expectedRevenue: s.revenue,
    recommendedProduct: (s as ExecutiveDashboardStatePerformance).top_product ?? topProduct ?? "—",
    promoProduct: (s as ExecutiveDashboardStatePerformance).top_product ?? topProduct ?? "—",
  }));
}

export default function MissionControlPage() {
  const router = useRouter();
  const { selectedUploadId, uploads, setSelectedUploadId, dataRevision, uploadsSignatureKey } = useFilters();
  const [data, setData] = useState<ExecutiveSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    const cacheKey = dashboardCacheKey(
      "executive",
      PROMOTION_COVERAGE_CACHE_VERSION,
      selectedUploadId,
      uploadsSignatureKey || "boot",
      dataRevision,
    );
    const cached = readDashboardCache<ExecutiveSummary>(cacheKey, 5 * 60 * 1000);
    const usableCache = cached && !isStalePromotionCoverageCache(cached.commercial_intelligence);

    if (usableCache) {
      setData(cached);
      setLoading(false);
      setRefreshing(true);
    } else {
      setLoading(true);
      setRefreshing(false);
    }
    setError(null);

    api
      .getExecutive(selectedUploadId ?? undefined)
      .then((summary) => {
        if (cancelled) return;
        setData(summary);
        writeDashboardCache(cacheKey, summary);
      })
      .catch((e) => {
        if (cancelled) return;
        if (!usableCache) {
          setError(e instanceof Error ? e.message : "Failed to load mission control");
        }
      })
      .finally(() => {
        if (cancelled) return;
        setLoading(false);
        setRefreshing(false);
      });

    return () => {
      cancelled = true;
    };
  }, [selectedUploadId, dataRevision, uploadsSignatureKey]);

  const model = useMemo(() => {
    if (!data) return null;

    const topZip = data.top_zips?.[0];
    const topOpportunityState =
      data.top_opportunity_state ??
      [...(data.state_performance ?? [])].sort(
        (a, b) => (b.opportunity_score ?? 0) - (a.opportunity_score ?? 0),
      )[0]?.state ??
      data.top_performing_state ??
      null;
    const topOpportunityStateRevenue =
      (data.state_performance ?? data.revenue_by_state).find((s) => s.state === topOpportunityState)?.revenue ?? 0;
    const topZipState = topZip?.state ?? topOpportunityState;
    const topProduct =
      topZip?.promo_outreach_product ??
      topZip?.intelligence_product ??
      topZip?.top_product ??
      (data.state_performance ?? []).find((s) => s.state === topZipState)?.top_product ??
      data.top_product_opportunity;
    const confidence = avgRadarScore(data.intelligence_radar);
    const predictedConversion = resolvePredictedConversionRate(data);

    const timeline = data.revenue_over_time ?? [];
    const prevRevenue = timeline.length >= 2 ? timeline[timeline.length - 2].revenue : 0;
    const prevCustomers = timeline.length >= 2 ? (timeline[timeline.length - 2].customers ?? 0) : 0;
    const prevConversion =
      timeline.length >= 2 ? (timeline[timeline.length - 2].conversion_rate ?? 0) : 0;
    const revenueTrend = formatTrend(data.expected_revenue, prevRevenue);
    const customerTrend = formatTrend(data.targetable_customers, prevCustomers);
    const conversionTrend = formatTrend(predictedConversion, prevConversion, "vs prior forecast");

    const topPerf =
      (data.state_performance ?? []).find((s) => s.state === topZipState) ?? data.state_performance?.[0];
    const reasons: string[] = [];
    if ((topPerf?.purchase_power_score ?? 0) >= 60) reasons.push("Strong Purchase Power");
    if ((topPerf?.pain_index_score ?? 0) >= 60) reasons.push("High Pain Index");
    if ((topPerf?.lifestyle_score ?? 0) >= 60) reasons.push("High Lifestyle Index");
    if ((topPerf?.digital_score ?? 0) >= 60) reasons.push("Strong Digital Engagement");
    if ((topPerf?.brand_score ?? 0) >= 60) reasons.push("High Brand Familiarity");
    if (data.top_performing_segment) reasons.push(data.top_performing_segment);

    const targetable = data.targetable_customers;
    const engaged = Math.round(targetable * 0.283);
    const likely = Math.round(targetable * 0.079);
    const purchases = Math.round(data.expected_orders);

    return {
      topZip,
      topOpportunityState,
      topOpportunityStateRevenue,
      topZipState,
      topProduct,
      confidence,
      predictedConversion,
      revenueTrend,
      customerTrend,
      conversionTrend,
      reasons: [...new Set(reasons)].slice(0, 5),
      ceragemDistribution: buildCeragemDistribution(data),
      radarPoints: buildRadarPoints(data, topProduct),
      recentOpportunities: buildRecentOpportunities(data, topProduct),
      funnelStages: [
        { label: "Opportunity Customers", count: targetable, pct: 1 },
        { label: "Engaged (Predicted)", count: engaged, pct: targetable ? engaged / targetable : 0 },
        { label: "Likely to Convert", count: likely, pct: targetable ? likely / targetable : 0 },
        { label: "Target Obtainable Purchases", count: purchases, pct: targetable ? purchases / targetable : 0 },
      ],
      intelligenceScoreDistribution: data.intelligence_score_distribution ?? [],
      stateMap:
        data.state_performance ??
        data.revenue_by_state.map((s) => ({ ...s, orders: 0, customers: 0, conversion: 0 })),
    };
  }, [data]);

  if (loading) {
    return (
      <div className="space-y-6">
        <header>
          <h1 className="text-2xl font-semibold tracking-tight text-gray-900">Mission Control</h1>
          <p className="mt-1 text-sm text-[var(--cios-secondary)]">
            AI-powered intelligence for maximum conversion and revenue.
          </p>
        </header>
        <PageSkeleton />
        <p className="text-center text-sm text-[var(--cios-secondary)]">
          Mission Control 데이터를 불러오는 중입니다…
        </p>
      </div>
    );
  }

  if (error || !data || !model) {
    return (
      <div className="orion-widget p-6 text-sm text-[var(--cios-error)]">
        {error ?? "Unable to load mission control."}
      </div>
    );
  }

  const hasCustomers = data.total_customers > 0;
  const scopedUpload = selectedUploadId ? uploads.find((u) => u.id === selectedUploadId) : null;

  return (
    <div className="space-y-6">
      <header>
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-gray-900">Mission Control</h1>
          <p className="mt-1 text-sm text-[var(--cios-secondary)]">
            AI-powered intelligence for maximum conversion and revenue.
          </p>
          {refreshing && (
            <p className="mt-1 text-xs text-indigo-600">최신 데이터를 불러오는 중…</p>
          )}
          {data.commercial_version && (
            <p className="mt-1 text-xs text-gray-500">
              Commercial Intelligence v{data.commercial_version}
              {data.pricing_version && data.pricing_version !== data.commercial_version
                ? ` · Pricing v${data.pricing_version}`
                : ""}
            </p>
          )}
        </div>
      </header>

      {!hasCustomers && (
        <div className="orion-widget border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
          No customer data yet.{" "}
          <button type="button" className="font-medium text-indigo-600 hover:underline" onClick={() => router.push("/import")}>
            Upload customers
          </button>{" "}
          to populate opportunities.
        </div>
      )}

      {selectedUploadId && !hasCustomers && (
        <div className="orion-widget border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
          Selected upload{scopedUpload ? ` (${scopedUpload.file_name})` : ""} has no data.{" "}
          <button type="button" className="font-medium text-indigo-600 hover:underline" onClick={() => setSelectedUploadId(null)}>
            Switch to All uploads
          </button>
        </div>
      )}

      <ExecutiveKpiRow
        items={[
          {
            label: "Expected Revenue",
            value: formatCurrency(data.expected_revenue),
            delta: model.revenueTrend?.text,
            trendUp: model.revenueTrend?.up,
            icon: TrendingUp,
            accent: "purple",
            hint: <ExpectedRevenueInfo align="left" />,
          },
          {
            label: "Opportunity Customers",
            value: formatNumber(data.targetable_customers),
            delta: model.customerTrend?.text,
            trendUp: model.customerTrend?.up,
            icon: Users,
            accent: "blue",
          },
          {
            label: "Predicted Conversion",
            value: formatPercent(model.predictedConversion),
            delta: model.conversionTrend?.text,
            trendUp: model.conversionTrend?.up,
            icon: Target,
            accent: "green",
          },
          {
            label: "Top Opportunity State",
            value: model.topOpportunityState ?? "—",
            subtext: model.topOpportunityState
              ? `${formatCurrency(model.topOpportunityStateRevenue)} expected`
              : undefined,
            icon: MapPin,
            accent: "amber",
          },
          {
            label: "AI Confidence",
            value: `${Math.round(model.confidence)}%`,
            subtext: confidenceLabel(model.confidence),
            icon: Sparkles,
            accent: "purple",
          },
        ]}
      />

      {data.commercial_intelligence && (
        <LazyWhenVisible minHeight={360}>
          <CommercialIntelligencePanel data={data.commercial_intelligence} uploadId={selectedUploadId} />
        </LazyWhenVisible>
      )}

      <LazyWhenVisible minHeight={580}>
        <MissionControlOpportunitySection
          stateMap={model.stateMap}
          radarPoints={model.radarPoints}
          scopedUpload={scopedUpload}
        />
      </LazyWhenVisible>

      <LazyWhenVisible minHeight={580}>
        <MissionControlPurchaseSection />
      </LazyWhenVisible>

      <LazyWhenVisible minHeight={420} className="grid gap-6 lg:grid-cols-3">
        <div className="h-full">
          <TodaysTopOpportunity
            state={model.topZipState}
            zip={model.topZip?.zip ?? null}
            product={model.topProduct}
            expectedRevenue={model.topZip?.revenue ?? 0}
            predictedConversion={model.topZip?.conversion ?? model.predictedConversion}
            confidence={model.confidence}
            reasons={model.reasons}
          />
        </div>

        <div className="h-full">
          <WidgetShell
            fill
            title="Ceragem Distribution"
            subtitle="Ceragem Segmentation+ customer mix"
          >
            <CeragemDistributionWidget segments={model.ceragemDistribution} totalCustomers={data.targetable_customers} />
          </WidgetShell>
        </div>

        <div className="h-full">
          <WidgetShell
            fill
            title="Revenue Funnel"
            subtitle="Opportunity to revenue progression"
          >
            <RevenueFunnelWidget stages={model.funnelStages} expectedRevenue={data.expected_revenue} />
          </WidgetShell>
        </div>
      </LazyWhenVisible>

      <LazyWhenVisible minHeight={360} className="grid items-stretch gap-6 xl:grid-cols-12">
        <div className="h-full xl:col-span-4">
          <WidgetShell
            fill
            title="Recent Opportunities"
            subtitle="Top 6 intelligence-weighted opportunities"
            action={
              <Link href="/opportunities" className="text-xs font-medium text-indigo-600 hover:underline">
                View all opportunities →
              </Link>
            }
          >
            <RecentOpportunitiesTable rows={model.recentOpportunities} />
          </WidgetShell>
        </div>
        <div className="h-full xl:col-span-4">
          <WidgetShell fill title="Intelligence Score Distribution" subtitle="High / Medium / Low customer bands">
            <IntelligenceScoreDistribution rows={model.intelligenceScoreDistribution} />
          </WidgetShell>
        </div>
        <div className="h-full xl:col-span-4">
          <WidgetShell fill title="ORION DNA" subtitle="Customer intelligence distribution">
            <OrionDnaWidget intelligenceRadar={data.intelligence_radar ?? []} />
          </WidgetShell>
        </div>
      </LazyWhenVisible>
    </div>
  );
}
