/**
 * Client-side dashboard cache — single version bumps invalidate all CIOS menu caches.
 * Keep in sync with backend EXECUTIVE_DASHBOARD_BUILD_VERSION after policy changes.
 */
export const DASHBOARD_CLIENT_CACHE_VERSION = "2026-07-conservative-promo-reach-v4";

const VERSION_KEY = "cios:dashboard-cache-version";
const KEY_PREFIX = `cios:v${DASHBOARD_CLIENT_CACHE_VERSION}:`;

export function ensureDashboardCacheGeneration(): void {
  if (typeof window === "undefined") return;
  try {
    const stored = localStorage.getItem(VERSION_KEY);
    if (stored === DASHBOARD_CLIENT_CACHE_VERSION) return;
    for (let i = sessionStorage.length - 1; i >= 0; i -= 1) {
      const key = sessionStorage.key(i);
      if (key?.startsWith("cios:")) {
        sessionStorage.removeItem(key);
      }
    }
    localStorage.setItem(VERSION_KEY, DASHBOARD_CLIENT_CACHE_VERSION);
  } catch {
    // ignore storage errors
  }
}

export function dashboardCacheKey(namespace: string, ...parts: Array<string | number | null | undefined>): string {
  const suffix = parts.map((part) => String(part ?? "all")).join(":");
  return `${KEY_PREFIX}${namespace}:${suffix}`;
}

export function readDashboardCache<T>(key: string, maxAgeMs?: number): T | null {
  try {
    const raw = sessionStorage.getItem(key);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as T | { savedAt?: number; data?: T };
    if (parsed && typeof parsed === "object" && "data" in parsed) {
      const envelope = parsed as { savedAt?: number; data?: T };
      if (maxAgeMs && envelope.savedAt && Date.now() - envelope.savedAt > maxAgeMs) {
        return null;
      }
      return envelope.data ?? null;
    }
    return parsed as T;
  } catch {
    return null;
  }
}

export function writeDashboardCache(key: string, value: unknown): void {
  try {
    sessionStorage.setItem(key, JSON.stringify({ savedAt: Date.now(), data: value }));
  } catch {
    // ignore quota errors
  }
}

export function clearDashboardCaches(): void {
  if (typeof window === "undefined") return;
  try {
    for (let i = sessionStorage.length - 1; i >= 0; i -= 1) {
      const key = sessionStorage.key(i);
      if (key?.startsWith("cios:")) {
        sessionStorage.removeItem(key);
      }
    }
    localStorage.removeItem(VERSION_KEY);
  } catch {
    // ignore
  }
}
