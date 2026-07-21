"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { formatCurrency } from "@/lib/utils";

type StackedBarChartProps = {
  data: { label: string; revenue: number }[];
  onBarClick?: (label: string) => void;
};

export function StackedBarChart({ data, onBarClick }: StackedBarChartProps) {
  const chartData = data.map((d) => ({ name: d.label, revenue: d.revenue }));

  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart data={chartData} margin={{ top: 8, right: 8, left: 0, bottom: 40 }}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="name" tick={{ fontSize: 11 }} angle={-25} textAnchor="end" interval={0} />
        <YAxis tick={{ fontSize: 11 }} />
        <Tooltip formatter={(v) => formatCurrency(Number(v))} />
        <Bar
          dataKey="revenue"
          fill="#0056D2"
          radius={[4, 4, 0, 0]}
          cursor={onBarClick ? "pointer" : undefined}
          onClick={(entry) => onBarClick?.(String(entry?.payload?.name ?? ""))}
        />
      </BarChart>
    </ResponsiveContainer>
  );
}
