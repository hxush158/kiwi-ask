"""Download the documents listed in data/sources.csv into data/raw/<agency>/.

Web pages are saved as PDF (print layout); PDF links are downloaded as-is.
The `retrieved` column is filled with today's date for each file saved.

Usage:
    uv run python scripts/fetch_sources.py            # headless browser
    uv run python scripts/fetch_sources.py --headed   # visible browser, if a site blocks headless

Be polite: this fetches a short, fixed list with a pause between requests.
Only the listed URLs are fetched; raw files stay out of git (data/raw/ is ignored).
"""

import argparse
import csv
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from playwright.sync_api import Page, sync_playwright

ROOT = Path(__file__).resolve().parent.parent
SOURCES = ROOT / "data" / "sources.csv"
RAW = ROOT / "data" / "raw"
PAUSE_SECONDS = 3
BLOCK_MARKERS = ("Request unsuccessful", "Incapsula", "Access Denied")


def save_pdf_link(page: Page, url: str, target: Path) -> bool:
    response = page.request.get(url)
    content_type = response.headers.get("content-type", "")
    if not response.ok or "pdf" not in content_type:
        print(f"  ✗ HTTP {response.status}, content-type {content_type!r}")
        return False
    target.write_bytes(response.body())
    return True


def save_page_as_pdf(page: Page, url: str, target: Path, headed: bool) -> bool:
    response = page.goto(url, wait_until="networkidle")
    if response is None or not response.ok:
        status = response.status if response else "no response"
        print(f"  ✗ HTTP {status}")
        return False
    text = page.inner_text("body")
    if any(marker in text for marker in BLOCK_MARKERS):
        print("  ✗ blocked by the site's bot protection")
        return False
    if headed:
        # Chromium can only print to PDF in headless mode; keep the HTML instead.
        target.with_suffix(".html").write_text(page.content(), encoding="utf-8")
        return True
    page.emulate_media(media="print")
    page.pdf(path=str(target), format="A4", print_background=False)
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--headed", action="store_true", help="use a visible browser")
    parser.add_argument(
        "--channel",
        default="chrome",
        help="installed browser to use: chrome (default) or msedge",
    )
    args = parser.parse_args()

    with SOURCES.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    fieldnames = list(rows[0].keys())

    saved = 0
    with sync_playwright() as p:
        # channel="chrome" uses the installed Google Chrome, so no browser
        # download from cdn.playwright.dev is needed.
        browser = p.chromium.launch(channel=args.channel, headless=not args.headed)
        page = browser.new_page()
        for row in rows:
            target = RAW / row["agency"] / row["file"]
            target.parent.mkdir(parents=True, exist_ok=True)
            print(f"{row['file']}  ←  {row['url']}")
            if row["url"].lower().endswith(".pdf"):
                ok = save_pdf_link(page, row["url"], target)
            else:
                ok = save_page_as_pdf(page, row["url"], target, args.headed)
            if ok:
                row["retrieved"] = (
                    datetime.now(ZoneInfo("Pacific/Auckland")).date().isoformat()
                )
                saved += 1
                print("  ✓ saved")
            time.sleep(PAUSE_SECONDS)
        browser.close()

    with SOURCES.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n{saved}/{len(rows)} saved under {RAW.relative_to(ROOT)}/")
    if saved < len(rows):
        print("For the ones that failed, save them manually from your browser.")


if __name__ == "__main__":
    main()
