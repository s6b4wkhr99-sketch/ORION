import type { ReactNode } from "react";
import { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

type KpiCardProps = {
  label: string;
  value: string;
  trend?: string;
  trendUp?: boolean;
  icon?: LucideIcon;
  onClick?: () => void;
  className?: string;
  hint?: ReactNode;
};

export function KpiCard({ label, value, trend, trendUp, icon: Icon, onClick, className, hint }: KpiCardProps) {
  const Wrapper = onClick ? "button" : "div";

  return (
    <Wrapper
      type={onClick ? "button" : undefined}
      onClick={onClick}
      className={cn(
        "cios-card flex h-[140px] w-full flex-col justify-between p-4 text-left transition-shadow",
        onClick && "cursor-pointer hover:shadow-md focus:outline-none focus:ring-2 focus:ring-[var(--cios-primary)]",
        className,
      )}
    >
      <div className="flex items-start justify-between gap-2">
        <span className="flex items-center gap-1">
          <p className="text-sm font-medium text-[var(--cios-secondary)]">{label}</p>
          {hint}
        </span>
        {Icon && (
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-[var(--cios-primary-light)] text-[var(--cios-primary)]">
            <Icon className="h-4 w-4" />
          </div>
        )}
      </div>
      <div>
        <p className="text-2xl font-bold text-gray-900">{value}</p>
        {trend && (
          <p
            className={cn(
              "mt-1 text-xs font-medium",
              trendUp === true && "text-[var(--cios-success)]",
              trendUp === false && "text-[var(--cios-error)]",
              trendUp === undefined && "text-[var(--cios-secondary)]",
            )}
          >
            {trend}
          </p>
        )}
      </div>
    </Wrapper>
  );
}
