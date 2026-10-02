#!/usr/bin/env node
/**
 * Capture ORION menu screenshots (default sidebar nav).
 * Usage: node scripts/capture_menu_screenshots.mjs
 * Requires: dev servers on http://127.0.0.1:3002
 */
import { chromium } from "@playwright/test";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, "..");
const OUT_DIR = path.join(ROOT, "docs/menu-screenshots/v1.5.1");
const BASE = process.env.PLAYWRIGHT_BASE_URL ?? "http://127.0.0.1:3002";
const ADMIN = { email: "user@company.com", password: "Ceragem2026!Adm" };

const SCREENS = [
  { file: "00-login", route: "/login", auth: false, settleMs: 2000 },
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

async function login(page) {
  await page.goto(`${BASE}/login?next=${encodeURIComponent("/mission-control")}`);
  await page.locator("#email").fill(ADMIN.email);
  await page.locator("#password").fill(ADMIN.password);
  await page.getByRole("button", { name: "Sign in" }).click();
  await page.waitForURL("**/mission-control**", { timeout: 60_000 });
}

async function settle(page, ms) {
  await page.waitForLoadState("domcontentloaded");
  try {
    await page.waitForLoadState("networkidle", { timeout: Math.min(ms, 20_000) });
  } catch {
    // heavy dashboards may never reach networkidle
  }
  await page.waitForTimeout(Math.min(ms, 8_000));
}

async function main() {
  fs.mkdirSync(OUT_DIR, { recursive: true });
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });

  let loggedIn = false;
  for (const screen of SCREENS) {
    console.log(`→ ${screen.file} (${screen.route})`);
    if (screen.auth !== false && !loggedIn) {
      await login(page);
      loggedIn = true;
      if (screen.route === "/mission-control") {
        await settle(page, screen.settleMs);
        await page.screenshot({ path: path.join(OUT_DIR, `${screen.file}.png`), fullPage: true });
        continue;
      }
    }
    if (screen.route === "/login") {
      await page.goto(`${BASE}${screen.route}`);
      await settle(page, screen.settleMs);
    } else {
      await page.goto(`${BASE}${screen.route}`);
      await settle(page, screen.settleMs);
    }
    const out = path.join(OUT_DIR, `${screen.file}.png`);
    await page.screenshot({ path: out, fullPage: true });
    console.log(`  saved ${out}`);
  }

  const manifest = SCREENS.map((s) => `${s.file}.png — ${s.route}`).join("\n");
  fs.writeFileSync(
    path.join(OUT_DIR, "MANIFEST.txt"),
    `ORION menu screenshots v1.5.1\nGenerated: ${new Date().toISOString()}\nBase URL: ${BASE}\n\n${manifest}\n`,
  );

  await browser.close();
  console.log(`\n✓ ${SCREENS.length} screenshots → ${OUT_DIR}`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
