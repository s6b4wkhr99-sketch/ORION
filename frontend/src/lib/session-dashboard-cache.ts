/** @deprecated Use `@/lib/dashboard-cache` — re-exported for backward compatibility. */
export {
  readDashboardCache as readSessionCache,
  writeDashboardCache as writeSessionCache,
  dashboardCacheKey,
  ensureDashboardCacheGeneration,
  clearDashboardCaches,
  DASHBOARD_CLIENT_CACHE_VERSION,
} from "@/lib/dashboard-cache";
