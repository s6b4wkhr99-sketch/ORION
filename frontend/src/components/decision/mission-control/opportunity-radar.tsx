"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { CartesianGrid, ResponsiveContainer, Scatter, ScatterChart, XAxis, YAxis } from "recharts";
import {
  displayProductLabel,
  filterScatterPointsForLegend,
} from "@/lib/product-legend-groups";
import { expandProductsWithStandingPromoCredit } from "@/lib/standing-promo-legend";
import {
  ProductChartLegend,
  productColor,
} from "@/lib/product-visual";
import {
  RADAR_SPREAD_X_AXES,
  radarXDomain,
  radarXScore,
  radarYDomain,
  spreadRadarOpportunityY,
  spreadRadarStateAxis,
  type RadarXAxis as SpreadRadarXAxis,
} from "@/lib/radar-axis-spread";

import { cn, formatCurrency, formatNumber } from "@/lib/utils";

export type RadarXAxis = SpreadRadarXAxis;

export type OpportunityRadarPoint = {
  id: string;
  label: string;
  state: string;
  product: string;
  opportunityScore: number;
  lifestyleScore: number;
  purchasePowerScore: number;
  purchasePowerTier?: string;
  painIndexScore: number;
  lifestyleTier?: string;
  digitalScore: number;
  digitalTier?: string;
  brandScore: number;
  brandTier?: string;
  customers: number;
  revenue: number;
};

type RadarDimension = {
  id: RadarXAxis;
  label: string;
  scoreKey: keyof Pick<
    OpportunityRadarPoint,
    "lifestyleScore" | "purchasePowerScore" | "painIndexScore" | "digitalScore" | "brandScore"
  >;
  tooltipTitle: string;
  tooltipBody: string;
};

/** Axis switcher labels; tooltipTitle/tooltipBody kept for axis semantics (no hover popup). */
const RADAR_DIMENSIONS: RadarDimension[] = [
  {
    id: "lifestyle",
    label: "Lifestyle Index",
    scoreKey: "lifestyleScore",
    tooltipTitle: "Lifestyle Index",
    tooltipBody:
      "Wellness segment share, Pause M penetration, and therapeutic vs wellness geography. Higher scores indicate premium wellness markets; lower scores reflect pain/therapeutic markets.",
  },
  {
    id: "purchase_power",
    label: "Purchase Power",
    scoreKey: "purchasePowerScore",
    tooltipTitle: "Purchase Power",
    tooltipBody:
      "Geo-weighted income tiers and premium ZIP concentration. High-income geographies (e.g. VA, NJ) plot right; lower-income geographies plot left. Cohort-stretched for radar readability.",
  },
  {
    id: "pain_index",
    label: "Pain Index",
    scoreKey: "painIndexScore",
    tooltipTitle: "Pain Index",
    tooltipBody:
      "Geo-weighted pain / therapeutic need. High-pain states (e.g. OH) spread right vs wellness-oriented markets (e.g. AL) on the left.",
  },
  {
    id: "digital",
    label: "Digital Engagement",
    scoreKey: "digitalScore",
    tooltipTitle: "Digital Engagement",
    tooltipBody:
      "Metro commerce tier: Tier-1 core urban, Tier-2 major MSA, mid digital, or lower rural/low-metro engagement.",
  },
  {
    id: "brand",
    label: "Brand Familiarity",
    scoreKey: "brandScore",
    tooltipTitle: "Brand Familiarity",
    tooltipBody:
      "Brand v5 geo signals: ACS Korean metros (LA, NYC/NJ, DC tier-1; Dallas/Houston/Philadelphia tier-3), IndexMundi Asian city density vs 5.9% US baseline, and brand-enclave ZIPs.",
  },
];

export const RADAR_TOP_STATE_COUNT = 10;

/** Score axis labels — 20–100 at 20-point steps; origin (0) stays unlabeled. */
const RADAR_SCORE_AXIS_TICKS = [20, 40, 60, 80, 100];

const MIN_BUBBLE_R = 10;
const MAX_BUBBLE_R = 38;

const RADAR_POPUP_AUTO_HIDE_MS = 2000;
const RADAR_POPUP_FADE_MS = 300;

/** Room for largest bubble radius + stroke so SVG plot clip does not cut high-score points. */
const CHART_MARGIN = {
  top: MAX_BUBBLE_R + 14,
  right: MAX_BUBBLE_R + 14,
  bottom: 32,
  left: MAX_BUBBLE_R + 28,
};

const Y_AXIS_LABEL = "Intelligence Opportunity Score";

function bubbleRadius(value: number, min: number, max: number): number {
  if (max <= min) return (MIN_BUBBLE_R + MAX_BUBBLE_R) / 2;
  const ratio = (value - min) / (max - min);
  return MIN_BUBBLE_R + ratio * (MAX_BUBBLE_R - MIN_BUBBLE_R);
}

function AxisDimensionButton({
  option,
  active,
  onSelect,
}: {
  option: RadarDimension;
  active: boolean;
  onSelect: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onSelect}
      title={option.label}
      className={cn(
        "rounded-full border px-2.5 py-1 text-xs transition-colors",
        active
          ? "border-[var(--cios-primary)] bg-[var(--cios-primary-light)] font-medium text-[var(--cios-primary)]"
          : "border-[var(--cios-border)] text-[var(--cios-secondary)] hover:border-gray-300 hover:text-gray-900",
      )}
      aria-pressed={active}
    >
      {option.label}
    </button>
  );
}

export function OpportunityRadar({
  points,
  chartHeight = 380,
  fill = false,
}: {
  points: OpportunityRadarPoint[];
  /** Chart height in px when not stretching — default matches Opportunity by State map */
  chartHeight?: number;
  /** Grow chart to fill WidgetShell body */
  fill?: boolean;
}) {
  const router = useRouter();
  const [activeProduct, setActiveProduct] = useState<string | null>(null);
  const [xAxis, setXAxis] = useState<RadarXAxis>("lifestyle");
  const [displayPoint, setDisplayPoint] = useState<(OpportunityRadarPoint & { xScore: number; yScore: number }) | null>(
    null,
  );
  const [popupVisible, setPopupVisible] = useState(false);
  const autoHideTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const fadeOutTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

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
      setDisplayPoint(null);
      fadeOutTimerRef.current = null;
    }, RADAR_POPUP_FADE_MS);
  }, [clearPopupTimers]);

  const showPopup = useCallback(
    (point: OpportunityRadarPoint & { xScore: number; yScore: number }) => {
      clearPopupTimers();
      setDisplayPoint(point);
      requestAnimationFrame(() => setPopupVisible(true));
      autoHideTimerRef.current = setTimeout(() => {
        autoHideTimerRef.current = null;
        hidePopup();
      }, RADAR_POPUP_AUTO_HIDE_MS);
    },
    [clearPopupTimers, hidePopup],
  );

  useEffect(() => () => clearPopupTimers(), [clearPopupTimers]);

  const xAxisLabel = RADAR_DIMENSIONS.find((o) => o.id === xAxis)?.label ?? "Lifestyle Index";

  const topPoints = useMemo(() => points, [points]);

  const productsWithData = useMemo(
    () => expandProductsWithStandingPromoCredit(topPoints.map((p) => p.product)),
    [topPoints],
  );

  const xSpreadMap = useMemo(() => {
    if (!RADAR_SPREAD_X_AXES.has(xAxis)) return null;
    const byState = new Map<string, OpportunityRadarPoint>();
    for (const point of topPoints) {
      if (!byState.has(point.state)) {
        byState.set(point.state, point);
      }
    }
    return spreadRadarStateAxis([...byState.values()], xAxis);
  }, [topPoints, xAxis]);

  const chartPoints = useMemo(() => {
    const withX = topPoints.map((p) => ({
      ...p,
      xScore: radarXScore(p, xAxis, xSpreadMap),
    }));
    const spreadSource = activeProduct
      ? filterScatterPointsForLegend(withX, activeProduct, (p) => p.state)
      : withX;
    const ySpreadMap = spreadRadarOpportunityY(spreadSource);
    return withX.map((p) => ({
      ...p,
      yScore: ySpreadMap.get(p.id) ?? p.opportunityScore,
    }));
  }, [topPoints, xAxis, xSpreadMap, activeProduct]);

  const visiblePoints = useMemo(
    () => filterScatterPointsForLegend(chartPoints, activeProduct, (p) => p.state, RADAR_TOP_STATE_COUNT),
    [activeProduct, chartPoints],
  );

  const xDomain = useMemo(
    () => radarXDomain(visiblePoints.map((p) => p.xScore), xAxis),
    [visiblePoints, xAxis],
  );

  const yDomain = useMemo(() => radarYDomain(visiblePoints.map((p) => p.yScore)), [visiblePoints]);

  const xTicks = useMemo(
    () => RADAR_SCORE_AXIS_TICKS.filter((tick) => tick <= xDomain[1]),
    [xDomain],
  );

  const yTicks = useMemo(
    () => RADAR_SCORE_AXIS_TICKS.filter((tick) => tick <= yDomain[1]),
    [yDomain],
  );

  const sizeRange = useMemo(() => {
    const sizes = visiblePoints.map((p) => Math.max(p.customers, p.revenue / 100, 1));
    if (!sizes.length) return { min: 1, max: 1 };
    return {
      min: Math.min(...sizes),
      max: Math.max(...sizes),
    };
  }, [visiblePoints]);

  if (!points.length) {
    return <p className="text-sm text-[var(--cios-secondary)]">Upload data to see opportunity radar.</p>;
  }

  const toggleProduct = (product: string) => {
    hidePopup();
    setActiveProduct((current) => (current === product ? null : product));
  };

  return (
    <div className={cn(fill && "flex h-full min-h-0 flex-col")}>
      <div className="mb-3 flex shrink-0 flex-wrap items-center gap-2">
        <div className="flex flex-wrap gap-1.5">
          {RADAR_DIMENSIONS.map((option) => (
            <AxisDimensionButton
              key={option.id}
              option={option}
              active={xAxis === option.id}
              onSelect={() => setXAxis(option.id)}
            />
          ))}
        </div>
      </div>

      <div
        className={cn("relative", fill ? "min-h-0 flex-1" : "")}
        style={fill ? { minHeight: chartHeight } : { height: chartHeight }}
      >
        {visiblePoints.length === 0 ? (
          <div className="flex h-full items-center justify-center text-sm text-[var(--cios-secondary)]">
            No opportunities for this filter.{" "}
            <button
              type="button"
              className="ml-1 text-[var(--cios-primary)] hover:underline"
              onClick={() => setActiveProduct(null)}
            >
              Reset filter
            </button>
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <ScatterChart margin={CHART_MARGIN}>
              <CartesianGrid
                strokeDasharray="3 3"
                stroke="#E5E7EB"
                horizontalValues={yTicks}
                verticalValues={xTicks}
              />
              <XAxis
                type="number"
                dataKey="xScore"
                name={xAxisLabel}
                domain={[0, xDomain[1]]}
                ticks={xTicks}
                allowDecimals={false}
                tick={{ fontSize: 11 }}
                label={{ value: `${xAxisLabel} Score →`, position: "insideBottom", offset: -4, fontSize: 10, fill: "#6B7280" }}
              />
              <YAxis
                type="number"
                dataKey="yScore"
                name="Opportunity"
                domain={[0, yDomain[1]]}
                ticks={yTicks}
                allowDecimals={false}
                tick={{ fontSize: 11 }}
                label={{
                  value: Y_AXIS_LABEL,
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
                  const payload = (node as { payload?: OpportunityRadarPoint & { xScore: number; yScore: number } })
                    ?.payload;
                  if (payload) showPopup(payload);
                }}
                onMouseLeave={hidePopup}
                onClick={(p) => {
                  const point = p as unknown as OpportunityRadarPoint;
                  router.push(
                    `/opportunities?product=${encodeURIComponent(point.product)}&state=${encodeURIComponent(point.state)}`,
                  );
                }}
                shape={(props) => {
                  const { cx, cy, payload } = props as { cx: number; cy: number; payload: OpportunityRadarPoint };
                  const fillColor = productColor(activeProduct ?? payload.product);
                  const sizeValue = Math.max(payload.customers, payload.revenue / 100, 1);
                  const r = bubbleRadius(sizeValue, sizeRange.min, sizeRange.max);
                  return (
                    <circle
                      cx={cx}
                      cy={cy}
                      r={r}
                      fill={fillColor}
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

        {displayPoint && (
          <div
            className={cn(
              "pointer-events-none absolute right-2 top-2 z-10 max-w-[220px] rounded-lg border border-[var(--cios-border)] bg-white p-3 text-xs shadow-lg transition-opacity",
              popupVisible ? "opacity-100" : "opacity-0",
            )}
            style={{ transitionDuration: `${RADAR_POPUP_FADE_MS}ms` }}
          >
            <p className="font-semibold text-gray-900">{displayPoint.label}</p>
            <p className="mt-1 text-[var(--cios-secondary)]">
              Product Target: {displayProductLabel(displayPoint.product)}
            </p>
            <p className="mt-1 text-[var(--cios-secondary)]">
              Opportunity Score: {displayPoint.opportunityScore}
            </p>
            {RADAR_DIMENSIONS.map((dimension) => (
              <p
                key={dimension.id}
                className={cn("text-gray-700", dimension.id === xAxis && "font-medium text-gray-900")}
              >
                {dimension.label}: {displayPoint[dimension.scoreKey]}
              </p>
            ))}
            <p className="text-gray-700">Customers: {formatNumber(displayPoint.customers)}</p>
            <p className="text-gray-700">TAR: {formatCurrency(displayPoint.revenue)}</p>
          </div>
        )}
      </div>

      <ProductChartLegend
        className="mt-3 shrink-0"
        activeProduct={activeProduct}
        onShowAll={() => setActiveProduct(null)}
        onToggleProduct={toggleProduct}
        productsWithData={productsWithData}
        showAllLabel="Show all"
      />
    </div>
  );
}
