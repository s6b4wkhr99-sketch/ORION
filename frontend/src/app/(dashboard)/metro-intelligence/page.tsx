"use client";

import { Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { MetroView } from "@/components/market-intelligence/metro-view";
import { ZipDetailView } from "@/components/market-intelligence/zip-detail-view";
import { PageHeader } from "@/components/mockup/page-header";
import { PageSkeleton } from "@/components/ui/skeleton";
import { useFilters } from "@/contexts/filter-context";
import { normalizeZipQuery } from "@/lib/utils";

export default function MetroIntelligencePage() {
  return (
    <Suspense fallback={<PageSkeleton />}>
      <MetroIntelligenceContent />
    </Suspense>
  );
}

function MetroIntelligenceContent() {
  const searchParams = useSearchParams();
  const { selectedUploadId } = useFilters();
  const stateParam = searchParams.get("state");
  const zipParam = normalizeZipQuery(searchParams.get("zip"));

  return (
    <div className="space-y-6">
      <PageHeader
        title="Metro Intelligence"
        subtitle="Metro (Core Based Statistical Area) analysis with ZIP-level opportunity heatmaps for deep geographic targeting."
        actions={
          selectedUploadId ? (
            <span className="rounded-full bg-gray-100 px-3 py-1 text-xs text-[var(--cios-secondary)]">Scoped to selected upload</span>
          ) : undefined
        }
      />

      {zipParam ? <ZipDetailView zipParam={zipParam} stateParam={stateParam} /> : <MetroView />}
    </div>
  );
}
