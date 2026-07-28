"use client";

import { createContext, useCallback, useContext, useEffect, useRef, useState } from "react";
import { usePathname } from "next/navigation";
import { api, type UploadSummary } from "@/lib/api";
import { useAuth } from "@/contexts/auth-context";
import { ensureDashboardCacheGeneration } from "@/lib/dashboard-cache";
import { resolveUploadSelection, pickDefaultUploadId } from "@/lib/upload-selection";

function uploadsSignature(list: UploadSummary[]): string {
  return list.map((u) => `${u.id}:${u.status}:${u.total_rows}`).join("|");
}

function isUploadAccessDeniedError(message: string): boolean {
  return /forbidden|insufficient permission.*upload/i.test(message);
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
  forceOpenWorkspace: () => void;
  leFrameIncentive: number | null;
  refreshExecutive: () => Promise<void>;
  stateFilter: string | null;
  setStateFilter: (v: string | null) => void;
  segmentFilter: string | null;
  setSegmentFilter: (v: string | null) => void;
  productFilter: string | null;
  setProductFilter: (v: string | null) => void;
  /** Last upload-list bootstrap error (non-blocking — workspace still opens). */
  bootError: string | null;
  /** False until the upload list (and default batch scope) is ready — avoids null-scope API scans. */
  filtersReady: boolean;
};

const FilterContext = createContext<FilterContextValue | null>(null);

const UPLOADS_BOOT_TIMEOUT_MS = 15_000;
const FILTERS_READY_SAFETY_MS = 8_000;
const UPLOAD_DEFER_IDLE_MS = 4_000;

/** Routes that do not need upload scope on first paint — defer upload list fetch. */
const UPLOAD_OPTIONAL_PREFIXES = [
  "/admin",
  "/buyer-import",
  "/settings",
  "/learning",
  "/campaigns",
  "/campaign-center",
  "/export",
];

function pathNeedsUploadScope(pathname: string): boolean {
  return !UPLOAD_OPTIONAL_PREFIXES.some(
    (prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`),
  );
}

export function FilterProvider({ children }: { children: React.ReactNode }) {
  const { canAccess } = useAuth();
  const pathname = usePathname();
  const needsUploadScope = pathNeedsUploadScope(pathname);
  const [uploads, setUploads] = useState<UploadSummary[]>([]);
  const [uploadsSignatureKey, setUploadsSignatureKey] = useState("");
  const [selectedUploadId, setSelectedUploadId] = useState<string | null>(null);
  const [dataRevision, setDataRevision] = useState(0);
  const [leFrameIncentive, setLeFrameIncentive] = useState<number | null>(null);
  const [stateFilter, setStateFilter] = useState<string | null>(null);
  const [segmentFilter, setSegmentFilter] = useState<string | null>(null);
  const [productFilter, setProductFilter] = useState<string | null>(null);
  // Start open — upload list loads in background; avoids permanent "Loading workspace…" if dev HMR is blocked.
  const [filtersReady, setFiltersReady] = useState(true);
  const [bootError, setBootError] = useState<string | null>(null);
  const uploadsSignatureRef = useRef("");
  const uploadDefaultInitializedRef = useRef(false);

  const setSelectedUploadIdTracked = useCallback((id: string | null) => {
    uploadDefaultInitializedRef.current = true;
    setSelectedUploadId(id);
  }, []);

  const refreshUploads = useCallback(async () => {
    setBootError(null);
    if (!canAccess("upload")) {
      setUploads([]);
      setUploadsSignatureKey("");
      uploadsSignatureRef.current = "";
      setFiltersReady(true);
      return;
    }
    try {
      const data = await Promise.race([
        api.getUploads("prospect"),
        new Promise<UploadSummary[]>((_, reject) => {
          window.setTimeout(() => reject(new Error("Upload list request timed out")), UPLOADS_BOOT_TIMEOUT_MS);
        }),
      ]);
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
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to load upload workspace scope";
      if (isUploadAccessDeniedError(message)) {
        setUploads([]);
        setUploadsSignatureKey("");
        uploadsSignatureRef.current = "";
        return;
      }
      console.error("Failed to load upload workspace scope", err);
      setBootError(message);
    } finally {
      setFiltersReady(true);
    }
  }, [canAccess]);

  const forceOpenWorkspace = useCallback(() => {
    setFiltersReady(true);
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

    if (!canAccess("upload")) {
      setFiltersReady(true);
      return;
    }

    const loadUploads = () => {
      void refreshUploads();
    };

    let deferTimer: number | undefined;
    let idleId: number | undefined;

    if (needsUploadScope || uploadsSignatureRef.current !== "") {
      loadUploads();
    } else {
      deferTimer = window.setTimeout(loadUploads, UPLOAD_DEFER_IDLE_MS);
      if (typeof requestIdleCallback !== "undefined") {
        idleId = requestIdleCallback(loadUploads, { timeout: UPLOAD_DEFER_IDLE_MS });
      }
    }

    const safetyTimer = window.setTimeout(() => {
      setFiltersReady(true);
    }, FILTERS_READY_SAFETY_MS);
    const onVisible = () => {
      if (document.visibilityState === "visible") {
        setFiltersReady(true);
      }
    };
    document.addEventListener("visibilitychange", onVisible);
    return () => {
      if (deferTimer != null) window.clearTimeout(deferTimer);
      if (idleId != null && typeof cancelIdleCallback !== "undefined") {
        cancelIdleCallback(idleId);
      }
      window.clearTimeout(safetyTimer);
      document.removeEventListener("visibilitychange", onVisible);
    };
  }, [refreshUploads, canAccess, needsUploadScope]);

  useEffect(() => {
    if (!needsUploadScope || !canAccess("upload") || uploadsSignatureRef.current !== "") return;
    void refreshUploads();
  }, [needsUploadScope, canAccess, refreshUploads]);

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
        forceOpenWorkspace,
        leFrameIncentive,
        refreshExecutive,
        stateFilter,
        setStateFilter,
        segmentFilter,
        setSegmentFilter,
        productFilter,
        setProductFilter,
        bootError,
        filtersReady,
      }}
    >
      {children}
    </FilterContext.Provider>
  );
}

/** Gate dashboard page content until upload scope is initialized — keeps sidebar visible. */
export function FiltersReadyGate({ children }: { children: React.ReactNode }) {
  const { filtersReady, refreshUploads, bootError, forceOpenWorkspace } = useFilters();
  if (!filtersReady) {
    return (
      <div className="flex min-h-[50vh] flex-col items-center justify-center gap-3">
        <p className="text-sm text-[var(--cios-secondary)]">Loading workspace…</p>
        <p className="max-w-sm text-center text-xs text-[var(--cios-secondary)]">
          Waiting for upload list (up to {Math.round(UPLOADS_BOOT_TIMEOUT_MS / 1000)}s). The page opens automatically
          after {Math.round(FILTERS_READY_SAFETY_MS / 1000)}s even if the API is slow.
        </p>
        <div className="flex gap-4">
          <button
            type="button"
            className="text-xs font-medium text-indigo-600 hover:underline"
            onClick={() => void refreshUploads()}
          >
            Retry
          </button>
          <button
            type="button"
            className="text-xs font-medium text-indigo-600 hover:underline"
            onClick={forceOpenWorkspace}
          >
            Open anyway
          </button>
        </div>
      </div>
    );
  }
  return (
    <>
      {bootError ? (
        <div className="mb-4 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-900">
          Upload list could not be loaded ({bootError}). Showing workspace with limited upload scope — use Retry in the
          sidebar filter or refresh the page.
          <button type="button" className="ml-2 font-medium underline" onClick={() => void refreshUploads()}>
            Retry
          </button>
        </div>
      ) : null}
      {children}
    </>
  );
}

export function useFilters() {
  const ctx = useContext(FilterContext);
  if (!ctx) throw new Error("useFilters must be used within FilterProvider");
  return ctx;
}
