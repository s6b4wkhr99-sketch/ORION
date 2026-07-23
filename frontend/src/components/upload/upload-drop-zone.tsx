"use client";

import { useCallback, useRef, useState } from "react";
import { CloudUpload } from "lucide-react";
import { cn } from "@/lib/utils";

const MAX_BYTES = 500 * 1024 * 1024;

type UploadDropZoneProps = {
  onFileSelected: (file: File) => void;
  disabled?: boolean;
  label?: string;
  hint?: string;
};

export function UploadDropZone({
  onFileSelected,
  disabled,
  label = "Drag Excel or CSV files here",
  hint = "or click to browse",
}: UploadDropZoneProps) {
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const dragDepthRef = useRef(0);

  const validateAndSelect = useCallback(
    (file: File) => {
      setError(null);
      const ext = file.name.toLowerCase().split(".").pop();
      if (!ext || !["csv", "xlsx", "xls"].includes(ext)) {
        setError("Supported files: .xlsx, .csv");
        return;
      }
      if (file.size > MAX_BYTES) {
        setError("Maximum file size is 500 MB");
        return;
      }
      onFileSelected(file);
      if (inputRef.current) {
        inputRef.current.value = "";
      }
    },
    [onFileSelected],
  );

  const handleDragEnter = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      if (disabled) return;
      dragDepthRef.current += 1;
      setDragging(true);
    },
    [disabled],
  );

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    dragDepthRef.current = Math.max(0, dragDepthRef.current - 1);
    if (dragDepthRef.current === 0) {
      setDragging(false);
    }
  }, []);

  const handleDragOver = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      if (disabled) return;
      e.dataTransfer.dropEffect = "copy";
      setDragging(true);
    },
    [disabled],
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      dragDepthRef.current = 0;
      setDragging(false);
      if (disabled) return;
      const file = e.dataTransfer.files?.[0];
      if (file) validateAndSelect(file);
    },
    [disabled, validateAndSelect],
  );

  const openPicker = useCallback(() => {
    if (!disabled) inputRef.current?.click();
  }, [disabled]);

  return (
    <div
      className={cn(
        "relative flex h-[320px] w-full cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed transition-colors",
        dragging
          ? "border-[var(--cios-primary)] bg-[var(--cios-primary-light)]"
          : "border-[var(--cios-border)] bg-[#FAFAFA]",
        disabled && "cursor-not-allowed opacity-60",
      )}
      onDragEnter={handleDragEnter}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      onClick={openPicker}
      role="button"
      tabIndex={disabled ? -1 : 0}
      aria-disabled={disabled}
      onKeyDown={(e) => {
        if (!disabled && (e.key === "Enter" || e.key === " ")) {
          e.preventDefault();
          openPicker();
        }
      }}
    >
      {/* pointer-events-none so drops hit the container, not inner text/icons */}
      <div className="pointer-events-none flex flex-col items-center justify-center px-6 text-center">
        <CloudUpload className="h-12 w-12 text-[var(--cios-primary)]" />
        <p className="mt-4 text-base font-medium text-gray-900">{label}</p>
        <p className="mt-1 text-sm text-[var(--cios-secondary)]">{hint}</p>
        <p className="mt-3 text-xs text-[var(--cios-secondary)]">.xlsx · .csv · max 500 MB</p>
        {error && <p className="mt-4 text-sm text-[var(--cios-error)]">{error}</p>}
      </div>
      <input
        ref={inputRef}
        type="file"
        accept=".csv,.xlsx,.xls,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,text/csv"
        className="sr-only"
        disabled={disabled}
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) validateAndSelect(file);
        }}
      />
      {disabled && <div className="absolute inset-0 rounded-2xl bg-white/30" aria-hidden />}
    </div>
  );
}
