"use client";

import { useState } from "react";
import { DonutChart } from "@/components/ui/donut-chart";
import { cn } from "@/lib/utils";

const TABS = [
  { id: "ceragem", label: "Ceragem Segment" },
  { id: "prizm", label: "PRIZM Proxy" },
  { id: "purchase_power", label: "Purchase Power" },
  { id: "pain_index", label: "Pain Index" },
  { id: "lifestyle", label: "Lifestyle" },
  { id: "message_direction", label: "Message Direction" },
] as const;

type AudienceDistribution = {
  ceragem: Record<string, number>;
  prizm: Record<string, number>;
  purchase_power: Record<string, number>;
  pain_index: Record<string, number>;
  lifestyle: Record<string, number>;
  message_direction: Record<string, number>;
};

export function AudienceDistributionPanel({
  data,
  onFilter,
}: {
  data: AudienceDistribution;
  onFilter?: (dimension: string, value: string) => void;
}) {
  const [tab, setTab] = useState<(typeof TABS)[number]["id"]>("ceragem");
  const current = data[tab] ?? {};

  return (
    <section className="cios-card p-5">
      <h2 className="mb-4 text-base font-semibold text-gray-900">Audience Distribution</h2>
      <div className="mb-4 flex flex-wrap gap-2">
        {TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => setTab(t.id)}
            className={cn(
              "rounded-full px-3 py-1 text-xs font-medium",
              tab === t.id ? "bg-[var(--cios-primary)] text-white" : "bg-gray-100 text-[var(--cios-secondary)] hover:bg-gray-200",
            )}
          >
            {t.label}
          </button>
        ))}
      </div>
      <DonutChart data={current} title={tab} />
      {onFilter && (
        <div className="mt-4 flex flex-wrap gap-2">
          {Object.keys(current)
            .slice(0, 4)
            .map((key) => (
              <button
                key={key}
                type="button"
                onClick={() => onFilter(tab, key)}
                className="cios-btn border border-[var(--cios-border)] bg-white px-2 py-1 text-xs hover:bg-gray-50"
              >
                Filter: {key}
              </button>
            ))}
        </div>
      )}
    </section>
  );
}
