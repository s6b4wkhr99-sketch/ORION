"use client";

import { ReactNode } from "react";

type IntelligencePanelProps = {
  title: string;
  children: ReactNode;
};

export function IntelligencePanel({ title, children }: IntelligencePanelProps) {
  return (
    <aside className="hidden w-80 shrink-0 xl:block">
      <div className="sticky top-[calc(var(--header-height)+1.5rem)] cios-card p-5">
        <p className="text-xs font-semibold uppercase tracking-wider text-[var(--cios-secondary)]">{title}</p>
        <div className="mt-4 text-sm text-gray-800">{children}</div>
      </div>
    </aside>
  );
}
