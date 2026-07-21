"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { FlaskConical, Loader2, MapPin, Target, TrendingUp, Users } from "lucide-react";
import { KpiComparisonStrip, TopMetroPanel } from "@/components/decision/opportunity-finder/campaign-phase-panels";
import { PrimeSkuSelector } from "@/components/decision/opportunity-finder/prime-sku-selector";
import {
  emptySegmentFilters,
  SelectableSegmentDonuts,
  type SegmentFilterState,
} from "@/components/decision/opportunity-finder/selectable-segment-donuts";
import { ExecutiveKpiRow } from "@/components/decision/mission-control/executive-kpi-row";
import { WidgetShell } from "@/components/decision/mission-control/widget-shell";
import { UsChoroplethMap } from "@/components/dashboard/us-choropleth-map";
import { PageSkeleton } from "@/components/ui/skeleton";
import { US_STATE_ABBRS } from "@/data/us-state-names";
import { useFilters } from "@/contexts/filter-context";
import { api, type CampaignOpportunitySimulateResult } from "@/lib/api";
import { PRODUCT_OPTIONS } from "@/lib/config";
import { normalizeActivePromotions, type StandingPromotionRow } from "@/lib/standing-promotions";
import { formatCurrency, formatNumber, formatPercent } from "@/lib/utils";
import { useToast } from "@/components/ui/toast";

export default function OpportunitiesPage() {
  const router = useRouter();
  const { toast } = useToast();
  const { selectedUploadId } = useFilters();
  const [mainSku, setMainSku] = useState<string>(PRODUCT_OPTIONS[2] ?? "Master V6");
  const [additionalSkus, setAdditionalSkus] = useState<string[]>([]);
  const [selectedStates, setSelectedStates] = useState<string[]>([]);
  const [segmentFilters, setSegmentFilters] = useState<SegmentFilterState>(emptySegmentFilters());
  const [result, setResult] = useState<CampaignOpportunitySimulateResult | null>(null);
  const [activePromotions, setActivePromotions] = useState<StandingPromotionRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [simulating, setSimulating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [savingRecommendation, setSavingRecommendation] = useState(false);

  const hasSegmentFilters = useMemo(
    () => Object.values(segmentFilters).some((values) => values.length > 0),
    [segmentFilters],
  );

  const runSimulation = useCallback(async () => {
    if (!mainSku) return;
    setSimulating(true);
    setError(null);
    try {
      const payload = await api.simulateCampaignOpportunity({
        mainSku,
        additionalSkus,
        states: selectedStates,
        segmentFilters: hasSegmentFilters ? segmentFilters : undefined,
        uploadId: selectedUploadId ?? undefined,
      });
      setResult(payload);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Simulation failed");
    } finally {
      setSimulating(false);
      setLoading(false);
    }
  }, [mainSku, additionalSkus, selectedStates, segmentFilters, hasSegmentFilters, selectedUploadId]);

  useEffect(() => {
    api
      .getExecutive(selectedUploadId ?? undefined)
      .then((exec) => setActivePromotions(normalizeActivePromotions(exec.commercial_intelligence?.active_promotions ?? [])))
      .catch(console.error);
  }, [selectedUploadId]);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void runSimulation();
    }, 350);
    return () => window.clearTimeout(timer);
  }, [runSimulation]);

  const toggleState = useCallback((state: string) => {
    setSelectedStates((prev) => {
      const upper = state.toUpperCase();
      if (prev.some((s) => s.toUpperCase() === upper)) {
        return prev.filter((s) => s.toUpperCase() !== upper);
      }
      return [...prev, upper];
    });
  }, []);

  const stateMap = useMemo(() => {
    const source = result?.phase1.sku_by_state ?? result?.phase1.by_state ?? [];
    const byState = new Map(source.map((row) => [row.state.toUpperCase(), row]));
    return US_STATE_ABBRS.map((state) => {
      const row = byState.get(state.toUpperCase());
      return {
        state,
        revenue: row?.revenue ?? 0,
        customers: row?.customers ?? 0,
        orders: row?.orders ?? 0,
        conversion: row?.conversion ?? 0,
      };
    });
  }, [result]);

  const activeKpis = result?.phase2.kpis ?? result?.phase1.kpis ?? result?.db_potential;
  const geoScope = selectedStates.length ? selectedStates.join(", ") : "National";

  const handleBuildRecommendation = useCallback(async () => {
    if (!result || !mainSku || !activeKpis) return;
    setSavingRecommendation(true);
    try {
      await api.saveAudienceExport({
        mainSku,
        additionalSkus,
        states: selectedStates,
        segmentFilters: hasSegmentFilters ? segmentFilters : undefined,
        uploadId: selectedUploadId ?? undefined,
        forecastCustomers: activeKpis.customers,
        forecastRevenue: activeKpis.revenue,
        predictedConversion: activeKpis.conversion,
        expectedOrders: activeKpis.orders,
        geoScope,
      });
      toast("success", "Recommendation saved to Audience Export");
      router.push("/export");
    } catch (err) {
      toast("error", err instanceof Error ? err.message : "Failed to save recommendation");
    } finally {
      setSavingRecommendation(false);
    }
  }, [
    result,
    mainSku,
    activeKpis,
    additionalSkus,
    selectedStates,
    hasSegmentFilters,
    segmentFilters,
    selectedUploadId,
    geoScope,
    toast,
    router,
  ]);

  if (loading && !result) return <PageSkeleton />;

  return (
    <div className="space-y-6">
      <header>
        <div className="flex flex-wrap items-center gap-2">
          <FlaskConical className="h-6 w-6 text-indigo-600" />
          <h1 className="text-2xl font-semibold tracking-tight text-gray-900">Opportunity Finder</h1>
          {simulating ? <Loader2 className="h-4 w-4 animate-spin text-indigo-500" aria-label="Simulating" /> : null}
        </div>
        <p className="mt-1 text-sm text-[var(--cios-secondary)]">
          Email campaign KPI simulator — select a Main SKU plus add-ons, evaluate full DB potential, multi-select states,
          analyze Top 5 metros, then refine with segment donuts.
        </p>
      </header>

      {error ? (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">{error}</div>
      ) : null}

      <PrimeSkuSelector
        mainSku={mainSku}
        additionalSkus={additionalSkus}
        onMainChange={setMainSku}
        onAdditionalChange={setAdditionalSkus}
        bySku={result?.by_sku}
        activePromotions={activePromotions}
      />

      {result ? (
        <>
          <KpiComparisonStrip
            label="Campaign Opportunity Forecast"
            dbPotential={result.db_potential}
            phase1={result.phase1.kpis}
            phase2={result.phase2.kpis}
          />

          <ExecutiveKpiRow
            items={[
              {
                label: "Active Forecast Customers",
                value: formatNumber(activeKpis?.customers ?? 0),
                icon: Users,
                accent: "purple",
              },
              {
                label: "Active Forecast Revenue",
                value: formatCurrency(activeKpis?.revenue ?? 0),
                icon: TrendingUp,
                accent: "blue",
              },
              {
                label: "Predicted Conversion",
                value: formatPercent(activeKpis?.conversion ?? 0),
                icon: Target,
                accent: "green",
              },
              {
                label: "Expected Orders",
                value: formatNumber(activeKpis?.orders ?? 0),
                icon: FlaskConical,
                accent: "amber",
              },
              {
                label: "Geo Scope",
                value: geoScope,
                icon: MapPin,
                accent: "purple",
              },
            ]}
          />

          <div className="space-y-6">
            <WidgetShell
              title="Phase 1 · US State Selection"
              subtitle="Multi-select states on the map to scope the email campaign geography"
            >
              <UsChoroplethMap
                data={stateMap}
                multiSelect
                selectedStates={selectedStates}
                onStateClick={toggleState}
                mapHeight={360}
              />
              {selectedStates.length ? (
                <div className="mt-3 flex flex-wrap gap-2">
                  {selectedStates.map((state) => (
                    <button
                      key={state}
                      type="button"
                      onClick={() => toggleState(state)}
                      className="rounded-full border border-fuchsia-300 bg-fuchsia-50 px-2.5 py-1 text-xs font-medium text-fuchsia-900"
                    >
                      {state} ×
                    </button>
                  ))}
                  <button
                    type="button"
                    onClick={() => setSelectedStates([])}
                    className="text-xs font-medium text-[var(--cios-secondary)] hover:text-gray-900"
                  >
                    Clear all
                  </button>
                </div>
              ) : (
                <p className="mt-3 text-xs text-[var(--cios-secondary)]">
                  No states selected — showing national DB potential scaled to SKU bundle.
                </p>
              )}
            </WidgetShell>

            <TopMetroPanel metros={result.phase1.top_metros} selectedStates={selectedStates} />
          </div>

          <section className="orion-widget p-5">
            <div className="mb-4 flex flex-wrap items-start justify-between gap-2">
              <div>
                <h2 className="text-base font-semibold text-gray-900">Phase 2 · Segment Refinement</h2>
                <p className="mt-1 text-xs text-[var(--cios-secondary)]">
                  Multi-select Ceragem Segmentation, LifeStyle, PRIZM, Pain Index, and Brand Familiarity (Asian Population
                  Index) to refine forecast within Phase 1 scope.
                </p>
              </div>
              <span className="rounded-full bg-teal-50 px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wide text-teal-700">
                2nd Pass
              </span>
            </div>

            <SelectableSegmentDonuts
              data={result.phase2.segment_distributions}
              selected={segmentFilters}
              onChange={setSegmentFilters}
            />

            {hasSegmentFilters ? (
              <div className="mt-4 flex flex-wrap items-center justify-between gap-3 rounded-lg bg-teal-50 px-4 py-3 text-sm text-teal-900">
                <p>
                  Segment filters active — refined forecast: {formatNumber(result.phase2.kpis.customers)} customers,{" "}
                  {formatCurrency(result.phase2.kpis.revenue)} revenue.
                </p>
                <button
                  type="button"
                  onClick={() => setSegmentFilters(emptySegmentFilters())}
                  className="text-xs font-medium text-teal-800 underline"
                >
                  Clear segment filters
                </button>
              </div>
            ) : null}
          </section>

          <WidgetShell
            title="Launch Readiness"
            subtitle="Use simulator output to configure the email campaign workflow"
            action={
              <button
                type="button"
                onClick={() => void handleBuildRecommendation()}
                disabled={savingRecommendation}
                className="orion-btn-primary px-3 py-1.5 text-xs font-medium disabled:opacity-60"
              >
                {savingRecommendation ? "Saving..." : "Build Recommendation →"}
              </button>
            }
          >
            <ul className="space-y-3 text-sm">
              <li className="rounded-lg bg-slate-50 px-4 py-3">
                <p className="font-medium text-gray-900">1. Prime SKU bundle locked</p>
                <p className="mt-1 text-[var(--cios-secondary)]">
                  Main {mainSku}
                  {additionalSkus.length ? ` + ${additionalSkus.join(", ")}` : ""} —{" "}
                  {formatNumber(result.db_potential.customers)} customers in full DB potential.
                </p>
              </li>
              <li className="rounded-lg bg-slate-50 px-4 py-3">
                <p className="font-medium text-gray-900">2. Geographic scope set</p>
                <p className="mt-1 text-[var(--cios-secondary)]">
                  {selectedStates.length
                    ? `${selectedStates.length} state(s) selected · Top metro ${result.phase1.top_metros[0]?.cbsa_name ?? "—"}`
                    : "National scope — select states to narrow Phase 1 forecast"}
                  .
                </p>
              </li>
              <li className="rounded-lg bg-indigo-50 px-4 py-3">
                <p className="font-medium text-indigo-950">3. Segment-refined KPI target</p>
                <p className="mt-1 text-indigo-800">
                  Operate toward {formatNumber(result.phase2.kpis.customers)} customers,{" "}
                  {formatCurrency(result.phase2.kpis.revenue)} revenue, {formatPercent(result.phase2.kpis.conversion)}{" "}
                  conversion.
                </p>
              </li>
            </ul>
          </WidgetShell>
        </>
      ) : null}
    </div>
  );
}
