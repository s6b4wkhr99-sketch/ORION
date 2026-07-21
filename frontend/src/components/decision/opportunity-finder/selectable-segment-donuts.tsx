"use client";

import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import { segmentDisplayForDimension, segmentLegendOrder } from "@/lib/segment-display-labels";
import { cn } from "@/lib/utils";

const PALETTE = ["#0056D2", "#5B9BD5", "#7BA7E8", "#16A34A", "#F59E0B", "#DC2626", "#9333EA", "#64748B"];
const SELECTED_SLICE_FILL = "#4338CA";

type Slice = { name: string; value: number; percent: number; title: string; subtitle?: string };

function SegmentDonutTooltip({ active, payload }: { active?: boolean; payload?: { payload: Slice }[] }) {
  if (!active || !payload?.length) return null;
  const slice = payload[0].payload;
  return (
    <div className="rounded-lg border border-[var(--cios-border)] bg-white p-3 text-xs shadow-lg">
      <p className="font-semibold text-gray-900">{slice.title}</p>
      {slice.subtitle ? <p className="mt-0.5 text-[10px] text-[var(--cios-secondary)]">{slice.subtitle}</p> : null}
      <p className="mt-1 text-[var(--cios-secondary)]">
        Customers: <span className="font-medium text-gray-700">{slice.value.toLocaleString()}</span>
      </p>
      <p className="mt-1 text-[var(--cios-secondary)]">
        Share: <span className="font-medium text-gray-700">{slice.percent.toFixed(1)}%</span>
      </p>
    </div>
  );
}

const SEGMENTS = [
  { id: "ceragem", label: "Ceragem Segmentation" },
  { id: "lifestyle", label: "LifeStyle" },
  { id: "prizm", label: "PRIZM Proxy" },
  { id: "pain_index", label: "Pain Index" },
  { id: "purchase_power", label: "Purchase Power" },
  { id: "brand_familiarity", label: "Brand Familiarity (Asian Population Index)" },
] as const;

type SegmentKey = (typeof SEGMENTS)[number]["id"];

export type SegmentFilterState = Record<SegmentKey, string[]>;

export function emptySegmentFilters(): SegmentFilterState {
  return { ceragem: [], prizm: [], lifestyle: [], pain_index: [], purchase_power: [], brand_familiarity: [] };
}

type SegmentDistribution = Partial<Record<SegmentKey, Record<string, number>>>;

export function SelectableSegmentDonuts({
  data,
  selected,
  onChange,
}: {
  data: SegmentDistribution;
  selected: SegmentFilterState;
  onChange: (next: SegmentFilterState) => void;
}) {
  return (
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
      {SEGMENTS.map((segment) => (
        <SelectableDonut
          key={segment.id}
          segmentId={segment.id}
          title={segment.label}
          data={data[segment.id] ?? {}}
          selected={selected[segment.id]}
          onToggle={(label) => {
            const current = selected[segment.id];
            const nextValues = current.includes(label) ? current.filter((v) => v !== label) : [...current, label];
            onChange({ ...selected, [segment.id]: nextValues });
          }}
        />
      ))}
    </div>
  );
}

function SelectableDonut({
  segmentId,
  title,
  data,
  selected,
  onToggle,
}: {
  segmentId: SegmentKey;
  title: string;
  data: Record<string, number>;
  selected: string[];
  onToggle: (label: string) => void;
}) {
  const legendEntries = Object.entries(data);
  const sortedLegendNames = segmentLegendOrder(
    segmentId,
    legendEntries.map(([name]) => name),
  );
  const legendEntriesSorted = sortedLegendNames
    .map((name) => [name, data[name] ?? 0] as const)
    .filter(([, value]) => value >= 0);
  const positiveEntries = legendEntriesSorted.filter(([, value]) => value > 0);
  const total = positiveEntries.reduce((sum, [, value]) => sum + value, 0);

  const colorByName = new Map<string, string>();
  legendEntriesSorted.forEach(([name], index) => {
    colorByName.set(name, PALETTE[index % PALETTE.length]);
  });

  const chartData: Slice[] = positiveEntries.map(([name, value]) => {
    const display = segmentDisplayForDimension(segmentId, name);
    return {
      name,
      value,
      percent: total > 0 ? (value / total) * 100 : 0,
      title: display.title,
      subtitle: display.subtitle,
    };
  });

  const legendRows: Slice[] = legendEntriesSorted.map(([name, value]) => {
    const display = segmentDisplayForDimension(segmentId, name);
    return {
      name,
      value,
      percent: total > 0 ? (value / total) * 100 : 0,
      title: display.title,
      subtitle: display.subtitle,
    };
  });

  if (!legendRows.length) {
    return (
      <div className="cios-card p-4">
        <h3 className="text-sm font-semibold text-gray-900">{title}</h3>
        <p className="mt-3 text-sm text-[var(--cios-secondary)]">No cohort data in current scope.</p>
      </div>
    );
  }

  return (
    <div className="cios-card p-4">
      <h3 className="mb-1 text-sm font-semibold text-gray-900">{title}</h3>
      <p className="mb-3 text-[10px] text-[var(--cios-secondary)]">Click legend items to multi-select 2nd-pass filters</p>
      <ResponsiveContainer width="100%" height={160}>
        <PieChart>
          <Pie
            data={chartData}
            dataKey="value"
            nameKey="name"
            innerRadius={45}
            outerRadius={70}
            paddingAngle={2}
            isAnimationActive={false}
          >
            {chartData.map((slice) => {
              const active = selected.includes(slice.name);
              const baseColor = colorByName.get(slice.name) ?? PALETTE[0];
              return (
                <Cell
                  key={slice.name}
                  fill={active ? SELECTED_SLICE_FILL : baseColor}
                  stroke={active ? "#312E81" : undefined}
                  strokeWidth={active ? 1 : 0}
                />
              );
            })}
          </Pie>
          <Tooltip
            content={<SegmentDonutTooltip />}
            wrapperStyle={{ outline: "none", zIndex: 20 }}
            contentStyle={{ background: "transparent", border: "none", padding: 0, boxShadow: "none" }}
          />
        </PieChart>
      </ResponsiveContainer>
      <ul className="mt-2 flex flex-wrap gap-1.5">
        {legendRows.map((slice) => {
          const active = selected.includes(slice.name);
          const baseColor = colorByName.get(slice.name) ?? PALETTE[0];
          return (
            <li key={slice.name}>
              <button
                type="button"
                onClick={() => onToggle(slice.name)}
                title={
                  slice.subtitle
                    ? `${slice.subtitle}\nCustomers: ${slice.value.toLocaleString()} · Share: ${slice.percent.toFixed(1)}%`
                    : `Customers: ${slice.value.toLocaleString()} · Share: ${slice.percent.toFixed(1)}%`
                }
                className={cn(
                  "rounded-full border px-2 py-0.5 text-[10px] font-medium",
                  active ? "border-indigo-600 bg-indigo-50 text-indigo-800" : "border-gray-200 bg-white text-gray-600 hover:border-indigo-300",
                )}
              >
                <span
                  className="mr-1 inline-block h-2 w-2 rounded-full"
                  style={{ background: active ? SELECTED_SLICE_FILL : baseColor }}
                />
                {slice.title}
              </button>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
