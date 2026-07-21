"use client";

import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { formatPercent } from "@/lib/utils";

type AreaChartProps = {
  data: { label: string; value: number }[];
};

export function RoiAreaChart({ data }: AreaChartProps) {
  const chartData = data.map((d) => ({ name: d.label, roi: d.value }));

  return (
    <ResponsiveContainer width="100%" height={280}>
      <AreaChart data={chartData} margin={{ top: 8, right: 8, left: 0, bottom: 40 }}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="name" tick={{ fontSize: 10 }} angle={-20} textAnchor="end" interval={0} />
        <YAxis tick={{ fontSize: 11 }} tickFormatter={(v) => `${(Number(v) * 100).toFixed(0)}%`} />
        <Tooltip formatter={(v) => formatPercent(Number(v))} />
        <Area type="monotone" dataKey="roi" stroke="#0056D2" fill="#E8F0FE" strokeWidth={2} />
      </AreaChart>
    </ResponsiveContainer>
  );
}
