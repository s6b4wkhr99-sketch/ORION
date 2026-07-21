"use client";

import { useMemo, useState } from "react";
import {
  CartesianGrid,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { CityOpportunityRow } from "@/lib/api";
import {
  buildLegendTargetMap,
  displayProductLabel,
  filterScatterPointsForLegend,
} from "@/lib/product-legend-groups";
import { expandProductsWithStandingPromoCredit } from "@/lib/standing-promo-legend";
import {
  ProductChartLegend,
  productColor,
  type ProductTargetSummary,
} from "@/lib/product-visual";
import { radarYDomain, spreadCohortPercentile, spreadRadarOpportunityY } from "@/lib/radar-axis-spread";
import { cn, formatCurrency, formatNumber, formatPercent } from "@/lib/utils";

const TOP_CITY_PER_PRODUCT = 25;
const MIN_BUBBLE_R = 8.75;
const MAX_BUBBLE_R = 32.5;
const SCORE_TICKS = [20, 40, 60, 80, 100];
const DEFAULT_CHART_HEIGHT = 400;

type CityXAxis = "pain_index" | "lifestyle_index";

const CITY_X_DIMENSIONS: { id: CityXAxis; label: string }[] = [
  { id: "pain_index", label: "Pain Index" },
  { id: "lifestyle_index", label: "Lifestyle Index" },
];

type ChartPoint = CityOpportunityRow & {
  id: string;
  product: string;
  xRaw: number;
  xScore: number;
  yScore: number;
  sizeValue: number;
};

function bubbleRadius(value: number, min: number, max: number): number {
  if (max <= min) return (MIN_BUBBLE_R + MAX_BUBBLE_R) / 2;
  const ratio = (value - min) / (max - min);
  return MIN_BUBBLE_R + ratio * (MAX_BUBBLE_R - MIN_BUBBLE_R);
}

function xRawValue(row: CityOpportunityRow, axis: CityXAxis): number {
  if (axis === "pain_index") return row.pain_index_score ?? 0;
  return row.lifestyle_index_score ?? 0;
}

function xAxisLabel(axis: CityXAxis, spread: boolean): string {
  const base = CITY_X_DIMENSIONS.find((d) => d.id === axis)?.label ?? "X";
  return spread ? `${base} (spread) →` : `${base} →`;
}

function buildByProductMap(
  byProduct?: Record<string, CityOpportunityRow[]>,
  fallback?: CityOpportunityRow[],
): Record<string, CityOpportunityRow[]> {
  if (byProduct && Object.keys(byProduct).length > 0) {
    return byProduct;
  }

  const grouped: Record<string, CityOpportunityRow[]> = {};
  for (const row of fallback ?? []) {
    const product = row.product ?? row.top_product;
    if (!product) continue;
    if (!grouped[product]) grouped[product] = [];
    grouped[product].push({ ...row, product });
  }

  const out: Record<string, CityOpportunityRow[]> = {};
  for (const [product, rows] of Object.entries(grouped)) {
    out[product] = [...rows]
      .sort((a, b) => b.revenue - a.revenue)
      .slice(0, TOP_CITY_PER_PRODUCT);
  }
  return out;
}

function CityBubbleTooltip({
  active,
  payload,
}: {
  active?: boolean;
  payload?: { payload: ChartPoint }[];
}) {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  return (
    <div className="rounded-lg border border-[var(--cios-border)] bg-white p-3 text-xs shadow-lg">
      <p className="text-sm font-semibold text-gray-900">{d.city}</p>
      <div className="mt-2 space-y-1 text-[var(--cios-secondary)]">
        <p>
          <span className="font-medium text-gray-700">Product Target:</span> {displayProductLabel(d.product)}
        </p>
        <p>
          <span className="font-medium text-gray-700">Total Address Revenue:</span> {formatCurrency(d.revenue)}
        </p>
        <p>
          <span className="font-medium text-gray-700">Opportunity Score:</span> {Math.round(d.opportunity_score)}
        </p>
        <p>
          <span className="font-medium text-gray-700">Pain Index:</span> {Math.round(d.pain_index_score ?? 0)}
        </p>
        <p>
          <span className="font-medium text-gray-700">Lifestyle Index:</span> {Math.round(d.lifestyle_index_score ?? 0)}
        </p>
        <p>
          <span className="font-medium text-gray-700">Prospect Customers:</span> {formatNumber(d.customers)}
        </p>
        <p>
          <span className="font-medium text-gray-700">Expected Orders:</span> {formatNumber(Math.round(d.orders))}
        </p>
        <p>
          <span className="font-medium text-gray-700">Conversion:</span> {formatPercent(d.conversion)}
        </p>
        {d.purchase_power ? (
          <p>
            <span className="font-medium text-gray-700">Purchase Power:</span> {d.purchase_power}
          </p>
        ) : null}
        {d.campaign_priority ? (
          <p>
            <span className="font-medium text-gray-700">Campaign Priority:</span> {d.campaign_priority}
          </p>
        ) : null}
      </div>
    </div>
  );
}

function AxisDimensionButton({
  label,
  active,
  onSelect,
}: {
  label: string;
  active: boolean;
  onSelect: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onSelect}
      className={cn(
        "rounded-full border px-2.5 py-1 text-xs transition-colors",
        active
          ? "border-[var(--cios-primary)] bg-[var(--cios-primary-light)] font-medium text-[var(--cios-primary)]"
          : "border-[var(--cios-border)] text-[var(--cios-secondary)] hover:border-gray-300 hover:text-gray-900",
      )}
      aria-pressed={active}
    >
      {label}
    </button>
  );
}

export function RevenueByCityBubbleChart({
  data,
  dataByProduct,
  productTargets = [],
  chartHeight = DEFAULT_CHART_HEIGHT,
  className,
}: {
  data: CityOpportunityRow[];
  dataByProduct?: Record<string, CityOpportunityRow[]>;
  productTargets?: ProductTargetSummary[];
  /** Plot area height in px — match adjacent state map when side-by-side. */
  chartHeight?: number;
  className?: string;
}) {
  const [activeProduct, setActiveProduct] = useState<string | null>(null);
  const [xAxis, setXAxis] = useState<CityXAxis>("pain_index");

  const byProduct = useMemo(
    () => buildByProductMap(dataByProduct, data),
    [dataByProduct, data],
  );

  const targetByProduct = useMemo(() => buildLegendTargetMap(productTargets), [productTargets]);

  const productsWithData = useMemo(
    () => expandProductsWithStandingPromoCredit(Object.keys(byProduct)),
    [byProduct],
  );

  const allPoints = useMemo(() => {
    const rows: CityOpportunityRow[] = [];
    for (const [product, cities] of Object.entries(byProduct)) {
      for (const city of cities) {
        rows.push({ ...city, product: city.product ?? product, top_product: city.top_product ?? product });
      }
    }
    return rows;
  }, [byProduct]);

  const visibleRows = useMemo(
    () => filterScatterPointsForLegend(allPoints, activeProduct, (row) => row.city ?? "", TOP_CITY_PER_PRODUCT),
    [activeProduct, allPoints],
  );

  const maxRevenue = Math.max(...visibleRows.map((d) => d.revenue), 1);

  const chartData = useMemo(() => {
    if (!visibleRows.length) return [] as ChartPoint[];

    const normalized = visibleRows.map((d) => {
      const product = d.product ?? d.top_product ?? "Unknown";
      return {
        ...d,
        product,
        opportunity_score:
          d.opportunity_score ??
          resolveOpportunityScore(undefined, {
            revenue: d.revenue,
            maxRevenue,
            conversion: d.conversion ?? 0,
          }),
      };
    });

    const xSpread = spreadCohortPercentile(
      normalized.map((d) => ({ id: `${d.product}::${d.city}`, value: xRawValue(d, xAxis) })),
      14,
      92,
    );
    const ySpread = spreadRadarOpportunityY(
      normalized.map((d) => ({
        id: `${d.product}::${d.city}`,
        opportunityScore: d.opportunity_score,
      })),
    );

    return normalized.map((d) => {
      const id = `${d.product}::${d.city}`;
      const xRaw = xRawValue(d, xAxis);
      return {
        ...d,
        id,
        xRaw,
        xScore: xSpread.get(id) ?? xRaw,
        yScore: ySpread.get(id) ?? d.opportunity_score,
        sizeValue: Math.max(d.customers, d.revenue / 1000, 1),
      };
    });
  }, [visibleRows, maxRevenue, xAxis]);

  const xDomain = useMemo(
    () => radarYDomain(chartData.map((d) => d.xScore)),
    [chartData],
  );

  const yDomain = useMemo(() => radarYDomain(chartData.map((d) => d.yScore)), [chartData]);
  const xTicks = useMemo(() => SCORE_TICKS.filter((tick) => tick <= xDomain[1]), [xDomain]);
  const yTicks = useMemo(() => SCORE_TICKS.filter((tick) => tick <= yDomain[1]), [yDomain]);

  const sizeRange = useMemo(() => {
    const sizes = chartData.map((d) => d.sizeValue);
    if (!sizes.length) return { min: 1, max: 1 };
    return { min: Math.min(...sizes), max: Math.max(...sizes) };
  }, [chartData]);

  const toggleProduct = (product: string) => {
    setActiveProduct((current) => (current === product ? null : product));
  };

  if (!allPoints.length) {
    return <p className="text-sm text-[var(--cios-secondary)]">No city revenue data for this state.</p>;
  }

  return (
    <div className={cn("flex flex-col", className)}>
      <div className="mb-3 flex shrink-0 flex-wrap gap-1.5">
        {CITY_X_DIMENSIONS.map((option) => (
          <AxisDimensionButton
            key={option.id}
            label={option.label}
            active={xAxis === option.id}
            onSelect={() => setXAxis(option.id)}
          />
        ))}
      </div>

      <div className="shrink-0" style={{ height: chartHeight }}>
        {chartData.length === 0 ? (
          <div className="flex h-full items-center justify-center text-sm text-[var(--cios-secondary)]">
            No cities for this product filter.
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <ScatterChart margin={{ top: 12, right: 16, bottom: 32, left: 16 }}>
              <CartesianGrid strokeDasharray="3 3" horizontalValues={yTicks} verticalValues={xTicks} />
              <XAxis
                type="number"
                dataKey="xScore"
                name="X spread"
                domain={[0, xDomain[1]]}
                ticks={xTicks}
                allowDecimals={false}
                tick={{ fontSize: 10 }}
                label={{
                  value: xAxisLabel(xAxis, true),
                  position: "insideBottom",
                  offset: -12,
                  fontSize: 11,
                }}
              />
              <YAxis
                type="number"
                dataKey="yScore"
                name="Opportunity spread"
                domain={[0, yDomain[1]]}
                ticks={yTicks}
                allowDecimals={false}
                tick={{ fontSize: 11 }}
                label={{ value: "Opportunity Score (spread)", angle: -90, position: "insideLeft", fontSize: 11 }}
              />
              <Tooltip content={<CityBubbleTooltip />} cursor={{ strokeDasharray: "3 3" }} />
              <Scatter
                data={chartData}
                allowDataOverflow
                shape={(props) => {
                  const { cx, cy, payload } = props as { cx: number; cy: number; payload: ChartPoint };
                  const r = bubbleRadius(payload.sizeValue, sizeRange.min, sizeRange.max);
                  return (
                    <circle
                      cx={cx}
                      cy={cy}
                      r={r}
                      fill={productColor(activeProduct ?? payload.product)}
                      fillOpacity={activeProduct ? 0.88 : 0.78}
                      stroke="#fff"
                      strokeWidth={1.5}
                    />
                  );
                }}
              />
            </ScatterChart>
          </ResponsiveContainer>
        )}
      </div>

      <ProductChartLegend
        className="mt-auto shrink-0 pt-3"
        activeProduct={activeProduct}
        onShowAll={() => setActiveProduct(null)}
        onToggleProduct={toggleProduct}
        productsWithData={productsWithData}
        targetByProduct={targetByProduct}
      />

    </div>
  );
}
