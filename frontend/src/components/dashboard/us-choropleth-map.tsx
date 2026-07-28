"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { ComposableMap, Geographies, Geography } from "react-simple-maps";
import { scaleQuantile } from "d3-scale";
import { STATE_NAME_TO_ABBR } from "@/data/us-state-names";
import { cn, formatCurrency, formatPercent } from "@/lib/utils";

const GEO_URL = "https://cdn.jsdelivr.net/npm/us-atlas@3/states-10m.json";

const MAP_POPUP_AUTO_HIDE_MS = 2000;
const MAP_POPUP_FADE_MS = 300;
const MAP_WIDTH = 800;
/** Reference canvas for d3 geoAlbersUsa defaults (975×610, scale 1300). */
const ALBERS_USA_REF = { width: 975, height: 610, scale: 1300 };

function albersUsaProjectionConfig(mapWidth: number, mapHeight: number) {
  const fitScale = Math.min(mapWidth / ALBERS_USA_REF.width, mapHeight / ALBERS_USA_REF.height);
  // Inset AK/HI and southern FL need breathing room — scale down slightly inside the viewport.
  const padding = 0.88;
  return {
    scale: ALBERS_USA_REF.scale * fitScale * padding,
    translate: [mapWidth / 2, mapHeight * 0.52] as [number, number],
  };
}

const CHOROPLETH_COLORS_OPPORTUNITY = ["#DBEAFE", "#93C5FD", "#3B82F6", "#1D4ED8", "#1E3A8A"] as const;
/** Actual purchases — teal scale (distinct from opportunity blues). */
const CHOROPLETH_COLORS_PURCHASES = ["#CCFBF1", "#5EEAD4", "#14B8A6", "#0F766E", "#115E59"] as const;
const NO_DATA_COLOR = "#F3F4F6";
const MULTI_SELECTED_FILL = "#D946EF";

const VARIANT_STYLES = {
  opportunity: {
    colors: CHOROPLETH_COLORS_OPPORTUNITY,
    emptyFill: "#E8F0FE",
    hoverFill: "#0056D2",
    pressedFill: "#0041A3",
  },
  purchases: {
    colors: CHOROPLETH_COLORS_PURCHASES,
    emptyFill: "#ECFDF5",
    hoverFill: "#0D9488",
    pressedFill: "#0F766E",
  },
} as const;

type StateDatum = {
  state: string;
  revenue: number;
  orders?: number;
  customers?: number;
  conversion?: number;
};

type UsChoroplethMapProps = {
  data: StateDatum[];
  onStateClick?: (state: string) => void;
  /** Highlight the currently selected state */
  selectedState?: string | null;
  /** Multi-select mode — highlight all selected states */
  selectedStates?: string[];
  /** Toggle state in multi-select mode */
  multiSelect?: boolean;
  /** Map height in px — default 300; used as minimum when `fill` is true */
  mapHeight?: number;
  /** Grow map to fill the flex parent (measures container via ResizeObserver) */
  fill?: boolean;
  /** Center map within widget */
  centered?: boolean;
  /**
   * Tailwind max-width class(es) for the centered container. Accepts responsive variants
   * (e.g. "max-w-2xl xl:max-w-4xl") so the map can grow on larger screens. Only used when
   * `centered` is true. Defaults to "max-w-2xl".
   */
  centerMaxWidthClass?: string;
  /** Tailwind classes for the gradient legend block below the map. */
  legendClassName?: string;
  /** Opportunity (expected revenue) vs actual purchase counts */
  variant?: "opportunity" | "purchases";
};

export function UsChoroplethMap({
  data,
  onStateClick,
  selectedState,
  selectedStates,
  multiSelect = false,
  mapHeight = 300,
  fill = false,
  centered = false,
  centerMaxWidthClass = "max-w-2xl",
  legendClassName = "mt-4 sm:mt-6",
  variant = "opportunity",
}: UsChoroplethMapProps) {
  const [displayState, setDisplayState] = useState<StateDatum | null>(null);
  const [popupVisible, setPopupVisible] = useState(false);
  const [filledHeight, setFilledHeight] = useState(mapHeight);
  const plotRef = useRef<HTMLDivElement | null>(null);
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
      setDisplayState(null);
      fadeOutTimerRef.current = null;
    }, MAP_POPUP_FADE_MS);
  }, [clearPopupTimers]);

  const showPopup = useCallback(
    (state: StateDatum) => {
      clearPopupTimers();
      setDisplayState(state);
      requestAnimationFrame(() => setPopupVisible(true));
      autoHideTimerRef.current = setTimeout(() => {
        autoHideTimerRef.current = null;
        hidePopup();
      }, MAP_POPUP_AUTO_HIDE_MS);
    },
    [clearPopupTimers, hidePopup],
  );

  useEffect(() => () => clearPopupTimers(), [clearPopupTimers]);

  useEffect(() => {
    if (!fill || !plotRef.current) return;
    const element = plotRef.current;
    const observer = new ResizeObserver(([entry]) => {
      const next = Math.floor(entry.contentRect.height);
      if (next > 0) setFilledHeight(Math.max(mapHeight, next));
    });
    observer.observe(element);
    return () => observer.disconnect();
  }, [fill, mapHeight]);

  const effectiveMapHeight = fill ? filledHeight : mapHeight;

  const byState = useMemo(() => {
    const map = new Map<string, StateDatum>();
    for (const row of data) {
      map.set(row.state.toUpperCase(), row);
    }
    return map;
  }, [data]);

  const variantStyle = VARIANT_STYLES[variant];

  const { colorScale, hasLegend } = useMemo(() => {
    const palette = VARIANT_STYLES[variant];
    const values = data
      .map((d) => (variant === "purchases" ? (d.orders ?? d.revenue) : d.revenue))
      .filter((v) => v > 0);
    if (!values.length) {
      return {
        colorScale: () => palette.emptyFill,
        hasLegend: false,
      };
    }
    return {
      colorScale: scaleQuantile<string>().domain(values).range([...palette.colors]),
      hasLegend: true,
    };
  }, [data, variant]);

  const projectionConfig = useMemo(
    () => albersUsaProjectionConfig(MAP_WIDTH, effectiveMapHeight),
    [effectiveMapHeight],
  );

  if (!data.length && !multiSelect) {
    return (
      <p className="text-sm text-[var(--cios-secondary)]">
        {variant === "purchases" ? "No purchase data by state." : "No state revenue data for the selected upload."}
      </p>
    );
  }

  const widthClass = centered ? `mx-auto w-full ${centerMaxWidthClass}` : "w-full";

  const mapBody = (
    <div className={`${widthClass} flex min-h-0 flex-1 flex-col`}>
      <div
        ref={fill ? plotRef : undefined}
        className={
          fill
            ? "relative flex min-h-0 flex-1 items-center justify-center overflow-visible px-1 pb-1 pt-0.5"
            : "relative overflow-visible px-1 pb-1 pt-0.5"
        }
        style={fill ? { minHeight: mapHeight } : undefined}
      >
        <ComposableMap
          projection="geoAlbersUsa"
          projectionConfig={projectionConfig}
          width={MAP_WIDTH}
          height={effectiveMapHeight}
          className="mx-auto block h-auto w-full max-w-full"
        >
          <Geographies geography={GEO_URL}>
            {({ geographies }) =>
              geographies.map((geo) => {
                const name = String((geo.properties as { name?: string }).name ?? "");
                const abbr = STATE_NAME_TO_ABBR[name] ?? "";
                const row = abbr ? byState.get(abbr.toUpperCase()) : undefined;
                const metricValue =
                  variant === "purchases" ? (row?.orders ?? row?.revenue ?? 0) : (row?.revenue ?? 0);
                const isSelected =
                  selectedState != null && abbr.toUpperCase() === selectedState.toUpperCase()
                    ? true
                    : multiSelect && selectedStates?.some((s) => s.toUpperCase() === abbr.toUpperCase());
                const stateCode = row?.state ?? abbr;
                const popupRow: StateDatum = row ?? {
                  state: stateCode,
                  revenue: 0,
                  customers: 0,
                  orders: 0,
                  conversion: 0,
                };
                const defaultFill =
                  isSelected && multiSelect
                    ? MULTI_SELECTED_FILL
                    : metricValue > 0
                      ? colorScale(metricValue)
                      : NO_DATA_COLOR;
                return (
                  <Geography
                    key={geo.rsmKey}
                    geography={geo}
                    onMouseEnter={() => abbr && showPopup(popupRow)}
                    onMouseLeave={hidePopup}
                    onClick={() => {
                      if (!abbr) return;
                      if (!multiSelect && !row) return;
                      onStateClick?.(stateCode);
                    }}
                    style={{
                      default: {
                        fill: defaultFill,
                        stroke: "#FFFFFF",
                        strokeWidth: isSelected ? 1 : 0.6,
                        outline: "none",
                      },
                      hover: {
                        fill: isSelected && multiSelect ? "#C026D3" : variantStyle.hoverFill,
                        outline: "none",
                        cursor: abbr ? "pointer" : "default",
                      },
                      pressed: {
                        fill: isSelected && multiSelect ? "#86198F" : variantStyle.pressedFill,
                        outline: "none",
                      },
                    }}
                  />
                );
              })
            }
          </Geographies>
        </ComposableMap>

        {displayState && (
          <div
            className={`pointer-events-none absolute right-2 top-2 rounded-lg border border-[var(--cios-border)] bg-white p-3 text-xs shadow-lg transition-opacity ${
              popupVisible ? "opacity-100" : "opacity-0"
            }`}
            style={{ transitionDuration: `${MAP_POPUP_FADE_MS}ms` }}
          >
            <p className="font-semibold text-gray-900">{displayState.state}</p>
            {variant === "purchases" ? (
              <>
                <p className="mt-1 text-[var(--cios-secondary)]">
                  Purchases:{" "}
                  <span className="font-medium text-gray-700">
                    {(displayState.orders ?? displayState.revenue ?? 0).toLocaleString()}
                  </span>
                </p>
                {displayState.customers != null && (
                  <p className="mt-1 text-[var(--cios-secondary)]">
                    Unique buyers:{" "}
                    <span className="font-medium text-gray-700">{displayState.customers.toLocaleString()}</span>
                  </p>
                )}
              </>
            ) : (
              <>
                {displayState.customers != null && (
                  <p className="mt-1 text-[var(--cios-secondary)]">
                    Prospect Customers:{" "}
                    <span className="font-medium text-gray-700">{displayState.customers.toLocaleString()}</span>
                  </p>
                )}
                <p className="mt-1 text-[var(--cios-secondary)]">
                  Expected Revenue:{" "}
                  <span className="font-medium text-gray-700">{formatCurrency(displayState.revenue)}</span>
                </p>
                <p className="mt-0.5 text-[10px] italic text-[var(--cios-secondary)]">
                  Probability-weighted (customers × conversion × price)
                </p>
                {displayState.orders != null && (
                  <p className="mt-1 text-[var(--cios-secondary)]">
                    Orders: {Math.round(displayState.orders).toLocaleString()}
                  </p>
                )}
                {displayState.conversion != null && (
                  <p className="mt-1 text-[var(--cios-secondary)]">
                    Conversion: {formatPercent(displayState.conversion)}
                  </p>
                )}
              </>
            )}
          </div>
        )}
      </div>

      {hasLegend && (
        <div className={cn(legendClassName, (centered || fill) && "flex flex-col items-center")}>
          {multiSelect && selectedStates?.length ? (
            <p className="mb-2 flex items-center gap-2 text-[10px] text-gray-700">
              <span className="inline-block h-2.5 w-4 rounded-sm" style={{ background: MULTI_SELECTED_FILL }} />
              Selected states ({selectedStates.length})
            </p>
          ) : null}
          <p className="mb-1 text-[10px] font-medium text-gray-700">
            {variant === "purchases" ? "Purchase volume" : "Expected Opportunity"}
          </p>
          {/* Bar and Low/High labels share ONE fixed-width wrapper so they always keep identical
              bounds and stay aligned on every device (no reliance on matching per-element caps). */}
          <div className="w-40 max-w-full">
            <div
              className="h-2 w-full rounded-sm"
              style={{
                background: `linear-gradient(to right, ${variantStyle.colors.join(", ")})`,
              }}
            />
            <div className="mt-1 flex w-full justify-between text-[9px] text-[var(--cios-secondary)]">
              <span>Low</span>
              <span>High</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );

  if (centered || fill) {
    return <div className="flex h-full min-h-0 w-full flex-1 flex-col">{mapBody}</div>;
  }

  return mapBody;
}
