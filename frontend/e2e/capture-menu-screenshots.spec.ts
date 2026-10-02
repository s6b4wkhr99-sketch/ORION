/**
 * Capture full-page screenshots for all ORION sidebar menus (default deployment nav).
 * Run: cd frontend && npx playwright test e2e/capture-menu-screenshots.spec.ts
 * Or:  node scripts/capture_menu_screenshots.mjs  (from project root, servers running)
 */
import { expect, test } from "@playwright/test";
import fs from "fs";
import path from "path";
import { seedAdminSession } from "./helpers";

const OUT_DIR = path.resolve(__dirname, "../../docs/menu-screenshots/v1.5.1");

type ScreenTarget = {
  file: string;
  route: string;
  settleMs?: number;
};

const SCREENS: ScreenTarget[] = [
  { file: "00-login", route: "/login", settleMs: 2000 },
  { file: "01-mission-control", route: "/mission-control", settleMs: 45000 },
  { file: "02-market-intelligence", route: "/market-intelligence", settleMs: 12000 },
  { file: "03-market-intelligence-state-ca", route: "/market-intelligence?view=state&state=CA", settleMs: 20000 },
  { file: "04-metro-intelligence", route: "/metro-intelligence", settleMs: 12000 },
  { file: "05-metro-intelligence-heatmap-ca", route: "/metro-intelligence?view=heatmap&state=CA", settleMs: 25000 },
  { file: "06-opportunity-finder", route: "/opportunities", settleMs: 30000 },
  { file: "07-admin-sku-catalog", route: "/admin/catalog", settleMs: 8000 },
  { file: "08-admin-upload-center", route: "/import", settleMs: 8000 },
  { file: "09-admin-audience-export", route: "/export", settleMs: 8000 },
  { file: "10-admin-buyer-upload", route: "/buyer-import", settleMs: 8000 },
  { file: "11-admin-user-management", route: "/admin/users", settleMs: 8000 },
  { file: "12-admin-commercial-simulator", route: "/commercial-simulator", settleMs: 15000 },
  { file: "13-admin-platform-health", route: "/admin", settleMs: 8000 },
];

test.describe.configure({ mode: "serial" });

test("capture all menu screenshots", async ({ page }) => {
  test.setTimeout(20 * 60_000);
  fs.mkdirSync(OUT_DIR, { recursive: true });
  await page.setViewportSize({ width: 1440, height: 900 });
  let authed = false;

  for (const screen of SCREENS) {
    if (screen.route === "/login") {
      await page.goto(screen.route);
    } else {
      if (!authed) {
        await seedAdminSession(page);
        authed = true;
      }
      await page.goto(screen.route);
    }
    await page.waitForLoadState("domcontentloaded");
    try {
      await page.waitForLoadState("networkidle", { timeout: Math.min(screen.settleMs ?? 8000, 20_000) });
    } catch {
      /* heavy dashboards */
    }
    await page.waitForTimeout(Math.min(screen.settleMs ?? 8000, 10_000));
    const outPath = path.join(OUT_DIR, `${screen.file}.png`);
    await page.screenshot({ path: outPath, fullPage: true });
    expect(fs.existsSync(outPath)).toBeTruthy();
  }

  const manifest = SCREENS.map((s) => `${s.file}.png — ${s.route}`).join("\n");
  fs.writeFileSync(
    path.join(OUT_DIR, "MANIFEST.txt"),
    `ORION menu screenshots v1.5.1\nGenerated: ${new Date().toISOString()}\n\n${manifest}\n`,
  );
});
