"use client";

import { useCallback, useState } from "react";
import { Upload } from "lucide-react";
import { cn } from "@/lib/utils";

type UploadZoneProps = {
  onUpload: (file: File) => Promise<void>;
  label?: string;
};

export function UploadZone({ onUpload, label }: UploadZoneProps) {
  const [dragging, setDragging] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFile = useCallback(
    async (file: File) => {
      setLoading(true);
      setError(null);
      try {
        await onUpload(file);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Upload failed");
      } finally {
        setLoading(false);
      }
    },
    [onUpload],
  );

  return (
    <div
      className={cn(
        "rounded-xl border-2 border-dashed p-10 text-center transition-colors",
        dragging ? "border-blue-500 bg-blue-50" : "border-slate-300 bg-white",
      )}
      onDragOver={(e) => {
        e.preventDefault();
        setDragging(true);
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDragging(false);
        const file = e.dataTransfer.files[0];
        if (file) handleFile(file);
      }}
    >
      <Upload className="mx-auto h-10 w-10 text-slate-400" />
      <p className="mt-3 text-sm font-medium text-slate-700">
        {label ?? "Drag & drop Excel or CSV customer list"}
      </p>
      <p className="mt-1 text-xs text-slate-500">Supports .xlsx and .csv</p>
      <label className="mt-4 inline-block cursor-pointer rounded-lg bg-[#2563eb] px-4 py-2 text-sm font-medium text-white hover:bg-blue-700">
        {loading ? "Processing..." : "Browse files"}
        <input
          type="file"
          accept=".csv,.xlsx,.xls"
          className="hidden"
          disabled={loading}
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) handleFile(file);
          }}
        />
      </label>
      {error && <p className="mt-3 text-sm text-red-600">{error}</p>}
    </div>
  );
}
