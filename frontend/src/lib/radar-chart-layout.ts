/** Shared Opportunity / Purchase radar scatter plot layout. */

export const RADAR_MIN_BUBBLE_R = 10;
export const RADAR_MAX_BUBBLE_R = 38;

/** Room for largest bubble radius + stroke so SVG plot clip does not cut high-score points. */
export const RADAR_CHART_MARGIN = {
  top: RADAR_MAX_BUBBLE_R + 14,
  right: RADAR_MAX_BUBBLE_R + 14,
  bottom: 32,
  left: RADAR_MAX_BUBBLE_R + 28,
};

/** Score axis labels — 20–100 at 20-point steps; origin (0) stays unlabeled. */
export const RADAR_SCORE_AXIS_TICKS = [20, 40, 60, 80, 100] as const;

/** Max state bubbles per SKU on Purchase Radar. */
export const PURCHASE_RADAR_TOP_STATE_COUNT = 15;

/**
 * ResponsiveContainer width:height.
 * Mission Control Opportunity Radar reads ~2:1 (Y axis visually shorter than X).
 */
export const RADAR_PLOT_ASPECT_RATIO = 2.05;
