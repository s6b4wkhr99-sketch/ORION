"use client";

import { useEffect, useState } from "react";
import { X } from "lucide-react";
import type { CustomerRow, CustomerIntelligenceDetail } from "@/lib/api";
import { api } from "@/lib/api";
import { formatCurrency, formatPercent } from "@/lib/utils";
import { indexLevel } from "./customer-filters";
import { RecommendationRationalePanel } from "./recommendation-rationale-panel";

type CustomerDetailDrawerProps = {
  customer: CustomerRow | null;
  onClose: () => void;
};

export function CustomerDetailDrawer({ customer, onClose }: CustomerDetailDrawerProps) {
  const [intel, setIntel] = useState<CustomerIntelligenceDetail | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!customer?.id) {
      setIntel(null);
      return;
    }
    setLoading(true);
    api
      .getCustomerIntelligence(customer.id)
      .then(setIntel)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [customer?.id]);

  if (!customer) return null;

  const rationale = intel?.recommendationRationale ?? intel?.recommendation?.rationale;

  const sections = [
    {
      title: "Customer Information",
      rows: [
        ["Customer ID", customer.id],
        ["Email", customer.email],
        ["Name", customer.name],
        ["State", customer.state],
        ["ZIP", customer.zip],
      ],
    },
    {
      title: "Intelligence",
      rows: [
        ["PRIZM Proxy Segment", customer.prizm_proxy_segment ?? intel?.prizmProxy],
        ["Ceragem Segment", customer.ceragem_segment ?? intel?.ceragemSegment],
        ["Purchase Power (잠정 구매력)", customer.purchase_power_index != null ? indexLevel(customer.purchase_power_index) : intel?.purchasePower],
        ["Pain Index", customer.pain_index != null ? indexLevel(customer.pain_index) : intel?.painIndex],
        ["Lifestyle", customer.lifestyle_index != null ? indexLevel(customer.lifestyle_index) : intel?.lifestyle],
        ["Digital Engagement (온라인 구매력)", customer.email_response_index != null ? indexLevel(customer.email_response_index) : intel?.digitalEngagement],
        ["Brand Familiarity (브랜드 인지도)", customer.brand_familiarity_index != null ? indexLevel(customer.brand_familiarity_index) : intel?.brandFamiliarity],
        ["Sleep Signal (수면 장애)", customer.sleep_segment_label ?? intel?.sleepSegmentLabel ?? customer.sleep_segment ?? intel?.sleepSegment],
      ],
    },
    {
      title: "Recommendation",
      rows: [
        ["Recommended Product", customer.recommended_product],
        ["Message Direction", customer.message_direction],
        ["Campaign Priority", indexLevel(customer.campaign_priority)],
        ["Expected Conversion", formatPercent(customer.expected_conversion_rate, 3)],
        ["Expected Revenue", formatCurrency(customer.expected_revenue)],
      ],
    },
  ];

  return (
    <>
      <button type="button" className="fixed inset-0 z-40 bg-black/30" onClick={onClose} aria-label="Close drawer" />
      <aside className="fixed right-0 top-[var(--header-height)] z-50 flex h-[calc(100vh-var(--header-height))] w-full max-w-[480px] flex-col border-l border-[var(--cios-border)] bg-white shadow-xl">
        <div className="flex items-center justify-between border-b border-[var(--cios-border)] px-5 py-4">
          <h2 className="text-lg font-semibold text-gray-900">Customer Detail</h2>
          <button type="button" onClick={onClose} className="rounded-lg p-2 hover:bg-gray-100">
            <X className="h-5 w-5" />
          </button>
        </div>
        <div className="flex-1 overflow-y-auto p-5">
          {sections.map((section) => (
            <section key={section.title} className="mb-6">
              <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-[var(--cios-secondary)]">
                {section.title}
              </h3>
              <dl className="space-y-2 text-sm">
                {section.rows.map(([label, value]) => (
                  <div key={label} className="flex justify-between gap-4 border-b border-gray-50 pb-2">
                    <dt className="text-[var(--cios-secondary)]">{label}</dt>
                    <dd className="text-right font-medium text-gray-900">{value ?? "—"}</dd>
                  </div>
                ))}
              </dl>
            </section>
          ))}
          <section className="mb-6">
            <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-[var(--cios-secondary)]">
              Product Recommendation Rationale
            </h3>
            {loading ? (
              <p className="text-sm text-[var(--cios-secondary)]">Loading rationale…</p>
            ) : (
              <RecommendationRationalePanel rationale={rationale} product={customer.recommended_product} />
            )}
          </section>
          <section>
            <h3 className="mb-2 text-sm font-semibold uppercase tracking-wide text-[var(--cios-secondary)]">
              Campaign History
            </h3>
            <p className="text-sm text-[var(--cios-secondary)]">No campaign history recorded yet.</p>
          </section>
        </div>
      </aside>
    </>
  );
}
