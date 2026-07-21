"use client";

import { useMemo } from "react";
import { CERAGEM_SEGMENTS, INDEX_LEVELS, PRIZM_SEGMENTS, PRODUCT_OPTIONS } from "@/lib/config";
import { cn } from "@/lib/utils";

export type CustomerFilters = {
  states: string[];
  cities: string[];
  zips: string[];
  prizmSegments: string[];
  ceragemSegments: string[];
  purchasePower: string[];
  painIndex: string[];
  lifestyle: string[];
  campaignPriority: string[];
  products: string[];
};

export const EMPTY_CUSTOMER_FILTERS: CustomerFilters = {
  states: [],
  cities: [],
  zips: [],
  prizmSegments: [],
  ceragemSegments: [],
  purchasePower: [],
  painIndex: [],
  lifestyle: [],
  campaignPriority: [],
  products: [],
};

function MultiSelect({
  label,
  options,
  selected,
  onChange,
}: {
  label: string;
  options: readonly string[] | string[];
  selected: string[];
  onChange: (v: string[]) => void;
}) {
  return (
    <label className="block text-sm">
      <span className="mb-1.5 block font-medium text-gray-700">{label}</span>
      <select
        multiple
        className="cios-input h-24 w-full bg-white px-2 py-1.5"
        value={selected}
        onChange={(e) => onChange(Array.from(e.target.selectedOptions, (o) => o.value))}
      >
        {options.map((opt) => (
          <option key={opt} value={opt}>
            {opt}
          </option>
        ))}
      </select>
      <span className="mt-1 block text-xs text-[var(--cios-secondary)]">Hold Ctrl/Cmd to multi-select</span>
    </label>
  );
}

type CustomerFilterPanelProps = {
  filters: CustomerFilters;
  onChange: (filters: CustomerFilters) => void;
  availableStates: string[];
  availableZips: string[];
  className?: string;
};

export function CustomerFilterPanel({
  filters,
  onChange,
  availableStates,
  availableZips,
  className,
}: CustomerFilterPanelProps) {
  const set = <K extends keyof CustomerFilters>(key: K, value: CustomerFilters[K]) =>
    onChange({ ...filters, [key]: value });

  return (
    <aside className={cn("cios-card p-4", className)}>
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-base font-semibold text-gray-900">Filters</h2>
        <button
          type="button"
          className="text-xs font-medium text-[var(--cios-primary)] hover:underline"
          onClick={() => onChange(EMPTY_CUSTOMER_FILTERS)}
        >
          Clear all
        </button>
      </div>
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        <MultiSelect label="State" options={availableStates} selected={filters.states} onChange={(v) => set("states", v)} />
        <MultiSelect label="ZIP" options={availableZips.slice(0, 30)} selected={filters.zips} onChange={(v) => set("zips", v)} />
        <MultiSelect label="PRIZM Proxy Segment" options={PRIZM_SEGMENTS} selected={filters.prizmSegments} onChange={(v) => set("prizmSegments", v)} />
        <MultiSelect label="Ceragem Segment" options={CERAGEM_SEGMENTS} selected={filters.ceragemSegments} onChange={(v) => set("ceragemSegments", v)} />
        <MultiSelect label="Purchase Power" options={INDEX_LEVELS} selected={filters.purchasePower} onChange={(v) => set("purchasePower", v)} />
        <MultiSelect label="Pain Index" options={INDEX_LEVELS} selected={filters.painIndex} onChange={(v) => set("painIndex", v)} />
        <MultiSelect label="Lifestyle Index" options={INDEX_LEVELS} selected={filters.lifestyle} onChange={(v) => set("lifestyle", v)} />
        <MultiSelect label="Campaign Priority" options={INDEX_LEVELS} selected={filters.campaignPriority} onChange={(v) => set("campaignPriority", v)} />
        <MultiSelect label="Product Recommendation" options={PRODUCT_OPTIONS} selected={filters.products} onChange={(v) => set("products", v)} />
      </div>
    </aside>
  );
}

export function indexLevel(value: number | null | undefined): string {
  if (value == null) return "Low";
  if (value >= 0.75) return "High";
  if (value >= 0.45) return "Medium";
  return "Low";
}

export function matchesCustomerFilters(
  row: {
    state: string | null;
    zip: string | null;
    prizm_proxy_segment: string | null;
    ceragem_segment: string | null;
    purchase_power_index?: number | null;
    pain_index?: number | null;
    lifestyle_index?: number | null;
    campaign_priority: number | null;
    recommended_product: string | null;
  },
  filters: CustomerFilters,
): boolean {
  const matchList = (selected: string[], value: string | null) =>
    !selected.length || (value != null && selected.includes(value));

  if (!matchList(filters.states, row.state)) return false;
  if (!matchList(filters.zips, row.zip)) return false;
  if (!matchList(filters.prizmSegments, row.prizm_proxy_segment)) return false;
  if (!matchList(filters.ceragemSegments, row.ceragem_segment)) return false;
  if (!matchList(filters.products, row.recommended_product)) return false;
  if (filters.purchasePower.length && !filters.purchasePower.includes(indexLevel(row.purchase_power_index))) return false;
  if (filters.painIndex.length && !filters.painIndex.includes(indexLevel(row.pain_index))) return false;
  if (filters.lifestyle.length && !filters.lifestyle.includes(indexLevel(row.lifestyle_index))) return false;
  if (filters.campaignPriority.length && !filters.campaignPriority.includes(indexLevel(row.campaign_priority))) return false;
  return true;
}

export function useFilteredCustomers<T extends Parameters<typeof matchesCustomerFilters>[0]>(
  items: T[],
  filters: CustomerFilters,
) {
  return useMemo(() => items.filter((row) => matchesCustomerFilters(row, filters)), [items, filters]);
}
