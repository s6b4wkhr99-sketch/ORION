"use client";

import { formatCurrency, formatNumber } from "@/lib/utils";

export type SellableProductRow = {
  product: string;
  expected_customers: number;
  expected_revenue: number;
  expected_orders?: number;
};

type SellableProductsSectionProps = {
  products: SellableProductRow[];
  /** e.g. "California — Sellable Products" */
  title?: string;
  subtitle?: string;
  limit?: number;
};

export function SellableProductsSection({
  products,
  title = "Sellable Products",
  subtitle,
  limit = 8,
}: SellableProductsSectionProps) {
  if (!products.length) return null;

  return (
    <section>
      <h2 className="mb-1 text-base font-semibold text-gray-900">{title}</h2>
      {subtitle ? <p className="mb-3 text-xs text-[var(--cios-secondary)]">{subtitle}</p> : <div className="mb-3" />}
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {products.slice(0, limit).map((p) => (
          <div key={p.product} className="cios-card p-4">
            <p className="font-semibold text-gray-900">{p.product}</p>
            <p className="mt-2 text-sm text-[var(--cios-secondary)]">
              {formatNumber(p.expected_customers)} customers · {formatCurrency(p.expected_revenue)}
            </p>
          </div>
        ))}
      </div>
    </section>
  );
}
