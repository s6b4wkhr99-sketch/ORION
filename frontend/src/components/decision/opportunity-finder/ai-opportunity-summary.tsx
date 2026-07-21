"use client";

import Link from "next/link";
import { ArrowRight, Sparkles } from "lucide-react";
import { marketIntelligenceHref } from "@/lib/market-intelligence";
import { displayProductLabel } from "@/lib/product-legend-groups";
import { formatCurrency, formatNumber, formatPercent } from "@/lib/utils";

export type AiOpportunitySummaryProps = {
  state: string | null;
  zip: string | null;
  product: string | null;
  customers: number;
  expectedRevenue: number;
  predictedConversion: number;
  confidence: number;
  reasons: string[];
};

export function AiOpportunitySummary({
  state,
  zip,
  product,
  customers,
  expectedRevenue,
  predictedConversion,
  confidence,
  reasons,
}: AiOpportunitySummaryProps) {
  const href =
    state && zip
      ? marketIntelligenceHref({ view: "zip", state, zip })
      : state
        ? marketIntelligenceHref({ view: "state", state })
        : "/market-intelligence";

  return (
    <section className="orion-widget bg-gradient-to-br from-indigo-50/80 to-white">
      <div className="flex items-center gap-2 border-b border-indigo-100 px-5 py-4">
        <Sparkles className="h-5 w-5 text-indigo-600" />
        <div>
          <h2 className="text-base font-semibold text-gray-900">AI Opportunity Summary</h2>
          <p className="text-xs text-[var(--cios-secondary)]">Highest qualified opportunity from your search</p>
        </div>
      </div>
      <div className="p-5">
        <p className="text-lg font-semibold text-gray-900">
          {[product ? displayProductLabel(product) : null, state, zip].filter(Boolean).join(" · ") || "No opportunity matched"}
        </p>
        <div className="mt-4 grid gap-4 sm:grid-cols-4">
          <Stat label="Opportunity Customers" value={formatNumber(customers)} />
          <Stat label="Expected Revenue" value={formatCurrency(expectedRevenue)} highlight />
          <Stat label="Pred. Conversion" value={formatPercent(predictedConversion)} />
          <Stat label="AI Confidence" value={`${Math.round(confidence)}%`} />
        </div>
        {reasons.length > 0 && (
          <div className="mt-4 flex flex-wrap gap-2">
            {reasons.map((r) => (
              <span key={r} className="rounded-full bg-white px-3 py-1 text-xs font-medium text-indigo-800 ring-1 ring-indigo-100">
                {r}
              </span>
            ))}
          </div>
        )}
        <Link href={href} className="mt-4 inline-flex items-center gap-1 text-sm font-medium text-indigo-600 hover:underline">
          Open Market Intelligence
          <ArrowRight className="h-4 w-4" />
        </Link>
      </div>
    </section>
  );
}

function Stat({ label, value, highlight }: { label: string; value: string; highlight?: boolean }) {
  return (
    <div>
      <p className="text-xs text-[var(--cios-secondary)]">{label}</p>
      <p className={highlight ? "text-lg font-bold text-indigo-600" : "text-base font-bold text-gray-900"}>{value}</p>
    </div>
  );
}
