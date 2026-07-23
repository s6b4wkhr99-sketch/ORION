import { hasModule, type PermissionModule } from "@/lib/access-control";
import { ORION_PRIMARY_NAV, SHOW_CAMPAIGN_MODULES, SHOW_CUSTOMER_DATABASE, type NavItem } from "@/lib/config";

export type NavMenuOption = {
  href: string;
  label: string;
  module: PermissionModule;
};

const HIDDEN_WHEN_ANALYSIS_ONLY = new Set(["/recommendations", "/campaigns", "/learning"]);

function deploymentNavItems(): NavItem[] {
  let nav = SHOW_CAMPAIGN_MODULES
    ? ORION_PRIMARY_NAV
    : ORION_PRIMARY_NAV.filter((item) => !HIDDEN_WHEN_ANALYSIS_ONLY.has(item.href));
  if (!SHOW_CUSTOMER_DATABASE) {
    nav = nav.filter((item) => item.href !== "/customers");
  }
  return nav;
}

/** Individual sidebar menus available for a role (for User Management admin UI). */
export function navigableMenuOptionsForRole(role: string): NavMenuOption[] {
  const options: NavMenuOption[] = [];
  for (const item of deploymentNavItems()) {
    if (item.children?.length) {
      for (const child of item.children) {
        if (child.permissionModule && hasModule(role, child.permissionModule as PermissionModule)) {
          options.push({
            href: child.href,
            label: child.label,
            module: child.permissionModule as PermissionModule,
          });
        }
      }
      continue;
    }
    if (item.permissionModule && hasModule(role, item.permissionModule as PermissionModule)) {
      options.push({
        href: item.href,
        label: item.label,
        module: item.permissionModule as PermissionModule,
      });
    }
  }
  return options;
}

export function menuHrefsForRole(role: string): string[] {
  return navigableMenuOptionsForRole(role).map((item) => item.href);
}

export function menuLabelsForHrefs(role: string, hrefs: string[]): string[] {
  const byHref = new Map(navigableMenuOptionsForRole(role).map((item) => [item.href, item.label]));
  return hrefs.map((href) => byHref.get(href)).filter((label): label is string => Boolean(label));
}

export function usesMenuHrefs(values: string[] | null | undefined): boolean {
  return Boolean(values?.length && values.some((value) => value.startsWith("/")));
}
