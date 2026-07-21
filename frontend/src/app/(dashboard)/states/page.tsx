import { redirect } from "next/navigation";

type LegacyStatesPageProps = {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
};

function buildMarketIntelligenceUrl(params: Record<string, string | string[] | undefined>): string {
  const qs = new URLSearchParams();
  const state = params.state;
  const zip = params.zip;
  const view = params.view;

  if (typeof state === "string") qs.set("state", state);
  if (typeof zip === "string") {
    qs.set("zip", zip);
    qs.set("view", "zip");
  } else if (typeof view === "string" && view === "heat") {
    qs.set("view", "heatmap");
  }

  const query = qs.toString();
  return `/market-intelligence${query ? `?${query}` : ""}`;
}

export default async function LegacyStatesRedirect({ searchParams }: LegacyStatesPageProps) {
  const params = await searchParams;
  redirect(buildMarketIntelligenceUrl(params));
}
