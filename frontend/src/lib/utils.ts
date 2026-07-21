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
