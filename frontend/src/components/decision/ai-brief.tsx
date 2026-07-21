"use client";

import Link from "next/link";
import { Sparkles } from "lucide-react";
import { marketIntelligenceHref } from "@/lib/market-intelligence";
import { formatCurrency, formatPercent } from "@/lib/utils";

export type AiBriefProps = {
  state: string | null;
  zip: string | null;
  product: string | null;
  segment: string | null;
  expectedRevenue: number;
  predictedConversion: number;
  confidence: number;
  reasons: string[];
  loading?: boolean;
};

export function AiBrief({
  state,
  zip,
  product,
  segment,
  expectedRevenue,
  predictedConversion,
  confidence,
  reasons,
  loading,
}: AiBriefProps) {
  if (loading) {
    return (
      <section className="cios-card min-h-[180px] animate-pulse p-6">
        <div className="h-5 w-48 rounded bg-gray-200" />
        <div className="mt-4 h-4 w-full max-w-2xl rounded bg-gray-100" />
        <div className="mt-2 h-4 w-3/4 rounded bg-gray-100" />
      </section>
    );
  }

  const hasOpportunity = Boolean(state || product);

  if (!hasOpportunity) {
    return (
      <section className="cios-card flex min-h-[180px] flex-col justify-center p-6">
        <p className="text-base font-semibold text-gray-900">No qualified opportunities were identified.</p>
        <p className="mt-1 text-sm text-[var(--cios-secondary)]">
          Upload customer data or expand geography to surface today&apos;s best campaign decision.
        </p>
        <Link
          href="/opportunities"
          className="cios-btn mt-4 inline-flex w-fit bg-[var(--cios-primary)] px-4 py-2 text-sm text-white hover:opacity-90"
        >
          Go to Opportunity Finder
        </Link>
      </section>
    );
  }

  const explorerHref = state ? marketIntelligenceHref({ view: "state", state }) : "/market-intelligence";

  return (
    <Link href={explorerHref} className="cios-card block min-h-[180px] p-6 transition-shadow hover:shadow-md">
      <div className="flex items-start gap-3">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-[var(--cios-primary-light)] text-[var(--cios-primary)]">
          <Sparkles className="h-5 w-5" />
        </div>
        <div className="min-w-0 flex-1">
          <p className="text-xs font-semibold uppercase tracking-wider text-[var(--cios-primary)]">Today&apos;s Best Opportunity</p>
          <h2 className="mt-1 text-lg font-semibold text-gray-900">
            {[state, product, zip].filter(Boolean).join(" · ")}
          </h2>
          {segment && <p className="mt-1 text-sm text-[var(--cios-secondary)]">Target segment: {segment}</p>}
        </div>
      </div>

      <div className="mt-4 grid gap-4 sm:grid-cols-3 lg:grid-cols-5">
        <div>
          <p className="text-xs text-[var(--cios-secondary)]">Expected Revenue</p>
          <p className="text-lg font-bold text-[var(--cios-primary)]">{formatCurrency(expectedRevenue)}</p>
        </div>
        <div>
          <p className="text-xs text-[var(--cios-secondary)]">Predicted Conversion</p>
          <p className="text-lg font-bold text-gray-900">{formatPercent(predictedConversion)}</p>
        </div>
        <div>
          <p className="text-xs text-[var(--cios-secondary)]">AI Confidence</p>
          <p className="text-lg font-bold text-gray-900">{Math.round(confidence)}%</p>
        </div>
      </div>

      {reasons.length > 0 && (
        <ul className="mt-4 flex flex-wrap gap-2">
          {reasons.map((r) => (
            <li key={r} className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-medium text-emerald-800">
              {r}
            </li>
          ))}
        </ul>
      )}
    </Link>
  );
}
