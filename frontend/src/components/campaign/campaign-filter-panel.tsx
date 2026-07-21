"use client";

import { useMemo } from "react";
import {
  CERAGEM_SEGMENTS,
  INDEX_LEVELS,
  PRIZM_SEGMENTS,
  PRODUCT_OPTIONS,
} from "@/lib/config";
import { EMPTY_CUSTOMER_FILTERS, type CustomerFilters } from "@/components/customer/customer-filters";

export const CAMPAIGN_TYPES = ["Email", "Direct Mail", "SMS", "Multi-Channel"] as const;
export const MESSAGE_DIRECTIONS = [
  "Wellness & Prevention",
  "Pain Relief & Recovery",
  "Premium Lifestyle",
  "Value & Accessibility",
] as const;

export type CampaignFilters = CustomerFilters & {
  cities: string[];
  messageDirections: string[];
  campaignTypes: string[];
};

export const EMPTY_CAMPAIGN_FILTERS: CampaignFilters = {
  ...EMPTY_CUSTOMER_FILTERS,
  cities: [],
  messageDirections: [],
  campaignTypes: [],
};

type CampaignFilterPanelProps = {
  filters: CampaignFilters;
  onChange: (filters: CampaignFilters) => void;
  availableStates: string[];
  availableZips: string[];
  availableCities: string[];
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
    </label>
  );
}

export function CampaignFilterPanel({
  filters,
  onChange,
  availableStates,
  availableZips,
  availableCities,
}: CampaignFilterPanelProps) {
  const set = <K extends keyof CampaignFilters>(key: K, value: CampaignFilters[K]) =>
    onChange({ ...filters, [key]: value });

  return (
    <section className="cios-card p-5">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-base font-semibold text-gray-900">Campaign Filters</h2>
        <button
          type="button"
          className="text-xs font-medium text-[var(--cios-primary)] hover:underline"
          onClick={() => onChange(EMPTY_CAMPAIGN_FILTERS)}
        >
          Clear all
        </button>
      </div>
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        <MultiSelect label="State" options={availableStates} selected={filters.states} onChange={(v) => set("states", v)} />
        <MultiSelect label="ZIP" options={availableZips.slice(0, 30)} selected={filters.zips} onChange={(v) => set("zips", v)} />
        <MultiSelect label="City" options={availableCities.slice(0, 30)} selected={filters.cities} onChange={(v) => set("cities", v)} />
        <MultiSelect label="PRIZM Proxy Segment" options={PRIZM_SEGMENTS} selected={filters.prizmSegments} onChange={(v) => set("prizmSegments", v)} />
        <MultiSelect label="Ceragem Segment" options={CERAGEM_SEGMENTS} selected={filters.ceragemSegments} onChange={(v) => set("ceragemSegments", v)} />
        <MultiSelect label="Purchase Power" options={INDEX_LEVELS} selected={filters.purchasePower} onChange={(v) => set("purchasePower", v)} />
        <MultiSelect label="Pain Index" options={INDEX_LEVELS} selected={filters.painIndex} onChange={(v) => set("painIndex", v)} />
        <MultiSelect label="Lifestyle Index" options={INDEX_LEVELS} selected={filters.lifestyle} onChange={(v) => set("lifestyle", v)} />
        <MultiSelect label="Campaign Priority" options={INDEX_LEVELS} selected={filters.campaignPriority} onChange={(v) => set("campaignPriority", v)} />
        <MultiSelect label="Recommended Product" options={PRODUCT_OPTIONS} selected={filters.products} onChange={(v) => set("products", v)} />
        <MultiSelect label="Message Direction" options={MESSAGE_DIRECTIONS} selected={filters.messageDirections} onChange={(v) => set("messageDirections", v)} />
        <MultiSelect label="Campaign Type" options={CAMPAIGN_TYPES} selected={filters.campaignTypes} onChange={(v) => set("campaignTypes", v)} />
      </div>
    </section>
  );
}

export function useCampaignFilteredCustomers<
  T extends {
    state: string | null;
    zip: string | null;
    prizm_proxy_segment: string | null;
    ceragem_segment: string | null;
    purchase_power_index?: number | null;
    pain_index?: number | null;
    lifestyle_index?: number | null;
    campaign_priority: number | null;
    recommended_product: string | null;
    message_direction?: string | null;
  },
>(items: T[], filters: CampaignFilters) {
  return useMemo(() => {
    const matchList = (selected: string[], value: string | null) =>
      !selected.length || (value != null && selected.includes(value));

    return items.filter((row) => {
      if (filters.states.length && !matchList(filters.states, row.state)) return false;
      if (filters.zips.length && !matchList(filters.zips, row.zip)) return false;
      if (filters.prizmSegments.length && !matchList(filters.prizmSegments, row.prizm_proxy_segment)) return false;
      if (filters.ceragemSegments.length && !matchList(filters.ceragemSegments, row.ceragem_segment)) return false;
      if (filters.products.length && !matchList(filters.products, row.recommended_product)) return false;
      if (filters.messageDirections.length && !matchList(filters.messageDirections, row.message_direction ?? null)) return false;

      const level = (v: number | null | undefined) => {
        if (v == null) return "Low";
        if (v >= 0.75) return "High";
        if (v >= 0.45) return "Medium";
        return "Low";
      };
      if (filters.purchasePower.length && !filters.purchasePower.includes(level(row.purchase_power_index))) return false;
      if (filters.painIndex.length && !filters.painIndex.includes(level(row.pain_index))) return false;
      if (filters.lifestyle.length && !filters.lifestyle.includes(level(row.lifestyle_index))) return false;
      if (filters.campaignPriority.length && !filters.campaignPriority.includes(level(row.campaign_priority))) return false;
      return true;
    });
  }, [items, filters]);
}
