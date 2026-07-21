import { redirect } from "next/navigation";

type LegacyExplorerPageProps = {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
};

function buildRedirectUrl(params: Record<string, string | string[] | undefined>): string {
  const level = typeof params.level === "string" ? params.level : "state";
  const state = typeof params.state === "string" ? params.state : null;
  const zip = typeof params.zip === "string" ? params.zip : null;
  const product = typeof params.product === "string" ? params.product : null;

  if (level === "product") {
    const qs = new URLSearchParams();
    if (product) qs.set("product", product);
    if (state) qs.set("state", state);
    const query = qs.toString();
    return `/opportunities${query ? `?${query}` : ""}`;
  }

  const qs = new URLSearchParams();
  if (state) qs.set("state", state);
  if (zip) {
    qs.set("zip", zip);
    qs.set("view", "zip");
  } else if (level === "zip") {
    qs.set("view", "zip");
  }

  const query = qs.toString();
  return `/market-intelligence${query ? `?${query}` : ""}`;
}

export default async function LegacyExplorerRedirect({ searchParams }: LegacyExplorerPageProps) {
  const params = await searchParams;
  redirect(buildRedirectUrl(params));
}
