"use client";

import { createContext, useCallback, useContext, useEffect, useRef, useState } from "react";
import { api, type UploadSummary } from "@/lib/api";
import { ensureDashboardCacheGeneration } from "@/lib/dashboard-cache";
import { resolveUploadSelection, pickDefaultUploadId } from "@/lib/upload-selection";

function uploadsSignature(list: UploadSummary[]): string {
  return list.map((u) => `${u.id}:${u.status}:${u.total_rows}`).join("|");
}

type FilterContextValue = {
  uploads: UploadSummary[];
  /** Stable fingerprint of upload list — used to bust stale dashboard caches after new uploads. */
  uploadsSignatureKey: string;
  selectedUploadId: string | null;
  setSelectedUploadId: (id: string | null) => void;
  /** Bumps when upload list meaningfully changes — dashboard pages refetch on this. */
  dataRevision: number;
  refreshUploads: () => Promise<void>;
  refreshDashboards: () => Promise<void>;
  leFrameIncentive: number | null;
  refreshExecutive: () => Promise<void>;
  stateFilter: string | null;
  setStateFilter: (v: string | null) => void;
  segmentFilter: string | null;
  setSegmentFilter: (v: string | null) => void;
  productFilter: string | null;
  setProductFilter: (v: string | null) => void;
  /** False until the upload list (and default batch scope) is ready — avoids null-scope API scans. */
  filtersReady: boolean;
};

const FilterContext = createContext<FilterContextValue | null>(null);

export function FilterProvider({ children }: { children: React.ReactNode }) {
  const [uploads, setUploads] = useState<UploadSummary[]>([]);
  const [uploadsSignatureKey, setUploadsSignatureKey] = useState("");
  const [selectedUploadId, setSelectedUploadId] = useState<string | null>(null);
  const [dataRevision, setDataRevision] = useState(0);
  const [leFrameIncentive, setLeFrameIncentive] = useState<number | null>(null);
  const [stateFilter, setStateFilter] = useState<string | null>(null);
  const [segmentFilter, setSegmentFilter] = useState<string | null>(null);
  const [productFilter, setProductFilter] = useState<string | null>(null);
  const [filtersReady, setFiltersReady] = useState(false);
  const uploadsSignatureRef = useRef("");
  const uploadDefaultInitializedRef = useRef(false);

  const setSelectedUploadIdTracked = useCallback((id: string | null) => {
    uploadDefaultInitializedRef.current = true;
    setSelectedUploadId(id);
  }, []);

  const refreshUploads = useCallback(async () => {
    try {
      const data = await api.getUploads();
      const list = Array.isArray(data) ? data : [];
      const signature = uploadsSignature(list);
      if (signature !== uploadsSignatureRef.current) {
        const isInitialLoad = uploadsSignatureRef.current === "";
        uploadsSignatureRef.current = signature;
        // Skip dataRevision bump on first load — avoids double-fetch on every dashboard page.
        if (!isInitialLoad) {
          setDataRevision((v) => v + 1);
        }
      }
      setUploads(list);
      setUploadsSignatureKey(signature);
      setSelectedUploadId((current) => {
        const resolved = resolveUploadSelection(list, current);
        if (resolved) return resolved;
        if (!uploadDefaultInitializedRef.current && list.length > 0) {
          uploadDefaultInitializedRef.current = true;
          return pickDefaultUploadId(list);
        }
        return current;
      });
    } finally {
      setFiltersReady(true);
    }
  }, []);

  const refreshDashboards = useCallback(async () => {
    await refreshUploads();
  }, [refreshUploads]);

  const refreshExecutive = useCallback(async () => {
    try {
      const summary = await api.getExecutive(selectedUploadId ?? undefined);
      setLeFrameIncentive(summary.le_frame_incentive ?? null);
    } catch {
      setLeFrameIncentive(null);
    }
  }, [selectedUploadId]);

  useEffect(() => {
    ensureDashboardCacheGeneration();
    refreshUploads().catch(console.error);
  }, [refreshUploads]);

  useEffect(() => {
    const hasActive = uploads.some((u) => u.status === "pending" || u.status === "processing");
    if (!hasActive) return;
    const timer = setInterval(() => {
      refreshUploads().catch(console.error);
    }, 8000);
    return () => clearInterval(timer);
  }, [uploads, refreshUploads]);

  return (
    <FilterContext.Provider
      value={{
        uploads,
        uploadsSignatureKey,
        selectedUploadId,
        setSelectedUploadId: setSelectedUploadIdTracked,
        dataRevision,
        refreshUploads,
        refreshDashboards,
        leFrameIncentive,
        refreshExecutive,
        stateFilter,
        setStateFilter,
        segmentFilter,
        setSegmentFilter,
        productFilter,
        setProductFilter,
        filtersReady,
      }}
    >
      {children}
    </FilterContext.Provider>
  );
}

/** Gate dashboard page content until upload scope is initialized — keeps sidebar visible. */
export function FiltersReadyGate({ children }: { children: React.ReactNode }) {
  const { filtersReady } = useFilters();
  if (!filtersReady) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <p className="text-sm text-[var(--cios-secondary)]">Loading workspace…</p>
      </div>
    );
  }
  return <>{children}</>;
}

export function useFilters() {
  const ctx = useContext(FilterContext);
  if (!ctx) throw new Error("useFilters must be used within FilterProvider");
  return ctx;
}
