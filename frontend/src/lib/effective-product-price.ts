/** Effective customer payment — mirrors backend effective_customer_payment (gross × standing promo). */

const PRODUCT_GROSS_SALES: Record<string, number> = {
  "Master V9": 8199,
  "Master V7": 6999,
  "Master V6": 6399,
  "Master V5": 4799,
  "Master S4": 5499,
  "Pause M10": 9799,
  "Pause M6": 4999,
  "Pause M6s": 4799,
  "Pause M4": 3999,
};

const STANDING_PROMO_PCT: Record<string, number> = {
  "Master V6": 0.2,
  "Master V5": 0.2,
  "Master S4": 0.3,
  "Pause M10": 0.3,
  "Pause M6s": 0.2,
};

export function effectiveProductPrice(product: string): number {
  const gross = PRODUCT_GROSS_SALES[product] ?? 5500;
  const promoPct = STANDING_PROMO_PCT[product] ?? 0;
  return Math.round(gross * (1 - promoPct));
}
