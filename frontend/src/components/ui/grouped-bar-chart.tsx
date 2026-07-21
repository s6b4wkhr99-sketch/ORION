"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

type GroupedBarChartProps = {
  data: { metric: string; expected: number; actual: number }[];
  valueFormatter?: (v: number, metric: string) => string;
};

export function GroupedBarChart({ data, valueFormatter }: GroupedBarChartProps) {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 8 }}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="metric" tick={{ fontSize: 11 }} />
        <YAxis tick={{ fontSize: 11 }} />
        <Tooltip
          formatter={(v, name, props) => {
            const metric = String(props.payload?.metric ?? "");
            return valueFormatter?.(Number(v), metric) ?? v;
          }}
        />
        <Legend />
        <Bar dataKey="expected" name="Forecast" fill="#5B9BD5" radius={[4, 4, 0, 0]} />
        <Bar dataKey="actual" name="Actual" fill="#0056D2" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
