"use client";

import { useFilters } from "@/contexts/filter-context";
import { uploadRowCount } from "@/lib/upload-selection";

export function FilterPanel() {
  const {
    uploads,
    selectedUploadId,
    setSelectedUploadId,
    stateFilter,
    setStateFilter,
    segmentFilter,
    setSegmentFilter,
    productFilter,
    setProductFilter,
  } = useFilters();

  return (
    <aside className="w-64 shrink-0 border-r border-slate-200 bg-white p-4">
      <h2 className="mb-4 text-sm font-semibold text-slate-800">Filters</h2>
      <div className="space-y-4">
        <label className="block text-xs text-slate-500">
          Upload Batch
          <select
            className="mt-1 w-full rounded-lg border border-slate-200 px-2 py-1.5 text-sm"
            value={selectedUploadId ?? ""}
            onChange={(e) => setSelectedUploadId(e.target.value || null)}
          >
            <option value="">All uploads</option>
            {uploads.map((u) => (
              <option key={u.id} value={u.id}>
                {u.file_name} · {u.status}
                {uploadRowCount(u) > 0 ? ` · ${uploadRowCount(u).toLocaleString()} rows` : ""}
              </option>
            ))}
          </select>
        </label>

        <label className="block text-xs text-slate-500">
          State
          <input
            className="mt-1 w-full rounded-lg border border-slate-200 px-2 py-1.5 text-sm uppercase"
            placeholder="e.g. CT"
            value={stateFilter ?? ""}
            onChange={(e) => setStateFilter(e.target.value.toUpperCase() || null)}
          />
        </label>

        <label className="block text-xs text-slate-500">
          PRIZM Segment
          <input
            className="mt-1 w-full rounded-lg border border-slate-200 px-2 py-1.5 text-sm"
            placeholder="Segment name"
            value={segmentFilter ?? ""}
            onChange={(e) => setSegmentFilter(e.target.value || null)}
          />
        </label>

        <label className="block text-xs text-slate-500">
          Product
          <input
            className="mt-1 w-full rounded-lg border border-slate-200 px-2 py-1.5 text-sm"
            placeholder="Master V9"
            value={productFilter ?? ""}
            onChange={(e) => setProductFilter(e.target.value || null)}
          />
        </label>
      </div>
    </aside>
  );
}
