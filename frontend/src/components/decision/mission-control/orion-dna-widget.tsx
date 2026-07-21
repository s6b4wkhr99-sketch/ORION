"use client";

import {
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart,
  ResponsiveContainer,
} from "recharts";

/** ORION DNA dimensions — must match backend intelligence_radar axes */
export const ORION_DNA_AXES = [
  "Purchase Power",
  "Pain Index",
  "Lifestyle",
  "PRIZM Proxy",
  "Ceragem Segment",
  "Recommendation",
] as const;

const AXIS_LABELS: Record<(typeof ORION_DNA_AXES)[number], string> = {
  "Purchase Power": "Purchase\nPower",
  "Pain Index": "Pain\nIndex",
  Lifestyle: "Lifestyle",
  "PRIZM Proxy": "PRIZM\nProxy",
  "Ceragem Segment": "Ceragem\nSegment",
  Recommendation: "Recommendation",
};

export function buildOrionDnaRadarFromCustomers(
  customers: Array<{
    purchase_power_index?: number | null;
    pain_index?: number | null;
    lifestyle_index?: number | null;
    prizm_proxy_segment?: string | null;
    ceragem_segment?: string | null;
    campaign_priority?: number | null;
  }>,
): { axis: string; score: number }[] {
  if (!customers.length) return [];

  const pct = (value: number) => Math.round(Math.min(100, Math.max(0, value * 100)));
  const avg = (pick: (c: (typeof customers)[number]) => number | null | undefined) => {
    const vals = customers.map(pick).filter((v): v is number => typeof v === "number");
    return vals.length ? vals.reduce((sum, v) => sum + v, 0) / vals.length : 0;
  };
  const avgPct = (values: number[]) => Math.round((values.reduce((sum, v) => sum + v, 0) / values.length) * 100);

  const tierScores: Record<string, number> = { High: 0.9, "Mid-High": 0.7, "Mid-Low": 0.45, Low: 0.25 };
  const prizmScores = customers.map((c) => (c.prizm_proxy_segment && c.prizm_proxy_segment !== "Unknown" ? 0.85 : 0.2));
  const ceragemScores = customers.map((c) => {
    const tier = c.ceragem_segment?.split("+")[0]?.trim() ?? "Low";
    return tierScores[tier] ?? 0.3;
  });
  const recommendationScores = customers.map((c) => c.campaign_priority ?? 0);

  return [
    { axis: "Purchase Power", score: pct(avg((c) => c.purchase_power_index)) },
    { axis: "Pain Index", score: pct(avg((c) => c.pain_index)) },
    { axis: "Lifestyle", score: pct(avg((c) => c.lifestyle_index)) },
    { axis: "PRIZM Proxy", score: avgPct(prizmScores) },
    { axis: "Ceragem Segment", score: avgPct(ceragemScores) },
    { axis: "Recommendation", score: avgPct(recommendationScores) },
  ];
}

export function OrionDnaWidget({ intelligenceRadar }: { intelligenceRadar: { axis: string; score: number }[] }) {
  const byAxis = new Map(intelligenceRadar.map((r) => [r.axis, r.score]));

  const data = ORION_DNA_AXES.map((axis) => ({
    axis: AXIS_LABELS[axis],
    score: Math.round(byAxis.get(axis) ?? 0),
  }));

  if (!intelligenceRadar.length) {
    return <p className="text-sm text-[var(--cios-secondary)]">No ORION DNA data in current scope.</p>;
  }

  return (
    <div className="h-full min-h-[240px] flex-1">
      <ResponsiveContainer width="100%" height="100%">
        <RadarChart data={data} cx="50%" cy="50%" outerRadius="68%">
          <PolarGrid stroke="#E5E7EB" />
          <PolarAngleAxis dataKey="axis" tick={{ fontSize: 10, fill: "#4B5563" }} />
          <PolarRadiusAxis angle={30} domain={[0, 100]} tick={false} axisLine={false} />
          <Radar name="ORION DNA" dataKey="score" stroke="#6366F1" fill="#6366F1" fillOpacity={0.2} strokeWidth={2} />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
}
