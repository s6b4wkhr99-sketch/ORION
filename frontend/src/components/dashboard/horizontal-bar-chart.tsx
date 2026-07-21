"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

type HorizontalBarChartProps = {
  data: { label: string; value: number; color?: string }[];
  valueFormatter?: (v: number) => string;
};

const COLORS = ["#0056D2", "#5B9BD5", "#7BA7E8", "#9DBCF0", "#BED2F8", "#DFE9FC"];

export function HorizontalBarChart({ data, valueFormatter }: HorizontalBarChartProps) {
  const chartData = data.map((d) => ({ name: d.label, value: d.value }));

  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart data={chartData} layout="vertical" margin={{ top: 8, right: 24, left: 80, bottom: 8 }}>
        <CartesianGrid strokeDasharray="3 3" horizontal={false} />
        <XAxis type="number" tick={{ fontSize: 11 }} />
        <YAxis type="category" dataKey="name" tick={{ fontSize: 11 }} width={72} />
        <Tooltip formatter={(v) => valueFormatter?.(Number(v)) ?? v} />
        <Bar dataKey="value" radius={[0, 4, 4, 0]}>
          {chartData.map((_, i) => (
            <Cell key={i} fill={data[i]?.color ?? COLORS[i % COLORS.length]} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
