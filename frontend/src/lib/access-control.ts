/** Mirrors backend `MODULE_PERMISSIONS` — keep in sync with backend/app/security/permissions.py */

export const SYSTEM_ROLES = [
  "System Administrator",
  "Marketing Manager",
  "Marketing Analyst",
  "Data Administrator",
  "Executive Viewer",
  "Read Only",
] as const;

export type SystemRole = (typeof SYSTEM_ROLES)[number];

export type PermissionModule =
  | "dashboard"
  | "upload"
  | "customer_intelligence"
  | "campaign"
  | "campaign_write"
  | "campaign_approve"
  | "forecast"
  | "export"
  | "report_import"
  | "rule_library"
  | "settings"
  | "user_administration";

const MODULE_PERMISSIONS: Record<PermissionModule, readonly SystemRole[]> = {
  dashboard: SYSTEM_ROLES,
  upload: ["System Administrator", "Data Administrator"],
  customer_intelligence: SYSTEM_ROLES,
  campaign: ["System Administrator", "Marketing Manager", "Marketing Analyst", "Executive Viewer"],
  campaign_write: ["System Administrator", "Marketing Manager"],
  campaign_approve: ["System Administrator", "Marketing Manager"],
  forecast: ["System Administrator", "Marketing Manager", "Marketing Analyst", "Executive Viewer", "Read Only"],
  export: ["System Administrator", "Marketing Manager"],
  report_import: ["System Administrator", "Marketing Manager", "Marketing Analyst", "Data Administrator"],
  rule_library: ["System Administrator"],
  settings: ["System Administrator"],
  user_administration: ["System Administrator"],
};

export function hasModule(role: string, module: PermissionModule): boolean {
  const allowed = MODULE_PERMISSIONS[module] ?? [];
  return (allowed as readonly string[]).includes(role);
}

export function modulesForRole(role: string): PermissionModule[] {
  return (Object.keys(MODULE_PERMISSIONS) as PermissionModule[]).filter((module) => hasModule(role, module));
}

/** Menu-visible modules that can be customized per user (subset of role defaults). */
export const MENU_PERMISSION_MODULES: PermissionModule[] = [
  "dashboard",
  "customer_intelligence",
  "campaign",
  "forecast",
  "upload",
  "report_import",
  "export",
  "settings",
  "user_administration",
];

export function menuModulesForRole(role: string): PermissionModule[] {
  return MENU_PERMISSION_MODULES.filter((module) => hasModule(role, module));
}

export function hasEffectiveModule(role: string, modules: string[] | undefined, module: PermissionModule): boolean {
  if (modules?.length) return modules.includes(module);
  return hasModule(role, module);
}

/** Human-readable menu labels gated by each module (for User & Access admin UI). */
export const MODULE_MENU_LABELS: Record<PermissionModule, string[]> = {
  dashboard: ["Mission Control"],
  customer_intelligence: ["Market Intelligence", "Metro Intelligence", "Opportunity Finder", "Customer Database"],
  campaign: ["Recommendation Center", "Campaign Intelligence", "Learning Center"],
  forecast: ["Commercial Simulator"],
  upload: ["Upload Center"],
  report_import: ["Buyer Upload & GAP"],
  export: ["Audience Export"],
  settings: ["Platform Health", "SKU Catalog"],
  user_administration: ["User Management"],
  campaign_write: [],
  campaign_approve: [],
  rule_library: [],
};

export function menuLabelsForRole(role: string): string[] {
  return menuLabelsForModules(menuModulesForRole(role));
}

export function menuLabelsForModules(modules: PermissionModule[]): string[] {
  const labels = new Set<string>();
  for (const module of modules) {
    for (const label of MODULE_MENU_LABELS[module]) {
      labels.add(label);
    }
  }
  return [...labels].sort((a, b) => a.localeCompare(b));
}

export const AUTH_REQUIRED = process.env.NEXT_PUBLIC_AUTH_REQUIRED === "true";

export const DEV_FALLBACK_SESSION = {
  email: "dev@local",
  name: "Dev Session",
  role: "System Administrator" as SystemRole,
};
