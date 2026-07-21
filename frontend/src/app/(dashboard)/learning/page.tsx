"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { IntelligencePanel } from "@/components/decision/intelligence-panel";
import { MockupKpiCard } from "@/components/mockup/mockup-kpi-card";
import { PageHeader } from "@/components/mockup/page-header";
import { api, type LearningInsight } from "@/lib/api";
import { formatCurrency, formatNumber, formatPercent } from "@/lib/utils";

export default function LearningCenterPage() {
  const [insights, setInsights] = useState<LearningInsight[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .getLearningInsights()
      .then((res) => setInsights(res.insights ?? []))
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load learning insights"))
      .finally(() => setLoading(false));
  }, []);

  const avgConfidence =
    insights.length > 0
      ? insights.reduce((s, i) => s + (i.confidence_score ?? 0), 0) / insights.length
      : null;
  const totalRevenue = insights.reduce((s, i) => s + (i.revenue ?? 0), 0);

  if (loading) {
    return <p className="text-sm text-[var(--cios-secondary)]">Loading learning center...</p>;
  }

  return (
    <div className="flex gap-6">
      <div className="min-w-0 flex-1 space-y-6">
        <PageHeader
          title="Learning Center"
          subtitle="What became smarter? — Post-campaign insights and recommendation improvements."
        />

        {error && (
          <div className="cios-card p-4 text-sm text-[var(--cios-error)]">{error}</div>
        )}

        <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
          <MockupKpiCard label="Learning Records" value={formatNumber(insights.length)} showSparkline={false} usePlaceholderDelta={false} />
          <MockupKpiCard
            label="Avg. Confidence"
            value={avgConfidence != null ? formatPercent(avgConfidence / 100) : "—"}
            showSparkline={false}
            usePlaceholderDelta={false}
          />
          <MockupKpiCard label="Attributed Revenue" value={formatCurrency(totalRevenue)} showSparkline={false} usePlaceholderDelta={false} />
          <MockupKpiCard label="Campaigns Learned" value={formatNumber(new Set(insights.map((i) => i.campaign_id)).size)} showSparkline={false} usePlaceholderDelta={false} />
        </div>

        <section className="cios-card overflow-hidden">
          <h2 className="border-b border-[var(--cios-border)] px-5 py-4 text-base font-semibold text-gray-900">
            Learning Timeline
          </h2>
          {insights.length > 0 ? (
            <ul className="divide-y divide-gray-100">
              {insights.map((insight) => (
                <li key={insight.id} className="px-5 py-4">
                  <div className="flex flex-wrap items-start justify-between gap-2">
                    <div>
                      <p className="font-medium text-gray-900">{insight.campaign_name}</p>
                      <p className="mt-1 text-sm text-[var(--cios-secondary)]">
                        {[insight.state, insight.segment, insight.product].filter(Boolean).join(" · ") || "—"}
                      </p>
                    </div>
                    {insight.confidence_score != null && (
                      <span className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-medium text-emerald-800">
                        {Math.round(insight.confidence_score)}% confidence
                      </span>
                    )}
                  </div>
                  {insight.insight_summary && (
                    <p className="mt-2 text-sm text-gray-800">{insight.insight_summary}</p>
                  )}
                  {insight.recommendation && (
                    <p className="mt-1 text-sm text-[var(--cios-primary)]">→ {insight.recommendation}</p>
                  )}
                  <div className="mt-2 flex flex-wrap gap-4 text-xs text-[var(--cios-secondary)]">
                    {insight.revenue != null && <span>Revenue: {formatCurrency(insight.revenue)}</span>}
                    {insight.roi != null && <span>ROI: {formatPercent(insight.roi)}</span>}
                    <Link href={`/campaigns/${encodeURIComponent(insight.campaign_id)}`} className="text-[var(--cios-primary)] hover:underline">
                      View campaign
                    </Link>
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <p className="p-5 text-sm text-[var(--cios-secondary)]">
              No learning records yet. Import campaign reports after ESP execution to improve future recommendations.
            </p>
          )}
        </section>
      </div>

      <IntelligencePanel title="Learning Summary">
        <p>
          {insights.length > 0
            ? `${insights.length} insights from completed campaigns.`
            : "Learning activates after campaign result import."}
        </p>
        <Link href="/campaigns" className="cios-btn mt-4 inline-flex text-sm text-[var(--cios-primary)] hover:underline">
          Campaign Intelligence →
        </Link>
      </IntelligencePanel>
    </div>
  );
}
