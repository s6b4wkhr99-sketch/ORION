export type MetricInfo = {
  title: string;
  lines: string[];
};

export const METRIC_INFO: Record<string, MetricInfo> = {
  expectedRevenue: {
    title: "Expected Revenue",
    lines: [
      "Probability-weighted forecast — not gross potential.",
      "= prospect customers × expected conversion rate × product price",
      "(equivalently: expected orders × price).",
      "It already discounts for who is likely to convert, so it is far lower than revenue if every prospect purchased.",
    ],
  },
};

export const EXPECTED_REVENUE_INFO = METRIC_INFO.expectedRevenue;
