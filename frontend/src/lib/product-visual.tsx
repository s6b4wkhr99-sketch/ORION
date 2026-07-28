"use client";

import type { ReactNode } from "react";
import { PRODUCT_LEGEND_ORDER, V_SERIES_PRODUCTS } from "@/lib/config";
import {
  colorProductForLegend,
  legendEntryHasData,
  M_SERIES_DISPLAY_LEGEND,
} from "@/lib/product-legend-groups";
import { cn, formatCurrency, formatNumber } from "@/lib/utils";

export const PRODUCT_COLORS: Record<string, string> = {
  "Master V9": "#BE185D",
  "Master V7": "#3B82F6",
  "Master V6": "#14B8A6",
  "Master V5": "#0EA5E9",
  "Master S4": "#059669",
  "Pause S4": "#059669",
  "Pause M10": "#C2410C",
  "Pause M6": "#F59E0B",
  "Pause M6s": "#FB923C",
  "Pause M4": "#EAB308",
  "Pause M2": "#92400E",
  default: "#64748B",
};

export type ProductTargetSummary = {
  product: string;
  expected_customers: number;
  expected_orders: number;
  expected_revenue: number;
};

export function productColor(product: string | null | undefined): string {
  if (!product) return PRODUCT_COLORS.default;
  const colorKey = colorProductForLegend(product) ?? product;
  return PRODUCT_COLORS[colorKey] ?? PRODUCT_COLORS.default;
}

function hexToRgb(hex: string): [number, number, number] | null {
  const normalized = hex.replace("#", "");
  if (normalized.length !== 6) return null;
  const r = Number.parseInt(normalized.slice(0, 2), 16);
  const g = Number.parseInt(normalized.slice(2, 4), 16);
  const b = Number.parseInt(normalized.slice(4, 6), 16);
  if ([r, g, b].some((v) => Number.isNaN(v))) return null;
  return [r, g, b];
}

function rgbToHex(r: number, g: number, b: number): string {
  return `#${[r, g, b].map((v) => Math.round(v).toString(16).padStart(2, "0")).join("")}`;
}

/** Saturated ramp for highlighting ZIPs where a product is recommended. */
export function productChoroplethColors(product: string, steps = 5): string[] {
  const base = productColor(product);
  const rgb = hexToRgb(base);
  if (!rgb) return [base];
  const [r, g, b] = rgb;
  // M10 uses a deeper ramp so it stays visible against the purple all-products baseline.
  const maxBlend = product === "Pause M10" ? 0.28 : 0.42;
  const weights = Array.from({ length: steps }, (_, i) => maxBlend - (i / Math.max(steps - 1, 1)) * maxBlend);
  return weights.map((weight) => rgbToHex(r + (255 - r) * weight, g + (255 - g) * weight, b + (255 - b) * weight));
}

export function productLegendOrder(products: Iterable<string>): string[] {
  const seen = new Set(products);
  const ordered = PRODUCT_LEGEND_ORDER.filter((product) => seen.has(product));
  for (const product of seen) {
    if (!ordered.includes(product)) ordered.push(product);
  }
  return ordered;
}

export function splitProductLegend(_products: string[]) {
  return {
    vSeries: [...V_SERIES_PRODUCTS],
    mSeries: [...M_SERIES_DISPLAY_LEGEND],
  };
}

type ProductChartLegendProps = {
  activeProduct: string | null;
  onShowAll: () => void;
  onToggleProduct: (product: string) => void;
  productsWithData: Set<string>;
  targetByProduct?: Map<string, ProductTargetSummary>;
  showAllLabel?: string;
  headerExtra?: ReactNode;
  className?: string;
};

/** Two-row product legend shared by radar, city bubble, and ZIP choropleth charts. */
export function ProductChartLegend({
  activeProduct,
  onShowAll,
  onToggleProduct,
  productsWithData,
  targetByProduct,
  showAllLabel = "Show all products",
  headerExtra,
  className,
}: ProductChartLegendProps) {
  const { vSeries, mSeries } = splitProductLegend([]);

  return (
    <div className={cn("space-y-2", className)}>
      <div className="flex flex-wrap items-center gap-2">
        <button
          type="button"
          onClick={onShowAll}
          className={cn(
            "rounded-full border px-2.5 py-1 text-xs transition-colors",
            !activeProduct
              ? "border-[var(--cios-primary)] bg-[var(--cios-primary-light)] font-medium text-[var(--cios-primary)]"
              : "border-[var(--cios-border)] text-[var(--cios-secondary)] hover:border-gray-300 hover:text-gray-900",
          )}
          aria-pressed={activeProduct ? false : true}
        >
          {showAllLabel}
        </button>
        {headerExtra}
      </div>
      <div className="flex flex-col gap-0.5">
        <div className="flex flex-wrap gap-2">
          {vSeries.map((product) => (
            <ProductTargetLegendButton
              key={product}
              product={product}
              isActive={activeProduct === product}
              hasData={legendEntryHasData(productsWithData, product)}
              dimmed={Boolean(activeProduct && activeProduct !== product)}
              target={targetByProduct?.get(product)}
              onToggle={onToggleProduct}
            />
          ))}
        </div>
        <div className="flex flex-wrap gap-2">
          {mSeries.map((product) => (
            <ProductTargetLegendButton
              key={product}
              product={product}
              isActive={activeProduct === product}
              hasData={legendEntryHasData(productsWithData, product)}
              dimmed={Boolean(activeProduct && activeProduct !== product)}
              target={targetByProduct?.get(product)}
              onToggle={onToggleProduct}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

export function ProductTargetLegendButton({
  product,
  isActive,
  hasData,
  dimmed,
  target,
  onToggle,
}: {
  product: string;
  isActive: boolean;
  hasData: boolean;
  dimmed: boolean;
  target?: ProductTargetSummary;
  onToggle: (product: string) => void;
}) {
  const showPopup = Boolean(target && hasData);

  return (
    <span className="group relative inline-flex max-w-full">
      <button
        type="button"
        onClick={() => hasData && onToggle(product)}
        disabled={!hasData}
        className={cn(
          "flex max-w-full items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs transition-colors",
          isActive
            ? "border-[var(--cios-primary)] bg-[var(--cios-primary-light)] font-medium text-[var(--cios-primary)]"
            : !hasData
              ? "border-transparent text-gray-400 opacity-60"
              : dimmed
                ? "border-transparent text-[var(--cios-secondary)] opacity-50 hover:opacity-100"
                : "border-transparent text-[var(--cios-secondary)] hover:bg-gray-100",
        )}
        aria-pressed={isActive}
      >
        <span
          className="h-2.5 w-2.5 shrink-0 rounded-full"
          style={{ background: productColor(product) }}
        />
        <span className="truncate">{product}</span>
      </button>
      {showPopup && target ? (
        <span className="pointer-events-none absolute bottom-full left-1/2 z-20 mb-1.5 hidden -translate-x-1/2 whitespace-nowrap rounded-md border border-[var(--cios-border)] bg-white px-2.5 py-1.5 text-[11px] shadow-lg group-hover:block">
          <span className="mb-0.5 block font-semibold text-gray-900">{product}</span>
          <span className="block text-[var(--cios-secondary)]">
            Prospect Customers:{" "}
            <span className="font-medium text-gray-700">{formatNumber(target.expected_customers)}</span>
          </span>
          <span className="block text-[var(--cios-secondary)]">
            Expected Revenue:{" "}
            <span className="font-medium text-gray-700">{formatCurrency(target.expected_revenue)}</span>
          </span>
          <span className="mt-0.5 block text-[10px] italic text-[var(--cios-secondary)]">
            Probability-weighted (customers × conversion × price)
          </span>
        </span>
      ) : null}
    </span>
  );
}
