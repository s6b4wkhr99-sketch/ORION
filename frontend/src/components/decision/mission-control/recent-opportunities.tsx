"use client";

import { useMemo } from "react";
import { formatCurrency, formatNumber, formatPercent } from "@/lib/utils";

export type RecentOpportunityRow = {
  rank: number;
  state: string;
  city?: string | null;
  zip: string | null;
  opportunityScore: number;
  customers: number;
  predictedConversion: number;
  baselineConversion: number;
  promoUplift: number;
  expectedRevenue: number;
  recommendedProduct: string;
  promoProduct: string;
};

export function RecentOpportunitiesTable({ rows }: { rows: RecentOpportunityRow[] }) {
  const sortedRows = useMemo(
    () =>
      [...rows]
        .sort((a, b) => b.opportunityScore - a.opportunityScore || b.expectedRevenue - a.expectedRevenue)
        .map((row, index) => ({ ...row, rank: index + 1 })),
    [rows],
  );

  if (!sortedRows.length) {
    return <p className="text-sm text-[var(--cios-secondary)]">No ranked opportunities in current scope.</p>;
  }

  return (
    <div className="flex flex-col">
      <div className="overflow-x-auto">
      <table className="w-max max-w-full table-auto border-separate border-spacing-0 text-xs">
        <thead>
          <tr className="border-b border-gray-100 text-center">
            <th className="whitespace-nowrap px-3 py-1 text-center text-xs font-medium text-gray-700">Rank</th>
            <th className="whitespace-nowrap px-3 py-1 text-center text-xs font-medium text-gray-700">City / Zip</th>
            <th className="whitespace-nowrap px-3 py-1 text-center text-xs font-medium text-gray-700">Score</th>
            <th className="whitespace-nowrap px-3 py-1 text-center text-xs font-medium text-gray-700">Customers</th>
            <th className="whitespace-nowrap px-3 py-1 text-center text-xs font-medium text-gray-700">Baseline conv.</th>
            <th className="whitespace-nowrap px-3 py-1 text-center text-xs font-medium text-gray-700">Promo uplift</th>
            <th className="whitespace-nowrap px-3 py-1 text-center text-xs font-medium text-gray-700">TAR</th>
            <th className="whitespace-nowrap px-3 py-1 text-center text-xs font-medium text-gray-700">Intelligence</th>
            <th className="whitespace-nowrap px-3 py-1 text-center text-xs font-medium text-gray-700">Promo sku</th>
          </tr>
        </thead>
        <tbody>
          {sortedRows.map((row) => (
            <tr key={`${row.state}-${row.zip}-${row.rank}`} className="border-b border-gray-50 hover:bg-slate-50/80">
              <td className="whitespace-nowrap px-3 py-1.5 text-center">
                <span className="inline-flex h-5 w-5 items-center justify-center rounded-full bg-indigo-50 text-xs font-bold text-indigo-700">
                  {row.rank}
                </span>
              </td>
              <td className="whitespace-nowrap px-3 py-1.5 text-center text-xs font-medium text-gray-700">
                {row.city ? (
                  <>
                    <span className="block">{row.city}</span>
                    {row.zip ? (
                      <span className="block text-xs font-normal text-[var(--cios-secondary)]">{row.zip}</span>
                    ) : null}
                  </>
                ) : row.zip ? (
                  <span>{row.zip}</span>
                ) : (
                  <span>{row.state}</span>
                )}
              </td>
              <td className="whitespace-nowrap px-3 py-1.5 text-center text-xs font-semibold text-indigo-600">{row.opportunityScore}</td>
              <td className="whitespace-nowrap px-3 py-1.5 text-center text-xs text-gray-700">{formatNumber(row.customers)}</td>
              <td className="whitespace-nowrap px-3 py-1.5 text-center text-xs text-gray-700">{formatPercent(row.baselineConversion)}</td>
              <td className="whitespace-nowrap px-3 py-1.5 text-center text-xs text-gray-700">{formatPercent(row.promoUplift)}</td>
              <td className="whitespace-nowrap px-3 py-1.5 text-center text-xs font-medium text-gray-700">{formatCurrency(row.expectedRevenue)}</td>
              <td className="whitespace-nowrap px-3 py-1.5 text-center text-xs text-gray-700">{row.recommendedProduct}</td>
              <td className="whitespace-nowrap px-3 py-1.5 text-center text-xs text-gray-700">{row.promoProduct}</td>
            </tr>
          ))}
        </tbody>
      </table>
      </div>
    </div>
  );
}
