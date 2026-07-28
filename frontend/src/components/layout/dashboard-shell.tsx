"use client";

import { useEffect, useState } from "react";
import { Menu, X } from "lucide-react";
import { usePathname } from "next/navigation";
import { FilterProvider, FiltersReadyGate } from "@/contexts/filter-context";
import { AuthGate } from "@/components/auth/auth-gate";
import { ToastProvider } from "@/components/ui/toast";
import { cn } from "@/lib/utils";
import { APP_NAME } from "@/lib/config";
import { Footer, Sidebar } from "./app-chrome";

export function DashboardShell({ children }: { children: React.ReactNode }) {
  const [navCollapsed, setNavCollapsed] = useState(false);
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const pathname = usePathname();

  useEffect(() => {
    setMobileNavOpen(false);
  }, [pathname]);

  useEffect(() => {
    if (!mobileNavOpen) return;
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") setMobileNavOpen(false);
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [mobileNavOpen]);

  return (
    <AuthGate>
      <FilterProvider>
        <ToastProvider>
        <div className="min-h-screen bg-[var(--cios-background)]">
          <div
            className={cn(
              "fixed left-0 top-0 z-50 hidden h-screen lg:block",
              navCollapsed ? "w-[var(--nav-collapsed-width)]" : "w-[var(--nav-width)]",
            )}
          >
            <Sidebar collapsed={navCollapsed} onToggle={() => setNavCollapsed((v) => !v)} />
          </div>

          {mobileNavOpen && (
            <button
              type="button"
              className="fixed inset-0 z-50 bg-black/50 lg:hidden"
              aria-label="Close navigation menu"
              onClick={() => setMobileNavOpen(false)}
            />
          )}

          <div
            className={cn(
              "fixed left-0 top-0 z-[60] h-screen w-[var(--nav-width)] transition-transform duration-200 lg:hidden",
              mobileNavOpen ? "translate-x-0" : "-translate-x-full",
            )}
          >
            <Sidebar collapsed={false} onToggle={() => setMobileNavOpen(false)} />
          </div>

          <main
            className={cn(
              "min-h-screen transition-all duration-200",
              navCollapsed ? "lg:pl-[var(--nav-collapsed-width)]" : "lg:pl-[var(--nav-width)]",
            )}
          >
            <div className="sticky top-0 z-40 flex items-center gap-3 border-b border-[var(--cios-border)] bg-[var(--cios-surface)] px-4 py-3 lg:hidden">
              <button
                type="button"
                onClick={() => setMobileNavOpen((open) => !open)}
                className="cios-btn inline-flex items-center justify-center rounded-lg border border-[var(--cios-border)] p-2 text-gray-700"
                aria-label={mobileNavOpen ? "Close menu" : "Open menu"}
              >
                {mobileNavOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
              </button>
              <div className="min-w-0">
                <p className="truncate text-sm font-semibold text-gray-900">{APP_NAME}</p>
                <p className="truncate text-xs text-[var(--cios-secondary)]">Campaign Decision Intelligence</p>
              </div>
            </div>
            <div className="mx-auto max-w-[1600px] p-4 sm:p-6">
              <FiltersReadyGate>{children}</FiltersReadyGate>
            </div>
            <Footer />
          </main>
        </div>
        </ToastProvider>
      </FilterProvider>
    </AuthGate>
  );
}
