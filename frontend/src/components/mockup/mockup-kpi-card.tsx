import type { ReactNode } from "react";
import { Sparkline } from "@/components/mockup/sparkline";
import { DELTA_PLACEHOLDERS } from "@/lib/mockup-placeholders";
import { cn } from "@/lib/utils";

type MockupKpiCardProps = {
  label: string;
  value: string;
  delta?: string;
  trendUp?: boolean;
  showSparkline?: boolean;
  usePlaceholderDelta?: boolean;
  className?: string;
  hint?: ReactNode;
};

export function MockupKpiCard({
  label,
  value,
  delta,
  trendUp = true,
  showSparkline = true,
  usePlaceholderDelta = true,
  className,
  hint,
}: MockupKpiCardProps) {
  const deltaText = delta ?? (usePlaceholderDelta ? DELTA_PLACEHOLDERS[label] : undefined);

    return (
    <div className={cn("cios-card flex min-h-[120px] flex-col justify-between border-t-[3px] border-t-[var(--cios-primary)] p-4 shadow-sm", className)}>
      <div className="flex items-start justify-between gap-2">
        <span className="flex items-center gap-1">
          <p className="text-xs font-medium uppercase tracking-wide text-[var(--cios-secondary)]">{label}</p>
          {hint}
        </span>
        {showSparkline && <Sparkline />}
      </div>
      <div>
        <p className="text-2xl font-bold text-gray-900">{value}</p>
        {deltaText && (
          <p className={cn("mt-1 text-xs font-medium", trendUp ? "text-[var(--cios-success)]" : "text-[var(--cios-error)]")}>
            {deltaText}
          </p>
        )}
      </div>
    </div>
  );
}
