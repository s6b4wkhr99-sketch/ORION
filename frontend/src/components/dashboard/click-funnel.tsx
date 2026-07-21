"use client";

import { cn } from "@/lib/utils";

type FunnelStage = { stage: string; value: number };

export function ClickFunnel({ stages }: { stages: FunnelStage[] }) {
  const max = Math.max(...stages.map((s) => s.value), 1);

  return (
    <div className="space-y-2">
      {stages.map((stage, i) => {
        const width = Math.max((stage.value / max) * 100, 8);
        return (
          <div key={stage.stage} className="flex items-center gap-3">
            <div className="w-28 shrink-0 text-right text-xs font-medium text-[var(--cios-secondary)]">
              {stage.stage}
            </div>
            <div className="flex flex-1 items-center gap-2">
              <div
                className={cn(
                  "flex h-9 items-center rounded-lg px-3 text-xs font-semibold text-white transition-all",
                  i === 0 && "bg-[#0056D2]",
                  i > 0 && i < stages.length - 1 && "bg-[#5B9BD5]",
                  i === stages.length - 1 && "bg-[var(--cios-success)]",
                )}
                style={{ width: `${width}%`, minWidth: "4rem" }}
              >
                {stage.value.toLocaleString()}
              </div>
              {i < stages.length - 1 && (
                <span className="text-[var(--cios-secondary)]" aria-hidden>
                  ↓
                </span>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
