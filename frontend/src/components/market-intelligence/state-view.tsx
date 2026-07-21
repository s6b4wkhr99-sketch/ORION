"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { UsChoroplethMap } from "@/components/dashboard/us-choropleth-map";
import { RevenueByCityBubbleChart } from "@/components/market-intelligence/revenue-by-city-bubble-chart";
import { PageSkeleton } from "@/components/ui/skeleton";
import { SegmentDonutPanel } from "@/components/ui/segment-donut-panel";
import { MockupKpiCard } from "@/components/mockup/mockup-kpi-card";
import { ExpectedRevenueInfo } from "@/components/ui/info-tooltip";
import { useFilters } from "@/contexts/filter-context";
import { api, type StateDashboard } from "@/lib/api";
import { dashboardCacheKey, readDashboardCache, writeDashboardCache } from "@/lib/dashboard-cache";
import { marketIntelligenceHref } from "@/lib/market-intelligence";
import { mergeSellableProducts } from "@/lib/product-legend-groups";
import { formatCurrency, formatNumber, formatPercent } from "@/lib/utils";

/** Shared plot height for Opportunity by State map and Revenue by City chart. */
const STATE_CITY_PLOT_HEIGHT = 441;
const PANEL_HEADER_CLASS = "mb-4 flex min-h-[5.25rem] flex-wrap items-start justify-between gap-3";

type StateViewProps = {
  stateParam: string | null;
  zipParam: string | null;
};

function cacheKey(uploadId: string | null, state: string | null, revision: number) {
  return dashboardCacheKey("mi-state", uploadId, state ?? "national", revision);
}

export function StateView({ stateParam }: StateViewProps) {
  const router = useRouter();
  const { selectedUploadId, dataRevision } = useFilters();
  const [data, setData] = useState<StateDashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    const key = cacheKey(selectedUploadId, stateParam, dataRevision);
    let usedCache = false;

    const cached = readDashboardCache<StateDashboard>(key);
    if (cached) {
      setData(cached);
      setLoading(false);
      usedCache = true;
    }

    if (!usedCache) {
      setLoading(true);
    } else {
      setRefreshing(true);
    }

    let cancelled = false;
    api
      .getStateDashboard(selectedUploadId ?? undefined, stateParam ?? undefined, 0, { lite: true })
      .then((next) => {
        if (cancelled) return;
        setData(next);
        writeDashboardCache(key, next);
      })
      .catch(console.error)
      .finally(() => {
        if (!cancelled) {
          setLoading(false);
          setRefreshing(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [selectedUploadId, stateParam, dataRevision]);

  const selectState = (state: string) => {
    router.push(marketIntelligenceHref({ view: "state", state }));
  };

  const clearState = () => {
    router.push(marketIntelligenceHref({ view: "state" }));
  };

  if (loading && !data) return <PageSkeleton />;
  if (!data) return null;

  const mapData = data.state_heatmap.map((s) => ({
    state: s.state,
    revenue: s.revenue,
    customers: s.count,
  }));

  const hasMapData = mapData.some((s) => s.revenue > 0);
  // Drive labels off the data that is actually loaded (not the pending URL param) so titles and
  // numbers never disagree while a new scope is fetching.
  const scopeLabel = data.selected_state ?? "United States";
  const hasCityData = Boolean(data.revenue_by_city?.length);
  const hasSegmentData = Object.values(data.segment_distribution ?? {}).some(
    (dist) => dist && Object.keys(dist).length > 0,
  );

  return (
    <div className="space-y-6">
      {refreshing && (
        <p className="text-center text-xs text-[var(--cios-secondary)]">Refreshing market data…</p>
      )}

      <div className={data.selected_state && hasCityData ? "grid items-stretch gap-6 lg:grid-cols-2" : ""}>
        <section className="cios-card flex h-full flex-col p-5">
          <div className={PANEL_HEADER_CLASS}>
            <div>
              <h2 className="text-base font-semibold text-gray-900">Opportunity by State</h2>
              <p className="mt-1 text-xs text-[var(--cios-secondary)]">
                {data.selected_state
                  ? `${data.selected_state} selected — segment mix and city revenue below. Click another state to switch.`
                  : "Showing United States totals. Click a state on the map to drill down."}
              </p>
            </div>
            {data.selected_state && (
              <button
                type="button"
                onClick={clearState}
                className="text-sm font-medium text-[var(--cios-primary)] hover:underline"
              >
                Back to United States
              </button>
            )}
          </div>

          {hasMapData ? (
            <div className="flex min-h-0 flex-1 flex-col">
              <UsChoroplethMap
                data={mapData}
                selectedState={data.selected_state}
                mapHeight={STATE_CITY_PLOT_HEIGHT}
                fill={Boolean(data.selected_state && hasCityData)}
                centered
                centerMaxWidthClass={
                  data.selected_state && hasCityData ? "max-w-full" : "max-w-2xl lg:max-w-3xl xl:max-w-4xl 2xl:max-w-5xl"
                }
                onStateClick={selectState}
                legendClassName="mt-auto shrink-0 pt-4 sm:pt-6"
              />
            </div>
          ) : (
            <p className="text-sm text-[var(--cios-secondary)]">
              No analyzable state data in the current scope. Upload customer data to enable the map.
            </p>
          )}
        </section>

        {data.selected_state && hasCityData && (
          <section className="cios-card flex h-full flex-col p-5">
            <div className={PANEL_HEADER_CLASS}>
              <div>
                <h2 className="text-base font-semibold text-gray-900">
                  {scopeLabel} — Revenue by City
                </h2>
                <p className="mt-1 text-xs text-[var(--cios-secondary)]">
                  Bubble size reflects prospect customers; use the product legend to filter cities.
                </p>
              </div>
            </div>
            <RevenueByCityBubbleChart
              className="min-h-0 flex-1"
              chartHeight={STATE_CITY_PLOT_HEIGHT}
              data={data.revenue_by_city}
              dataByProduct={data.revenue_by_city_by_product}
              productTargets={mergeSellableProducts(data.product_opportunity ?? [])}
            />
          </section>
        )}
      </div>

      <section>
        <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
          <MockupKpiCard
            label="Prospect Customers (SAM)"
            value={formatNumber(data.kpis.target_customers)}
            showSparkline={false}
          />
          <MockupKpiCard
            label="Expected Revenue"
            value={formatCurrency(data.kpis.expected_revenue)}
            showSparkline={false}
            hint={<ExpectedRevenueInfo />}
          />
          <MockupKpiCard
            label="Expected Conversion"
            value={formatPercent(data.kpis.average_conversion)}
            showSparkline={false}
          />
          <MockupKpiCard
            label="Opportunity Score"
            value={(() => {
              const score = data.opportunity_score ?? data.geo_intelligence?.opportunity_score;
              return score != null ? String(Math.round(score)) : "—";
            })()}
            showSparkline={false}
          />
        </div>
      </section>

      {hasSegmentData && (
        <section>
          <h2 className="mb-4 text-base font-semibold text-gray-900">{scopeLabel} — Segment Mix</h2>
          <SegmentDonutPanel data={data.segment_distribution} />
        </section>
      )}
    </div>
  );
}
