/** Explicit Ceragem + PRIZM product recommendation order — mirrors backend product_ladders.py */

export const CERAGEM_PRODUCT_LADDERS: Record<string, readonly string[]> = {
  "High+ · Wellness": ["Master V9", "Master V7", "Pause M10", "Master V6"],
  "High+ · Pain Index": ["Master V7", "Master V6", "Master V5", "Master S4"],
  "Mid-High+ · Wellness": ["Master V7", "Pause M10", "Master V6", "Pause M6"],
  "Mid-High+ · Pain Index": ["Master V6", "Master V5", "Pause M6", "Master S4"],
  "Mid+ · Wellness": ["Pause M6s", "Pause M6", "Pause M4", "Pause M10"],
  "Mid+ · Pain Index": ["Master V6", "Master V5", "Master S4", "Pause M4"],
  "Mid-Low+ · Wellness": ["Pause M6s", "Pause M6", "Pause M4", "Master S4"],
  "Mid-Low+ · Pain Index": ["Master V5", "Master V6", "Master S4", "Pause M4"],
  "Low+ · Wellness": ["Master S4", "Pause M6s", "Pause M4", "Pause M10"],
  "Low+ · Pain Index": ["Master S4", "Master V5", "Pause M4", "Master V6"],
};

export const PRIZM_PRODUCT_LADDERS: Record<string, readonly string[]> = {
  "Established Elite": ["Pause M10", "Master V9", "Master V7", "Pause M6"],
  "Suburban Sophisticates": ["Master V9", "Master V7", "Pause M10", "Master V6"],
  "Booming with Confidence": ["Master V7", "Master V6", "Pause M10", "Pause M6"],
  "Kids and Cul-de-Sacs": ["Pause M6s", "Pause M6", "Pause M4", "Master S4"],
  "Wellness Seekers": ["Master V7", "Pause M6s", "Pause M6", "Master V6"],
  "Aging in Place": ["Pause M6s", "Pause M4", "Master S4", "Master V5"],
  "Caregiving Households": ["Master S4", "Pause M6s", "Pause M4", "Master V5"],
  "Simple Life": ["Master S4", "Pause M6s", "Pause M4", "Master V5"],
  Unknown: ["Pause M4", "Pause M6s", "Master S4", "Pause M6"],
};

const CERAGEM_TIER_ORDER = ["High+", "Mid-High+", "Mid+", "Mid-Low+", "Low+"] as const;

function parseCeragemTier(segment: string): string {
  const text = segment.trim();
  if (text.includes(" · ")) return text.split(" · ")[0]?.trim() ?? text;
  if (text.includes(" + ")) {
    const legacy = text.split(" + ")[0]?.trim() ?? text;
    if (legacy.endsWith("+")) return legacy;
    return `${legacy}+`;
  }
  if (text.endsWith("+")) return text;
  return `${text}+`;
}

function parseCeragemAxis(segment: string): string {
  const text = segment.trim();
  if (text.includes(" · ")) {
    const axis = text.split(" · ")[1]?.trim() ?? "";
    return axis === "Pain Index" || axis === "Wellness" ? axis : "Wellness";
  }
  if (text.includes(" + ")) {
    const axis = text.split(" + ")[1]?.trim() ?? "";
    return axis === "Pain Index" || axis === "Wellness" ? axis : "Wellness";
  }
  return "Wellness";
}

export function ceragemLadderKey(segment: string): string {
  return `${parseCeragemTier(segment)} · ${parseCeragemAxis(segment)}`;
}

export function ladderForCeragem(segment: string): string[] {
  const key = ceragemLadderKey(segment);
  return [...(CERAGEM_PRODUCT_LADDERS[key] ?? CERAGEM_PRODUCT_LADDERS["Mid-Low+ · Wellness"])];
}

export function ladderForPrizm(prizm: string | null | undefined): string[] {
  const key = !prizm || prizm === "Unclassified" || prizm === "" ? "Unknown" : prizm;
  return [...(PRIZM_PRODUCT_LADDERS[key] ?? PRIZM_PRODUCT_LADDERS.Unknown)];
}

export function mergeLadderWithObserved(
  ladder: string[],
  topRecommended: string[] | undefined,
  limit = 6,
): string[] {
  const result: string[] = [];
  const seen = new Set<string>();
  for (const product of [...ladder, ...(topRecommended ?? [])]) {
    if (!product || seen.has(product)) continue;
    seen.add(product);
    result.push(product);
    if (result.length >= limit) break;
  }
  return result;
}

export function ceragemSegmentSortKey(segment: string): [number, number, string] {
  const tier = parseCeragemTier(segment);
  const tierIdx = CERAGEM_TIER_ORDER.indexOf(tier as (typeof CERAGEM_TIER_ORDER)[number]);
  const axis = parseCeragemAxis(segment);
  const axisIdx = axis === "Pain Index" ? 0 : axis === "Wellness" ? 1 : 2;
  return [tierIdx >= 0 ? tierIdx : 99, axisIdx, segment];
}
