"use client";

import { useRouter } from "next/navigation";
import { formatCurrency, formatNumber, formatPercent } from "@/lib/utils";

export type FunnelStage = {
  label: string;
  count: number;
  pct?: number;
};

export function RevenueFunnelWidget({ stages, expectedRevenue }: { stages: FunnelStage[]; expectedRevenue: number }) {
  const router = useRouter();
  const max = Math.max(...stages.map((s) => s.count), 1);

  return (
    <div className="flex h-full min-h-0 flex-col">
      <div className="flex-1 space-y-3">
        {stages.map((stage, i) => {
          const width = Math.max((stage.count / max) * 100, 12);
          const isLast = i === stages.length - 1;
          return (
            <button
              key={stage.label}
              type="button"
              onClick={() => router.push("/campaigns")}
              className="group w-full text-left"
            >
              <div className="mb-1 flex items-center justify-between text-xs">
                <span className="font-medium text-gray-700">{stage.label}</span>
                <span className="text-[var(--cios-secondary)]">
                  {formatNumber(stage.count)}
                  {stage.pct != null && stage.pct < 1 && ` · ${formatPercent(stage.pct)}`}
                </span>
              </div>
              <div
                className="h-9 rounded-lg transition-opacity group-hover:opacity-90"
                style={{
                  width: `${width}%`,
                  background: isLast
                    ? "linear-gradient(90deg, #6366F1, #818CF8)"
                    : `rgba(99, 102, 241, ${0.35 + (i / stages.length) * 0.45})`,
                }}
              />
            </button>
          );
        })}
      </div>
      <div className="mt-auto space-y-3 pt-4">
        <div className="rounded-xl bg-indigo-50 px-4 py-3">
          <p className="text-xs text-indigo-700">Total Address Revenue</p>
          <p className="text-xl font-bold text-indigo-900">{formatCurrency(expectedRevenue)}</p>
        </div>
      </div>
    </div>
  );
}
