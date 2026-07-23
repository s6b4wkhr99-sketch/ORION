import { expect, Page, test } from "@playwright/test";

const ADMIN = { email: "user@company.com", password: "Ceragem2026!Adm" };
const READONLY = { email: "readonly@company.com", password: "Ceragem2026!Ro" };

export async function login(page: Page, email: string, password: string, next = "/mission-control") {
  await page.goto(`/login?next=${encodeURIComponent(next)}`);
  await page.locator("#email").fill(email);
  await page.locator("#password").fill(password);
  await page.getByRole("button", { name: "Sign in" }).click();
  await page.waitForURL(`**${next}**`, { timeout: 30_000 });
}

test.describe("Auth smoke", () => {
  test("admin login reaches Mission Control", async ({ page }) => {
    await login(page, ADMIN.email, ADMIN.password);
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
    await expect(page).toHaveURL(/mission-control/);
  });

  test("read only login does not show upload forbidden banner", async ({ page }) => {
    await login(page, READONLY.email, READONLY.password);
    await expect(page.getByText(/Upload list could not be loaded/i)).toHaveCount(0);
  });
});

test.describe("User Management smoke", () => {
  test.beforeEach(async ({ page }) => {
    await login(page, ADMIN.email, ADMIN.password, "/admin/users");
  });

  test("email input keeps focus while typing", async ({ page }) => {
    const row = page.locator("tbody tr").first();
    await row.locator('input[type="radio"]').check();
    const emailInput = row.locator('input[type="email"]');
    await expect(emailInput).toBeEnabled();
    await emailInput.click();
    await page.keyboard.type("z");
    await expect(emailInput).toBeFocused();
    const value = await emailInput.inputValue();
    expect(value).toContain("z");
  });

  test("Platform Health is not active on User Management page", async ({ page }) => {
    const userMgmt = page.getByRole("link", { name: "User Management" }).first();
    const platformHealth = page.getByRole("link", { name: "Platform Health" }).first();
    await expect(userMgmt).toHaveClass(/text-white/);
    await expect(platformHealth).toHaveClass(/text-slate-400/);
  });
});

test.describe("Administration menu", () => {
  test.beforeEach(async ({ page }) => {
    await login(page, ADMIN.email, ADMIN.password, "/admin/users");
  });

  test("shows User Management in Administration section", async ({ page }) => {
    await expect(page.getByRole("link", { name: "User Management" })).toBeVisible();
    await expect(page.getByRole("link", { name: "SKU Catalog" })).toBeVisible();
    await expect(page.getByRole("heading", { name: /User Management/i })).toBeVisible();
  });
});
