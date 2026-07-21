/**
 * Capture Mission Control widget screenshots for Intelligence Modeling docs.
 * Usage: node scripts/capture_mission_control_screenshots.mjs
 */
import { chromium } from "playwright";
import { mkdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const OUT_DIR = path.resolve(__dirname, "../docs/assets/intelligence-modeling");
const BASE_URL = process.env.CIOS_FRONTEND_URL || "http://127.0.0.1:3002";
const PAGE_URL = `${BASE_URL}/mission-control`;

const SHOTS = [
  { name: "01-mission-control-full", selector: "body", fullPage: true },
  { name: "02-kpi-row", selector: "header + div, .space-y-6 > div:nth-child(3)" },
  { name: "03-opportunity-by-state", text: "Opportunity by State" },
  { name: "04-opportunity-radar", text: "Opportunity Radar" },
  { name: "05-todays-top-opportunity", text: "Today's Top Opportunity" },
  { name: "06-ceragem-distribution", text: "Ceragem Distribution" },
  { name: "07-revenue-funnel", text: "Revenue Funnel" },
  { name: "08-recent-opportunities", text: "Recent Opportunities" },
  { name: "09-intelligence-score-distribution", text: "Intelligence Score Distribution" },
  { name: "10-orion-dna", text: "ORION DNA" },
];

async function clipWidget(page, titleText) {
  const heading = page.locator("h2", { hasText: titleText }).first();
  await heading.waitFor({ state: "visible", timeout: 120000 });
  const section = heading.locator("xpath=ancestor::section[1]");
  return section.boundingBox();
}

async function main() {
  await mkdir(OUT_DIR, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });

  console.log(`Navigating to ${PAGE_URL} ...`);
  await page.goto(PAGE_URL, { waitUntil: "domcontentloaded", timeout: 120000 });

  // Wait for main heading or skeleton to resolve
  await page.waitForSelector("h1:has-text('Mission Control'), .orion-widget", {
    timeout: 120000,
  });

  // Allow executive API + widgets to render (cold build can take ~40s)
  try {
    await page.waitForSelector("text=Expected Revenue", { timeout: 180000 });
  } catch {
    console.warn("KPI row not fully loaded — capturing current state.");
  }

  await page.waitForTimeout(2000);

  for (const shot of SHOTS) {
    const outPath = path.join(OUT_DIR, `${shot.name}.png`);
    try {
      if (shot.fullPage) {
        await page.screenshot({ path: outPath, fullPage: true });
      } else if (shot.text) {
        const box = await clipWidget(page, shot.text);
        if (box) {
          await page.screenshot({ path: outPath, clip: box });
        }
      } else if (shot.selector) {
        const el = page.locator(shot.selector).first();
        if (await el.count()) {
          await el.screenshot({ path: outPath });
        }
      }
      console.log(`Saved ${shot.name}.png`);
    } catch (err) {
      console.warn(`Failed ${shot.name}:`, err.message);
    }
  }

  await browser.close();
  console.log(`Done. Output: ${OUT_DIR}`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
