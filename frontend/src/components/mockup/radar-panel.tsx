import {
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart,
  ResponsiveContainer,
} from "recharts";

type RadarPanelProps = {
  data: { axis: string; score: number }[];
  title?: string;
};

export function RadarPanel({ data, title = "Intelligence Distribution" }: RadarPanelProps) {
  return (
    <section className="cios-card p-5">
      <h2 className="mb-4 text-base font-semibold text-gray-900">{title}</h2>
      <div className="h-[260px]">
        <ResponsiveContainer width="100%" height="100%">
          <RadarChart data={data} cx="50%" cy="50%" outerRadius="72%">
            <PolarGrid stroke="#E5E7EB" />
            <PolarAngleAxis dataKey="axis" tick={{ fontSize: 11, fill: "#4A4A4A" }} />
            <PolarRadiusAxis angle={30} domain={[0, 100]} tick={false} axisLine={false} />
            <Radar name="Score" dataKey="score" stroke="#0056D2" fill="#0056D2" fillOpacity={0.25} />
          </RadarChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}
