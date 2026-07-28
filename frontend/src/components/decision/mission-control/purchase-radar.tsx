"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { CartesianGrid, ResponsiveContainer, Scatter, ScatterChart, XAxis, YAxis } from "recharts";
import {
  RADAR_CHART_MARGIN,
  RADAR_MAX_BUBBLE_R,
  RADAR_MIN_BUBBLE_R,
  RADAR_PLOT_ASPECT_RATIO,
  RADAR_SCORE_AXIS_TICKS,
  PURCHASE_RADAR_TOP_STATE_COUNT,
} from "@/lib/radar-chart-layout";
import { radarXDomain, radarYDomain, spreadRadarOpportunityY } from "@/lib/radar-axis-spread";
import {
  purchaseSkuBelongsToVSeries,
  purchaseSkuColor,
  purchaseSkuLegendLabel,
  purchaseSkuLegendOrder,
} from "@/lib/purchase-sku";
import { cn, formatNumber } from "@/lib/utils";

export type PurchaseRadarPoint = {
  id: string;
  label: string;
  state: string;
  sku_token: string;
  product: string;
  purchase_count: number;
  unique_buyers: number;
  purchase_volume_score: number;
  state_volume_score: number;
  buyer_density_score: number;
  national_share_pct: number;
};

type PurchaseXAxis = "state_volume" | "buyer_density";

const X_DIMENSIONS: { id: PurchaseXAxis; label: string; key: keyof PurchaseRadarPoint }[] = [
  { id: "state_volume", label: "State Purchase Index", key: "state_volume_score" },
  { id: "buyer_density", label: "Buyer Density", key: "buyer_density_score" },
];

const MIN_BUBBLE_R = RADAR_MIN_BUBBLE_R;
const MAX_BUBBLE_R = RADAR_MAX_BUBBLE_R;
const CHART_MARGIN = RADAR_CHART_MARGIN;
const SCORE_TICKS = [...RADAR_SCORE_AXIS_TICKS];
const POPUP_MS = 2000;
const FADE_MS = 300;
const Y_LABEL = "Purchase Volume Score";

function bubbleRadius(value: number, min: number, max: number): number {
  if (max <= min) return (MIN_BUBBLE_R + MAX_BUBBLE_R) / 2;
  return MIN_BUBBLE_R + ((value - min) / (max - min)) * (MAX_BUBBLE_R - MIN_BUBBLE_R);
}

function rawXValue(point: PurchaseRadarPoint, axis: PurchaseXAxis): number {
  const key = X_DIMENSIONS.find((d) => d.id === axis)?.key ?? "state_volume_score";
  return Number(point[key] ?? 0);
}

function filterBySku<T extends { sku_token: string; purchase_count: number; state?: string }>(
  points: T[],
  sku: string,
  limit: number,
): T[] {
  const token = sku.toUpperCase();
  return [...points]
    .filter((p) => p.sku_token.toUpperCase() === token)
    .sort((a, b) => b.purchase_count - a.purchase_count || (a.state ?? "").localeCompare(b.state ?? ""))
    .slice(0, limit);
}

function topStatesPerSku<T extends { sku_token: string; purchase_count: number; state?: string }>(
  pts: T[],
  limit: number,
): T[] {
  const bySku = new Map<string, T[]>();
  for (const point of pts) {
    const token = point.sku_token.toUpperCase();
    const bucket = bySku.get(token) ?? [];
    bucket.push(point);
    bySku.set(token, bucket);
  }
  const out: T[] = [];
  for (const bucket of bySku.values()) {
    out.push(
      ...[...bucket]
        .sort((a, b) => b.purchase_count - a.purchase_count || (a.state ?? "").localeCompare(b.state ?? ""))
        .slice(0, limit),
    );
  }
  return out;
}

function PurchaseSkuLegendButton({
  sku,
  isActive,
  dimmed,
  onToggle,
}: {
  sku: string;
  isActive: boolean;
  dimmed: boolean;
  onToggle: (sku: string) => void;
}) {
  return (
    <button
      type="button"
      onClick={() => onToggle(sku)}
      className={cn(
        "flex max-w-full items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs transition-colors",
        isActive
          ? "border-[var(--cios-primary)] bg-[var(--cios-primary-light)] font-medium text-[var(--cios-primary)]"
          : dimmed
            ? "border-transparent text-[var(--cios-secondary)] opacity-50 hover:opacity-100"
            : "border-transparent text-[var(--cios-secondary)] hover:bg-gray-100",
      )}
      aria-pressed={isActive}
    >
      <span className="h-2.5 w-2.5 shrink-0 rounded-full" style={{ background: purchaseSkuColor(sku) }} />
      <span className="truncate">{purchaseSkuLegendLabel(sku)}</span>
    </button>
  );
}

export function PurchaseRadar({
  points,
  fill = false,
}: {
  points: PurchaseRadarPoint[];
  chartHeight?: number;
  fill?: boolean;
}) {
  const [activeSku, setActiveSku] = useState<string | null>(null);
  const [xAxis, setXAxis] = useState<PurchaseXAxis>("state_volume");
  const [displayPoint, setDisplayPoint] = useState<
    (PurchaseRadarPoint & { xScore: number; yScore: number; xRaw: number }) | null
  >(null);
  const [popupVisible, setPopupVisible] = useState(false);
  const autoHideRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const fadeRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const clearTimers = useCallback(() => {
    if (autoHideRef.current) clearTimeout(autoHideRef.current);
    if (fadeRef.current) clearTimeout(fadeRef.current);
    autoHideRef.current = null;
    fadeRef.current = null;
  }, []);

  const hidePopup = useCallback(() => {
    clearTimers();
    setPopupVisible(false);
    fadeRef.current = setTimeout(() => setDisplayPoint(null), FADE_MS);
  }, [clearTimers]);

  const showPopup = useCallback(
    (point: PurchaseRadarPoint & { xScore: number; yScore: number; xRaw: number }) => {
      clearTimers();
      setDisplayPoint(point);
      requestAnimationFrame(() => setPopupVisible(true));
      autoHideRef.current = setTimeout(hidePopup, POPUP_MS);
    },
    [clearTimers, hidePopup],
  );

  useEffect(() => () => clearTimers(), [clearTimers]);

  const xLabel = X_DIMENSIONS.find((d) => d.id === xAxis)?.label ?? "State Purchase Index";

  const legendSkus = useMemo(
    () => purchaseSkuLegendOrder(points.map((p) => p.sku_token)),
    [points],
  );

  const { vSeriesLegend, mSeriesLegend } = useMemo(() => {
    const vSeries = legendSkus.filter((sku) => purchaseSkuBelongsToVSeries(sku));
    const mSeries = legendSkus.filter((sku) => !vSeries.includes(sku));
    return { vSeriesLegend: vSeries, mSeriesLegend: mSeries };
  }, [legendSkus]);

  const visiblePoints = useMemo(() => {
    const cohort = activeSku
      ? filterBySku(points, activeSku, PURCHASE_RADAR_TOP_STATE_COUNT)
      : topStatesPerSku(points, PURCHASE_RADAR_TOP_STATE_COUNT);

    const ySpreadMap = spreadRadarOpportunityY(
      cohort.map((p) => ({ id: p.id, opportunityScore: p.purchase_volume_score })),
    );

    return cohort.map((p) => {
      const xRaw = rawXValue(p, xAxis);
      return {
        ...p,
        xRaw,
        xScore: xRaw,
        yScore: ySpreadMap.get(p.id) ?? p.purchase_volume_score,
      };
    });
  }, [points, xAxis, activeSku]);

  const xDomain = useMemo(
    () => radarXDomain(visiblePoints.map((p) => p.xScore), "lifestyle"),
    [visiblePoints],
  );

  const yDomain = useMemo(() => radarYDomain(visiblePoints.map((p) => p.yScore)), [visiblePoints]);

  const xTicks = useMemo(
    () => SCORE_TICKS.filter((tick) => tick <= xDomain[1]),
    [xDomain],
  );

  const yTicks = useMemo(
    () => SCORE_TICKS.filter((tick) => tick <= yDomain[1]),
    [yDomain],
  );

  const sizeRange = useMemo(() => {
    const sizes = visiblePoints.map((p) => p.purchase_count);
    if (!sizes.length) return { min: 1, max: 1 };
    return { min: Math.min(...sizes), max: Math.max(...sizes) };
  }, [visiblePoints]);

  if (!points.length) {
    return <p className="text-sm text-[var(--cios-secondary)]">Upload buyer data to see purchase radar.</p>;
  }

  return (
    <div className={cn(fill && "flex h-full min-h-0 flex-col")}>
      <div className="mb-3 flex shrink-0 flex-wrap gap-1.5">
        {X_DIMENSIONS.map((option) => (
          <button
            key={option.id}
            type="button"
            onClick={() => {
              hidePopup();
              setXAxis(option.id);
            }}
            className={cn(
              "rounded-full border px-2.5 py-1 text-xs transition-colors",
              xAxis === option.id
                ? "border-[var(--cios-primary)] bg-[var(--cios-primary-light)] font-medium text-[var(--cios-primary)]"
                : "border-[var(--cios-border)] text-[var(--cios-secondary)] hover:border-gray-300 hover:text-gray-900",
            )}
            aria-pressed={xAxis === option.id}
          >
            {option.label}
          </button>
        ))}
      </div>

      <div
        className="relative w-full shrink-0"
        style={{ aspectRatio: RADAR_PLOT_ASPECT_RATIO }}
      >
        {visiblePoints.length === 0 ? (
          <div className="flex h-full items-center justify-center text-sm text-[var(--cios-secondary)]">
            No purchases for this filter.{" "}
            <button type="button" className="ml-1 text-[var(--cios-primary)] hover:underline" onClick={() => setActiveSku(null)}>
              Reset filter
            </button>
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <ScatterChart margin={CHART_MARGIN}>
              <CartesianGrid
                stroke="#E5E7EB"
                strokeDasharray="3 3"
                horizontalValues={yTicks}
                verticalValues={xTicks}
              />
              <XAxis
                type="number"
                dataKey="xScore"
                domain={[0, xDomain[1]]}
                ticks={xTicks}
                allowDecimals={false}
                tick={{ fontSize: 11, fill: "#6B7280" }}
                label={{
                  value: `${xLabel} →`,
                  position: "insideBottom",
                  offset: -4,
                  fontSize: 10,
                  fill: "#6B7280",
                }}
              />
              <YAxis
                type="number"
                dataKey="yScore"
                domain={[0, yDomain[1]]}
                ticks={yTicks}
                allowDecimals={false}
                tick={{ fontSize: 11, fill: "#6B7280" }}
                label={{
                  value: Y_LABEL,
                  angle: -90,
                  position: "insideLeft",
                  offset: 8,
                  fontSize: 10,
                  fill: "#6B7280",
                }}
              />
              <Scatter
                data={visiblePoints}
                allowDataOverflow
                onMouseEnter={(node) => {
                  const payload = (
                    node as { payload?: PurchaseRadarPoint & { xScore: number; yScore: number; xRaw: number } }
                  )?.payload;
                  if (payload) showPopup(payload);
                }}
                onMouseLeave={hidePopup}
                onClick={(node) => {
                  const payload = (
                    node as { payload?: PurchaseRadarPoint & { xScore: number; yScore: number; xRaw: number } }
                  )?.payload;
                  if (payload) showPopup(payload);
                }}
                shape={(props: {
                  cx?: number;
                  cy?: number;
                  payload?: PurchaseRadarPoint & { xScore: number; yScore: number; xRaw: number };
                }) => {
                  const { cx = 0, cy = 0, payload } = props;
                  if (!payload) return null;
                  const r = bubbleRadius(payload.purchase_count, sizeRange.min, sizeRange.max);
                  const colorSku = activeSku ?? payload.sku_token;
                  return (
                    <circle
                      cx={cx}
                      cy={cy}
                      r={r}
                      fill={purchaseSkuColor(colorSku)}
                      fillOpacity={0.85}
                      stroke="rgba(255, 255, 255, 0.55)"
                      strokeWidth={0.75}
                      style={{ cursor: "pointer" }}
                    />
                  );
                }}
              />
            </ScatterChart>
          </ResponsiveContainer>
        )}

        {displayPoint ? (
          <div
            className={cn(
              "pointer-events-none absolute right-2 top-2 z-10 max-w-[240px] rounded-lg border border-[var(--cios-border)] bg-white p-3 text-xs shadow-lg transition-opacity",
              popupVisible ? "opacity-100" : "opacity-0",
            )}
            style={{ transitionDuration: `${FADE_MS}ms` }}
          >
            <p className="font-semibold text-gray-900">
              {displayPoint.state} · {purchaseSkuLegendLabel(displayPoint.sku_token)}
            </p>
            <p className="text-[var(--cios-secondary)]">SKU: {displayPoint.sku_token}</p>
            <p className="mt-1 text-[var(--cios-secondary)]">
              Purchases: <span className="font-medium text-gray-700">{formatNumber(displayPoint.purchase_count)}</span>
            </p>
            <p className="text-gray-700">
              Unique buyers: {formatNumber(displayPoint.unique_buyers)} · National share:{" "}
              {displayPoint.national_share_pct}%
            </p>
            <p className="mt-2 border-t border-[var(--cios-border)] pt-2 text-gray-700">
              {Y_LABEL}: {Math.round(displayPoint.purchase_volume_score)}
            </p>
            <p className="text-gray-700">
              {xLabel}: {Math.round(displayPoint.xRaw)}
            </p>
          </div>
        ) : null}
      </div>

      <div className="mt-3 shrink-0 space-y-2">
        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            onClick={() => {
              hidePopup();
              setActiveSku(null);
            }}
            className={cn(
              "rounded-full border px-2.5 py-1 text-xs transition-colors",
              !activeSku
                ? "border-[var(--cios-primary)] bg-[var(--cios-primary-light)] font-medium text-[var(--cios-primary)]"
                : "border-[var(--cios-border)] text-[var(--cios-secondary)] hover:border-gray-300 hover:text-gray-900",
            )}
            aria-pressed={!activeSku}
          >
            Show all
          </button>
        </div>
        {vSeriesLegend.length > 0 ? (
          <div className="flex flex-wrap gap-2">
            {vSeriesLegend.map((sku) => (
              <PurchaseSkuLegendButton
                key={sku}
                sku={sku}
                isActive={activeSku?.toUpperCase() === sku.toUpperCase()}
                dimmed={Boolean(activeSku && activeSku.toUpperCase() !== sku.toUpperCase())}
                onToggle={(token) => {
                  hidePopup();
                  setActiveSku((current) => (current?.toUpperCase() === token.toUpperCase() ? null : token.toUpperCase()));
                }}
              />
            ))}
          </div>
        ) : null}
        {mSeriesLegend.length > 0 ? (
          <div className="flex flex-wrap gap-2">
            {mSeriesLegend.map((sku) => (
              <PurchaseSkuLegendButton
                key={sku}
                sku={sku}
                isActive={activeSku?.toUpperCase() === sku.toUpperCase()}
                dimmed={Boolean(activeSku && activeSku.toUpperCase() !== sku.toUpperCase())}
                onToggle={(token) => {
                  hidePopup();
                  setActiveSku((current) => (current?.toUpperCase() === token.toUpperCase() ? null : token.toUpperCase()));
                }}
              />
            ))}
          </div>
        ) : null}
      </div>
    </div>
  );
}
