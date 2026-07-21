"use client";

import { useFilters } from "@/contexts/filter-context";
import { uploadRowCount } from "@/lib/upload-selection";

export function UploadBatchSelect({ className }: { className?: string }) {
  const { uploads, selectedUploadId, setSelectedUploadId } = useFilters();

  return (
    <label className={className}>
      <span className="sr-only">Upload batch filter</span>
      <select
        className="cios-input max-w-[220px] py-1.5 text-xs sm:max-w-[280px] sm:text-sm"
        value={selectedUploadId ?? ""}
        onChange={(e) => setSelectedUploadId(e.target.value || null)}
        aria-label="Upload batch filter"
      >
        <option value="">All uploads</option>
        {uploads.map((u) => (
          <option key={u.id} value={u.id}>
            {u.file_name} · {u.status}
            {uploadRowCount(u) > 0 ? ` · ${uploadRowCount(u).toLocaleString()}` : ""}
          </option>
        ))}
      </select>
    </label>
  );
}
