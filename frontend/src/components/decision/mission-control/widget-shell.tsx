"use client";

import { ReactNode } from "react";
import { cn } from "@/lib/utils";

type WidgetShellProps = {
  title: string;
  subtitle?: string;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
  bodyClassName?: string;
  /** Stretch card to match sibling height in a grid row */
  fill?: boolean;
};

export function WidgetShell({ title, subtitle, action, children, className, bodyClassName, fill }: WidgetShellProps) {
  return (
    <section className={cn("orion-widget", fill && "flex h-full min-h-0 flex-col", className)}>
      <div className="flex shrink-0 items-start justify-between gap-3 border-b border-[var(--cios-border)] px-5 py-4">
        <div>
          <h2 className="text-base font-semibold text-gray-900">{title}</h2>
          {subtitle && <p className="mt-0.5 text-xs text-[var(--cios-secondary)]">{subtitle}</p>}
        </div>
        {action}
      </div>
      <div className={cn("p-5", fill && "flex min-h-0 flex-1 flex-col", bodyClassName)}>{children}</div>
    </section>
  );
}
