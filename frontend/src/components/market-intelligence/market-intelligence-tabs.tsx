"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { PageTabs } from "@/components/mockup/page-tabs";
import {
  MARKET_INTELLIGENCE_VIEWS,
  marketIntelligenceHref,
  type MarketIntelligenceView,
} from "@/lib/market-intelligence";
import { normalizeZipQuery } from "@/lib/utils";

export function MarketIntelligenceTabs() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const state = searchParams.get("state");
  const zip = normalizeZipQuery(searchParams.get("zip"));
  const view = (searchParams.get("view") ?? "state") as MarketIntelligenceView;

  // "metro" and "heatmap" both live under the merged "Metro Intelligence" tab.
  const active: MarketIntelligenceView = zip ? "state" : view === "metro" || view === "heatmap" ? "metro" : "state";

  const onChange = (id: string) => {
    router.push(
      marketIntelligenceHref({
        view: id as MarketIntelligenceView,
        state,
      }),
    );
  };

  return <PageTabs tabs={[...MARKET_INTELLIGENCE_VIEWS]} active={active} onChange={onChange} />;
}
