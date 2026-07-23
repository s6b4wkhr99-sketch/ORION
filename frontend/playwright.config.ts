import { defineConfig, devices } from "@playwright/test";

/**
 * E2E smoke tests — require running local stack:
 *   bash scripts/dev.sh start
 *   make test-e2e
 */
export default defineConfig({
  testDir: "./e2e",
  timeout: 60_000,
  expect: { timeout: 15_000 },
  fullyParallel: false,
  retries: process.env.CI ? 2 : 0,
  reporter: [["list"]],
  use: {
    baseURL: process.env.PLAYWRIGHT_BASE_URL ?? "http://127.0.0.1:3002",
    trace: "on-first-retry",
    ...devices["Desktop Chrome"],
  },
});
