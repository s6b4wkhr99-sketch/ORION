export type RadarXAxis = "lifestyle" | "purchase_power" | "pain_index" | "digital" | "brand";

export type RadarSpreadPoint = {
  state: string;
  lifestyleScore: number;
  purchasePowerScore: number;
  digitalScore: number;
  painIndexScore: number;
  brandScore: number;
};

/** Axes that use percentile cohort spread for horizontal discrimination on the radar. */
export const RADAR_SPREAD_X_AXES = new Set<RadarXAxis>(["lifestyle", "purchase_power", "digital"]);

const SPREAD_FLOOR = 14;
const SPREAD_CEILING = 92;

const AXIS_SCORE_KEY: Record<
  Extract<RadarXAxis, "lifestyle" | "purchase_power" | "digital">,
  keyof Pick<RadarSpreadPoint, "lifestyleScore" | "purchasePowerScore" | "digitalScore">
> = {
  lifestyle: "lifestyleScore",
  purchase_power: "purchasePowerScore",
  digital: "digitalScore",
};

const ALL_AXIS_SCORE_KEY: Record<RadarXAxis, keyof RadarSpreadPoint> = {
  lifestyle: "lifestyleScore",
  purchase_power: "purchasePowerScore",
  pain_index: "painIndexScore",
  digital: "digitalScore",
  brand: "brandScore",
};

/**
 * Stretch axis scores across unique states in the visible cohort using percentile ranks.
 * All products in the same state share one x-position (state-level intelligence).
 */
export function spreadRadarStateAxis(
  points: RadarSpreadPoint[],
  axis: Extract<RadarXAxis, "lifestyle" | "purchase_power" | "digital">,
): Map<string, number> {
  const scoreKey = AXIS_SCORE_KEY[axis];
  const stateRaw = new Map<string, number>();

  for (const point of points) {
    if (!stateRaw.has(point.state)) {
      stateRaw.set(point.state, Number(point[scoreKey] ?? 0));
    }
  }

  const entries = [...stateRaw.entries()].sort((a, b) => a[1] - b[1] || a[0].localeCompare(b[0]));
  const result = new Map<string, number>();

  if (entries.length <= 1) {
    const mid = (SPREAD_FLOOR + SPREAD_CEILING) / 2;
    for (const [state] of entries) result.set(state, mid);
    return result;
  }

  const span = SPREAD_CEILING - SPREAD_FLOOR;
  entries.forEach(([state], rank) => {
    const ratio = rank / (entries.length - 1);
    result.set(state, Math.round((SPREAD_FLOOR + ratio * span) * 10) / 10);
  });

  return result;
}

export function radarXScore(point: RadarSpreadPoint, axis: RadarXAxis, spreadMap: Map<string, number> | null): number {
  if (spreadMap?.has(point.state)) {
    return spreadMap.get(point.state)!;
  }
  return Number(point[ALL_AXIS_SCORE_KEY[axis]] ?? 0);
}

/** Minimum data-unit inset so bubble centers are not pinned to the plot edge. */
const DOMAIN_BUBBLE_PAD = 12;
const DOMAIN_SOFT_OVERFLOW = 22;

function radarPlotDomain(
  scores: number[],
  softMin = 0,
  softMax = 100,
): [number, number] {
  if (scores.length === 0) return [softMin, softMax];

  const max = Math.max(...scores);
  const min = Math.min(...scores);
  const span = max - min;
  const topPad = Math.max(DOMAIN_BUBBLE_PAD, span * 0.16);
  const hi = Math.ceil(max + topPad);

  // Always anchor axes at 0 so X/Y intersect at the origin; chart margins handle bubble bleed.
  return [
    softMin,
    Math.max(softMax, Math.min(softMax + DOMAIN_SOFT_OVERFLOW, hi)),
  ];
}

export function radarXDomain(scores: number[], axis: RadarXAxis): [number, number] {
  return radarPlotDomain(scores, 0, 100);
}

const Y_SPREAD_FLOOR = 16;
const Y_SPREAD_CEILING = 94;

/** Percentile-rank spread so a tight cohort remains visually discriminable on scatter axes. */
export function spreadCohortPercentile(
  points: { id: string; value: number }[],
  floor = Y_SPREAD_FLOOR,
  ceiling = Y_SPREAD_CEILING,
): Map<string, number> {
  const sorted = [...points].sort((a, b) => a.value - b.value || a.id.localeCompare(b.id));
  const result = new Map<string, number>();

  if (sorted.length <= 1) {
    const mid = (floor + ceiling) / 2;
    for (const point of sorted) result.set(point.id, mid);
    return result;
  }

  const span = ceiling - floor;
  sorted.forEach((point, rank) => {
    const ratio = rank / (sorted.length - 1);
    result.set(point.id, Math.round((floor + ratio * span) * 10) / 10);
  });

  return result;
}

/** Percentile-rank spread for Opportunity Score (Y-axis) within the visible cohort. */
export function spreadRadarOpportunityY(
  points: { id: string; opportunityScore: number }[],
): Map<string, number> {
  return spreadCohortPercentile(
    points.map((point) => ({ id: point.id, value: point.opportunityScore })),
    Y_SPREAD_FLOOR,
    Y_SPREAD_CEILING,
  );
}

export function radarYDomain(yScores: number[]): [number, number] {
  return radarPlotDomain(yScores, 0, 100);
}
