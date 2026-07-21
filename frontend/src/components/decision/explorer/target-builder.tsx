"use client";

import { Search, Sparkles } from "lucide-react";
import { RangeSlider } from "@/components/decision/shared/range-slider";
import {
  deriveCampaignMessage,
  deriveRecommendedProduct,
  EXPLORER_GOALS,
  EXPLORER_PRODUCT_CHOICES,
  type ExplorerTargetCriteria,
} from "@/lib/opportunity-targeting";

type TargetBuilderProps = {
  criteria: ExplorerTargetCriteria;
  onChange: (criteria: ExplorerTargetCriteria) => void;
  availableStates: string[];
  onApply: () => void;
  applying?: boolean;
  matchedCount?: number;
  previewProduct?: string;
};

export function TargetBuilder({
  criteria,
  onChange,
  availableStates,
  onApply,
  applying,
  matchedCount,
  previewProduct,
}: TargetBuilderProps) {
  const set = <K extends keyof ExplorerTargetCriteria>(key: K, value: ExplorerTargetCriteria[K]) =>
    onChange({ ...criteria, [key]: value });

  const campaignMessage = deriveCampaignMessage(criteria);
  const recommendedProduct = previewProduct ?? deriveRecommendedProduct(criteria, []);

  return (
    <section className="orion-widget">
      <div className="border-b border-[var(--cios-border)] px-5 py-4">
        <h2 className="text-base font-semibold text-gray-900">Target Builder</h2>
        <p className="mt-0.5 text-xs text-[var(--cios-secondary)]">
          Product · Lifestyle · Pain · Purchase Power — drives target SKU and campaign message
        </p>
      </div>
      <div className="space-y-5 p-5">
        <div>
          <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-[var(--cios-secondary)]">Product Series</p>
          <div className="flex flex-wrap gap-2">
            {EXPLORER_PRODUCT_CHOICES.slice(0, 6).map((p) => (
              <ProductPill
                key={p || "all"}
                label={p || "All Products"}
                active={criteria.product === p}
                onClick={() => set("product", p)}
              />
            ))}
          </div>
          <div className="mt-2 flex flex-wrap gap-2">
            {EXPLORER_PRODUCT_CHOICES.slice(6).map((p) => (
              <ProductPill key={p} label={p} active={criteria.product === p} onClick={() => set("product", p)} />
            ))}
          </div>
        </div>

        <div className="grid gap-4 sm:grid-cols-3">
          <RangeSlider label="Minimum Lifestyle" min={0} max={100} value={criteria.lifestyleMin} onChange={(v) => set("lifestyleMin", v)} />
          <RangeSlider label="Minimum Pain Index" min={0} max={100} value={criteria.painMin} onChange={(v) => set("painMin", v)} />
          <RangeSlider
            label="Minimum Purchase Power"
            min={0}
            max={100}
            value={criteria.purchasePowerMin}
            onChange={(v) => set("purchasePowerMin", v)}
          />
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <label className="block text-sm">
            <span className="mb-1.5 block font-medium text-gray-700">Geography (State)</span>
            <select
              className="cios-input w-full bg-white px-3 py-2"
              value={criteria.state}
              onChange={(e) => set("state", e.target.value)}
            >
              <option value="">United States (All)</option>
              {availableStates.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </label>
          <label className="block text-sm">
            <span className="mb-1.5 block font-medium text-gray-700">Campaign Goal</span>
            <select className="cios-input w-full bg-white px-3 py-2" value={criteria.goal} onChange={(e) => set("goal", e.target.value)}>
              {EXPLORER_GOALS.map((g) => (
                <option key={g} value={g}>
                  {g}
                </option>
              ))}
            </select>
          </label>
        </div>

        <div className="rounded-lg border border-indigo-100 bg-indigo-50/60 p-4 text-sm">
          <p className="flex items-center gap-2 font-semibold text-indigo-900">
            <Sparkles className="h-4 w-4" />
            Target Preview
          </p>
          <dl className="mt-3 grid gap-2 sm:grid-cols-2">
            <div>
              <dt className="text-xs uppercase tracking-wide text-indigo-700/80">Recommended Product</dt>
              <dd className="font-medium text-gray-900">{recommendedProduct}</dd>
            </div>
            <div>
              <dt className="text-xs uppercase tracking-wide text-indigo-700/80">Campaign Message</dt>
              <dd className="font-medium text-gray-900">{campaignMessage}</dd>
            </div>
            {matchedCount != null && (
              <div className="sm:col-span-2">
                <dt className="text-xs uppercase tracking-wide text-indigo-700/80">Matched Audience</dt>
                <dd className="font-medium text-gray-900">{matchedCount.toLocaleString()} customers</dd>
              </div>
            )}
          </dl>
          <p className="mt-2 text-xs text-indigo-800/80">
            V Series weight increases with Pain · M Series with Lifestyle/sleep · Premium ZIP with Purchase Power
          </p>
        </div>

        <button
          type="button"
          onClick={onApply}
          disabled={applying}
          className="orion-btn-primary flex w-full items-center justify-center gap-2 py-3 text-sm font-semibold disabled:opacity-60"
        >
          <Search className="h-4 w-4" />
          {applying ? "Analyzing..." : "Apply Target Profile"}
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
