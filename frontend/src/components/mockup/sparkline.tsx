import { cn } from "@/lib/utils";

type SparklineProps = {
  points?: number[];
  color?: string;
  className?: string;
};

export function Sparkline({ points, color = "#0056D2", className }: SparklineProps) {
  const data = points ?? [12, 18, 14, 22, 19, 28, 24, 32, 29, 36, 34, 40];
  const max = Math.max(...data, 1);
  const min = Math.min(...data);
  const range = max - min || 1;
  const w = 80;
  const h = 28;
  const step = w / (data.length - 1);
  const d = data
    .map((v, i) => {
      const x = i * step;
      const y = h - ((v - min) / range) * (h - 4) - 2;
      return `${i === 0 ? "M" : "L"}${x},${y}`;
    })
    .join(" ");

  return (
    <svg viewBox={`0 0 ${w} ${h}`} className={cn("h-7 w-20", className)} aria-hidden>
      <path d={d} fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}
