"use client";

import {
  CartesianGrid,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
  ZAxis,
} from "recharts";
import { formatCurrency, formatPercent } from "@/lib/utils";

type SegmentPoint = {
  segment: string;
  revenue: number;
  conversion: number;
};

export function SegmentBubbleChart({ data }: { data: SegmentPoint[] }) {
  const chartData = data.map((d) => ({
    ...d,
    x: d.conversion * 100,
    y: d.revenue / 1000,
    z: Math.max(120, d.revenue / 8000),
  }));

  return (
    <div className="h-[280px]">
      <ResponsiveContainer width="100%" height="100%">
        <ScatterChart margin={{ top: 8, right: 8, bottom: 8, left: 8 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            type="number"
            dataKey="x"
            name="Conversion"
            unit="%"
            tick={{ fontSize: 11 }}
            label={{ value: "Conversion Rate (%)", position: "insideBottom", offset: -4, fontSize: 11 }}
          />
          <YAxis
            type="number"
            dataKey="y"
            name="Revenue"
            unit="k"
            tick={{ fontSize: 11 }}
            label={{ value: "Revenue (USD)", angle: -90, position: "insideLeft", fontSize: 11 }}
          />
          <ZAxis type="number" dataKey="z" range={[80, 400]} />
          <Tooltip
            cursor={{ strokeDasharray: "3 3" }}
            formatter={(value, name) => {
              const v = Number(value);
              if (name === "Revenue") return formatCurrency(v * 1000);
              if (name === "Conversion") return formatPercent(v / 100);
              return v;
            }}
            labelFormatter={(_, payload) => payload?.[0]?.payload?.segment ?? ""}
          />
          <Scatter data={chartData} fill="#0056D2" fillOpacity={0.65} />
        </ScatterChart>
      </ResponsiveContainer>
    </div>
  );
}
