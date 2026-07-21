export type MarketIntelligenceView = "state" | "metro" | "heatmap" | "zip";

export const MARKET_INTELLIGENCE_VIEWS: { id: MarketIntelligenceView; label: string }[] = [
  { id: "state", label: "State View" },
  { id: "metro", label: "Metro Intelligence" },
];

export function marketIntelligenceHref(opts?: {
  view?: MarketIntelligenceView;
  state?: string | null;
  zip?: string | null;
  cbsa?: string | null;
}): string {
  const view = opts?.view;
  // Metro/ZIP-level views live under the dedicated "Metro Intelligence" menu.
  const base =
    view === "metro" || view === "heatmap" || view === "zip" ? "/metro-intelligence" : "/market-intelligence";
  const params = new URLSearchParams();
  if (view && view !== "state") params.set("view", view);
  if (opts?.state) params.set("state", opts.state);
  if (opts?.zip) params.set("zip", opts.zip);
  if (opts?.cbsa) params.set("cbsa", opts.cbsa);
  const qs = params.toString();
  return `${base}${qs ? `?${qs}` : ""}`;
}

export function resolveMarketIntelligenceView(
  viewParam: string | null,
  zipParam: string | null,
  levelParam?: string | null,
): MarketIntelligenceView {
  if (zipParam) return "zip";
  if (viewParam === "metro" || viewParam === "heatmap" || viewParam === "zip") return viewParam;
  if (levelParam === "zip") return "zip";
  return "state";
}
