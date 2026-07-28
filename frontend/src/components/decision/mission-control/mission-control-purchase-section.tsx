"use client";

import { useEffect, useMemo, useState } from "react";
import { PurchaseRadar } from "@/components/decision/mission-control/purchase-radar";
import { WidgetShell } from "@/components/decision/mission-control/widget-shell";
import { UsChoroplethMap } from "@/components/dashboard/us-choropleth-map";
import { useFilters } from "@/contexts/filter-context";
import { api, type PurchaseDashboard } from "@/lib/api";
import { formatNumber } from "@/lib/utils";

/** Loads purchase dashboard data only when this section mounts (deferred via LazyWhenVisible). */
export function MissionControlPurchaseSection() {
  const { dataRevision } = useFilters();
  const [purchaseData, setPurchaseData] = useState<PurchaseDashboard | null>(null);

  useEffect(() => {
    let cancelled = false;
    api
      .getPurchasesDashboard()
      .then((summary) => {
        if (!cancelled) setPurchaseData(summary);
      })
      .catch(() => {
        if (!cancelled) setPurchaseData(null);
      });
    return () => {
      cancelled = true;
    };
  }, [dataRevision]);

  const purchaseStateMap = useMemo(
    () =>
      (purchaseData?.purchases_by_state ?? []).map((row) => ({
        state: row.state,
        revenue: 0,
        orders: row.purchase_count,
        customers: row.unique_buyers,
        brandLoyalty: row.brand_loyalty_index,
      })),
    [purchaseData],
  );

  return (
    <>
      <div className="grid items-stretch gap-6 xl:grid-cols-2">
        <div className="h-full">
          <WidgetShell
            fill
            title="Purchases by State"
            subtitle={
              purchaseData?.meta.other_count
                ? `Actual device purchases by geography · OTHER: ${formatNumber(purchaseData.meta.other_count)} (${purchaseData.meta.other_pct}%)`
                : "Actual device purchases by geography"
            }
          >
            <UsChoroplethMap data={purchaseStateMap} variant="purchases" mapHeight={551} centered />
          </WidgetShell>
        </div>
        <div className="h-full">
          <WidgetShell fill title="Purchase Radar" subtitle="Y: purchase volume score · X: switch axis">
            <PurchaseRadar points={purchaseData?.purchase_radar ?? []} fill chartHeight={380} />
          </WidgetShell>
        </div>
      </div>
    </>
  );
}
