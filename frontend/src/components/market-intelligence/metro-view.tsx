"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { PageSkeleton } from "@/components/ui/skeleton";
import { useFilters } from "@/contexts/filter-context";
import { api, type MetroDashboard } from "@/lib/api";
import { dashboardCacheKey } from "@/lib/dashboard-cache";
import { marketIntelligenceHref } from "@/lib/market-intelligence";
import { mergeSellableProducts } from "@/lib/product-legend-groups";
import { readSessionCache, writeSessionCache } from "@/lib/session-dashboard-cache";
import { MarketDetailPanels } from "@/components/market-intelligence/market-detail-panels";
import { ZipChoroplethMap } from "@/components/market-intelligence/zip-choropleth-map";

export function MetroView() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { selectedUploadId, dataRevision } = useFilters();
  const cbsaParam = searchParams.get("cbsa");
  const [data, setData] = useState<MetroDashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  // The dashboard returns the full metros list, so selecting a metro is resolved client-side.
  // We intentionally do NOT refetch when only cbsaParam changes to avoid recomputing all 30 metros.
  useEffect(() => {
    const key = dashboardCacheKey("mi-metro", selectedUploadId, dataRevision);
    const cached = readSessionCache<MetroDashboard>(key);
    if (cached) {
      setData(cached);
      setLoading(false);
      setRefreshing(true);
    } else {
      setLoading(true);
    }

    let cancelled = false;
    api
      .getMetroDashboard(selectedUploadId ?? undefined)
      .then((next) => {
        if (cancelled) return;
        setData(next);
        writeSessionCache(key, next);
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
  }, [selectedUploadId, dataRevision]);

  if (loading && !data) return <PageSkeleton />;
  if (!data) return null;

  const selected = data.selected_metro ?? data.metros.find((m) => m.cbsa_code === cbsaParam) ?? data.metros[0];
  const sellableProducts = selected
    ? mergeSellableProducts(
        selected.sellable_products?.length
          ? selected.sellable_products
          : selected.top_product
            ? [
                {
                  product: selected.top_product,
                  expected_customers: selected.target_customers,
                  expected_revenue: selected.expected_revenue,
                  expected_orders: selected.expected_orders,
                },
              ]
            : [],
      )
    : [];

  return (
    <div className="space-y-6">
      {refreshing && (
        <p className="text-center text-xs text-[var(--cios-secondary)]">Refreshing metro data…</p>
      )}
      <section className="cios-card p-5">
        <label className="block text-sm font-medium text-gray-700">
          Top 50 Metro (Core Based Statistical Area)
          <select
            className="cios-input mt-2 w-full bg-white px-3 py-2"
            value={selected?.cbsa_code ?? ""}
            onChange={(e) => {
              const code = e.target.value;
              router.push(
                code ? marketIntelligenceHref({ view: "metro", cbsa: code }) : marketIntelligenceHref({ view: "metro" }),
              );
            }}
          >
            {[...data.metros]
              .sort((a, b) => a.rank - b.rank)
              .map((m) => (
                <option key={m.cbsa_code} value={m.cbsa_code}>
                  #{m.rank} {m.cbsa_name}
                </option>
              ))}
          </select>
        </label>
          <p className="mt-2 text-xs text-[var(--cios-secondary)]">
            Core Based Statistical Area: a statistical region defined by the U.S. Census Bureau and OMB that groups one or
            more counties around a densely populated urban core and its socioeconomically integrated surrounding area.
          </p>
      </section>

      {selected && (
        <MarketDetailPanels
          title={selected.cbsa_name}
          opportunityScore={selected.opportunity_score}
          kpis={{
            target_customers: selected.target_customers,
            expected_revenue: selected.expected_revenue,
            average_conversion: selected.conversion,
          }}
          demographics={{
            population: selected.demographics.population,
            median_household_income: selected.demographics.median_household_income,
            asian_population_pct: selected.demographics.asian_population_pct,
            asian_relative_index: selected.demographics.asian_relative_index,
            income_bands: selected.segment_distribution.purchase_power,
          }}
          marketSizing={selected.market_sizing}
          segmentDistribution={{
            prizm: selected.segment_distribution.prizm ?? {},
            ceragem: selected.segment_distribution.ceragem,
            purchase_power: selected.segment_distribution.purchase_power,
            pain_index: selected.segment_distribution.pain_index ?? {},
            lifestyle: selected.segment_distribution.lifestyle,
            brand_familiarity: selected.segment_distribution.brand_familiarity ?? {},
          }}
          sellableProducts={sellableProducts}
        />
      )}

      {selected && (
        <section className="cios-card p-5">
          <h2 className="mb-1 text-base font-semibold text-gray-900">{selected.cbsa_name} — ZIP Opportunity Heatmap</h2>
          <p className="mb-4 text-xs text-[var(--cios-secondary)]">
            ZIP-level expected revenue across this metro. Use the product legend to highlight zones where a SKU is recommended. Click a zone to open ZIP detail.
          </p>
          <ZipChoroplethMap
            cbsa={selected.cbsa_code}
            state={selected.states[0] ?? ""}
            uploadId={selectedUploadId}
            productTargets={sellableProducts}
            onZipClick={(zip) =>
              router.push(
                marketIntelligenceHref({
                  view: "zip",
                  state: selected.states[0] ?? null,
                  zip,
                }),
              )
            }
          />
        </section>
      )}
    </div>
  );
}
