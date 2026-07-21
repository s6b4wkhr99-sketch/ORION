"use client";

import { Info } from "lucide-react";
import { EXPECTED_REVENUE_INFO, type MetricInfo } from "@/lib/metric-definitions";
import { cn } from "@/lib/utils";

type InfoTooltipProps = {
  title?: string;
  lines: string[];
  className?: string;
  iconClassName?: string;
  align?: "center" | "left" | "right";
};

const ALIGN_CLASS: Record<NonNullable<InfoTooltipProps["align"]>, string> = {
  center: "left-1/2 -translate-x-1/2",
  left: "left-0",
  right: "right-0",
};

export function InfoTooltip({ title, lines, className, iconClassName, align = "center" }: InfoTooltipProps) {
  return (
    <span className={cn("group relative inline-flex align-middle", className)}>
      <Info className={cn("h-3.5 w-3.5 cursor-help text-[var(--cios-secondary)]", iconClassName)} aria-hidden />
      <span
        role="tooltip"
        className={cn(
          "pointer-events-none absolute top-full z-30 mt-1.5 hidden w-64 rounded-md border border-[var(--cios-border)] bg-white p-2.5 text-left text-[11px] font-normal normal-case leading-relaxed tracking-normal text-gray-700 shadow-lg group-hover:block",
          ALIGN_CLASS[align],
        )}
      >
        {title && <span className="mb-1 block font-semibold text-gray-900">{title}</span>}
        {lines.map((line, i) => (
          <span key={i} className="block text-[var(--cios-secondary)]">
            {line}
          </span>
        ))}
      </span>
    </span>
  );
}

export function ExpectedRevenueInfo(props: Omit<InfoTooltipProps, "title" | "lines"> & { def?: MetricInfo }) {
  const def = props.def ?? EXPECTED_REVENUE_INFO;
  return <InfoTooltip {...props} title={def.title} lines={def.lines} />;
}
