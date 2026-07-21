"use client";

import type { ReactNode } from "react";
import type { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

export type ExecutiveKpi = {
  label: string;
  value: string;
  subtext?: string;
  delta?: string;
  trendUp?: boolean;
  icon: LucideIcon;
  accent?: "purple" | "blue" | "green" | "amber";
  hint?: ReactNode;
};

const ACCENT_BG: Record<NonNullable<ExecutiveKpi["accent"]>, string> = {
  purple: "bg-indigo-50 text-indigo-600",
  blue: "bg-blue-50 text-blue-600",
  green: "bg-emerald-50 text-emerald-600",
  amber: "bg-amber-50 text-amber-600",
};

export function ExecutiveKpiRow({ items }: { items: ExecutiveKpi[] }) {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-5">
      {items.map((item) => {
        const Icon = item.icon;
        const accent = item.accent ?? "purple";
        return (
          <div key={item.label} className="orion-kpi-card">
            <div className="flex items-start justify-between gap-2">
              <div className={cn("flex h-10 w-10 items-center justify-center rounded-xl", ACCENT_BG[accent])}>
                <Icon className="h-5 w-5" />
              </div>
            </div>
            <div className="mt-4">
              <span className="flex items-center gap-1">
                <p className="text-xs font-medium uppercase tracking-wide text-[var(--cios-secondary)]">{item.label}</p>
                {item.hint}
              </span>
              <p className="mt-1 text-2xl font-bold text-gray-900">{item.value}</p>
              {item.subtext && <p className="mt-1 text-sm font-medium text-gray-700">{item.subtext}</p>}
              {item.delta && (
                <p className={cn("mt-1 text-xs font-medium", item.trendUp !== false ? "text-emerald-600" : "text-red-600")}>
                  {item.delta}
                </p>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
