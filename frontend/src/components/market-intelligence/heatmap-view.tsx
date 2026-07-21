"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { UsHeatMap } from "@/components/dashboard/us-heat-map";
import { ZipChoroplethMap } from "@/components/market-intelligence/zip-choropleth-map";
import { StateSelector } from "@/components/ui/state-selector";
import { PageSkeleton } from "@/components/ui/skeleton";
import { useFilters } from "@/contexts/filter-context";
import { api, type StateDashboard } from "@/lib/api";
import { marketIntelligenceHref } from "@/lib/market-intelligence";
import { mergeSellableProducts } from "@/lib/product-legend-groups";

type HeatmapViewProps = {
  stateParam: string | null;
};

export function HeatmapView({ stateParam }: HeatmapViewProps) {
  const router = useRouter();
  const { selectedUploadId, dataRevision } = useFilters();
  const [data, setData] = useState<StateDashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const prevFiltersRef = useRef({ upload: selectedUploadId, state: stateParam });

  useEffect(() => {
    let cancelled = false;
    const filterChanged =
      prevFiltersRef.current.upload !== selectedUploadId || prevFiltersRef.current.state !== stateParam;
    prevFiltersRef.current = { upload: selectedUploadId, state: stateParam };
    const showSkeleton = data === null || filterChanged;
    if (showSkeleton) setLoading(true);
    api
      .getStateDashboard(selectedUploadId ?? undefined, stateParam ?? undefined, 0, { lite: true })
      .then((next) => {
        if (!cancelled) setData(next);
      })
      .catch(console.error)
      .finally(() => {
        if (!cancelled && showSkeleton) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [selectedUploadId, stateParam, dataRevision]);

  if (loading) return <PageSkeleton />;

  if (!data?.available_states.length) {
    return (
      <p className="text-sm text-[var(--cios-secondary)]">
        No heat map data yet.{" "}
        <Link href="/import" className="font-medium text-[var(--cios-primary)] hover:underline">
          Upload customer data
        </Link>
      </p>
    );
  }

  const selectState = (state: string | null) => {
    router.push(
      marketIntelligenceHref({
        view: "heatmap",
        state,
      }),
    );
  };

  return (
    <div className="space-y-4">
      <StateSelector states={data.available_states} value={stateParam} onChange={selectState} />

      {stateParam ? (
        <section className="cios-card p-5">
          <h2 className="mb-1 text-base font-semibold text-gray-900">{stateParam} ZIP Opportunity Heatmap</h2>
          <p className="mb-4 text-xs text-[var(--cios-secondary)]">
            ZIP-level expected revenue choropleth. Use the product legend to filter by recommended SKU. Click a zone to open ZIP detail.
          </p>
          <ZipChoroplethMap
            state={stateParam}
            uploadId={selectedUploadId}
            productTargets={mergeSellableProducts(data.product_opportunity ?? [])}
            onZipClick={(zip) =>
              router.push(
                marketIntelligenceHref({
                  view: "zip",
                  state: stateParam,
                  zip,
                }),
              )
            }
          />
        </section>
      ) : (
        <section className="cios-card p-5">
          <h2 className="mb-4 text-base font-semibold text-gray-900">National State Heat Map</h2>
          <p className="mb-4 text-xs text-[var(--cios-secondary)]">Select a state above for ZIP-level ZCTA choropleth.</p>
          <UsHeatMap data={data.state_heatmap.map((s) => ({ state: s.state, revenue: s.revenue, count: s.count }))} />
        </section>
      )}
    </div>
  );
}
