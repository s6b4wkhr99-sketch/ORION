"use client";

import { KpiCard } from "@/components/ui/kpi-card";
import { formatNumber } from "@/lib/utils";

type ValidationSummaryProps = {
  totalRows: number;
  duplicateEmail: number;
  duplicateEmailInDb?: number;
  invalidEmail: number;
  missingZip: number;
  missingState: number;
  unknownFields: number;
  fatalErrors: string[];
  warnings: string[];
};

export function ValidationSummaryPanel(props: ValidationSummaryProps) {
  return (
    <section className="cios-card p-5">
      <h2 className="mb-4 text-base font-semibold text-gray-900">Validation Summary</h2>
      <p className="mb-4 text-xs text-[var(--cios-secondary)]">
        Rows with duplicate emails (same file or already in database) are skipped — existing records are not updated.
      </p>
      {props.fatalErrors.length > 0 && (
        <div className="mb-4 rounded-lg border border-[var(--cios-error)]/30 bg-red-50 p-3 text-sm text-[var(--cios-error)]">
          Fatal errors prevent upload: {props.fatalErrors.join(", ")}
        </div>
      )}
      {props.warnings.length > 0 && (
        <div className="mb-4 rounded-lg border border-[var(--cios-warning)]/30 bg-amber-50 p-3 text-sm text-amber-800">
          Warnings (upload continues): missing recommended fields — {props.warnings.join(", ")}
        </div>
      )}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
        <KpiCard label="Total Rows" value={formatNumber(props.totalRows)} className="!h-auto min-h-[100px]" />
        <KpiCard label="Duplicate Email (in file)" value={formatNumber(props.duplicateEmail)} className="!h-auto min-h-[100px]" />
        {props.duplicateEmailInDb != null && props.duplicateEmailInDb > 0 && (
          <KpiCard label="Already in DB (skipped)" value={formatNumber(props.duplicateEmailInDb)} className="!h-auto min-h-[100px]" />
        )}
        <KpiCard label="Invalid Email" value={formatNumber(props.invalidEmail)} className="!h-auto min-h-[100px]" />
        <KpiCard label="Missing ZIP" value={formatNumber(props.missingZip)} className="!h-auto min-h-[100px]" />
        <KpiCard label="Missing State" value={formatNumber(props.missingState)} className="!h-auto min-h-[100px]" />
        <KpiCard label="Unknown Fields" value={formatNumber(props.unknownFields)} className="!h-auto min-h-[100px]" />
      </div>
    </section>
  );
}
