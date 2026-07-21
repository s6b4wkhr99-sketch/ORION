"use client";

import { useCallback, useRef, useState } from "react";
import { CloudUpload } from "lucide-react";
import { cn } from "@/lib/utils";

const MAX_BYTES = 100 * 1024 * 1024;

type UploadDropZoneProps = {
  onFileSelected: (file: File) => void;
  disabled?: boolean;
};

export function UploadDropZone({ onFileSelected, disabled }: UploadDropZoneProps) {
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const validateAndSelect = useCallback(
    (file: File) => {
      setError(null);
      const ext = file.name.toLowerCase().split(".").pop();
      if (!ext || !["csv", "xlsx", "xls"].includes(ext)) {
        setError("Supported files: .xlsx, .csv");
        return;
      }
      if (file.size > MAX_BYTES) {
        setError("Maximum file size is 100 MB");
        return;
      }
      onFileSelected(file);
    },
    [onFileSelected],
  );

  return (
    <div
      className={cn(
        "flex h-[320px] w-full flex-col items-center justify-center rounded-2xl border-2 border-dashed transition-colors",
        dragging ? "border-[var(--cios-primary)] bg-[var(--cios-primary-light)]" : "border-[var(--cios-border)] bg-[#FAFAFA]",
        disabled && "pointer-events-none opacity-60",
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
        if (file) validateAndSelect(file);
      }}
      onClick={() => inputRef.current?.click()}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === "Enter" && inputRef.current?.click()}
    >
      <CloudUpload className="h-12 w-12 text-[var(--cios-primary)]" />
      <p className="mt-4 text-base font-medium text-gray-900">Drag Excel or CSV files here</p>
      <p className="mt-1 text-sm text-[var(--cios-secondary)]">or click to browse</p>
      <p className="mt-3 text-xs text-[var(--cios-secondary)]">.xlsx · .csv · max 100 MB</p>
      <input
        ref={inputRef}
        type="file"
        accept=".csv,.xlsx,.xls"
        className="hidden"
        disabled={disabled}
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) validateAndSelect(file);
        }}
      />
      {error && <p className="mt-4 text-sm text-[var(--cios-error)]">{error}</p>}
    </div>
  );
}
