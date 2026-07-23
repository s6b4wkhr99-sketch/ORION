import type { PermissionModule } from "@/lib/access-control";

/** Dashboard routes gated by RBAC module (longest prefix wins). */
export const ROUTE_PERMISSIONS: { prefix: string; module: PermissionModule }[] = [
  { prefix: "/admin/users", module: "user_administration" },
  { prefix: "/admin/catalog", module: "settings" },
  { prefix: "/admin", module: "settings" },
  { prefix: "/import", module: "upload" },
  { prefix: "/buyer-import", module: "report_import" },
  { prefix: "/export", module: "export" },
  { prefix: "/commercial-simulator", module: "forecast" },
  { prefix: "/recommendations", module: "campaign" },
  { prefix: "/campaigns", module: "campaign" },
  { prefix: "/learning", module: "campaign" },
  { prefix: "/customers", module: "customer_intelligence" },
  { prefix: "/market-intelligence", module: "customer_intelligence" },
  { prefix: "/metro-intelligence", module: "customer_intelligence" },
  { prefix: "/opportunities", module: "customer_intelligence" },
  { prefix: "/mission-control", module: "dashboard" },
];

export function moduleForPath(pathname: string): PermissionModule {
  const match = ROUTE_PERMISSIONS.find(
    (entry) => pathname === entry.prefix || pathname.startsWith(`${entry.prefix}/`),
  );
  return match?.module ?? "dashboard";
}
