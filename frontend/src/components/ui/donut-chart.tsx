"use client";

import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import { cn } from "@/lib/utils";

const PALETTE = ["#0056D2", "#5B9BD5", "#7BA7E8", "#16A34A", "#F59E0B", "#DC2626", "#9333EA", "#64748B"];

type Slice = { name: string; value: number; percent: number };

function DonutTooltip({ active, payload }: { active?: boolean; payload?: { payload: Slice }[] }) {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  return (
    <div className="rounded-lg border border-[var(--cios-border)] bg-white px-3 py-2 text-xs shadow-lg">
      <span className="font-medium text-gray-900">{d.name}</span>
      <span className="ml-2 text-[var(--cios-secondary)]">{d.percent.toFixed(1)}%</span>
    </div>
  );
}

export function DonutChart({
  data,
  title,
  legendPosition = "side",
}: {
  data: Record<string, number>;
  title?: string;
  legendPosition?: "side" | "bottom";
}) {
  const entries = Object.entries(data).filter(([, v]) => v > 0);
  const total = entries.reduce((sum, [, v]) => sum + v, 0);
  const chartData: Slice[] = entries.map(([name, value]) => ({
    name,
    value,
    percent: total > 0 ? (value / total) * 100 : 0,
  }));

  if (!chartData.length) {
    return <p className="text-sm text-[var(--cios-secondary)]">No data for {title ?? "chart"}.</p>;
  }

  const bottom = legendPosition === "bottom";

  return (
    <div className={cn("flex flex-col items-center gap-3", !bottom && "sm:flex-row")}>
      <ResponsiveContainer width={160} height={160}>
        <PieChart>
          <Pie data={chartData} dataKey="value" nameKey="name" innerRadius={45} outerRadius={70} paddingAngle={2}>
            {chartData.map((_, i) => (
              <Cell key={i} fill={PALETTE[i % PALETTE.length]} />
            ))}
          </Pie>
          <Tooltip content={<DonutTooltip />} />
        </PieChart>
      </ResponsiveContainer>
      <ul className={cn("flex flex-wrap gap-x-3 gap-y-1 text-xs", bottom && "w-full justify-center")}>
        {chartData.map((d, i) => (
          <li key={d.name} className="flex items-center gap-2">
            <span className="h-2.5 w-2.5 rounded-full" style={{ background: PALETTE[i % PALETTE.length] }} />
            <span className="text-[var(--cios-secondary)]">{d.name}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
