/**
 * Standing-promo legend credit — display layer only.
 * Backend API payloads stay per intelligence SKU; charts credit outreach / donor SKUs
 * so promo legends (V6, V5, S4, M6s, M10) light up when adjacent lines carry demand.
 */

/** Mission Control outreach mapping (intelligence SKU → standing promo SKU). */
export const STANDING_PROMO_OUTREACH_MAP: Record<string, string> = {
  "Master V9": "Master V6",
  "Master V7": "Master V6",
  "Master S4": "Master S4",
  "Pause M4": "Master S4",
  "Pause M6": "Pause M10",
  "Pause M6s": "Pause M10",
};

/** Synthetic promo demand donors (mirrors backend STANDING_PROMO_DEMAND_DONORS). */
export const STANDING_PROMO_DEMAND_DONORS: Record<string, readonly string[]> = {
  "Master V6": ["Master V7", "Master S4", "Master V9"],
  "Master V5": ["Master S4", "Master V7"],
  "Master S4": ["Pause M4", "Master V5"],
  "Pause M6s": ["Pause M6", "Pause M4"],
  "Pause M10": ["Master V9", "Master V7", "Pause M6", "Pause M6s"],
};

const OUTREACH_DONORS_BY_PROMO = new Map<string, Set<string>>();

for (const [donor, promo] of Object.entries(STANDING_PROMO_OUTREACH_MAP)) {
  if (donor === promo) continue;
  const set = OUTREACH_DONORS_BY_PROMO.get(promo) ?? new Set<string>();
  set.add(donor);
  OUTREACH_DONORS_BY_PROMO.set(promo, set);
}

for (const [promo, donors] of Object.entries(STANDING_PROMO_DEMAND_DONORS)) {
  const set = OUTREACH_DONORS_BY_PROMO.get(promo) ?? new Set<string>();
  donors.forEach((donor) => set.add(donor));
  OUTREACH_DONORS_BY_PROMO.set(promo, set);
}

/** SKUs whose primary recommendation rolls into a standing-promo legend entry. */
export function standingPromoCreditSkus(label: string): string[] {
  const donors = OUTREACH_DONORS_BY_PROMO.get(label);
  if (!donors?.size) return [label];
  return [label, ...donors];
}

/** Promo SKUs that may borrow donor geos when direct rows are below chart minimums. */
export const STANDING_PROMO_DONOR_DERIVED_PRODUCTS = [
  "Master V6",
  "Master V5",
  "Master S4",
  "Pause M10",
] as const;

/** Donor SKUs that roll into a standing-promo legend entry (excludes the promo SKU itself). */
export function standingPromoDonorSkus(label: string): readonly string[] {
  const donors = OUTREACH_DONORS_BY_PROMO.get(label);
  return donors ? [...donors] : [];
}

/** Expand a raw product set so promo SKUs appear when donors have data. */
export function expandProductsWithStandingPromoCredit(raw: Iterable<string>): Set<string> {
  const expanded = new Set(raw);
  for (const sku of raw) {
    const outreach = STANDING_PROMO_OUTREACH_MAP[sku];
    if (outreach) expanded.add(outreach);
  }
  for (const [promo, donors] of OUTREACH_DONORS_BY_PROMO) {
    for (const donor of donors) {
      if (expanded.has(donor)) expanded.add(promo);
    }
  }
  return expanded;
}
