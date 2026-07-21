"use client";

import Link from "next/link";
import { AlertTriangle, CheckCircle2 } from "lucide-react";
import { KpiCard } from "@/components/ui/kpi-card";
import { formatNumber } from "@/lib/utils";

type UploadResultPanelProps = {
  fileName: string;
  summary: Record<string, unknown>;
  processingMs?: number;
};

export function UploadResultPanel({ fileName, summary, processingMs }: UploadResultPanelProps) {
  const errors = (summary.row_errors as { row_number: number; error: string }[] | undefined) ?? [];
  const warnings = Number(summary.invalid_emails ?? 0) + Number(summary.missing_zip ?? 0);
  const imported = Number(summary.rows_processed ?? 0);
  const duplicatesSkipped = Number(summary.duplicates_skipped ?? summary.duplicates_updated ?? 0);
  const duplicateOnly = imported === 0 && duplicatesSkipped > 0;

  return (
    <section className="cios-card p-5">
      <div className="mb-4 flex items-center gap-2">
        <CheckCircle2 className="h-5 w-5 text-[var(--cios-success)]" />
        <h2 className="text-base font-semibold text-gray-900">Upload Result — {fileName}</h2>
      </div>

      {duplicateOnly && (
        <p className="mb-4 rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900">
          Upload finished successfully. All {formatNumber(duplicatesSkipped)} rows were already in the database and were skipped.
          No new customers were added.
        </p>
      )}

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
        <KpiCard label="Imported Customers" value={formatNumber(Number(summary.rows_processed ?? 0))} className="!h-auto min-h-[100px]" />
        <KpiCard label="Skipped Customers" value={formatNumber(Number(summary.total_rows ?? 0) - Number(summary.rows_processed ?? 0))} className="!h-auto min-h-[100px]" />
        <KpiCard label="Skipped Duplicates" value={formatNumber(Number(summary.duplicates_skipped ?? summary.duplicates_updated ?? 0))} className="!h-auto min-h-[100px]" />
        <KpiCard label="Processing Time" value={processingMs != null ? `${(processingMs / 1000).toFixed(1)}s` : "—"} className="!h-auto min-h-[100px]" />
        <KpiCard label="Generated Intelligence" value={formatNumber(Number(summary.rows_processed ?? 0))} className="!h-auto min-h-[100px]" />
        <KpiCard label="Errors" value={formatNumber(errors.length)} className="!h-auto min-h-[100px]" />
        <KpiCard label="Warnings" value={formatNumber(warnings)} className="!h-auto min-h-[100px]" />
      </div>

      {errors.length > 0 && (
        <div className="mt-4 rounded-lg border border-[var(--cios-error)]/30 bg-red-50 p-3 text-sm text-red-800">
          <div className="mb-2 flex items-center gap-2 font-medium">
            <AlertTriangle className="h-4 w-4" />
            Row errors
          </div>
          <ul className="list-inside list-disc space-y-1">
            {errors.slice(0, 5).map((e) => (
              <li key={e.row_number}>
                Row {e.row_number}: {e.error}
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="mt-6 flex flex-wrap gap-3">
        <Link href="/mission-control" className="cios-btn bg-[var(--cios-primary)] px-4 py-2 text-white hover:opacity-90">
          View Mission Control
        </Link>
        <Link href="/market-intelligence" className="cios-btn border border-[var(--cios-border)] bg-white px-4 py-2 text-gray-900 hover:bg-gray-50">
          Go to Market Intelligence
        </Link>
      </div>
    </section>
  );
}
