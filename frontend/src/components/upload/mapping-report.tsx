"use client";

import { useState } from "react";
import { CheckCircle2, AlertTriangle, ChevronDown, HelpCircle } from "lucide-react";
import { cn } from "@/lib/utils";

export type MappingReportRow = {
  uploaded_header: string;
  internal_field: string | null;
  match_type: string;
  confidence: number;
  status: string;
  suggestion?: string | null;
};

type MappingReportProps = {
  rows: MappingReportRow[];
  summary?: {
    total_headers: number;
    mapped: number;
    review: number;
    unknown: number;
    auto_mapped: number;
  };
  collapsible?: boolean;
  defaultOpen?: boolean;
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
};

const MATCH_LABELS: Record<string, string> = {
  exact: "Exact",
  alias: "Alias",
  provider_template: "Provider Template",
  ai_similarity: "AI Match",
  unknown: "Unknown",
};

function StatusIcon({ status, matchType }: { status: string; matchType: string }) {
  if (status === "mapped" && matchType !== "unknown") {
    return <CheckCircle2 className="h-4 w-4 text-[var(--cios-success)]" aria-label="Mapped" />;
  }
  if (status === "review" || matchType === "unknown") {
    return <AlertTriangle className="h-4 w-4 text-amber-500" aria-label="Review" />;
  }
  return <HelpCircle className="h-4 w-4 text-gray-400" aria-label="Ignored" />;
}

export function MappingReportPanel({
  rows,
  summary,
  collapsible = false,
  defaultOpen = true,
  open: openProp,
  onOpenChange,
}: MappingReportProps) {
  const [uncontrolledOpen, setUncontrolledOpen] = useState(defaultOpen);
  const isControlled = openProp !== undefined;
  const open = isControlled ? openProp : uncontrolledOpen;

  const setOpen = (next: boolean) => {
    if (!isControlled) setUncontrolledOpen(next);
    onOpenChange?.(next);
  };

  const summaryLine =
    summary &&
    `${summary.auto_mapped} of ${summary.total_headers} headers auto-mapped` +
      (summary.review > 0 ? ` · ${summary.review} need review` : "") +
      (summary.unknown > 0 ? ` · ${summary.unknown} unknown` : "");

  const header = collapsible ? (
    <button
      type="button"
      onClick={() => setOpen(!open)}
      aria-expanded={open ? "true" : "false"}
      className="flex w-full items-start justify-between gap-3 px-5 py-4 text-left transition-colors hover:bg-gray-50/80"
    >
      <div className="min-w-0 flex-1">
        <h2 className="text-base font-semibold text-gray-900">Mapping Report</h2>
        <p className="mt-1 text-sm text-[var(--cios-secondary)]">
          {open
            ? "Read-only report explaining how uploaded columns were automatically interpreted."
            : summaryLine ?? "View how uploaded columns were automatically mapped."}
        </p>
        {open && summaryLine && <p className="mt-2 text-xs text-[var(--cios-secondary)]">{summaryLine}</p>}
      </div>
      <ChevronDown
        className={cn("mt-0.5 h-5 w-5 shrink-0 text-[var(--cios-secondary)] transition-transform", open && "rotate-180")}
        aria-hidden
      />
    </button>
  ) : (
    <div className="border-b border-[var(--cios-border)] px-5 py-4">
      <h2 className="text-base font-semibold text-gray-900">Mapping Report</h2>
      <p className="mt-1 text-sm text-[var(--cios-secondary)]">
        Read-only report explaining how uploaded columns were automatically interpreted.
      </p>
      {summaryLine && <p className="mt-2 text-xs text-[var(--cios-secondary)]">{summaryLine}</p>}
    </div>
  );

  return (
    <section className="cios-card overflow-hidden">
      <div className={cn(collapsible && open && "border-b border-[var(--cios-border)]")}>{header}</div>
      {(!collapsible || open) && (
        <div className="overflow-x-auto">
          <table className="min-w-full text-left text-sm">
            <thead className="bg-gray-50 text-xs uppercase text-[var(--cios-secondary)]">
              <tr>
                <th className="px-5 py-3">Uploaded Header</th>
                <th className="px-5 py-3">Internal Field</th>
                <th className="px-5 py-3">Match Type</th>
                <th className="px-5 py-3">Confidence</th>
                <th className="px-5 py-3">Status</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.uploaded_header} className="border-t border-gray-100">
                  <td className="px-5 py-3 font-medium text-gray-900">{row.uploaded_header}</td>
                  <td className="px-5 py-3 text-gray-700">{row.internal_field ?? "—"}</td>
                  <td className="px-5 py-3 text-gray-600">{MATCH_LABELS[row.match_type] ?? row.match_type}</td>
                  <td className="px-5 py-3">
                    <span
                      className={cn(
                        "font-medium",
                        row.confidence >= 95 ? "text-[var(--cios-success)]" : row.confidence >= 80 ? "text-gray-700" : "text-amber-600",
                      )}
                    >
                      {row.confidence}%
                    </span>
                  </td>
                  <td className="px-5 py-3">
                    <span className="inline-flex items-center gap-1.5">
                      <StatusIcon status={row.status} matchType={row.match_type} />
                      <span className="capitalize text-gray-600">{row.status === "mapped" ? "OK" : row.status}</span>
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
