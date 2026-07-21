"use client";

import { useCallback, useEffect, useState } from "react";
import { PageHeader } from "@/components/mockup/page-header";
import { KpiCard } from "@/components/ui/kpi-card";
import { PageSkeleton } from "@/components/ui/skeleton";
import { PRODUCT_OPTIONS } from "@/lib/config";
import { api, type CommercialSimulationResult } from "@/lib/api";
import { formatCurrency, formatNumber, formatPercent } from "@/lib/utils";

export default function CommercialSimulatorPage() {
  const [product, setProduct] = useState("Master V7");
  const [targetCustomers, setTargetCustomers] = useState(10000);
  const [sellingPrice, setSellingPrice] = useState("");
  const [promotionPct, setPromotionPct] = useState("");
  const [maxPromotion, setMaxPromotion] = useState("");
  const [promoCode, setPromoCode] = useState("");
  const [leFrameRate, setLeFrameRate] = useState("0.15");
  const [corporatePriority, setCorporatePriority] = useState(0.5);
  const [inventoryUnits, setInventoryUnits] = useState("");
  const [result, setResult] = useState<CommercialSimulationResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const runSimulation = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.simulateCommercial({
        product,
        targetCustomers,
        sellingPrice: sellingPrice ? Number(sellingPrice) : undefined,
        promotionPct: promotionPct ? Number(promotionPct) : undefined,
        maxPromotion: maxPromotion ? Number(maxPromotion) : undefined,
        promoCode: promoCode || undefined,
        leFrameIncentiveRate: leFrameRate ? Number(leFrameRate) : undefined,
        corporatePriority,
        inventoryUnits: inventoryUnits ? Number(inventoryUnits) : undefined,
      });
      setResult(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Simulation failed");
      setResult(null);
    } finally {
      setLoading(false);
    }
  }, [
    product,
    targetCustomers,
    sellingPrice,
    promotionPct,
    maxPromotion,
    promoCode,
    leFrameRate,
    corporatePriority,
    inventoryUnits,
  ]);

  useEffect(() => {
    runSimulation();
  }, [runSimulation]);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Commercial Simulator"
        subtitle="What-if pricing and promotion scenarios — results are temporary and never modify production data."
      />

      <section className="cios-card grid gap-4 p-5 lg:grid-cols-3">
        <label className="text-sm">
          <span className="mb-1 block font-medium text-gray-700">SKU</span>
          <select className="cios-input w-full bg-white px-3 py-2" value={product} onChange={(e) => setProduct(e.target.value)}>
            {PRODUCT_OPTIONS.map((p) => (
              <option key={p} value={p}>
                {p}
              </option>
            ))}
          </select>
        </label>
        <label className="text-sm">
          <span className="mb-1 block font-medium text-gray-700">Target Customers</span>
          <input
            type="number"
            className="cios-input w-full bg-white px-3 py-2"
            value={targetCustomers}
            onChange={(e) => setTargetCustomers(Number(e.target.value) || 0)}
          />
        </label>
        <label className="text-sm">
          <span className="mb-1 block font-medium text-gray-700">Selling Price (override)</span>
          <input
            className="cios-input w-full bg-white px-3 py-2"
            placeholder="Catalog default"
            value={sellingPrice}
            onChange={(e) => setSellingPrice(e.target.value)}
          />
        </label>
        <label className="text-sm">
          <span className="mb-1 block font-medium text-gray-700">Promotion % (decimal)</span>
          <input
            className="cios-input w-full bg-white px-3 py-2"
            placeholder="e.g. 0.18"
            value={promotionPct}
            onChange={(e) => setPromotionPct(e.target.value)}
          />
        </label>
        <label className="text-sm">
          <span className="mb-1 block font-medium text-gray-700">Max Promotion ($)</span>
          <input
            className="cios-input w-full bg-white px-3 py-2"
            value={maxPromotion}
            onChange={(e) => setMaxPromotion(e.target.value)}
          />
        </label>
        <label className="text-sm">
          <span className="mb-1 block font-medium text-gray-700">Promotion Code</span>
          <input
            className="cios-input w-full bg-white px-3 py-2"
            placeholder="SAVE20"
            value={promoCode}
            onChange={(e) => setPromoCode(e.target.value)}
          />
        </label>
        <label className="text-sm">
          <span className="mb-1 block font-medium text-gray-700">Le Frame Rate</span>
          <input
            className="cios-input w-full bg-white px-3 py-2"
            value={leFrameRate}
            onChange={(e) => setLeFrameRate(e.target.value)}
          />
        </label>
        <label className="text-sm">
          <span className="mb-1 block font-medium text-gray-700">Corporate Priority ({corporatePriority.toFixed(2)})</span>
          <input
            type="range"
            min={0}
            max={1}
            step={0.05}
            className="w-full"
            value={corporatePriority}
            onChange={(e) => setCorporatePriority(Number(e.target.value))}
          />
        </label>
        <label className="text-sm">
          <span className="mb-1 block font-medium text-gray-700">Inventory Units</span>
          <input
            className="cios-input w-full bg-white px-3 py-2"
            placeholder="Unlimited"
            value={inventoryUnits}
            onChange={(e) => setInventoryUnits(e.target.value)}
          />
        </label>
        <div className="flex items-end lg:col-span-3">
          <button
            type="button"
            onClick={runSimulation}
            disabled={loading}
            className="cios-btn bg-[var(--cios-primary)] px-4 py-2 text-white disabled:opacity-50"
          >
            {loading ? "Simulating…" : "Recalculate Scenario"}
          </button>
        </div>
      </section>

      {error && <div className="cios-card p-4 text-sm text-red-600">{error}</div>}

      {loading && !result ? (
        <PageSkeleton />
      ) : result ? (
        <>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <KpiCard label="Opportunity Score" value={String(result.opportunity_score)} />
            <KpiCard label="Conversion Prediction" value={formatPercent(result.conversion_prediction)} />
            <KpiCard label="Revenue Forecast" value={formatCurrency(result.revenue_forecast)} />
            <KpiCard label="Net Profit" value={formatCurrency(result.net_profit)} />
            <KpiCard label="Le Frame Revenue" value={formatCurrency(result.le_frame_revenue)} />
            <KpiCard label="Expected Orders" value={formatNumber(result.expected_orders)} />
            <KpiCard label="Recommended Promo" value={formatCurrency(result.recommended_promotion)} />
            <KpiCard label="Promo Code" value={result.promo_code ?? "None"} />
          </div>

          <section className="cios-card p-5">
            <h2 className="mb-3 text-base font-semibold text-gray-900">Recommendation Preview</h2>
            <dl className="grid gap-2 text-sm sm:grid-cols-2">
              <Row label="Recommended SKU" value={result.recommended_sku} />
              <Row label="Recommended Lifestyle" value={result.recommended_lifestyle ?? "—"} />
              <Row label="Effective Customers" value={formatNumber(result.effective_customers)} />
              <Row
                label="Promotion Capped"
                value={result.capped_promotion ? "Yes — reduced to maximum allowable" : "No"}
              />
            </dl>
          </section>
        </>
      ) : null}
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between gap-4 border-b border-gray-100 py-1">
      <dt className="text-[var(--cios-secondary)]">{label}</dt>
      <dd className="font-medium text-gray-900">{value}</dd>
    </div>
  );
}
