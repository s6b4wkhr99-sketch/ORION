"use client";

import { CheckCircle2, Sparkles } from "lucide-react";
import { displayProductLabel } from "@/lib/product-legend-groups";
import { formatCurrency, formatPercent } from "@/lib/utils";

export type TodaysTopOpportunityProps = {
  state: string | null;
  zip: string | null;
  product: string | null;
  expectedRevenue: number;
  predictedConversion: number;
  confidence: number;
  reasons: string[];
};

const DEFAULT_REASONS = [
  "High Income",
  "High Pain Index",
  "Premium Lifestyle",
  "High Healthcare Access",
  "Strong Digital Responsiveness",
];

export function TodaysTopOpportunity({
  state,
  zip,
  product,
  expectedRevenue,
  predictedConversion,
  confidence,
  reasons,
}: TodaysTopOpportunityProps) {
  const whyReasons = reasons.length > 0 ? reasons : DEFAULT_REASONS;

  return (
    <section className="orion-widget flex h-full min-h-0 flex-col">
      <div className="flex shrink-0 items-start justify-between gap-3 border-b border-[var(--cios-border)] px-5 py-4">
        <div>
          <h2 className="text-base font-semibold text-gray-900">Today&apos;s Top Opportunity</h2>
          <p className="mt-0.5 text-xs text-[var(--cios-secondary)]">
            AI-Recommendation by Opportunity Anlaysis
          </p>
        </div>
        <span className="inline-flex items-center gap-1.5 rounded-full bg-indigo-50 px-3 py-1 text-xs font-semibold text-indigo-700">
          <Sparkles className="h-3.5 w-3.5" />
          AI Recommendation
        </span>
      </div>

      <div className="flex min-h-0 flex-1 flex-col gap-5 p-5 lg:flex-row">
        <div className="flex shrink-0 flex-col items-center lg:w-48">
          <div className="flex h-36 w-full items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-100 via-violet-50 to-slate-100">
            <div className="flex h-24 w-24 items-center justify-center rounded-2xl bg-white/90 shadow-md ring-1 ring-indigo-100">
              <div className="h-16 w-16 rounded-xl bg-gradient-to-br from-slate-700 to-slate-900" />
            </div>
          </div>
          <p className="mt-3 text-center text-[10px] font-semibold uppercase tracking-wide text-[var(--cios-secondary)]">
            Recommended Product
          </p>
          <p className="mt-1 text-center text-sm font-bold text-gray-900">{displayProductLabel(product)}</p>
          <p className="mt-8 text-center text-[10px] font-semibold uppercase tracking-wide text-[var(--cios-secondary)]">
            Total Address Revenue
          </p>
          <p className="mt-1 text-center text-xl font-bold text-indigo-600">{formatCurrency(expectedRevenue)}</p>
        </div>

        <div className="min-w-0 flex-1">
          <div className="grid gap-3 sm:grid-cols-2">
            <DetailField label="State" value={state ?? "—"} />
            <DetailField label="ZIP" value={zip ?? "—"} />
          </div>

          <div className="mt-4 grid gap-4 sm:grid-cols-2">
            <Metric label="Pred. Conversion" value={formatPercent(predictedConversion)} />
            <Metric
              label="AI Confidence"
              value={`${Math.round(confidence)}%`}
              badge={confidence >= 90 ? "Very High" : confidence >= 75 ? "High" : "Moderate"}
            />
          </div>

          <div className="mt-5">
            <p className="text-xs font-semibold uppercase tracking-wide text-[var(--cios-secondary)]">Why this opportunity?</p>
            <ul className="mt-2 flex flex-wrap gap-2">
              {whyReasons.slice(0, 5).map((reason) => (
                <li
                  key={reason}
                  className="inline-flex items-center gap-1.5 rounded-full bg-emerald-50 px-3 py-1 text-xs font-medium text-emerald-800"
                >
                  <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" />
                  {reason}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </section>
  );
}

function DetailField({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-[var(--cios-border)] bg-slate-50/60 px-3 py-2">
      <p className="text-[10px] font-semibold uppercase tracking-wide text-[var(--cios-secondary)]">{label}</p>
      <p className="mt-0.5 text-sm font-semibold text-gray-900">{value}</p>
    </div>
  );
}

function Metric({ label, value, badge }: { label: string; value: string; badge?: string }) {
  return (
    <div>
      <p className="text-xs text-[var(--cios-secondary)]">{label}</p>
      <p className="text-lg font-bold text-gray-900">{value}</p>
      {badge && (
        <span className="mt-1 inline-block rounded-full bg-emerald-50 px-2 py-0.5 text-[10px] font-semibold text-emerald-700">
          {badge}
        </span>
      )}
    </div>
  );
}
