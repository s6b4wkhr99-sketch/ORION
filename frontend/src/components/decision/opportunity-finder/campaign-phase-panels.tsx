"use client";

import Link from "next/link";
import { MapPin, TrendingUp } from "lucide-react";
import type { CampaignOpportunitySimulateResult } from "@/lib/api";
import { formatCurrency, formatNumber, formatPercent } from "@/lib/utils";

type TopMetroPanelProps = {
  metros: CampaignOpportunitySimulateResult["phase1"]["top_metros"];
  selectedStates: string[];
};

export function TopMetroPanel({ metros, selectedStates }: TopMetroPanelProps) {
  return (
    <section className="orion-widget p-5">
      <div className="mb-4 flex flex-wrap items-start justify-between gap-2">
        <div>
          <h2 className="text-base font-semibold text-gray-900">Phase 1 · Top 5 Metro Analysis</h2>
          <p className="mt-1 text-xs text-[var(--cios-secondary)]">
            {selectedStates.length
              ? `Ranked metros within ${selectedStates.join(", ")} for the selected SKU bundle.`
              : "National top metros for the selected SKU bundle — select states on the map to narrow scope."}
          </p>
        </div>
        <span className="rounded-full bg-indigo-50 px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wide text-indigo-700">
          1st Pass
        </span>
      </div>

      {!metros.length ? (
        <p className="text-sm text-[var(--cios-secondary)]">No metro opportunities in the current geographic scope.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead>
              <tr className="border-b border-[var(--cios-border)] text-left text-xs uppercase tracking-wide text-[var(--cios-secondary)]">
                <th className="py-2 pr-4">Rank</th>
                <th className="py-2 pr-4">Metro (CBSA)</th>
                <th className="py-2 pr-4">States</th>
                <th className="py-2 pr-4">Customers</th>
                <th className="py-2 pr-4">Revenue</th>
                <th className="py-2 pr-4">Conversion</th>
                <th className="py-2">Asian Pop. Index</th>
              </tr>
            </thead>
            <tbody>
              {metros.map((metro, index) => (
                <tr key={metro.cbsa_code} className="border-b border-gray-100">
                  <td className="py-3 pr-4 font-medium text-gray-900">#{index + 1}</td>
                  <td className="py-3 pr-4">
                    <div className="font-medium text-gray-900">{metro.cbsa_name}</div>
                    <div className="text-xs text-[var(--cios-secondary)]">{metro.cbsa_code}</div>
                  </td>
                  <td className="py-3 pr-4 text-xs">{(metro.states ?? []).join(", ") || "—"}</td>
                  <td className="py-3 pr-4">{formatNumber(metro.customers)}</td>
                  <td className="py-3 pr-4">{formatCurrency(metro.revenue)}</td>
                  <td className="py-3 pr-4">{formatPercent(metro.conversion)}</td>
                  <td className="py-3">{metro.asian_relative_index != null ? metro.asian_relative_index.toFixed(2) : "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {metros[0] ? (
        <div className="mt-4 flex flex-wrap items-center justify-between gap-3 rounded-lg bg-slate-50 px-4 py-3 text-sm">
          <div className="flex items-center gap-2 text-gray-900">
            <MapPin className="h-4 w-4 text-indigo-600" />
            <span>
              Lead metro: <strong>{metros[0].cbsa_name}</strong>
            </span>
          </div>
          <Link href={`/metro-intelligence?cbsa=${encodeURIComponent(metros[0].cbsa_code)}`} className="text-xs font-medium text-indigo-600 hover:underline">
            Open Metro Intelligence →
          </Link>
        </div>
      ) : null}
    </section>
  );
}

export function KpiComparisonStrip({
  label,
  dbPotential,
  phase1,
  phase2,
}: {
  label: string;
  dbPotential: CampaignOpportunitySimulateResult["db_potential"];
  phase1: CampaignOpportunitySimulateResult["phase1"]["kpis"];
  phase2: CampaignOpportunitySimulateResult["phase2"]["kpis"];
}) {
  const cards = [
    { title: "Full DB Potential", kpis: dbPotential, accent: "border-slate-200 bg-slate-50" },
    { title: "Phase 1 · Geo Scope", kpis: phase1, accent: "border-indigo-200 bg-indigo-50" },
    { title: "Phase 2 · Segment Refined", kpis: phase2, accent: "border-teal-200 bg-teal-50" },
  ];

  return (
    <section className="orion-widget p-5">
      <div className="mb-4 flex items-center gap-2">
        <TrendingUp className="h-5 w-5 text-indigo-600" />
        <h2 className="text-base font-semibold text-gray-900">{label}</h2>
      </div>
      <div className="grid gap-4 md:grid-cols-3">
        {cards.map((card) => (
          <div key={card.title} className={`rounded-xl border p-4 ${card.accent}`}>
            <p className="text-xs font-semibold uppercase tracking-wide text-gray-700">{card.title}</p>
            <dl className="mt-3 space-y-2 text-sm">
              <div className="flex justify-between gap-3">
                <dt className="text-[var(--cios-secondary)]">Customers</dt>
                <dd className="font-medium text-gray-900">{formatNumber(card.kpis.customers)}</dd>
              </div>
              <div className="flex justify-between gap-3">
                <dt className="text-[var(--cios-secondary)]">Revenue</dt>
                <dd className="font-medium text-gray-900">{formatCurrency(card.kpis.revenue)}</dd>
              </div>
              <div className="flex justify-between gap-3">
                <dt className="text-[var(--cios-secondary)]">Expected Orders</dt>
                <dd className="font-medium text-gray-900">{formatNumber(card.kpis.orders)}</dd>
              </div>
              <div className="flex justify-between gap-3">
                <dt className="text-[var(--cios-secondary)]">Conversion</dt>
                <dd className="font-medium text-gray-900">{formatPercent(card.kpis.conversion)}</dd>
              </div>
            </dl>
          </div>
        ))}
      </div>
    </section>
  );
}
