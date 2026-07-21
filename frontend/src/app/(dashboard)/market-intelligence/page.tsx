"use client";

import { Suspense, useEffect } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { StateView } from "@/components/market-intelligence/state-view";
import { PageHeader } from "@/components/mockup/page-header";
import { PageSkeleton } from "@/components/ui/skeleton";
import { useFilters } from "@/contexts/filter-context";
import { marketIntelligenceHref, resolveMarketIntelligenceView } from "@/lib/market-intelligence";
import { normalizeZipQuery } from "@/lib/utils";

export default function MarketIntelligencePage() {
  return (
    <Suspense fallback={<PageSkeleton />}>
      <MarketIntelligenceContent />
    </Suspense>
  );
}

function MarketIntelligenceContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { selectedUploadId } = useFilters();
  const stateParam = searchParams.get("state");
  const zipParam = normalizeZipQuery(searchParams.get("zip"));
  const viewParam = searchParams.get("view");
  const levelParam = searchParams.get("level");
  const view = resolveMarketIntelligenceView(viewParam, zipParam, levelParam);

  // Metro/ZIP-level analysis now lives under the dedicated "Metro Intelligence" menu.
  const shouldRedirect = view === "metro" || view === "heatmap" || view === "zip";
  useEffect(() => {
    if (shouldRedirect) {
      router.replace(marketIntelligenceHref({ view, state: stateParam, zip: zipParam }));
    }
  }, [shouldRedirect, view, stateParam, zipParam, router]);

  if (shouldRedirect) return <PageSkeleton />;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Market Intelligence"
        subtitle="National opportunity overview and state-level deep dive."
        actions={
          selectedUploadId ? (
            <span className="rounded-full bg-gray-100 px-3 py-1 text-xs text-[var(--cios-secondary)]">Scoped to selected upload</span>
          ) : undefined
        }
      />

      <StateView stateParam={stateParam} zipParam={zipParam} />

      <p className="text-center text-xs text-[var(--cios-secondary)]">
        Product-specific market analysis?{" "}
        <Link href="/opportunities" className="font-medium text-[var(--cios-primary)] hover:underline">
          Open Opportunity Finder
        </Link>
      </p>
    </div>
  );
}
