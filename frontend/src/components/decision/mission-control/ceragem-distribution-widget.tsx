"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Cell, Pie, PieChart, ResponsiveContainer } from "recharts";
import {
  ensureSegmentRecommendationProducts,
  sortCeragemSegments,
  splitSegmentProductsBySeries,
} from "@/lib/ceragem-segment-recommendations";
import { displayProductLegendLabels } from "@/lib/product-legend-groups";
import { formatCurrency, formatNumber } from "@/lib/utils";

export type CeragemSegmentBand = {
  segment: string;
  count: number;
  pct: number;
  revenue?: number;
  products?: string[];
};

const SEGMENT_COLORS = ["#6366F1", "#818CF8", "#A5B4FC", "#C7D2FE", "#E0E7FF", "#4F46E5", "#7C3AED", "#8B5CF6"];

const POPUP_AUTO_HIDE_MS = 2000;
const POPUP_FADE_MS = 300;
const PIE_INNER_RADIUS = 81;
const PIE_OUTER_RADIUS = 115;
const MIN_SLICE_LABEL_PCT = 4;

function renderSlicePercentLabel(props: {
  cx?: number;
  cy?: number;
  midAngle?: number;
  innerRadius?: number;
  outerRadius?: number;
  percent?: number;
  payload?: CeragemSegmentBand;
}) {
  const pct = props.payload?.pct ?? (props.percent ?? 0) * 100;
  if (pct < MIN_SLICE_LABEL_PCT) return null;

  const { cx = 0, cy = 0, midAngle = 0, innerRadius = PIE_INNER_RADIUS, outerRadius = PIE_OUTER_RADIUS } = props;
  const RADIAN = Math.PI / 180;
  const radius = innerRadius + (outerRadius - innerRadius) * 0.55;
  const x = cx + radius * Math.cos(-midAngle * RADIAN);
  const y = cy + radius * Math.sin(-midAngle * RADIAN);
  const label = Number.isInteger(pct) ? `${pct}%` : `${pct.toFixed(1)}%`;

  return (
    <text x={x} y={y} fill="#1F2937" textAnchor="middle" dominantBaseline="central" fontSize={10} fontWeight={600}>
      {label}
    </text>
  );
}

function resolveSegment(segment: CeragemSegmentBand, catalog: CeragemSegmentBand[]): CeragemSegmentBand {
  const match = catalog.find((row) => row.segment === segment.segment);
  const products = ensureSegmentRecommendationProducts(segment.segment, match?.products ?? segment.products);
  return { ...(match ?? segment), products };
}

export function CeragemDistributionWidget({
  segments,
  totalCustomers,
}: {
  segments: CeragemSegmentBand[];
  totalCustomers: number;
}) {
  const [displaySegment, setDisplaySegment] = useState<CeragemSegmentBand | null>(null);
  const [popupVisible, setPopupVisible] = useState(false);
  const autoHideTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const fadeOutTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const enrichedSegments = useMemo(
    () =>
      sortCeragemSegments(
        segments.map((segment) => ({
          ...segment,
          products: ensureSegmentRecommendationProducts(segment.segment, segment.products),
        })),
      ),
    [segments],
  );

  const chartSegments = useMemo(() => enrichedSegments.filter((segment) => segment.count > 0), [enrichedSegments]);

  const clearPopupTimers = useCallback(() => {
    if (autoHideTimerRef.current) {
      clearTimeout(autoHideTimerRef.current);
      autoHideTimerRef.current = null;
    }
    if (fadeOutTimerRef.current) {
      clearTimeout(fadeOutTimerRef.current);
      fadeOutTimerRef.current = null;
    }
  }, []);

  const hidePopup = useCallback(() => {
    clearPopupTimers();
    setPopupVisible(false);
    fadeOutTimerRef.current = setTimeout(() => {
      setDisplaySegment(null);
      fadeOutTimerRef.current = null;
    }, POPUP_FADE_MS);
  }, [clearPopupTimers]);

  const showPopup = useCallback(
    (segment: CeragemSegmentBand) => {
      clearPopupTimers();
      if (fadeOutTimerRef.current) {
        clearTimeout(fadeOutTimerRef.current);
        fadeOutTimerRef.current = null;
      }
      setDisplaySegment(resolveSegment(segment, enrichedSegments));
      requestAnimationFrame(() => setPopupVisible(true));
      autoHideTimerRef.current = setTimeout(() => {
        autoHideTimerRef.current = null;
        hidePopup();
      }, POPUP_AUTO_HIDE_MS);
    },
    [clearPopupTimers, enrichedSegments, hidePopup],
  );

  useEffect(() => () => clearPopupTimers(), [clearPopupTimers]);

  const popupProducts = useMemo(() => {
    if (!displaySegment?.products?.length) return { vSeries: [], mSeries: [] };
    return splitSegmentProductsBySeries(displaySegment.products);
  }, [displaySegment]);

  if (!segments.length) {
    return <p className="text-sm text-[var(--cios-secondary)]">No Ceragem segmentation distribution in scope.</p>;
  }

  return (
    <div className="flex h-full min-h-0 flex-col">
      <div className="flex min-h-0 flex-1 items-start gap-4" onMouseLeave={hidePopup}>
        <div className="relative h-[280px] w-[280px] shrink-0">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={chartSegments}
                dataKey="count"
                nameKey="segment"
                cx="50%"
                cy="50%"
                innerRadius={PIE_INNER_RADIUS}
                outerRadius={PIE_OUTER_RADIUS}
                paddingAngle={2}
                isAnimationActive={false}
                labelLine={false}
                label={renderSlicePercentLabel}
                onMouseEnter={(entry) => {
                  const payload = entry as CeragemSegmentBand;
                  if (payload?.segment) showPopup(payload);
                }}
              >
                {chartSegments.map((segment) => (
                  <Cell
                    key={segment.segment}
                    fill={SEGMENT_COLORS[enrichedSegments.findIndex((s) => s.segment === segment.segment) % SEGMENT_COLORS.length]}
                    style={{ cursor: "pointer" }}
                  />
                ))}
              </Pie>
            </PieChart>
          </ResponsiveContainer>
          <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
            <p className="text-xl font-bold text-gray-900">{formatNumber(totalCustomers)}</p>
            <p className="text-[10px] uppercase tracking-wide text-[var(--cios-secondary)]">Customers</p>
          </div>
        </div>

        <div className="relative min-h-[280px] min-w-0 flex-1 self-stretch">
          {displaySegment && (
            <div
              className={`pointer-events-none w-full max-w-[280px] rounded-lg border border-[var(--cios-border)] bg-white p-3 text-xs shadow-lg transition-opacity ${
                popupVisible ? "opacity-100" : "opacity-0"
              }`}
              style={{ transitionDuration: `${POPUP_FADE_MS}ms` }}
            >
              <p className="font-semibold text-gray-900">{displaySegment.segment}</p>
              <p className="mt-1 text-[var(--cios-secondary)]">
                Customers: {formatNumber(displaySegment.count)} ({displaySegment.pct}%)
              </p>
              <p className="text-gray-700">TAR: {formatCurrency(displaySegment.revenue ?? 0)}</p>
              {(popupProducts.vSeries.length > 0 || popupProducts.mSeries.length > 0) && (
                <div className="mt-2 space-y-2 border-t border-[var(--cios-border)] pt-2">
                  <p className="font-medium text-gray-900">Recommended Products</p>
                  {popupProducts.vSeries.length > 0 && (
                    <div>
                      <p className="text-[10px] font-semibold uppercase tracking-wide text-[var(--cios-secondary)]">V Series</p>
                      <ul className="mt-0.5 space-y-0.5 text-gray-700">
                        {displayProductLegendLabels(popupProducts.vSeries).map((product) => (
                          <li key={product}>{product}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {popupProducts.mSeries.length > 0 && (
                    <div>
                      <p className="text-[10px] font-semibold uppercase tracking-wide text-[var(--cios-secondary)]">M Series</p>
                      <ul className="mt-0.5 space-y-0.5 text-gray-700">
                        {displayProductLegendLabels(popupProducts.mSeries).map((product) => (
                          <li key={product}>{product}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
      <ul className="mt-3 flex w-full shrink-0 flex-wrap items-center justify-start gap-2">
        {enrichedSegments.map((segment, i) => (
          <li
            key={segment.segment}
            className="flex cursor-pointer items-center gap-1.5 text-xs"
            onMouseEnter={() => showPopup(segment)}
          >
            <span className="h-2.5 w-2.5 shrink-0 rounded-full" style={{ background: SEGMENT_COLORS[i % SEGMENT_COLORS.length] }} />
            <span className="text-[var(--cios-secondary)]">{segment.segment}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
