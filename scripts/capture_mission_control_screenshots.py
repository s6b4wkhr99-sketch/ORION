#!/usr/bin/env python3
"""Capture Mission Control widget screenshots for Intelligence Modeling docs.

Requires:
  - Backend on http://127.0.0.1:8000
  - Frontend on http://localhost:3002 (use localhost — CORS + API fetch)
  - playwright in backend .venv: pip install playwright && playwright install chromium
"""

from __future__ import annotations

import asyncio
import json
import urllib.request
from pathlib import Path

from playwright.async_api import async_playwright

OUT_DIR = Path(__file__).resolve().parents[1] / "docs" / "assets" / "intelligence-modeling"
BASE_URL = "http://localhost:3002"
PAGE_URL = f"{BASE_URL}/mission-control"
API_BASE = "http://127.0.0.1:8000/api/v1"

WIDGET_TITLES = [
    ("01-mission-control-full", None),
    ("02-executive-kpi-row", "Expected Revenue"),
    ("03-commercial-intelligence", "Active Promotions"),
    ("04-opportunity-by-state", "Opportunity by State"),
    ("05-opportunity-radar", "Opportunity Radar"),
    ("06-todays-top-opportunity", "Today's Top Opportunity"),
    ("07-ceragem-distribution", "Ceragem Distribution"),
    ("08-revenue-funnel", "Revenue Funnel"),
    ("09-recent-opportunities", "Recent Opportunities"),
    ("10-intelligence-score-distribution", "Intelligence Score Distribution"),
    ("11-orion-dna", "ORION DNA"),
]


def _load_json(url: str) -> object:
    body = json.loads(urllib.request.urlopen(url, timeout=120).read())
    if isinstance(body, dict) and "data" in body:
        return body["data"]
    return body


def _uploads_signature(uploads: list[dict]) -> str:
    return "|".join(f"{u['id']}:{u['status']}:{u['total_rows']}" for u in uploads)


def _cache_init_script(exec_data: dict, signature: str) -> str:
    payload = json.dumps(exec_data)
    keys = [
        f"cios:executive:perf-v3:all:boot",
        f"cios:executive:perf-v3:all:{signature}",
    ]
    lines = [f"sessionStorage.setItem({json.dumps(k)}, {json.dumps(payload)});" for k in keys]
    return "\n".join(lines)


async def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    exec_data = _load_json(f"{API_BASE}/dashboard/executive")
    uploads_raw = _load_json(f"{API_BASE}/uploads")
    uploads = uploads_raw.get("uploads", uploads_raw) if isinstance(uploads_raw, dict) else uploads_raw
    signature = _uploads_signature(uploads)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1440, "height": 900})
        await page.add_init_script(_cache_init_script(exec_data, signature))

        print(f"Navigating to {PAGE_URL} ...")
        await page.goto(PAGE_URL, wait_until="load", timeout=120_000)

        for i in range(120):
            text = await page.inner_text("body")
            if "EXPECTED REVENUE" in text.upper() and "Opportunity by State" in text:
                print(f"Dashboard ready ({i}s)")
                break
            await page.wait_for_timeout(1000)
        else:
            raise RuntimeError("Mission Control did not finish loading within 120s")

        await page.wait_for_timeout(3000)
        await page.screenshot(path=str(OUT_DIR / "01-mission-control-full.png"), full_page=True)
        print("Saved 01-mission-control-full.png")

        for filename, title in WIDGET_TITLES[1:]:
            try:
                if title == "Expected Revenue":
                    locator = page.locator("text=EXPECTED REVENUE").first.locator(
                        "xpath=ancestor::div[contains(@class,'grid')][1]"
                    )
                else:
                    heading = page.locator("h2", has_text=title).first
                    await heading.wait_for(state="visible", timeout=30_000)
                    locator = heading.locator("xpath=ancestor::section[1]")
                await locator.screenshot(path=str(OUT_DIR / f"{filename}.png"))
                print(f"Saved {filename}.png")
            except Exception as exc:
                print(f"Failed {filename}: {exc}")

        await browser.close()

    print(f"Done. Output: {OUT_DIR}")


if __name__ == "__main__":
    asyncio.run(main())
