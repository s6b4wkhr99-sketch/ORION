"use client";

import { AlertTriangle, CheckCircle2 } from "lucide-react";
import { cn } from "@/lib/utils";

export type ReadinessCheck = {
  label: string;
  status: "pass" | "warn" | "fail";
  note?: string;
};

export function CampaignReadinessGauge({ score, checks }: { score: number; checks: ReadinessCheck[] }) {
  const ready = score >= 80;
  const circumference = 2 * Math.PI * 54;
  const offset = circumference - (score / 100) * circumference;

  return (
    <div className="flex h-full min-h-0 flex-col items-center justify-between gap-5">
      <div className="relative h-36 w-36 shrink-0">
        <svg className="h-full w-full -rotate-90" viewBox="0 0 120 120">
          <circle cx="60" cy="60" r="54" fill="none" stroke="#E5E7EB" strokeWidth="10" />
          <circle
            cx="60"
            cy="60"
            r="54"
            fill="none"
            stroke={ready ? "#6366F1" : "#F59E0B"}
            strokeWidth="10"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <p className="text-2xl font-bold text-gray-900">{score}%</p>
          <p className="text-[10px] font-semibold uppercase tracking-wide text-[var(--cios-secondary)]">Ready</p>
        </div>
      </div>

      <ul className="w-full space-y-2.5">
        {checks.map((check) => (
          <li key={check.label} className="flex items-center justify-between gap-2 text-sm">
            <span className="flex items-center gap-2">
              {check.status === "pass" && <CheckCircle2 className="h-4 w-4 text-emerald-500" />}
              {check.status === "warn" && <AlertTriangle className="h-4 w-4 text-amber-500" />}
              {check.status === "fail" && <AlertTriangle className="h-4 w-4 text-red-500" />}
              <span className={cn(check.status === "pass" ? "text-gray-800" : "text-gray-600")}>{check.label}</span>
            </span>
            {check.note && (
              <span className={cn("text-xs font-medium", check.status === "warn" ? "text-amber-600" : "text-gray-500")}>
                {check.note}
              </span>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}
