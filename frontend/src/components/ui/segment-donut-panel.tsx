"use client";

import { DonutChart } from "@/components/ui/donut-chart";

// Display-only relabels for engine fallback values that read as low-confidence.
// The underlying stored value (e.g. "Unknown") is preserved for audit/rollup/export.
const LABEL_OVERRIDES: Record<string, string> = {
  Unknown: "Unclassified",
};

function relabel(data: Record<string, number>): Record<string, number> {
  const out: Record<string, number> = {};
  for (const [key, value] of Object.entries(data)) {
    const label = LABEL_OVERRIDES[key] ?? key;
    out[label] = (out[label] ?? 0) + value;
  }
  return out;
}

const SEGMENTS = [
  { id: "pain_index", label: "Pain Index" },
  { id: "lifestyle", label: "Lifestyle" },
  { id: "prizm", label: "PRIZM Proxy" },
  { id: "ceragem", label: "Ceragem Segment" },
  { id: "purchase_power", label: "Purchase Power" },
  { id: "brand_familiarity", label: "Brand Familiarity" },
] as const;

type SegmentDistribution = {
  prizm: Record<string, number>;
  ceragem: Record<string, number>;
  purchase_power: Record<string, number>;
  pain_index: Record<string, number>;
  lifestyle: Record<string, number>;
  brand_familiarity?: Record<string, number>;
};

export function SegmentDonutPanel({ data }: { data: SegmentDistribution }) {
  return (
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
      {SEGMENTS.map((segment) => (
        <div key={segment.id} className="cios-card p-4">
          <h3 className="mb-3 text-sm font-semibold text-gray-900">{segment.label}</h3>
          <DonutChart data={relabel(data[segment.id] ?? {})} title={segment.label} legendPosition="bottom" />
        </div>
      ))}
    </div>
  );
}
