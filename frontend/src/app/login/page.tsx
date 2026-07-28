"use client";

import { FormEvent, Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/contexts/auth-context";
import { LOGIN_MOTION_HEIGHT, LoginBrandMotion } from "@/components/auth/login-brand-motion";
import { SiteFooter } from "@/components/layout/site-footer";

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { login, session, loading } = useAuth();
  const [email, setEmail] = useState("user@company.com");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const nextPath = searchParams.get("next") || "/mission-control";

  useEffect(() => {
    if (!loading && session) {
      router.replace(nextPath);
    }
  }, [loading, session, router, nextPath]);

  if (!loading && session) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[var(--cios-background)]">
        <p className="text-sm text-[var(--cios-secondary)]">Redirecting…</p>
      </div>
    );
  }

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await login(email.trim(), password);
      router.replace(nextPath);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Sign in failed");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="flex min-h-screen flex-col bg-[var(--cios-background)]">
      <div className="flex flex-1 items-center justify-center px-4 py-10">
        <div className="w-full max-w-md">
          <div style={{ minHeight: LOGIN_MOTION_HEIGHT }} className="mb-10">
            <LoginBrandMotion />
          </div>

          <form className="space-y-4" onSubmit={onSubmit}>
            <div>
              <label
                htmlFor="email"
                className="mb-1.5 block text-xs font-medium uppercase tracking-wide text-[var(--cios-secondary)]"
              >
                Email
              </label>
              <input
                id="email"
                type="email"
                autoComplete="username"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full rounded-lg border border-[var(--cios-border)] bg-white px-3 py-2.5 text-sm shadow-sm outline-none transition-shadow focus:border-[var(--orion-accent)] focus:ring-2 focus:ring-[var(--orion-accent-light)]"
              />
            </div>
            <div>
              <label
                htmlFor="password"
                className="mb-1.5 block text-xs font-medium uppercase tracking-wide text-[var(--cios-secondary)]"
              >
                Password
              </label>
              <input
                id="password"
                type="password"
                autoComplete="current-password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full rounded-lg border border-[var(--cios-border)] bg-white px-3 py-2.5 text-sm shadow-sm outline-none transition-shadow focus:border-[var(--orion-accent)] focus:ring-2 focus:ring-[var(--orion-accent-light)]"
              />
            </div>
            {error ? <p className="text-sm text-red-600">{error}</p> : null}
            <button
              type="submit"
              disabled={submitting}
              className="w-full rounded-lg bg-[var(--orion-accent)] px-4 py-2.5 text-sm font-semibold text-white shadow-sm hover:opacity-95 disabled:opacity-60"
            >
              {submitting ? "Signing in…" : "Sign in"}
            </button>
          </form>
        </div>
      </div>
      <div className="border-t border-[var(--cios-border)] bg-white">
        <SiteFooter />
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-screen items-center justify-center text-sm text-[var(--cios-secondary)]">Loading…</div>
      }
    >
      <LoginForm />
    </Suspense>
  );
}
