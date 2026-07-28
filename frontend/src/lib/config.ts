export const APP_NAME = "ORION";
export const APP_TAGLINE = "Campaign Decision Intelligence";
export const APP_VERSION = "1.4.0";

import { hasModule, type PermissionModule } from "@/lib/access-control";

export const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "";

/** ORION UX Blueprint Part 02 — mandatory workflow navigation (SCR-001–008) */
export type NavItem = {
  href: string;
  label: string;
  icon: string;
  screenId?: string;
  /** RBAC module — user must have this permission to see the item. */
  permissionModule?: import("@/lib/access-control").PermissionModule;
  children?: NavItem[];
};

/** Flat primary navigation — order is mandatory per ORION Constitution + mockup */
export const ORION_PRIMARY_NAV: NavItem[] = [
  { href: "/mission-control", label: "Mission Control", icon: "Home", screenId: "SCR-001", permissionModule: "dashboard" },
  { href: "/market-intelligence", label: "Market Intelligence", icon: "Map", screenId: "SCR-003", permissionModule: "customer_intelligence" },
  { href: "/metro-intelligence", label: "Metro Intelligence", icon: "Compass", permissionModule: "customer_intelligence" },
  { href: "/opportunities", label: "Opportunity Finder", icon: "Crosshair", screenId: "SCR-002", permissionModule: "customer_intelligence" },
  { href: "/customers", label: "Customer Database", icon: "Database", permissionModule: "customer_intelligence" },
  { href: "/recommendations", label: "Recommendation Center", icon: "Sparkles", screenId: "SCR-004", permissionModule: "campaign" },
  { href: "/campaigns", label: "Campaign Intelligence", icon: "BarChart3", screenId: "SCR-006", permissionModule: "campaign" },
  { href: "/learning", label: "Learning Center", icon: "GraduationCap", screenId: "SCR-007", permissionModule: "campaign" },
  {
    href: "/admin",
    label: "Administration",
    icon: "Settings",
    screenId: "SCR-008",
    children: [
      { href: "/admin/catalog", label: "SKU Catalog", icon: "Package", permissionModule: "settings" },
      { href: "/import", label: "Upload Center", icon: "Upload", permissionModule: "upload" },
      { href: "/export", label: "Audience Export", icon: "Download", screenId: "SCR-005", permissionModule: "export" },
      { href: "/buyer-import", label: "Buyer Upload & GAP", icon: "ShoppingCart", permissionModule: "report_import" },
      { href: "/admin/users", label: "User Management", icon: "Users", permissionModule: "user_administration" },
      { href: "/commercial-simulator", label: "Commercial Simulator", icon: "Calculator", permissionModule: "forecast" },
      { href: "/admin", label: "Platform Health", icon: "Activity", permissionModule: "settings" },
    ],
  },
];

/** Flat list for backward compatibility */
export const NAV_ITEMS = ORION_PRIMARY_NAV.flatMap((item) => (item.children ? [item, ...item.children] : [item]));

/** Hide campaign workflow screens (customer-analysis-only deployments). */
export const SHOW_CAMPAIGN_MODULES = process.env.NEXT_PUBLIC_SHOW_CAMPAIGN_MODULES === "true";

/** Individual customer browse screen — off by default for lightweight ORION deployments. */
export const SHOW_CUSTOMER_DATABASE = process.env.NEXT_PUBLIC_SHOW_CUSTOMER_DATABASE === "true";

const HIDDEN_WHEN_ANALYSIS_ONLY = new Set(["/recommendations", "/campaigns", "/learning"]);

export function filterNavByAllowedMenus(items: NavItem[], allowedMenus: string[]): NavItem[] {
  const allowed = new Set(allowedMenus);
  return items.flatMap((item) => {
    if (item.children?.length) {
      const children = filterNavByAllowedMenus(item.children, allowedMenus);
      if (!children.length) return [];
      return [{ ...item, children }];
    }
    if (!allowed.has(item.href)) return [];
    return [item];
  });
}

export function filterNavByModules(items: NavItem[], modules: PermissionModule[]): NavItem[] {
  const allowed = new Set(modules);
  return items.flatMap((item) => {
    if (item.children?.length) {
      const children = filterNavByModules(item.children, modules);
      if (!children.length) return [];
      return [{ ...item, children }];
    }
    if (item.permissionModule && !allowed.has(item.permissionModule as PermissionModule)) {
      return [];
    }
    return [item];
  });
}

export function filterNavByRole(items: NavItem[], role: string): NavItem[] {
  return items.flatMap((item) => {
    if (item.children?.length) {
      const children = filterNavByRole(item.children, role);
      if (!children.length) return [];
      return [{ ...item, children }];
    }
    if (item.permissionModule && !hasModule(role, item.permissionModule as PermissionModule)) {
      return [];
    }
    return [item];
  });
}

export function getPrimaryNav(
  role = "System Administrator",
  modules?: PermissionModule[],
  allowedMenus?: string[] | null,
): NavItem[] {
  let nav = SHOW_CAMPAIGN_MODULES ? ORION_PRIMARY_NAV : ORION_PRIMARY_NAV.filter((item) => !HIDDEN_WHEN_ANALYSIS_ONLY.has(item.href));
  if (!SHOW_CUSTOMER_DATABASE) {
    nav = nav.filter((item) => item.href !== "/customers");
  }
  if (allowedMenus?.length && allowedMenus[0]?.startsWith("/")) {
    return filterNavByAllowedMenus(nav, allowedMenus);
  }
  if (modules?.length) return filterNavByModules(nav, modules);
  return filterNavByRole(nav, role);
}

export const CAMPAIGN_MODULE_ROUTES = [
  "/recommendations",
  "/campaign-center",
  "/campaigns",
  "/learning",
] as const;

/** Legacy routes redirected to ORION workflow */
export const LEGACY_REDIRECTS: Record<string, string> = {
  "/dashboard": "/mission-control",
  "/executive": "/mission-control",
  "/retail": "/market-intelligence",
  "/roi": "/mission-control",
  "/campaign-center": "/recommendations",
  "/explorer": "/market-intelligence",
  "/states": "/market-intelligence?view=state",
  "/zip": "/metro-intelligence?view=zip",
  "/products": "/opportunities",
  "/settings": "/admin",
};

export const EXPORT_PROVIDERS = [
  "Generic CSV",
  "Klaviyo",
  "Mailchimp",
  "HubSpot",
  "Attentive",
  "Salesforce Marketing Cloud",
] as const;

export const PRODUCT_OPTIONS = [
  "Master V9",
  "Master V7",
  "Master V6",
  "Master V5",
  "Master S4",
  "Pause M10",
  "Pause M6",
  "Pause M6s",
  "Pause M4",
] as const;

/** Opportunity Radar legend order — V Series then M Series */
export const PRODUCT_LEGEND_ORDER = [
  "Master V9",
  "Master V7",
  "Master V6",
  "Master V5",
  "Master S4",
  "Pause M10",
  "Pause M6",
  "Pause M6s",
  "Pause M4",
  "Pause M2",
] as const;

export function sortProductsForLegend(products: string[]): string[] {
  const order = PRODUCT_LEGEND_ORDER as readonly string[];
  return [...products].sort((a, b) => {
    const ai = order.indexOf(a);
    const bi = order.indexOf(b);
    return (ai === -1 ? 999 : ai) - (bi === -1 ? 999 : bi);
  });
}

/** Master V line (chart legend row 1). Master S4 is V-line value entry with SAVE30 promo. */
export const V_SERIES_PRODUCTS = [
  "Master V9",
  "Master V7",
  "Master V6",
  "Master V5",
  "Master S4",
] as const;

export const M_SERIES_PRODUCTS = ["Pause M10", "Pause M6", "Pause M6s", "Pause M4"] as const;

export type ProductSeriesFilter = "all" | "v" | "m";

export function productBelongsToSeries(product: string, series: ProductSeriesFilter): boolean {
  if (series === "all") return true;
  if (series === "v") return product.startsWith("Master V") || product === "Master S4";
  return product.startsWith("Pause M");
}

export function productsForSeries(series: ProductSeriesFilter): readonly string[] {
  if (series === "v") return V_SERIES_PRODUCTS;
  if (series === "m") return M_SERIES_PRODUCTS;
  return PRODUCT_LEGEND_ORDER;
}

export const PRIZM_SEGMENTS = [
  "Established Elite",
  "Suburban Sophisticates",
  "Booming with Confidence",
  "Kids and Cul-de-Sacs",
  "Wellness Seekers",
  "Aging in Place",
  "Caregiving Households",
  "Simple Life",
  "Unknown",
] as const;

export const CERAGEM_SEGMENTS = [
  "High + Wellness",
  "High + Pain Index",
  "Mid-High + Wellness",
  "Mid-High + Pain Index",
  "Mid-Low + Wellness",
  "Mid-Low + Pain Index",
] as const;

export const INDEX_LEVELS = ["High", "Medium", "Low"] as const;

/** Traditional US massage-chair demand concentration (DC grouped with VA). */
export const PRIORITY_MARKET_STATES = [
  "CA",
  "TX",
  "FL",
  "NY",
  "NJ",
  "VA",
  "DC",
  "IL",
  "PA",
  "MA",
] as const;

export const M10_PREMIUM_STATES = ["CA", "NY", "NJ", "VA", "DC"] as const;
export const S4_VALUE_STATES = ["FL", "TX"] as const;

export const DESIGN = {
  primary: "#0056D2",
  secondary: "#4A4A4A",
  background: "#F7F9FC",
  surface: "#FFFFFF",
  border: "#E5E7EB",
} as const;
