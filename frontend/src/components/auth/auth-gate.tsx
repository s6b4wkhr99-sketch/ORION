"use client";

import { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import { PageSkeleton } from "@/components/ui/skeleton";
import { useAuth } from "@/contexts/auth-context";
import { AUTH_REQUIRED } from "@/lib/access-control";
import { moduleForPath } from "@/lib/route-permissions";

export function AuthGate({ children }: { children: React.ReactNode }) {
  const { session, loading, canAccess } = useAuth();
  const pathname = usePathname();
  const router = useRouter();

  useEffect(() => {
    if (loading) return;
    if (AUTH_REQUIRED && !session) {
      router.replace(`/login?next=${encodeURIComponent(pathname)}`);
      return;
    }
    const module = moduleForPath(pathname);
    if (session && !canAccess(module)) {
      router.replace("/mission-control");
    }
  }, [loading, session, pathname, router, canAccess]);

  if (loading && !session) {
    return (
      <div className="min-h-screen bg-[var(--cios-background)] p-6">
        <PageSkeleton />
      </div>
    );
  }

  if (AUTH_REQUIRED && !session) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[var(--cios-background)]">
        <p className="text-sm text-[var(--cios-secondary)]">Redirecting to sign in…</p>
      </div>
    );
  }

  if (session && !canAccess(moduleForPath(pathname))) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[var(--cios-background)]">
        <p className="text-sm text-[var(--cios-secondary)]">You do not have access to this page.</p>
      </div>
    );
  }

  return <>{children}</>;
}
