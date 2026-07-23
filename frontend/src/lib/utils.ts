import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function normalizeZipQuery(zip: string | null | undefined): string | null {
  if (!zip) return null;
  const digits = zip.replace(/\D/g, "");
  if (!digits) return null;
  return digits.padStart(5, "0").slice(0, 5);
}

export function formatCurrency(value: number | null | undefined): string {
  if (value == null) return "—";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(value);
}

export function formatNumber(value: number | null | undefined): string {
  if (value == null) return "—";
  return new Intl.NumberFormat("en-US").format(value);
}

export function formatPercent(value: number | null | undefined, digits = 2): string {
  if (value == null) return "—";
  return `${(value * 100).toFixed(digits)}%`;
}

/** Conversion rates (0–1 decimal) often need extra precision below 1%. */
export function formatConversionRate(value: number | null | undefined): string {
  if (value == null) return "—";
  return formatConversionPercentValue(value * 100);
}

/** Format a percent magnitude (0.00025 → "0.00025%"). */
export function formatConversionPercentValue(percent: number | null | undefined): string {
  if (percent == null) return "—";
  if (percent >= 1) return `${percent.toFixed(2)}%`;
  const formatted = percent.toFixed(6).replace(/(\.\d*?[1-9])0+$/, "$1").replace(/\.0+$/, "");
  return `${formatted}%`;
}

/** UI percent input (0.00025 = 0.00025%) → decimal rate for API (0.0000025). */
export function parseConversionRateInput(value: string): number | undefined {
  const parsed = parseOptionalDecimal(value);
  if (parsed == null) return undefined;
  return parsed / 100;
}

/** Decimal rate from API → percent magnitude for UI display/input. */
export function conversionRateToPercentInput(decimalRate: number | null | undefined): string {
  if (decimalRate == null) return "";
  const percent = decimalRate * 100;
  if (percent >= 1) return percent.toFixed(2);
  return percent.toFixed(6).replace(/(\.\d*?[1-9])0+$/, "$1").replace(/\.0+$/, "");
}

export function parseOptionalDecimal(value: string): number | undefined {
  const trimmed = value.trim();
  if (!trimmed) return undefined;
  const parsed = Number(trimmed);
  return Number.isFinite(parsed) ? parsed : undefined;
}

/** Predicted conversion is a rate (0–1), not expected order count. */
export function resolvePredictedConversionRate(data: {
  conversion_rate?: number | null;
  predicted_conversion_rate?: number | null;
  expected_orders?: number | null;
  expected_conversion?: number | null;
  targetable_customers?: number | null;
  total_customers?: number | null;
}): number {
  if (data.predicted_conversion_rate != null) return data.predicted_conversion_rate;
  if (data.conversion_rate != null) return data.conversion_rate;
  const customers = data.targetable_customers || data.total_customers || 0;
  const orders = data.expected_orders ?? data.expected_conversion ?? 0;
  if (customers > 0 && orders > 0 && orders <= 1) return orders;
  if (customers > 0 && orders > 1) return orders / customers;
  return 0;
}

/** Eastern Time — matches backend APP_TIMEZONE (America/New_York). */
export const APP_TIMEZONE = "America/New_York";

export function parseAppDate(value: string | null | undefined): Date | null {
  if (!value) return null;
  const text = value.trim();
  const iso = /[zZ]|[+-]\d{2}:\d{2}$/.test(text) ? text : `${text}Z`;
  const date = new Date(iso);
  return Number.isNaN(date.getTime()) ? null : date;
}

export function formatDateTimeEST(
  value: string | Date | null | undefined,
  options?: Intl.DateTimeFormatOptions,
): string {
  const date = typeof value === "string" ? parseAppDate(value) : value ?? null;
  if (!date) return "—";
  return new Intl.DateTimeFormat("en-US", {
    timeZone: APP_TIMEZONE,
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
    timeZoneName: "short",
    ...options,
  }).format(date);
}

export function formatMonthDayEST(value: string | Date | null | undefined): string {
  const date = typeof value === "string" ? parseAppDate(value) : value ?? null;
  if (!date) return "—";
  return new Intl.DateTimeFormat("en-US", {
    timeZone: APP_TIMEZONE,
    month: "short",
    day: "numeric",
  }).format(date);
}
