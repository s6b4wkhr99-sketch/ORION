"use client";

import { CheckCircle2, Circle, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

export type UploadStage = {
  id: string;
  label: string;
  progress: number;
  status: "pending" | "active" | "done";
  eta?: string;
};

type UploadProgressProps = {
  stages: UploadStage[];
  overall: number;
};

export function UploadProgressPanel({ stages, overall }: UploadProgressProps) {
  return (
    <section className="cios-card p-5">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-base font-semibold text-gray-900">Upload Progress</h2>
        <span className="text-sm font-medium text-[var(--cios-primary)]">{overall}%</span>
      </div>
      <div className="mb-6 h-2 overflow-hidden rounded-full bg-gray-100">
        <div
          className="h-full rounded-full bg-[var(--cios-primary)] transition-all duration-300"
          style={{ width: `${overall}%` }}
        />
      </div>
      <ul className="space-y-3">
        {stages.map((stage) => (
          <li key={stage.id} className="flex items-center gap-3 text-sm">
            {stage.status === "done" && <CheckCircle2 className="h-5 w-5 text-[var(--cios-success)]" />}
            {stage.status === "active" && <Loader2 className="h-5 w-5 animate-spin text-[var(--cios-primary)]" />}
            {stage.status === "pending" && <Circle className="h-5 w-5 text-gray-300" />}
            <div className="flex flex-1 items-center justify-between gap-2">
              <span className={cn(stage.status === "active" && "font-medium text-gray-900")}>{stage.label}</span>
              <span className="text-xs text-[var(--cios-secondary)]">
                {stage.status === "done" ? "100%" : stage.status === "active" ? `${stage.progress}%` : "—"}
                {stage.eta && stage.status === "active" ? ` · ${stage.eta}` : ""}
              </span>
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
}

export const UPLOAD_STAGES: Omit<UploadStage, "progress" | "status">[] = [
  { id: "read", label: "Reading File" },
  { id: "detect", label: "Detected Headers" },
  { id: "map", label: "Auto Mapping" },
  { id: "report", label: "Mapping Report" },
  { id: "validate", label: "Validation" },
  { id: "save", label: "Import Summary" },
  { id: "intel", label: "Generate Intelligence" },
  { id: "done", label: "Completed" },
];
