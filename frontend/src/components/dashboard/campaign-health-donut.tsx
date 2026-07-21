"use client";

import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";

const COLORS = {
  Healthy: "#16A34A",
  Warning: "#F59E0B",
  Critical: "#DC2626",
};

export function CampaignHealthDonut({
  healthy,
  warning,
  critical,
}: {
  healthy: number;
  warning: number;
  critical: number;
}) {
  const data = [
    { name: "Healthy", value: healthy },
    { name: "Warning", value: warning },
    { name: "Critical", value: critical },
  ].filter((d) => d.value > 0);

  if (!data.length) {
    return <p className="text-sm text-[var(--cios-secondary)]">Upload customers to view campaign health.</p>;
  }

  return (
    <div className="flex flex-col items-center gap-4 sm:flex-row">
      <ResponsiveContainer width={180} height={180}>
        <PieChart>
          <Pie data={data} dataKey="value" nameKey="name" innerRadius={50} outerRadius={75} paddingAngle={2}>
            {data.map((entry) => (
              <Cell key={entry.name} fill={COLORS[entry.name as keyof typeof COLORS]} />
            ))}
          </Pie>
          <Tooltip formatter={(v) => [v, "Customers"]} />
        </PieChart>
      </ResponsiveContainer>
      <ul className="space-y-2 text-sm">
        {data.map((d) => (
          <li key={d.name} className="flex items-center gap-2">
            <span
              className="h-3 w-3 rounded-full"
              style={{ background: COLORS[d.name as keyof typeof COLORS] }}
            />
            <span className="text-[var(--cios-secondary)]">{d.name}</span>
            <span className="font-semibold text-gray-900">{d.value}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
