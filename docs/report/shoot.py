"""Capture screenshots of the deployed system for the report and the slide deck.

Run:  python docs/report/shoot.py [--url <base>]

Shots are taken against the live Cloud Run deployment, not a local server, so the figures in
the report show the system as an examiner will see it.
"""

from __future__ import annotations

import argparse
import json
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

OUT = Path(__file__).resolve().parent / "screenshots"
BASE = "https://codefix-ai-324501187617.asia-south1.run.app"


def _retry(fn, attempts=4, wait=5.0):
    """This machine's network intermittently aborts TLS handshakes (seen with gcloud too), so
    a single timeout should not fail the whole capture."""
    import time

    for i in range(attempts):
        try:
            return fn()
        except Exception as e:  # noqa: BLE001
            if i == attempts - 1:
                raise
            print(f"  retry {i + 1}/{attempts - 1} after: {str(e).splitlines()[0][:90]}")
            time.sleep(wait)


def pick_run(base: str) -> str:
    """A hierarchical run that passed, for the richest live-run view."""
    def fetch():
        with urllib.request.urlopen(f"{base}/api/runs", timeout=120) as r:  # noqa: S310
            return json.load(r)

    data = _retry(fetch)
    runs = data if isinstance(data, list) else data.get("runs", [])
    for want in ("hierarchical", None):
        for run in runs:
            if run.get("outcome") == "passed" and (want is None or run.get("arch") == want):
                return run["task_id"]
    return runs[0]["task_id"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default=BASE)
    args = ap.parse_args()
    base = args.url.rstrip("/")
    OUT.mkdir(parents=True, exist_ok=True)
    tid = pick_run(base)
    print("run for live view:", tid)

    shots = [
        ("new_fix.png", f"{base}/", 1500),
        ("runs_list.png", f"{base}/runs.html", 2500),
        ("dashboard.png", f"{base}/dashboard.html", 4000),
        ("run_live.png", f"{base}/run.html?id={tid}", 4500),
        ("agent_card.png", f"{base}/a2a/crew/.well-known/agent-card.json", 1200),
    ]
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900},
                                device_scale_factor=2)
        for name, url, wait in shots:
            _retry(lambda u=url: page.goto(u, wait_until="networkidle", timeout=120_000))
            page.wait_for_timeout(wait)
            page.screenshot(path=str(OUT / name), full_page=True)
            print("  wrote", name)
        browser.close()


if __name__ == "__main__":
    main()
