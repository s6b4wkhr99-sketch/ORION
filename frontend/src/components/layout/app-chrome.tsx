"use client";

import { useState } from "react";
import {
  Activity,
  BarChart3,
  Calculator,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  Compass,
  Crosshair,
  Database,
  Download,
  GraduationCap,
  Home,
  Map,
  Package,
  Settings,
  ShoppingCart,
  Sparkles,
  Upload,
  Users,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { APP_NAME, APP_TAGLINE, getPrimaryNav, type NavItem } from "@/lib/config";
import type { PermissionModule } from "@/lib/access-control";
import { useAuth } from "@/contexts/auth-context";
import { cn } from "@/lib/utils";

function userInitials(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (!parts.length) return "U";
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return `${parts[0][0] ?? ""}${parts[1][0] ?? ""}`.toUpperCase();
}

const ICONS: Record<string, React.ComponentType<{ className?: string }>> = {
  Home,
  Database,
  Map,
  Crosshair,
  Compass,
  Sparkles,
  Download,
  BarChart3,
  GraduationCap,
  Settings,
  Upload,
  Activity,
  Package,
  Calculator,
  ShoppingCart,
  Users,
};

function isNavActive(pathname: string, href: string): boolean {
  // Exact match only — child routes live under /admin/* and must not highlight Platform Health.
  if (href === "/mission-control" || href === "/admin") return pathname === href;
  return pathname === href || pathname.startsWith(`${href}/`);
}

function isItemOrChildActive(pathname: string, item: NavItem): boolean {
  if (isNavActive(pathname, item.href)) return true;
  return item.children?.some((child) => isNavActive(pathname, child.href)) ?? false;
}

type SidebarProps = {
  collapsed: boolean;
  onToggle: () => void;
  className?: string;
};

export function Sidebar({ collapsed, onToggle, className }: SidebarProps) {
  const pathname = usePathname();
  const { session, logout } = useAuth();
  const navItems = getPrimaryNav(
    session?.role ?? "System Administrator",
    session?.modules as PermissionModule[] | undefined,
    session?.allowedMenus,
  );
  const [adminOpen, setAdminOpen] = useState(
    () => pathname.startsWith("/admin") || pathname.startsWith("/import") || pathname.startsWith("/export"),
  );

  return (
    <aside
      className={cn(
        "relative flex h-full flex-col bg-[var(--cios-nav-bg)] text-[var(--cios-nav-text)] transition-all duration-200",
        collapsed ? "w-[var(--nav-collapsed-width)]" : "w-[var(--nav-width)]",
        className,
      )}
    >
      <div className={cn("border-b border-white/10 px-5 py-6", collapsed && "px-2 text-center")}>
        <Link href="/mission-control" className={cn("block", collapsed && "flex justify-center")}>
          {!collapsed ? (
            <div>
              <p className="text-xl font-bold tracking-tight text-white">{APP_NAME}</p>
              <p className="mt-0.5 text-[11px] text-slate-400">{APP_TAGLINE}</p>
            </div>
          ) : (
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-[var(--orion-accent)] text-sm font-bold text-white">
              O
            </div>
          )}
        </Link>
      </div>

      <nav className="flex-1 overflow-y-auto px-3 py-4">
        {navItems.map((item) => {
          const Icon = ICONS[item.icon] ?? Home;
          const active = isItemOrChildActive(pathname, item);
          const isMissionControl = item.href === "/mission-control";

          if (item.children?.length) {
            return (
              <div key={item.href} className="mb-1">
                <button
                  type="button"
                  onClick={() => setAdminOpen((v) => !v)}
                  title={collapsed ? item.label : undefined}
                  className={cn(
                    "flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition-colors",
                    active
                      ? "bg-[var(--cios-nav-active)]/20 font-medium text-white"
                      : "text-slate-400 hover:bg-[var(--cios-nav-hover)] hover:text-white",
                    collapsed && "justify-center px-2",
                  )}
                >
                  <Icon className="h-[18px] w-[18px] shrink-0" />
                  {!collapsed && (
                    <>
                      <span className="flex-1 text-left">{item.label}</span>
                      <ChevronDown className={cn("h-4 w-4 transition-transform", adminOpen && "rotate-180")} />
                    </>
                  )}
                </button>
                {!collapsed && adminOpen && (
                  <div className="ml-4 mt-1 space-y-0.5 border-l border-white/10 pl-3">
                    {item.children.map((child) => {
                      const ChildIcon = ICONS[child.icon] ?? Settings;
                      const childActive = isNavActive(pathname, child.href);
                      return (
                        <Link
                          key={child.href}
                          href={child.href}
                          className={cn(
                            "flex items-center gap-2 rounded-lg px-3 py-2 text-sm transition-colors",
                            childActive
                              ? "bg-[var(--cios-nav-active)] font-medium text-white"
                              : "text-slate-400 hover:bg-[var(--cios-nav-hover)] hover:text-white",
                          )}
                        >
                          <ChildIcon className="h-4 w-4 shrink-0" />
                          <span>{child.label}</span>
                        </Link>
                      );
                    })}
                  </div>
                )}
              </div>
            );
          }

          return (
            <Link
              key={item.href}
              href={item.href}
              title={collapsed ? item.label : undefined}
              className={cn(
                "mb-1 flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition-colors",
                active
                  ? isMissionControl
                    ? "orion-nav-active font-medium text-white"
                    : "bg-[var(--cios-nav-active)] font-medium text-white"
                  : "text-slate-400 hover:bg-[var(--cios-nav-hover)] hover:text-white",
                collapsed && "justify-center px-2",
              )}
            >
              <Icon className="h-[18px] w-[18px] shrink-0" />
              {!collapsed && <span>{item.label}</span>}
            </Link>
          );
        })}
      </nav>

      <div className={cn("border-t border-white/10 p-3", collapsed && "px-2")}>
        {!collapsed ? (
          <div className="flex items-center gap-3 rounded-lg px-2 py-2">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-[var(--orion-accent)] text-xs font-bold text-white">
              {userInitials(session?.name ?? "User")}
            </div>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium text-white">{session?.name ?? "User"}</p>
              <p className="truncate text-xs text-slate-400">{session?.role ?? "—"}</p>
            </div>
            <button
              type="button"
              onClick={onToggle}
              className="rounded p-1 text-slate-400 hover:bg-white/10 hover:text-white"
              aria-label="Collapse navigation"
            >
              <ChevronLeft className="h-4 w-4" />
            </button>
          </div>
        ) : (
          <button
            type="button"
            onClick={onToggle}
            className="mx-auto flex h-8 w-8 items-center justify-center rounded-lg text-slate-400 hover:bg-white/10 hover:text-white"
            aria-label="Expand navigation"
          >
            <ChevronRight className="h-4 w-4" />
          </button>
        )}
        {!collapsed ? (
          <button
            type="button"
            onClick={logout}
            className="mt-2 w-full rounded-lg px-2 py-2 text-left text-xs text-slate-400 hover:bg-white/10 hover:text-white"
          >
            Sign out
          </button>
        ) : null}
      </div>
    </aside>
  );
}

export function Header() {
  return null;
}

export function Footer() {
  return null;
}
