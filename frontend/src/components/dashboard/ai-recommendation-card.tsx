"use client";

import Link from "next/link";
import { Sparkles } from "lucide-react";
import { formatCurrency } from "@/lib/utils";

type AiRecommendationProps = {
  state: string | null;
  product: string | null;
  revenue: number;
  priority: string;
  messageDirection: string | null;
};

export function AiRecommendationCard({
  state,
  product,
  revenue,
  priority,
  messageDirection,
}: AiRecommendationProps) {
  return (
    <Link
      href="/recommendations"
      className="cios-card block h-full p-5 transition-shadow hover:shadow-md"
    >
      <div className="mb-4 flex items-center gap-2">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-[var(--cios-primary-light)] text-[var(--cios-primary)]">
          <Sparkles className="h-4 w-4" />
        </div>
        <h3 className="text-base font-semibold text-gray-900">AI Recommendation</h3>
      </div>
      <dl className="space-y-3 text-sm">
        <div className="flex justify-between gap-4">
          <dt className="text-[var(--cios-secondary)]">Recommended State</dt>
          <dd className="font-medium text-gray-900">{state ?? "—"}</dd>
        </div>
        <div className="flex justify-between gap-4">
          <dt className="text-[var(--cios-secondary)]">Recommended Product</dt>
          <dd className="font-medium text-gray-900">{product ?? "—"}</dd>
        </div>
        <div className="flex justify-between gap-4">
          <dt className="text-[var(--cios-secondary)]">Expected Revenue</dt>
          <dd className="font-medium text-[var(--cios-primary)]">{formatCurrency(revenue)}</dd>
        </div>
        <div className="flex justify-between gap-4">
          <dt className="text-[var(--cios-secondary)]">Campaign Priority</dt>
          <dd className="font-medium text-gray-900">{priority}</dd>
        </div>
        <div>
          <dt className="mb-1 text-[var(--cios-secondary)]">Message Direction</dt>
          <dd className="text-gray-900">{messageDirection ?? "—"}</dd>
        </div>
      </dl>
      <p className="mt-4 text-xs text-[var(--cios-primary)]">Open Campaign Builder →</p>
    </Link>
  );
}
