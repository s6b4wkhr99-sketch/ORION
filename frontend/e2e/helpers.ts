import type { Page } from "@playwright/test";

export const ADMIN = { email: "user@company.com", password: "Ceragem2026!Adm" };

const API_BASE = process.env.PLAYWRIGHT_API_URL ?? "http://127.0.0.1:8000/api/v1";

type ApiEnvelope<T> = { success?: boolean; data?: T; message?: string };

/** Inject admin session via API (faster and more reliable than UI login for screenshots). */
export async function seedAdminSession(page: Page) {
  const loginRes = await fetch(`${API_BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email: ADMIN.email, password: ADMIN.password }),
  });
  const loginBody = (await loginRes.json()) as ApiEnvelope<{ token: string; role: string; email?: string; name?: string }>;
  if (!loginRes.ok || !loginBody.success || !loginBody.data?.token) {
    throw new Error(loginBody.message ?? `API login failed (${loginRes.status})`);
  }
  const token = loginBody.data.token;

  let session: Record<string, unknown> = {
    email: loginBody.data.email ?? ADMIN.email,
    name: loginBody.data.name ?? "Admin",
    role: loginBody.data.role ?? "System Administrator",
  };
  try {
    const meRes = await fetch(`${API_BASE}/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    const meBody = (await meRes.json()) as ApiEnvelope<Record<string, unknown>>;
    if (meRes.ok && meBody.success && meBody.data) {
      session = meBody.data;
    }
  } catch {
    // fallback session above
  }

  await page.addInitScript(
    ({ authToken, authSession }) => {
      localStorage.setItem("cios_auth_token", authToken);
      localStorage.setItem("cios_auth_session", JSON.stringify(authSession));
    },
    { authToken: token, authSession: session },
  );
}

export async function login(
  page: Page,
  email: string,
  password: string,
  next = "/mission-control",
  timeoutMs = 30_000,
) {
  await page.goto(`/login?next=${encodeURIComponent(next)}`);
  await page.locator("#email").fill(email);
  await page.locator("#password").fill(password);
  await page.getByRole("button", { name: "Sign in" }).click();
  await page.waitForURL(`**${next}**`, { timeout: timeoutMs, waitUntil: "commit" });
  await page.waitForSelector("nav, h1", { timeout: timeoutMs }).catch(() => undefined);
}
