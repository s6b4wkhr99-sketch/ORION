"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { cn } from "@/lib/utils";

type StateDatum = { state: string; revenue: number; count?: number };

export function UsHeatMap({ data }: { data: StateDatum[] }) {
  const router = useRouter();
  const max = Math.max(...data.map((d) => d.revenue), 1);

  if (!data.length) {
    return <p className="text-sm text-[var(--cios-secondary)]">No state data available.</p>;
  }

  return (
    <div className="grid grid-cols-4 gap-2 sm:grid-cols-6 md:grid-cols-8 lg:grid-cols-10">
      {data.map((item) => {
        const intensity = item.revenue / max;
        return (
          <Link
            key={item.state}
            href={`/market-intelligence?state=${item.state}`}
            title={`${item.state}: $${item.revenue.toLocaleString()} expected revenue`}
            className={cn(
              "group relative flex aspect-square flex-col items-center justify-center rounded-lg border border-[var(--cios-border)] text-xs font-semibold transition-transform hover:scale-105",
              intensity > 0.66 && "bg-[#0056D2] text-white",
              intensity > 0.33 && intensity <= 0.66 && "bg-[#5B9BD5] text-white",
              intensity <= 0.33 && "bg-[#E8F0FE] text-[var(--cios-primary)]",
            )}
          >
            {item.state}
            <span className="mt-0.5 text-[10px] font-normal opacity-80 group-hover:opacity-100">
              ${Math.round(item.revenue / 1000)}k
            </span>
          </Link>
        );
      })}
    </div>
  );
}
