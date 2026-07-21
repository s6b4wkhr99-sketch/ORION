"use client";

import { Search } from "lucide-react";
import { RangeSlider } from "@/components/decision/shared/range-slider";
import { PRODUCT_OPTIONS } from "@/lib/config";

export type FinderSearchCriteria = {
  product: string;
  state: string;
  metroCbsa: string;
  minPainIndex: number;
  minPurchasePower: number;
  minLifestyle: number;
  goal: string;
  targetAdjustPct: number;
};

export const FINDER_GOALS = ["Revenue", "Conversion", "Acquisition", "Premium Product", "Clinical Product"] as const;

type SearchBuilderProps = {
  criteria: FinderSearchCriteria;
  onChange: (criteria: FinderSearchCriteria) => void;
  availableStates: string[];
  availableMetros: Array<{ cbsa_code: string; cbsa_name: string }>;
  onSimulate: () => void;
  simulating?: boolean;
};

export function SearchBuilder({ criteria, onChange, availableStates, availableMetros, onSimulate, simulating }: SearchBuilderProps) {
  const set = <K extends keyof FinderSearchCriteria>(key: K, value: FinderSearchCriteria[K]) =>
    onChange({ ...criteria, [key]: value });

  return (
    <section className="orion-widget sticky top-[calc(var(--header-height)+1rem)] z-10">
      <div className="border-b border-[var(--cios-border)] px-5 py-4">
        <h2 className="text-base font-semibold text-gray-900">Campaign KPI Planner</h2>
        <p className="mt-0.5 text-xs text-[var(--cios-secondary)]">Scope product, geography, audience — then simulate pre-launch KPIs</p>
      </div>
      <div className="space-y-5 p-5">
        <div>
          <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-[var(--cios-secondary)]">Product</p>
          <div className="flex flex-wrap gap-2">
            <ProductPill label="All Products" active={!criteria.product} onClick={() => set("product", "")} />
            {PRODUCT_OPTIONS.slice(0, 5).map((p) => (
              <ProductPill key={p} label={p} active={criteria.product === p} onClick={() => set("product", p)} />
            ))}
          </div>
        </div>

        <div className="grid gap-4 sm:grid-cols-3">
          <RangeSlider label="Minimum Lifestyle" min={0} max={100} value={criteria.minLifestyle} onChange={(v) => set("minLifestyle", v)} />
          <RangeSlider label="Minimum Pain Index" min={0} max={100} value={criteria.minPainIndex} onChange={(v) => set("minPainIndex", v)} />
          <RangeSlider
            label="Minimum Purchase Power"
            min={0}
            max={100}
            value={criteria.minPurchasePower}
            onChange={(v) => set("minPurchasePower", v)}
          />
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <label className="block text-sm">
            <span className="mb-1.5 block font-medium text-gray-700">State (Market Intelligence)</span>
            <select
              className="cios-input w-full bg-white px-3 py-2"
              value={criteria.state}
              onChange={(e) => onChange({ ...criteria, state: e.target.value, metroCbsa: "" })}
            >
              <option value="">United States (National)</option>
              {availableStates.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </label>
          <label className="block text-sm">
            <span className="mb-1.5 block font-medium text-gray-700">Metro (Metro Intelligence)</span>
            <select
              className="cios-input w-full bg-white px-3 py-2"
              value={criteria.metroCbsa}
              onChange={(e) => set("metroCbsa", e.target.value)}
              disabled={!criteria.state && availableMetros.length === 0}
            >
              <option value="">All metros / optional</option>
              {availableMetros.map((m) => (
                <option key={m.cbsa_code} value={m.cbsa_code}>
                  {m.cbsa_name}
                </option>
              ))}
            </select>
          </label>
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <label className="block text-sm">
            <span className="mb-1.5 block font-medium text-gray-700">Campaign Goal</span>
            <select
              className="cios-input w-full bg-white px-3 py-2"
              value={criteria.goal}
              onChange={(e) => set("goal", e.target.value)}
            >
              {FINDER_GOALS.map((g) => (
                <option key={g} value={g}>
                  {g}
                </option>
              ))}
            </select>
          </label>
          <div>
            <RangeSlider
              label="KPI Target Ambition"
              min={50}
              max={150}
              value={criteria.targetAdjustPct}
              onChange={(v) => set("targetAdjustPct", v)}
            />
            <p className="mt-1 text-xs text-[var(--cios-secondary)]">{criteria.targetAdjustPct}% of intelligence baseline</p>
          </div>
        </div>

        <button
          type="button"
          onClick={onSimulate}
          disabled={simulating}
          className="orion-btn-primary flex w-full items-center justify-center gap-2 py-3 text-sm font-semibold disabled:opacity-60"
        >
          <Search className="h-4 w-4" />
          {simulating ? "Simulating…" : "Run Campaign KPI Simulation"}
        </button>
      </div>
    </section>
  );
}

function ProductPill({ label, active, onClick }: { label: string; active: boolean; onClick: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`rounded-full px-3.5 py-1.5 text-sm font-medium transition-colors ${
        active ? "bg-indigo-600 text-white shadow-sm" : "border border-gray-200 bg-white text-gray-700 hover:border-indigo-200"
      }`}
    >
      {label}
    </button>
  );
}
