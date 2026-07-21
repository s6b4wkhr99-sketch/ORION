"use client";

import { cn } from "@/lib/utils";

type PageTabsProps = {
  tabs: { id: string; label: string; count?: number }[];
  active: string;
  onChange: (id: string) => void;
  className?: string;
};

export function PageTabs({ tabs, active, onChange, className }: PageTabsProps) {
  return (
    <div className={cn("flex flex-wrap gap-1 border-b border-[var(--cios-border)]", className)}>
      {tabs.map((tab) => (
        <button
          key={tab.id}
          type="button"
          onClick={() => onChange(tab.id)}
          className={cn(
            "cios-btn -mb-px border-b-2 px-4 py-2.5 text-sm font-medium transition-colors",
            active === tab.id
              ? "border-[var(--cios-primary)] text-[var(--cios-primary)]"
              : "border-transparent text-[var(--cios-secondary)] hover:text-gray-900",
          )}
        >
          {tab.label}
          {tab.count != null && (
            <span className="ml-2 rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-600">{tab.count}</span>
          )}
        </button>
      ))}
    </div>
  );
}
