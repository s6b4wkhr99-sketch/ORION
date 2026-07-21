"use client";

import type { SimulatedCampaignPlan } from "@/lib/campaign-kpi-simulator";
import { formatCurrency, formatNumber, formatPercent } from "@/lib/utils";

export function CampaignKpiBoard({ plan }: { plan: SimulatedCampaignPlan }) {
  const rows = [
    { label: "Target Customers", baseline: plan.baseline.customers, target: plan.targets.customers, format: formatNumber },
    { label: "Expected Revenue", baseline: plan.baseline.revenue, target: plan.targets.revenue, format: formatCurrency },
    { label: "Predicted Conversion", baseline: plan.baseline.conversion, target: plan.targets.conversion, format: formatPercent },
    { label: "Expected Orders", baseline: plan.baseline.orders, target: plan.targets.orders, format: formatNumber },
  ];

  return (
    <section className="orion-widget p-5">
      <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-base font-semibold text-gray-900">KPI Baseline vs Campaign Target</h2>
          <p className="mt-1 text-sm text-[var(--cios-secondary)]">
            Intelligence-derived baseline compared with your pre-launch campaign operating targets.
          </p>
        </div>
        <div className="text-right text-xs text-[var(--cios-secondary)]">
          <p>Recommended SKU: <span className="font-semibold text-gray-900">{plan.recommendedProduct ?? "—"}</span></p>
          <p>Confidence: <span className="font-semibold text-gray-900">{Math.round(plan.confidence)}</span></p>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-full text-sm">
          <thead>
            <tr className="border-b border-[var(--cios-border)] text-left text-xs uppercase tracking-wide text-[var(--cios-secondary)]">
              <th className="py-2 pr-4">KPI</th>
              <th className="py-2 pr-4">Intelligence Baseline</th>
              <th className="py-2 pr-4">Campaign Target</th>
              <th className="py-2">Delta</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => {
              const delta = row.target - row.baseline;
              const deltaPct = row.baseline ? (delta / row.baseline) * 100 : 0;
              return (
                <tr key={row.label} className="border-b border-gray-100">
                  <td className="py-3 pr-4 font-medium text-gray-900">{row.label}</td>
                  <td className="py-3 pr-4 text-[var(--cios-secondary)]">{row.format(row.baseline)}</td>
                  <td className="py-3 pr-4 font-semibold text-indigo-700">{row.format(row.target)}</td>
                  <td className={`py-3 font-medium ${delta >= 0 ? "text-emerald-700" : "text-amber-700"}`}>
                    {delta >= 0 ? "+" : ""}
                    {row.label.includes("Conversion") ? formatPercent(Math.abs(delta)) : row.format(Math.abs(delta))}
                    <span className="ml-2 text-xs text-[var(--cios-secondary)]">({deltaPct >= 0 ? "+" : ""}{deltaPct.toFixed(1)}%)</span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </section>
  );
}
