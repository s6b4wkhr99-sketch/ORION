"use client";

export type IntelligenceScoreBand = {
  label: string;
  high: number;
  medium: number;
  low: number;
};

const BANDS = [
  { key: "high" as const, color: "#22C55E", legend: "High (80-100)" },
  { key: "medium" as const, color: "#3B82F6", legend: "Medium (50-79)" },
  { key: "low" as const, color: "#A78BFA", legend: "Low (0-49)" },
];

function DistributionBar({ row }: { row: IntelligenceScoreBand }) {
  const segments = BANDS.map((band) => ({
    ...band,
    value: row[band.key],
  })).filter((segment) => segment.value > 0);

  return (
    <div className="flex items-center gap-3">
      <p className="w-28 shrink-0 text-xs font-medium text-gray-700">{row.label}</p>
      <div className="flex h-8 min-w-0 flex-1 overflow-hidden rounded-full bg-gray-100">
        {segments.map((segment) => (
          <div
            key={segment.key}
            className="flex items-center justify-center text-xs font-semibold text-white"
            style={{ width: `${segment.value}%`, backgroundColor: segment.color }}
            title={`${segment.legend}: ${segment.value}%`}
          >
            {segment.value >= 10 ? `${segment.value}%` : null}
          </div>
        ))}
      </div>
    </div>
  );
}

export function IntelligenceScoreDistribution({ rows }: { rows: IntelligenceScoreBand[] }) {
  if (!rows.length) {
    return <p className="text-sm text-[var(--cios-secondary)]">No intelligence score distribution in scope.</p>;
  }

  return (
    <div className="flex h-full min-h-0 flex-col justify-between gap-5">
      <div className="space-y-6">
        {rows.map((row) => (
          <DistributionBar key={row.label} row={row} />
        ))}
      </div>
      <ul className="mt-auto flex w-full shrink-0 flex-wrap items-center justify-start gap-2 border-t border-[var(--cios-border)] pt-4">
        {BANDS.map((band) => (
          <li key={band.key} className="flex items-center gap-1.5 text-xs">
            <span className="h-2.5 w-2.5 shrink-0 rounded-full" style={{ backgroundColor: band.color }} />
            <span className="text-[var(--cios-secondary)]">{band.legend}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
