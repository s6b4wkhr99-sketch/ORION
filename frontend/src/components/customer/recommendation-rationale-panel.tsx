"use client";

import type { RecommendationRationale } from "@/lib/api";

type RecommendationRationalePanelProps = {
  rationale: RecommendationRationale | null | undefined;
  product?: string | null;
};

const LEVEL_COLORS: Record<string, string> = {
  High: "bg-emerald-100 text-emerald-800",
  Medium: "bg-amber-100 text-amber-800",
  Low: "bg-gray-100 text-gray-700",
};

export function RecommendationRationalePanel({ rationale, product }: RecommendationRationalePanelProps) {
  if (!rationale) {
    return (
      <p className="text-sm text-[var(--cios-secondary)]">
        제품 추천 근거는 인텔리전스 재계산 후 표시됩니다.
      </p>
    );
  }

  return (
    <div className="space-y-4">
      {rationale.summary ? (
        <p className="rounded-lg bg-blue-50 px-3 py-2 text-sm text-blue-900">{rationale.summary}</p>
      ) : null}
      {rationale.selection_rule ? (
        <div className="text-sm">
          <span className="text-[var(--cios-secondary)]">선정 기준 · </span>
          <span className="font-medium text-gray-900">{rationale.selection_rule}</span>
        </div>
      ) : null}
      {(product || rationale.recommended_product) ? (
        <div className="text-sm">
          <span className="text-[var(--cios-secondary)]">추천 제품 · </span>
          <span className="font-semibold text-[var(--cios-primary)]">
            {product ?? rationale.recommended_product}
          </span>
        </div>
      ) : null}
      <div className="space-y-2">
        <h4 className="text-xs font-semibold uppercase tracking-wide text-[var(--cios-secondary)]">
          추천 요인
        </h4>
        {rationale.factors?.map((factor) => (
          <div
            key={factor.key}
            className="flex items-start justify-between gap-3 rounded-lg border border-gray-100 px-3 py-2"
          >
            <div className="min-w-0">
              <p className="text-sm font-medium text-gray-900">{factor.label}</p>
              {factor.detail ? (
                <p className="mt-0.5 text-xs text-[var(--cios-secondary)]">{factor.detail}</p>
              ) : null}
            </div>
            <div className="shrink-0 text-right">
              <span
                className={`inline-block rounded px-2 py-0.5 text-xs font-medium ${LEVEL_COLORS[factor.level] ?? LEVEL_COLORS.Low}`}
              >
                {factor.level}
              </span>
              <p className="mt-1 text-xs text-gray-500">{factor.score}%</p>
            </div>
          </div>
        ))}
      </div>
      {rationale.adjustments && rationale.adjustments.length > 0 ? (
        <div className="space-y-2">
          <h4 className="text-xs font-semibold uppercase tracking-wide text-[var(--cios-secondary)]">
            후처리 조정
          </h4>
          {rationale.adjustments.map((adj, idx) => (
            <div key={`${adj.type}-${idx}`} className="rounded-lg bg-amber-50 px-3 py-2 text-sm text-amber-900">
              <span className="font-medium">{adj.label}</span>
              {adj.detail ? <span className="block text-xs mt-0.5">{adj.detail}</span> : null}
            </div>
          ))}
        </div>
      ) : null}
    </div>
  );
}
