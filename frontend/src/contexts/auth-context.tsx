"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { api, type AuthSession } from "@/lib/api";
import { AUTH_REQUIRED, DEV_FALLBACK_SESSION, hasModule, modulesForRole, type PermissionModule } from "@/lib/access-control";

type AuthContextValue = {
  session: AuthSession | null;
  loading: boolean;
  /** True while /auth/me refreshes in the background after optimistic session hydrate. */
  refreshing: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  refreshSession: () => Promise<void>;
  canAccess: (module: PermissionModule) => boolean;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [session, setSession] = useState<AuthSession | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const refreshSession = useCallback(async () => {
    if (!api.hasStoredToken()) {
      if (AUTH_REQUIRED) {
        setSession(null);
      } else {
        setSession({
          ...DEV_FALLBACK_SESSION,
          modules: modulesForRole(DEV_FALLBACK_SESSION.role),
        });
      }
      return;
    }
    try {
      const me = await api.getAuthMe();
      const allowedMenus =
        me.allowedModules?.length && me.allowedModules[0]?.startsWith("/") ? me.allowedModules : null;
      setSession({ ...me, allowedMenus });
      api.persistSession({ ...me, allowedMenus });
    } catch {
      const stored = api.readStoredSession();
      if (stored && api.hasStoredToken()) {
        setSession(stored);
        return;
      }
      api.clearSession();
      setSession(AUTH_REQUIRED ? null : { ...DEV_FALLBACK_SESSION, modules: modulesForRole(DEV_FALLBACK_SESSION.role) });
    }
  }, []);

  useEffect(() => {
    let cancelled = false;

    if (api.hasStoredToken()) {
      const stored = api.readStoredSession();
      if (stored) {
        setSession(stored);
        setLoading(false);
      }
    } else if (!AUTH_REQUIRED) {
      setSession({
        ...DEV_FALLBACK_SESSION,
        modules: modulesForRole(DEV_FALLBACK_SESSION.role),
      });
      setLoading(false);
    }

    void (async () => {
      setRefreshing(true);
      await refreshSession();
      if (!cancelled) {
        setLoading(false);
        setRefreshing(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [refreshSession]);

  const login = useCallback(
    async (email: string, password: string) => {
      const session = await api.login(email, password);
      setSession({
        ...session,
        modules: session.modules ?? modulesForRole(session.role),
      });
    },
    [],
  );

  const logout = useCallback(() => {
    api.logout();
    setSession(null);
    router.replace("/login");
  }, [router]);

  const canAccess = useCallback(
    (module: PermissionModule) => {
      if (!session?.role) return !AUTH_REQUIRED;
      if (session.modules?.length) return session.modules.includes(module);
      return hasModule(session.role, module);
    },
    [session?.role, session?.modules],
  );

  const value = useMemo(
    () => ({ session, loading, refreshing, login, logout, refreshSession, canAccess }),
    [session, loading, refreshing, login, logout, refreshSession, canAccess],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
