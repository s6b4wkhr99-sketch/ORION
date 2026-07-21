"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { PageTabs } from "@/components/mockup/page-tabs";
import { marketIntelligenceHref, MARKET_INTELLIGENCE_VIEWS, type MarketIntelligenceView } from "@/lib/market-intelligence";
import { normalizeZipQuery } from "@/lib/utils";

/** @deprecated Use MarketIntelligenceTabs — kept for any stale imports; routes to /market-intelligence */
export function GeographyPageTabs() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const state = searchParams.get("state");
  const zip = normalizeZipQuery(searchParams.get("zip"));
  const view = searchParams.get("view");

  const active: MarketIntelligenceView =
    zip || view === "zip" ? "state" : view === "heatmap" || view === "heat" ? "heatmap" : view === "metro" ? "metro" : "state";

  const onChange = (id: string) => {
    const nextView = id === "heat" ? "heatmap" : (id as MarketIntelligenceView);
    router.push(
      marketIntelligenceHref({
        view: nextView === "state" ? undefined : nextView,
        state,
        zip: nextView === "zip" ? zip : null,
      }),
    );
  };

  const tabs = MARKET_INTELLIGENCE_VIEWS.map((t) =>
    t.id === "heatmap" ? { ...t, id: "heat", label: "Heat Map" } : t,
  );

  return <PageTabs tabs={tabs} active={active === "heatmap" ? "heat" : active} onChange={onChange} />;
}
