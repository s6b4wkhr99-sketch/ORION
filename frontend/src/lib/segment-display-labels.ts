/** Human-readable labels for intelligence segment codes shown in Opportunity Finder donuts. */

export const CERAGEM_TIER_ORDER = ["High", "Mid-High", "Mid", "Mid-Low", "Low", "Unclassified"] as const;

const CERAGEM_TIER_DESCRIPTIONS: Record<string, string> = {
  High: "High purchase-power tier (Ceragem High+)",
  "Mid-High": "Upper-mid purchase-power tier (Ceragem Mid-High+)",
  Mid: "Core mid purchase-power tier (Ceragem Mid+)",
  "Mid-Low": "Lower-mid purchase-power tier (Ceragem Mid-Low+)",
  Low: "Value / opportunity tier (Ceragem Low+)",
  Unclassified: "Ceragem tier could not be resolved",
};

export const PRIZM_SEGMENT_ORDER = [
  "Established Elite",
  "Suburban Sophisticates",
  "Booming with Confidence",
  "Kids and Cul-de-Sacs",
  "Wellness Seekers",
  "Aging in Place",
  "Caregiving Households",
  "Simple Life",
  "Unclassified",
] as const;

const PRIZM_DESCRIPTIONS: Record<string, string> = {
  "Established Elite": "Premium established households",
  "Suburban Sophisticates": "Affluent suburban households",
  "Booming with Confidence": "Growing affluent households",
  "Kids and Cul-de-Sacs": "Family suburban households",
  "Wellness Seekers": "Health and wellness focused",
  "Aging in Place": "Senior aging households",
  "Caregiving Households": "Caregiver households",
  "Simple Life": "Value-focused households",
  Unknown: "Unclassified PRIZM proxy",
  Unclassified: "Unclassified PRIZM proxy",
};

const INDEX_BAND_DESCRIPTIONS: Record<string, string> = {
  High: "Top index band (≥75%)",
  Medium: "Mid index band (45–74%)",
  Low: "Lower index band (<45%)",
};

const LIFESTYLE_DESCRIPTIONS: Record<string, string> = {
  High: "High lifestyle orientation index",
  Medium: "Medium lifestyle orientation index",
  Low: "Lower lifestyle orientation index",
};

const PURCHASE_POWER_DESCRIPTIONS: Record<string, string> = {
  High: "High purchase power index (≥75%)",
  Medium: "Mid purchase power index (45–74%)",
  Low: "Lower purchase power index (<45%)",
};

export type SegmentDisplay = {
  title: string;
  subtitle?: string;
};

export function ceragemSegmentDisplay(raw: string): SegmentDisplay {
  const code = (raw || "").trim();
  if (!code) return { title: "Unclassified", subtitle: CERAGEM_TIER_DESCRIPTIONS.Unclassified };
  const subtitle = CERAGEM_TIER_DESCRIPTIONS[code];
  if (subtitle) return { title: code, subtitle };
  return { title: code, subtitle: CERAGEM_TIER_DESCRIPTIONS.Unclassified };
}

export function prizmSegmentDisplay(raw: string): SegmentDisplay {
  const code = (raw || "").trim();
  if (!code || code === "Unclassified" || code === "Unknown" || /^[A-D]$/.test(code)) {
    return { title: "Unclassified", subtitle: PRIZM_DESCRIPTIONS.Unclassified };
  }
  const description = PRIZM_DESCRIPTIONS[code];
  if (description) return { title: code, subtitle: description };
  return { title: "Unclassified", subtitle: PRIZM_DESCRIPTIONS.Unclassified };
}

export function indexBandDisplay(raw: string): SegmentDisplay {
  const code = (raw || "").trim();
  if (!code) return { title: "Unclassified" };
  return { title: code, subtitle: INDEX_BAND_DESCRIPTIONS[code] };
}

export function lifestyleBandDisplay(raw: string): SegmentDisplay {
  const code = (raw || "").trim();
  if (!code) return { title: "Unclassified" };
  return { title: code, subtitle: LIFESTYLE_DESCRIPTIONS[code] ?? INDEX_BAND_DESCRIPTIONS[code] };
}

export function purchasePowerBandDisplay(raw: string): SegmentDisplay {
  const code = (raw || "").trim();
  if (!code) return { title: "Unclassified" };
  return { title: code, subtitle: PURCHASE_POWER_DESCRIPTIONS[code] ?? INDEX_BAND_DESCRIPTIONS[code] };
}

export function segmentDisplayForDimension(dimension: string, raw: string): SegmentDisplay {
  if (dimension === "ceragem") return ceragemSegmentDisplay(raw);
  if (dimension === "prizm") return prizmSegmentDisplay(raw);
  if (dimension === "lifestyle") return lifestyleBandDisplay(raw);
  if (dimension === "purchase_power") return purchasePowerBandDisplay(raw);
  return indexBandDisplay(raw);
}

export function segmentLegendOrder(dimension: string, labels: string[]): string[] {
  if (dimension === "ceragem") {
    const order = new Map(CERAGEM_TIER_ORDER.map((label, index) => [label, index]));
    return [...labels].sort((a, b) => (order.get(a) ?? 99) - (order.get(b) ?? 99) || a.localeCompare(b));
  }
  if (dimension === "prizm") {
    const order = new Map(PRIZM_SEGMENT_ORDER.map((label, index) => [label, index]));
    return [...labels].sort((a, b) => (order.get(a) ?? 99) - (order.get(b) ?? 99) || a.localeCompare(b));
  }
  const indexOrder = new Map(["High", "Medium", "Low"].map((label, index) => [label, index]));
  if (
    dimension === "lifestyle" ||
    dimension === "pain_index" ||
    dimension === "purchase_power" ||
    dimension === "brand_familiarity"
  ) {
    return [...labels].sort((a, b) => (indexOrder.get(a) ?? 99) - (indexOrder.get(b) ?? 99) || a.localeCompare(b));
  }
  return [...labels].sort((a, b) => a.localeCompare(b));
}
