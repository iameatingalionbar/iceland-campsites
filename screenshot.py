#!/usr/bin/env python3
"""Full-page screenshots of key pages at mobile (390px) and desktop (1280px).
Needs: pip install playwright (in a venv) + Chrome/Chromium.  Usage: /tmp/pwvenv/bin/python screenshot.py [name ...]"""
import os, sys
from playwright.sync_api import sync_playwright
ROOT = os.path.dirname(os.path.abspath(__file__))
PAGES = {
    "home": "index.html",
    "campsites-index": "campsites/index.html",
    "campsite-skaftafell": "campsites/skaftafell/index.html",
    "guide": "guides/south-coast-winter-campsites/index.html",
    "guide-dump-stations": "guides/dump-stations-iceland/index.html",
    "guide-near-reykjavik": "guides/campsites-near-reykjavik/index.html",
}
SIZES = {"mobile": 390, "desktop": 1280}
want = sys.argv[1:] or list(PAGES)
os.makedirs(os.path.join(ROOT, "screenshots"), exist_ok=True)
with sync_playwright() as p:
    exe = next((x for x in ["/usr/bin/google-chrome", "/usr/bin/chromium", "/usr/bin/chromium-browser"] if os.path.exists(x)), None)
    b = p.chromium.launch(executable_path=exe) if exe else p.chromium.launch()
    for name in want:
        path = os.path.join(ROOT, "dist", PAGES[name])
        if not os.path.exists(path): print("skip (not built)", name); continue
        for size, w in SIZES.items():
            pg = b.new_page(viewport={"width": w, "height": 900}, device_scale_factor=1)
            pg.goto("file://" + path); pg.wait_for_timeout(150)
            sw = pg.evaluate("document.documentElement.scrollWidth")
            out = os.path.join(ROOT, "screenshots", f"{name}-{size}.png")
            pg.screenshot(path=out, full_page=True); pg.close()
            print("wrote", out, f"(scrollWidth {sw} vs viewport {w}{' OVERFLOW' if sw > w else ''})")
    b.close()
