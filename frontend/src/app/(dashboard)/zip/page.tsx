import { redirect } from "next/navigation";

type LegacyZipPageProps = {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
};

function buildMarketIntelligenceUrl(params: Record<string, string | string[] | undefined>): string {
  const qs = new URLSearchParams();
  qs.set("view", "zip");

  const state = params.state;
  const zip = params.zip;
  if (typeof state === "string") qs.set("state", state);
  if (typeof zip === "string") qs.set("zip", zip);

  return `/metro-intelligence?${qs}`;
}

export default async function LegacyZipRedirect({ searchParams }: LegacyZipPageProps) {
  const params = await searchParams;
  redirect(buildMarketIntelligenceUrl(params));
}
