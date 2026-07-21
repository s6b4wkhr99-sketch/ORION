"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { ComposableMap, Geographies, Geography } from "react-simple-maps";
import { scaleQuantile } from "d3-scale";
import { geoAlbersUsa, geoPath, type ExtendedFeatureCollection } from "d3-geo";
import { api, type ZctaChoropleth } from "@/lib/api";
import { useFilters } from "@/contexts/filter-context";
import {
  buildLegendTargetMap,
  directProductMetrics,
  displayProductLabel,
  PAUSE_M6_GROUP_LABEL,
} from "@/lib/product-legend-groups";
import { dashboardCacheKey } from "@/lib/dashboard-cache";
import {
  ProductChartLegend,
  productChoroplethColors,
  productColor,
  type ProductTargetSummary,
} from "@/lib/product-visual";
import { readSessionCache, writeSessionCache } from "@/lib/session-dashboard-cache";
import { formatCurrency, formatNumber } from "@/lib/utils";

function zctaCacheKey(
  uploadId: string | null | undefined,
  state: string,
  cbsa: string | null | undefined,
  revision: number,
) {
  return dashboardCacheKey("zcta", uploadId, cbsa ?? state, revision);
}

// Base projection width; the SVG scales responsively to the card via CSS (w-full).
const BASE_MAP_WIDTH = 800;

const COUNTIES_GEO = "https://cdn.jsdelivr.net/npm/us-atlas@3/counties-10m.json";
const CHOROPLETH_COLORS = ["#EDE9FE", "#C4B5FD", "#8B5CF6", "#6D28D9", "#4C1D95"] as const;
const NO_DATA_COLOR = "#F3F4F6";
/** ZIPs with revenue but not for the active product — avoids purple masquerading as product color. */
const PRODUCT_INACTIVE_FILL = "#E5E7EB";
const POPUP_MS = 2000;

type ZipProductMetrics = {
  expected_revenue?: number;
  target_customers?: number;
};

type ZipChoroplethMapProps = {
  state: string;
  cbsa?: string | null;
  uploadId?: string | null;
  onZipClick?: (zip: string) => void;
  mapHeight?: number;
  productTargets?: ProductTargetSummary[];
};

function revenueByProduct(props: Record<string, unknown>): Record<string, ZipProductMetrics> {
  const raw = props.revenue_by_product;
  if (!raw || typeof raw !== "object") return {};
  return raw as Record<string, ZipProductMetrics>;
}

function displayMetrics(props: Record<string, unknown>, activeLegend: string | null) {
  if (!activeLegend) {
    return {
      revenue: Number(props.expected_revenue ?? 0),
      customers: Number(props.target_customers ?? 0),
    };
  }
  return directProductMetrics(revenueByProduct(props), activeLegend);
}

function hasProductRevenue(props: Record<string, unknown>, activeProduct: string): boolean {
  return displayMetrics(props, activeProduct).revenue > 0;
}

function fillForZip(
  props: Record<string, unknown>,
  activeProduct: string | null,
  allProductsScale: (value: number) => string,
  productScale: ((value: number) => string) | null,
): string {
  const totalRevenue = Number(props.expected_revenue ?? 0);

  if (activeProduct) {
    const productRevenue = displayMetrics(props, activeProduct).revenue;
    if (productRevenue > 0 && productScale) return productScale(productRevenue);
    if (totalRevenue <= 0) return NO_DATA_COLOR;
    return PRODUCT_INACTIVE_FILL;
  }

  if (totalRevenue <= 0) return NO_DATA_COLOR;
  return allProductsScale(totalRevenue);
}

function hoverFill(props: Record<string, unknown>, activeProduct: string | null): string {
  if (activeProduct && hasProductRevenue(props, activeProduct)) return productColor(activeProduct);
  if (Number(props.expected_revenue ?? 0) > 0) return "#6366F1";
  return NO_DATA_COLOR;
}

function pressedFill(props: Record<string, unknown>, activeProduct: string | null): string {
  if (activeProduct && hasProductRevenue(props, activeProduct)) return productColor(activeProduct);
  if (Number(props.expected_revenue ?? 0) > 0) return "#4338CA";
  return NO_DATA_COLOR;
}

export function ZipChoroplethMap({
  state,
  cbsa,
  uploadId,
  onZipClick,
  mapHeight = 480,
  productTargets = [],
}: ZipChoroplethMapProps) {
  const { dataRevision } = useFilters();
  const [geo, setGeo] = useState<ZctaChoropleth | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeProduct, setActiveProduct] = useState<string | null>(null);
  const [hover, setHover] = useState<Record<string, unknown> | null>(null);
  const [visible, setVisible] = useState(false);
  const [pos, setPos] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const containerRef = useRef<HTMLDivElement | null>(null);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    setActiveProduct(null);
    const key = zctaCacheKey(uploadId, state, cbsa, dataRevision);
    const cached = readSessionCache<ZctaChoropleth>(key);
    if (cached) {
      setGeo(cached);
      setLoading(false);
    } else {
      setLoading(true);
    }

    let cancelled = false;
    const request = cbsa
      ? api.getMetroZctaChoropleth(cbsa, uploadId ?? undefined)
      : api.getZctaChoropleth(state, uploadId ?? undefined);
    request
      .then((next) => {
        if (cancelled) return;
        setGeo(next);
        writeSessionCache(key, next);
      })
      .catch(console.error)
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [state, cbsa, uploadId, dataRevision]);

  const productsWithData = useMemo(() => {
    const found = new Set<string>();
    for (const feature of geo?.features ?? []) {
      for (const [product, metrics] of Object.entries(revenueByProduct(feature.properties ?? {}))) {
        if (Number(metrics.expected_revenue ?? 0) > 0) {
          found.add(product);
        }
      }
    }
    // Choropleth legend reflects map payload only (not Mission Control KPI donor credit).
    const out = new Set(found);
    if (found.has("Pause M6") || found.has("Pause M6s")) {
      out.add(PAUSE_M6_GROUP_LABEL);
    }
    return out;
  }, [geo]);

  const targetByProduct = useMemo(() => buildLegendTargetMap(productTargets), [productTargets]);

  const totalRevenueValues = useMemo(
    () =>
      (geo?.features ?? [])
        .map((f) => Number(((f.properties ?? {}) as Record<string, unknown>).expected_revenue ?? 0))
        .filter((v) => v > 0),
    [geo],
  );

  const productRevenueValues = useMemo(
    () =>
      activeProduct
        ? (geo?.features ?? [])
            .map((f) => displayMetrics((f.properties ?? {}) as Record<string, unknown>, activeProduct).revenue)
            .filter((v) => v > 0)
        : [],
    [geo, activeProduct],
  );

  const allProductsColorScale = useMemo(() => {
    if (!totalRevenueValues.length) return () => NO_DATA_COLOR;
    return scaleQuantile<string>().domain(totalRevenueValues).range([...CHOROPLETH_COLORS]);
  }, [totalRevenueValues]);

  const productColorScale = useMemo(() => {
    if (!activeProduct || !productRevenueValues.length) return null;
    return scaleQuantile<string>()
      .domain(productRevenueValues)
      .range(productChoroplethColors(activeProduct));
  }, [activeProduct, productRevenueValues]);

  const { projection, mapWidth, mapHeight: fittedHeight } = useMemo(() => {
    const hasPolygons = geo?.meta.geometry_source === "zcta500k" && Boolean(geo.features[0]?.geometry);
    if (!geo || !hasPolygons) {
      return { projection: "geoAlbersUsa" as const, mapWidth: BASE_MAP_WIDTH, mapHeight };
    }
    const collection = geo as unknown as ExtendedFeatureCollection;
    const measure = geoAlbersUsa().scale(1).translate([0, 0]);
    const [[x0, y0], [x1, y1]] = geoPath(measure).bounds(collection);
    const spanX = x1 - x0 || 1;
    const spanY = y1 - y0 || 1;
    const height = Math.min(1600, Math.max(600, Math.round(BASE_MAP_WIDTH * (spanY / spanX))));
    const proj = geoAlbersUsa().fitSize([BASE_MAP_WIDTH, height], collection);
    return { projection: proj, mapWidth: BASE_MAP_WIDTH, mapHeight: height };
  }, [geo, mapHeight]);

  const showHover = useCallback((props: Record<string, unknown>) => {
    if (timerRef.current) clearTimeout(timerRef.current);
    setHover(props);
    requestAnimationFrame(() => setVisible(true));
    timerRef.current = setTimeout(() => {
      setVisible(false);
      setTimeout(() => setHover(null), 250);
    }, POPUP_MS);
  }, []);

  useEffect(
    () => () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    },
    [],
  );

  const toggleProduct = (product: string) => {
    setActiveProduct((current) => (current === product ? null : product));
  };

  if (loading) return <p className="text-sm text-[var(--cios-secondary)]">Loading ZIP heatmap…</p>;
  if (!geo?.features.length) {
    return (
      <p className="text-sm text-[var(--cios-secondary)]">
        No ZIP-level data for {cbsa ? "this metro" : state}. Select an area with customer coverage.
      </p>
    );
  }

  const useZctaPolygons = geo.meta.geometry_source === "zcta500k" && geo.features[0]?.geometry;

  const onMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    setPos({ x: e.clientX - rect.left, y: e.clientY - rect.top });
  };

  const hoverMetrics = hover
    ? activeProduct && hasProductRevenue(hover, activeProduct)
      ? displayMetrics(hover, activeProduct)
      : {
          revenue: Number(hover.expected_revenue ?? 0),
          customers: Number(hover.target_customers ?? 0),
        }
    : null;

  return (
    <div className="space-y-3">
      <div ref={containerRef} className="relative" onMouseMove={onMouseMove}>
        <ComposableMap projection={projection} width={mapWidth} height={fittedHeight} className="mx-auto h-auto w-full max-w-full">
          {useZctaPolygons ? (
            <Geographies geography={geo}>
              {({ geographies }) =>
                geographies.map((g) => {
                  const props = (g.properties ?? {}) as Record<string, unknown>;
                  const zip = String(props.zip ?? g.id ?? "");
                  const fill = fillForZip(props, activeProduct, allProductsColorScale, productColorScale);
                  const interactive = Number(props.expected_revenue ?? 0) > 0;
                  const highlighted = Boolean(activeProduct && hasProductRevenue(props, activeProduct));
                  return (
                    <Geography
                      key={g.rsmKey}
                      geography={g}
                      onMouseEnter={() => interactive && showHover(props)}
                      onClick={() => zip && onZipClick?.(zip)}
                      style={{
                        default: {
                          fill,
                          stroke: "#fff",
                          strokeWidth: highlighted ? 0.45 : 0.25,
                          outline: "none",
                        },
                        hover: {
                          fill: hoverFill(props, activeProduct),
                          outline: "none",
                          cursor: interactive ? "pointer" : "default",
                        },
                        pressed: {
                          fill: pressedFill(props, activeProduct),
                          outline: "none",
                        },
                      }}
                    />
                  );
                })
              }
            </Geographies>
          ) : (
            <Geographies geography={COUNTIES_GEO}>
              {({ geographies }) =>
                geographies
                  .filter((g) => String((g.properties as { STATE?: string }).STATE ?? "") === stateToFips(state))
                  .map((g) => {
                    const name = String((g.properties as { name?: string }).name ?? "").toLowerCase();
                    const countyProps = byCountyProps(geo, name);
                    const fill = fillForZip(countyProps, activeProduct, allProductsColorScale, productColorScale);
                    const interactive = Number(countyProps.expected_revenue ?? 0) > 0;
                    const highlighted = Boolean(activeProduct && hasProductRevenue(countyProps, activeProduct));
                    return (
                      <Geography
                        key={g.rsmKey}
                        geography={g}
                        onMouseEnter={() => interactive && showHover(countyProps)}
                        style={{
                          default: {
                            fill,
                            stroke: "#fff",
                            strokeWidth: highlighted ? 0.55 : 0.4,
                            outline: "none",
                          },
                          hover: {
                            fill: hoverFill(countyProps, activeProduct),
                            outline: "none",
                          },
                          pressed: {
                            fill: pressedFill(countyProps, activeProduct),
                            outline: "none",
                          },
                        }}
                      />
                    );
                  })
              }
            </Geographies>
          )}
        </ComposableMap>

        {hover && hoverMetrics && hoverMetrics.revenue > 0 && (
          <div
            className={`pointer-events-none absolute z-10 w-44 rounded-lg border border-[var(--cios-border)] bg-white p-3 text-xs shadow-lg transition-opacity ${
              visible ? "opacity-100" : "opacity-0"
            }`}
            style={{
              left: Math.max(8, Math.min(pos.x + 14, (containerRef.current?.clientWidth ?? 0) - 184)),
              top: Math.max(8, pos.y + 14),
            }}
          >
            {hover.city ? (
              <p className="font-semibold text-gray-900">{String(hover.city)}</p>
            ) : hover.county ? (
              <p className="font-semibold text-gray-900">{String(hover.county)}</p>
            ) : null}
            {hover.zip ? <p className="mt-1">Key Zip Code: {String(hover.zip)}</p> : null}
            {activeProduct && hasProductRevenue(hover, activeProduct) ? (
              <p className="mt-1">
                <span className="font-medium text-gray-700">Product Target:</span> {displayProductLabel(activeProduct)}
              </p>
            ) : null}
            <p className="mt-1">Expected Revenue: {formatCurrency(hoverMetrics.revenue)}</p>
            <p>Customers: {formatNumber(hoverMetrics.customers)}</p>
            <p className="mt-0.5 text-[10px] italic text-[var(--cios-secondary)]">
              Probability-weighted (customers × conversion × price)
            </p>
          </div>
        )}
      </div>

      <ProductChartLegend
        activeProduct={activeProduct}
        onShowAll={() => setActiveProduct(null)}
        onToggleProduct={toggleProduct}
        productsWithData={productsWithData}
        targetByProduct={targetByProduct}
        headerExtra={
          activeProduct ? (
            <span className="flex items-center gap-2 text-xs text-[var(--cios-secondary)]">
              <span
                className="inline-block h-2.5 w-2.5 rounded-full"
                style={{ background: productColor(activeProduct) }}
              />
              <span>
                <span className="font-medium" style={{ color: productColor(activeProduct) }}>
                  {activeProduct}
                </span>{" "}
                ZIPs highlighted in deep orange; only affluent-ZIP M10 demand (V7/M6/M6s/M4 donors, not V9)
              </span>
            </span>
          ) : (
            <span className="text-xs text-[var(--cios-secondary)]">
              Purple gradient = total expected revenue across all products
            </span>
          )
        }
      />
    </div>
  );
}

function byCountyProps(geo: ZctaChoropleth, county: string): Record<string, unknown> {
  for (const f of geo.features ?? []) {
    const props = f.properties ?? {};
    const key = String(props.county ?? props.name ?? f.id ?? "").toLowerCase();
    if (key === county) return props as Record<string, unknown>;
  }
  return {};
}

const STATE_FIPS: Record<string, string> = {
  AL: "01", AK: "02", AZ: "04", AR: "05", CA: "06", CO: "08", CT: "09", DE: "10", DC: "11", FL: "12",
  GA: "13", HI: "15", ID: "16", IL: "17", IN: "18", IA: "19", KS: "20", KY: "21", LA: "22", ME: "23",
  MD: "24", MA: "25", MI: "26", MN: "27", MS: "28", MO: "29", MT: "30", NE: "31", NV: "32", NH: "33",
  NJ: "34", NM: "35", NY: "36", NC: "37", ND: "38", OH: "39", OK: "40", OR: "41", PA: "42", RI: "44",
  SC: "45", SD: "46", TN: "47", TX: "48", UT: "49", VT: "50", VA: "51", WA: "53", WV: "54", WI: "55", WY: "56",
};

function stateToFips(state: string) {
  return STATE_FIPS[state.toUpperCase()] ?? "";
}
