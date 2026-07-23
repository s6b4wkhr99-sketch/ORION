"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Loader2, Trash2 } from "lucide-react";
import { UploadDropZone } from "@/components/upload/upload-drop-zone";
import { PageHeader } from "@/components/mockup/page-header";
import { KpiCard } from "@/components/ui/kpi-card";
import { PageSkeleton } from "@/components/ui/skeleton";
import { useToast } from "@/components/ui/toast";
import { PrimeSkuSelector } from "@/components/decision/opportunity-finder/prime-sku-selector";
import { useFilters } from "@/contexts/filter-context";
import {
  api,
  type AudienceExportAnalysisResult,
  type CommercialSimulationResult,
  type CommercialSimulatorForecastInputs,
  type CommercialSimulatorForecastSummary,
} from "@/lib/api";
import {
  additionalPromoDollarsFromPct,
  additionalPromoPctFromDollars,
  formatAdditionalPromoDollars,
  formatAdditionalPromoPct,
} from "@/lib/commercial-promo-sync";
import {
  catalogPriceForSku,
  computeAverageSellingPrice,
  buildSkuTargetMix,
  skuTargetMixUsesPromoCodes,
  describeStandingPromo,
  formatSkuPromoCodes,
  parseAdditionalPromoInputs,
  resolveLayeredPromotionForSku,
  resolveSingleSkuPromoCode,
} from "@/lib/commercial-simulator-fields";
import {
  activePromotionMap,
  normalizeActivePromotions,
  type StandingPromotionRow,
} from "@/lib/standing-promotions";
import { formatCurrency, formatConversionRate, formatNumber, formatPercent, parseConversionRateInput } from "@/lib/utils";

export default function CommercialSimulatorPage() {
  const { toast } = useToast();
  const { selectedUploadId } = useFilters();
  const [mainSku, setMainSku] = useState("Master V7");
  const [additionalSkus, setAdditionalSkus] = useState<string[]>([]);
  const [targetCustomers, setTargetCustomers] = useState(10000);
  const [targetCustomersFromUpload, setTargetCustomersFromUpload] = useState(false);
  const [additionalPromotionPct, setAdditionalPromotionPct] = useState("");
  const [additionalPromotionMax, setAdditionalPromotionMax] = useState("");
  const [leFrameRate, setLeFrameRate] = useState("0.15");
  const [conversionRate, setConversionRate] = useState("");
  const [corporatePriority, setCorporatePriority] = useState(0.5);
  const [inventoryUnits, setInventoryUnits] = useState("");
  const [result, setResult] = useState<CommercialSimulationResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [activePromotions, setActivePromotions] = useState<StandingPromotionRow[]>([]);
  const [catalogPrices, setCatalogPrices] = useState<Map<string, number>>(new Map());

  const [audienceAnalysis, setAudienceAnalysis] = useState<AudienceExportAnalysisResult | null>(null);
  const [audienceLoading, setAudienceLoading] = useState(false);
  const [audienceError, setAudienceError] = useState<string | null>(null);
  const [audienceFileName, setAudienceFileName] = useState<string | null>(null);
  const [audienceFile, setAudienceFile] = useState<File | null>(null);
  const lastSyncedAudienceFile = useRef<string | null>(null);
  const additionalPctRef = useRef(additionalPromotionPct);
  const additionalMaxRef = useRef(additionalPromotionMax);
  additionalPctRef.current = additionalPromotionPct;
  additionalMaxRef.current = additionalPromotionMax;

  const [savedForecasts, setSavedForecasts] = useState<CommercialSimulatorForecastSummary[]>([]);
  const [forecastName, setForecastName] = useState("");
  const [savingForecast, setSavingForecast] = useState(false);
  const [loadingForecasts, setLoadingForecasts] = useState(false);
  const [loadedForecastId, setLoadedForecastId] = useState<string | null>(null);

  const standingPromoBySku = useMemo(() => activePromotionMap(activePromotions), [activePromotions]);
  const selectedSkus = useMemo(() => [mainSku, ...additionalSkus], [mainSku, additionalSkus]);

  const mainSkuSellingPrice = useMemo(
    () => catalogPriceForSku(mainSku, standingPromoBySku, catalogPrices),
    [mainSku, standingPromoBySku, catalogPrices],
  );

  const averageSellingPrice = useMemo(
    () =>
      computeAverageSellingPrice({
        mainSku,
        additionalSkus,
        standingPromoBySku,
        catalogPrices,
        audienceSkuMix: audienceAnalysis?.audience.sku_mix,
        audiencePromoCodeMix: audienceAnalysis?.audience.promo_code_mix,
        audienceAvgSellingPrice: audienceAnalysis?.audience.avg_selling_price,
      }),
    [mainSku, additionalSkus, standingPromoBySku, catalogPrices, audienceAnalysis],
  );

  const skuTargetMix = useMemo(
    () =>
      buildSkuTargetMix(selectedSkus, audienceAnalysis?.audience.sku_mix, {
        audiencePromoCodeMix: audienceAnalysis?.audience.promo_code_mix,
        standingPromoBySku,
      }),
    [selectedSkus, audienceAnalysis, standingPromoBySku],
  );

  const skuTargetsFromPromoCodes = useMemo(
    () =>
      skuTargetMixUsesPromoCodes(
        selectedSkus,
        audienceAnalysis?.audience.sku_mix,
        audienceAnalysis?.audience.promo_code_mix,
      ),
    [selectedSkus, audienceAnalysis],
  );

  const promoCodeDisplay = useMemo(
    () =>
      formatSkuPromoCodes({
        mainSku,
        additionalSkus,
        standingPromoBySku,
        audienceProduct: audienceAnalysis?.audience.product,
        audiencePromoCode: audienceAnalysis?.audience.promo_code,
      }),
    [mainSku, additionalSkus, standingPromoBySku, audienceAnalysis],
  );

  const promoSyncPrice = selectedSkus.length > 1 ? averageSellingPrice : mainSkuSellingPrice;

  const additionalPromoPayload = useMemo(
    () => parseAdditionalPromoInputs(additionalPromotionPct, additionalPromotionMax),
    [additionalPromotionPct, additionalPromotionMax],
  );

  const layeredPromoPreview = useMemo(() => {
    const hasPct = additionalPromotionPct.trim() !== "";
    const hasMax = additionalPromotionMax.trim() !== "";
    if (!hasPct && !hasMax) return [];
    const addPct = hasPct ? Number(additionalPromotionPct) : 0;
    const addMax = hasMax ? Number(additionalPromotionMax) : 0;
    return selectedSkus.map((sku) => ({
      sku,
      ...resolveLayeredPromotionForSku(sku, standingPromoBySku, addPct, addMax),
    }));
  }, [selectedSkus, standingPromoBySku, additionalPromotionPct, additionalPromotionMax]);

  useEffect(() => {
    api
      .getExecutive(selectedUploadId ?? undefined)
      .then((exec) =>
        setActivePromotions(normalizeActivePromotions(exec.commercial_intelligence?.active_promotions ?? [])),
      )
      .catch(console.error);
  }, [selectedUploadId]);

  useEffect(() => {
    api
      .getCommercialCatalog()
      .then((catalog) => {
        const prices = new Map<string, number>();
        for (const product of catalog.products) {
          prices.set(product.code, product.selling_price ?? product.msrp ?? 0);
        }
        setCatalogPrices(prices);
      })
      .catch(console.error);
  }, []);

  const refreshSavedForecasts = useCallback(async () => {
    setLoadingForecasts(true);
    try {
      const payload = await api.listCommercialSimulatorForecasts();
      setSavedForecasts(payload.items ?? []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoadingForecasts(false);
    }
  }, []);

  useEffect(() => {
    void refreshSavedForecasts();
  }, [refreshSavedForecasts]);

  const buildForecastInputs = useCallback((): CommercialSimulatorForecastInputs => ({
    mainSku,
    additionalSkus,
    targetCustomers,
    additionalPromotionPct,
    additionalPromotionMax,
    leFrameRate,
    conversionRate,
    corporatePriority,
    inventoryUnits,
    audienceFileName,
  }), [
    mainSku,
    additionalSkus,
    targetCustomers,
    additionalPromotionPct,
    additionalPromotionMax,
    leFrameRate,
    conversionRate,
    corporatePriority,
    inventoryUnits,
    audienceFileName,
  ]);

  const applyForecastInputs = useCallback((inputs: CommercialSimulatorForecastInputs) => {
    setMainSku(inputs.mainSku);
    setAdditionalSkus(inputs.additionalSkus ?? []);
    setTargetCustomers(inputs.targetCustomers);
    setAdditionalPromotionPct(inputs.additionalPromotionPct ?? "");
    setAdditionalPromotionMax(inputs.additionalPromotionMax ?? "");
    setLeFrameRate(inputs.leFrameRate ?? "0.15");
    setConversionRate(inputs.conversionRate ?? "");
    setCorporatePriority(inputs.corporatePriority ?? 0.5);
    setInventoryUnits(inputs.inventoryUnits ?? "");
    setAudienceFileName(inputs.audienceFileName ?? null);
    setTargetCustomersFromUpload(Boolean(inputs.audienceFileName));
    setAudienceFile(null);
    lastSyncedAudienceFile.current = inputs.audienceFileName ?? null;
  }, []);

  const handleSaveForecast = useCallback(async () => {
    if (!result) return;
    setSavingForecast(true);
    try {
      const saved = await api.saveCommercialSimulatorForecast({
        name: forecastName.trim() || undefined,
        mainSku,
        additionalSkus,
        inputs: buildForecastInputs(),
        result,
        audience: audienceAnalysis?.audience ?? null,
        audienceFileName,
      });
      setForecastName("");
      setLoadedForecastId(saved.id);
      await refreshSavedForecasts();
      toast("success", "Campaign forecast saved");
    } catch (e) {
      toast("error", e instanceof Error ? e.message : "Failed to save forecast");
    } finally {
      setSavingForecast(false);
    }
  }, [
    result,
    forecastName,
    mainSku,
    additionalSkus,
    buildForecastInputs,
    audienceAnalysis,
    audienceFileName,
    refreshSavedForecasts,
    toast,
  ]);

  const handleLoadForecast = useCallback(
    async (id: string) => {
      try {
        const record = await api.getCommercialSimulatorForecast(id);
        applyForecastInputs(record.inputs);
        setResult(record.result);
        setLoadedForecastId(record.id);
        if (record.audience) {
          setAudienceAnalysis({ audience: record.audience, simulation: record.result });
        } else {
          setAudienceAnalysis(null);
        }
        toast("success", `Loaded forecast: ${record.name}`);
      } catch (e) {
        toast("error", e instanceof Error ? e.message : "Failed to load forecast");
      }
    },
    [applyForecastInputs, toast],
  );

  const handleDeleteForecast = useCallback(
    async (id: string) => {
      try {
        await api.deleteCommercialSimulatorForecast(id);
        if (loadedForecastId === id) setLoadedForecastId(null);
        await refreshSavedForecasts();
        toast("success", "Forecast deleted");
      } catch (e) {
        toast("error", e instanceof Error ? e.message : "Failed to delete forecast");
      }
    },
    [loadedForecastId, refreshSavedForecasts, toast],
  );

  useEffect(() => {
    if (!audienceAnalysis || !audienceFileName) return;
    if (lastSyncedAudienceFile.current === audienceFileName) return;
    lastSyncedAudienceFile.current = audienceFileName;

    const { audience } = audienceAnalysis;
    setTargetCustomers(audience.target_customers);
    setTargetCustomersFromUpload(true);
    if (audience.product) {
      setMainSku(audience.product);
      setAdditionalSkus([]);
    }
  }, [audienceAnalysis, audienceFileName]);

  useEffect(() => {
    if (promoSyncPrice <= 0) return;

    const max = additionalMaxRef.current;
    const pct = additionalPctRef.current;
    if (max.trim()) {
      const amount = Number(max);
      if (Number.isFinite(amount)) {
        setAdditionalPromotionPct(
          formatAdditionalPromoPct(additionalPromoPctFromDollars(amount, promoSyncPrice)),
        );
      }
      return;
    }
    if (pct.trim()) {
      const parsedPct = Number(pct);
      if (Number.isFinite(parsedPct)) {
        setAdditionalPromotionMax(
          formatAdditionalPromoDollars(additionalPromoDollarsFromPct(parsedPct, promoSyncPrice)),
        );
      }
    }
  }, [mainSku, additionalSkus, promoSyncPrice]);

  const handleAdditionalPctChange = (value: string) => {
    setAdditionalPromotionPct(value);
    if (!value.trim()) {
      setAdditionalPromotionMax("");
      return;
    }
    const pct = Number(value);
    if (Number.isFinite(pct) && promoSyncPrice > 0) {
      setAdditionalPromotionMax(formatAdditionalPromoDollars(additionalPromoDollarsFromPct(pct, promoSyncPrice)));
    }
  };

  const handleAdditionalMaxChange = (value: string) => {
    setAdditionalPromotionMax(value);
    if (!value.trim()) {
      setAdditionalPromotionPct("");
      return;
    }
    const amount = Number(value);
    if (Number.isFinite(amount) && promoSyncPrice > 0) {
      setAdditionalPromotionPct(formatAdditionalPromoPct(additionalPromoPctFromDollars(amount, promoSyncPrice)));
    }
  };

  const handleAdditionalMaxBlur = () => {
    const amount = Number(additionalPromotionMax);
    if (Number.isFinite(amount)) {
      setAdditionalPromotionMax(formatAdditionalPromoDollars(amount));
    }
  };

  const runSimulation = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.simulateCommercial({
        products: selectedSkus,
        targetCustomers,
        targetCustomersBySku: skuTargetMix,
        sellingPrice:
          additionalSkus.length === 0 && averageSellingPrice > 0 ? averageSellingPrice : undefined,
        ...additionalPromoPayload,
        promoCode:
          additionalSkus.length === 0
            ? resolveSingleSkuPromoCode({
                mainSku,
                standingPromoBySku,
                audienceProduct: audienceAnalysis?.audience.product,
                audiencePromoCode: audienceAnalysis?.audience.promo_code,
              })
            : undefined,
        leFrameIncentiveRate: leFrameRate ? Number(leFrameRate) : undefined,
        corporatePriority,
        inventoryUnits: inventoryUnits ? Number(inventoryUnits) : undefined,
        conversionRate: parseConversionRateInput(conversionRate),
      });
      setResult(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Simulation failed");
      setResult(null);
    } finally {
      setLoading(false);
    }
  }, [
    mainSku,
    additionalSkus,
    selectedSkus,
    targetCustomers,
    skuTargetMix,
    averageSellingPrice,
    additionalPromoPayload,
    standingPromoBySku,
    audienceAnalysis,
    leFrameRate,
    corporatePriority,
    inventoryUnits,
    conversionRate,
  ]);

  const runAudienceAnalysis = useCallback(async (file: File) => {
    setAudienceLoading(true);
    setAudienceError(null);
    try {
      // Snapshot at upload time — default assumptions only; manual sensitivity changes do not refresh this block.
      const data = await api.analyzeAudienceExport(file, {
        corporatePriority: 0.5,
        leFrameRate: 0.15,
      });
      setAudienceAnalysis(data);
    } catch (e) {
      setAudienceAnalysis(null);
      setAudienceError(e instanceof Error ? e.message : "Audience analysis failed");
    } finally {
      setAudienceLoading(false);
    }
  }, []);

  const handleAudienceUpload = useCallback((file: File) => {
    setAudienceFileName(file.name);
    setAudienceFile(file);
    setAudienceAnalysis(null);
    setAudienceError(null);
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void runSimulation();
    }, 350);
    return () => window.clearTimeout(timer);
  }, [runSimulation]);

  useEffect(() => {
    if (!audienceFile) return;
    const timer = window.setTimeout(() => {
      void runAudienceAnalysis(audienceFile);
    }, 400);
    return () => window.clearTimeout(timer);
  }, [audienceFile, runAudienceAnalysis]);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Commercial Simulator"
        subtitle="What-if pricing and promotion scenarios — results are temporary and never modify production data."
      />

      <section className="cios-card space-y-4 p-5">
        <div>
          <h2 className="text-base font-semibold text-gray-900">Campaign Target Upload (Audience Export)</h2>
          <p className="mt-1 text-sm text-[var(--cios-secondary)]">
            Upload a CSV from{" "}
            <Link href="/export" className="font-medium text-[var(--cios-primary)] underline">
              Audience Export
            </Link>{" "}
            to capture a baseline snapshot from the exported audience. Auto Analysis KPIs stay fixed at upload; compare
            them with the live Sensitivity Analysis scenario below.
          </p>
        </div>
        <UploadDropZone
          onFileSelected={handleAudienceUpload}
          disabled={audienceLoading}
          label="Drag Audience Export CSV here"
          hint="Generic CSV from Administration → Audience Export"
        />
        {audienceLoading && (
          <p className="flex items-center gap-2 text-sm text-[var(--cios-secondary)]">
            <Loader2 className="h-4 w-4 animate-spin" />
            Analyzing {audienceFileName ?? "audience file"}…
          </p>
        )}
        {audienceError && <p className="text-sm text-red-600">{audienceError}</p>}
        {audienceAnalysis && (
          <div className="space-y-4 rounded-xl border border-emerald-200 bg-emerald-50/40 p-4">
            <div>
              <h3 className="font-medium text-emerald-900">Auto Analysis — {audienceFileName}</h3>
              <p className="mt-1 text-sm text-emerald-800">
                {audienceAnalysis.audience.campaign_name ?? "Audience Export"} ·{" "}
                <strong>{formatNumber(audienceAnalysis.audience.target_customers)}</strong> targets · SKU{" "}
                <strong>{audienceAnalysis.audience.product}</strong>
                {audienceAnalysis.audience.promo_code ? (
                  <>
                    {" "}
                    · Promo <strong>{audienceAnalysis.audience.promo_code}</strong>
                  </>
                ) : null}
                {audienceAnalysis.audience.avg_selling_price ? (
                  <>
                    {" "}
                    · Avg selling <strong>{formatCurrency(audienceAnalysis.audience.avg_selling_price)}</strong>
                  </>
                ) : null}
              </p>
              {audienceAnalysis.audience.promo_code_mix?.length ? (
                <p className="mt-2 text-xs text-emerald-900/90">
                  Promo Code targets:{" "}
                  {audienceAnalysis.audience.promo_code_mix
                    .map((row) => `${row.promo_code} ${formatNumber(row.count)}`)
                    .join(" · ")}
                </p>
              ) : null}
              <p className="mt-2 text-xs text-emerald-800/90">
                Baseline snapshot — catalog standing promo, priority 0.50, Le Frame 15%. Does not change when manual
                sensitivity settings are adjusted.
              </p>
              {audienceAnalysis.audience.top_states.length > 0 && (
                <p className="mt-1 text-xs text-emerald-800/90">
                  Top states:{" "}
                  {audienceAnalysis.audience.top_states
                    .map((s) => `${s.state} (${formatNumber(s.count)})`)
                    .join(", ")}
                </p>
              )}
            </div>
            <SimulationKpiGrid result={audienceAnalysis.simulation} />
          </div>
        )}
      </section>

      <section className="space-y-3">
        <div>
          <h2 className="text-base font-semibold text-gray-900">Sensitivity Analysis (Manual)</h2>
          <p className="text-sm text-[var(--cios-secondary)]">
            Adjust pricing, promotion, and inventory assumptions. Results update here only — the uploaded Auto Analysis
            snapshot above stays unchanged for comparison.
          </p>
        </div>

        <PrimeSkuSelector
          mainSku={mainSku}
          additionalSkus={additionalSkus}
          onMainChange={setMainSku}
          onAdditionalChange={setAdditionalSkus}
          activePromotions={activePromotions}
        />

        <div className="cios-card grid gap-4 p-5 lg:grid-cols-3">
          <label className="text-sm lg:col-span-3">
            <span className="mb-1 block font-medium text-gray-700">
              Selected SKUs ({1 + additionalSkus.length})
            </span>
            <p className="text-sm text-gray-900">{selectedSkus.join(" · ") || "—"}</p>
            {skuTargetMix?.length ? (
              <p className="mt-1 text-xs text-[var(--cios-secondary)]">
                {skuTargetsFromPromoCodes
                  ? "Per-SKU targets come from Promo Code counts in the uploaded audience export (mapped via each SKU's standing promo)."
                  : "Per-SKU targets come from the uploaded audience export."}
              </p>
            ) : additionalSkus.length > 0 ? (
              <p className="mt-1 text-xs text-[var(--cios-secondary)]">
                Target customers are split evenly across selected SKUs. Additional promotion layers apply to each SKU on
                top of its standing promo (e.g. shipping fee, limited-time extra % off).
              </p>
            ) : null}
          </label>

          <div className="rounded-lg border border-amber-200 bg-amber-50/60 p-3 text-sm lg:col-span-3">
            <p className="font-medium text-amber-950">Operating standing promotion (included in simulation)</p>
            <ul className="mt-2 space-y-1 text-amber-900">
              {selectedSkus.map((sku) => (
                <li key={sku}>
                  <strong>{sku}</strong>
                  {sku === mainSku ? " · Main" : " · Add-on"} —{" "}
                  {describeStandingPromo(sku, standingPromoBySku, catalogPrices)}
                </li>
              ))}
            </ul>
            <p className="mt-2 text-xs text-amber-800">
              Additional Promotion % / $ below are layered on top of each SKU&apos;s operating standing promo (e.g.
              +$200 shipping credit or +5% off through July 31).
              {selectedSkus.length > 1
                ? ` $/% sync uses average selling price (${formatCurrency(promoSyncPrice)}).`
                : ` Based on ${formatCurrency(promoSyncPrice)} selling price.`}
            </p>
          </div>

          <label className="text-sm">
            <span className="mb-1 block font-medium text-gray-700">Target Customers</span>
            <input
              type="number"
              className="cios-input w-full bg-white px-3 py-2"
              value={targetCustomers}
              onChange={(e) => {
                setTargetCustomers(Number(e.target.value) || 0);
                setTargetCustomersFromUpload(false);
              }}
            />
            {targetCustomersFromUpload && audienceAnalysis ? (
              <p className="mt-1 text-xs text-[var(--cios-secondary)]">
                From uploaded audience ({formatNumber(audienceAnalysis.audience.target_customers)} rows)
              </p>
            ) : null}
          </label>
          <label className="text-sm">
            <span className="mb-1 block font-medium text-gray-700">Average Selling Price</span>
            <input
              className="cios-input w-full bg-gray-50 px-3 py-2 text-gray-700 read-only:cursor-default"
              readOnly
              value={averageSellingPrice > 0 ? formatCurrency(averageSellingPrice) : "—"}
            />
            <p className="mt-1 text-xs text-[var(--cios-secondary)]">
              {audienceAnalysis?.audience.sku_mix?.length
                ? "Weighted average from uploaded SKU mix and catalog prices"
                : "Average of selected SKU catalog prices"}
            </p>
          </label>
          <label className="text-sm">
            <span className="mb-1 block font-medium text-gray-700">Additional Promotion % (decimal)</span>
            <input
              className="cios-input w-full bg-white px-3 py-2"
              placeholder="e.g. 0.05 = extra 5% off on all selected SKUs"
              value={additionalPromotionPct}
              onChange={(e) => handleAdditionalPctChange(e.target.value)}
            />
            {promoSyncPrice > 0 ? (
              <p className="mt-1 text-xs text-[var(--cios-secondary)]">
                {selectedSkus.length > 1
                  ? `Multi-SKU · avg selling ${formatCurrency(promoSyncPrice)}`
                  : `${mainSku} · ${formatCurrency(promoSyncPrice)}`}
              </p>
            ) : null}
          </label>
          <label className="text-sm">
            <span className="mb-1 block font-medium text-gray-700">Additional Promotion ($)</span>
            <input
              className="cios-input w-full bg-white px-3 py-2"
              placeholder="e.g. 200 = extra $200 per SKU (shipping fee)"
              value={additionalPromotionMax}
              onChange={(e) => handleAdditionalMaxChange(e.target.value)}
              onBlur={handleAdditionalMaxBlur}
            />
          </label>
          <label className="text-sm lg:col-span-2">
            <span className="mb-1 block font-medium text-gray-700">Promotion Code</span>
            <input
              className="cios-input w-full bg-gray-50 px-3 py-2 text-gray-700 read-only:cursor-default"
              readOnly
              value={promoCodeDisplay || "—"}
            />
            <p className="mt-1 text-xs text-[var(--cios-secondary)]">
              Linked standing promo codes for each selected SKU
            </p>
          </label>
          <label className="text-sm">
            <span className="mb-1 block font-medium text-gray-700">Conversion Rate (%)</span>
            <input
              className="cios-input w-full bg-white px-3 py-2"
              placeholder="e.g. 0.00025 = 0.00025%"
              value={conversionRate}
              onChange={(e) => setConversionRate(e.target.value)}
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
          {layeredPromoPreview.length > 0 ? (
            <div className="space-y-1 text-xs text-[var(--cios-secondary)] lg:col-span-3">
              <p className="font-medium text-gray-700">Standing + additional promotion per SKU</p>
              {layeredPromoPreview.map((row) => (
                <p key={row.sku}>
                  <strong>{row.sku}</strong>: standing{" "}
                  {row.basePct > 0 ? formatPercent(row.basePct) : "—"}
                  {row.baseMax > 0 ? ` · max ${formatCurrency(row.baseMax)}` : ""}
                  {" → total "}
                  {formatPercent(row.totalPct)} · max {formatCurrency(row.totalMax)}
                </p>
              ))}
            </div>
          ) : null}
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
        </div>
      </section>

      {error && <div className="cios-card p-4 text-sm text-red-600">{error}</div>}

      {loading && !result ? (
        <PageSkeleton />
      ) : result ? (
        <>
          <SimulationKpiGrid result={result} />
          {result.multi_sku && result.by_product && result.by_product.length > 1 && (
            <section className="cios-card overflow-x-auto p-5">
              <h2 className="mb-3 text-base font-semibold text-gray-900">Per-SKU Breakdown</h2>
              <table className="w-full min-w-[720px] text-left text-sm">
                <thead>
                  <tr className="border-b border-gray-200 text-[var(--cios-secondary)]">
                    <th className="py-2 pr-4">SKU</th>
                    <th className="py-2 pr-4">Targets</th>
                    <th className="py-2 pr-4">Conversion</th>
                    <th className="py-2 pr-4">Orders</th>
                    <th className="py-2 pr-4">Revenue</th>
                    <th className="py-2">Net Profit</th>
                  </tr>
                </thead>
                <tbody>
                  {result.by_product.map((row) => (
                    <tr key={row.product} className="border-b border-gray-100">
                      <td className="py-2 pr-4 font-medium">{row.product}</td>
                      <td className="py-2 pr-4">{formatNumber(row.target_customers ?? row.effective_customers ?? 0)}</td>
                      <td className="py-2 pr-4">{formatConversionRate(row.conversion_prediction)}</td>
                      <td className="py-2 pr-4">{formatNumber(row.expected_orders ?? 0)}</td>
                      <td className="py-2 pr-4">{formatCurrency(row.revenue_forecast ?? 0)}</td>
                      <td className="py-2">{formatCurrency(row.net_profit ?? 0)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </section>
          )}
        </>
      ) : null}

      <section className="cios-card space-y-4 p-5">
        <div>
          <h2 className="text-base font-semibold text-gray-900">Saved Campaign Forecasts</h2>
          <p className="mt-1 text-sm text-[var(--cios-secondary)]">
            Save the current scenario as a baseline. Reload it later to compare against actual campaign results.
          </p>
        </div>

        <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
          <label className="flex-1 text-sm">
            <span className="mb-1 block font-medium text-gray-700">Forecast name (optional)</span>
            <input
              className="cios-input w-full bg-white px-3 py-2"
              placeholder="e.g. July email · V6+S4 · shipping promo"
              value={forecastName}
              onChange={(e) => setForecastName(e.target.value)}
            />
          </label>
          <button
            type="button"
            onClick={() => void handleSaveForecast()}
            disabled={!result || savingForecast}
            className="cios-btn bg-[var(--cios-primary)] px-4 py-2 text-white disabled:opacity-50"
          >
            {savingForecast ? "Saving…" : "Save Current Forecast"}
          </button>
        </div>

        {loadingForecasts ? (
          <p className="flex items-center gap-2 text-sm text-[var(--cios-secondary)]">
            <Loader2 className="h-4 w-4 animate-spin" />
            Loading saved forecasts…
          </p>
        ) : savedForecasts.length === 0 ? (
          <p className="text-sm text-[var(--cios-secondary)]">No saved forecasts yet.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[880px] text-left text-sm">
              <thead>
                <tr className="border-b border-gray-200 text-[var(--cios-secondary)]">
                  <th className="py-2 pr-4">Name</th>
                  <th className="py-2 pr-4">SKUs</th>
                  <th className="py-2 pr-4">Targets</th>
                  <th className="py-2 pr-4">Revenue</th>
                  <th className="py-2 pr-4">Orders</th>
                  <th className="py-2 pr-4">Saved</th>
                  <th className="py-2">Actions</th>
                </tr>
              </thead>
              <tbody>
                {savedForecasts.map((row) => (
                  <tr
                    key={row.id}
                    className={row.id === loadedForecastId ? "border-b border-indigo-100 bg-indigo-50/40" : "border-b border-gray-100"}
                  >
                    <td className="py-2 pr-4 font-medium text-gray-900">{row.name}</td>
                    <td className="py-2 pr-4">
                      {[row.mainSku, ...(row.additionalSkus ?? [])].join(" · ")}
                    </td>
                    <td className="py-2 pr-4">{formatNumber(row.targetCustomers)}</td>
                    <td className="py-2 pr-4">{formatCurrency(row.revenueForecast)}</td>
                    <td className="py-2 pr-4">{formatNumber(row.expectedOrders)}</td>
                    <td className="py-2 pr-4 text-xs text-[var(--cios-secondary)]">
                      {row.createdAt ? new Date(row.createdAt).toLocaleString() : "—"}
                    </td>
                    <td className="py-2">
                      <div className="flex items-center gap-2">
                        <button
                          type="button"
                          className="cios-btn border border-gray-200 px-3 py-1 text-xs"
                          onClick={() => void handleLoadForecast(row.id)}
                        >
                          Load
                        </button>
                        <button
                          type="button"
                          className="inline-flex items-center gap-1 rounded border border-red-200 px-2 py-1 text-xs text-red-700"
                          onClick={() => void handleDeleteForecast(row.id)}
                          aria-label={`Delete ${row.name}`}
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}

function SimulationKpiGrid({ result }: { result: CommercialSimulationResult }) {
  return (
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
      <KpiCard label="Opportunity Score" value={String(result.opportunity_score)} />
      <KpiCard label="Conversion Prediction" value={formatConversionRate(result.conversion_prediction)} />
      <KpiCard label="Revenue Forecast" value={formatCurrency(result.revenue_forecast)} />
      <KpiCard label="Net Profit" value={formatCurrency(result.net_profit)} />
      <KpiCard label="Le Frame Revenue" value={formatCurrency(result.le_frame_revenue)} />
      <KpiCard label="Expected Orders" value={formatNumber(result.expected_orders)} />
      <KpiCard label="Recommended Promo" value={formatCurrency(result.recommended_promotion)} />
      <KpiCard label="Promo Code" value={result.promo_code ?? "None"} />
    </div>
  );
}
