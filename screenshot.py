#!/usr/bin/env python3
"""Full-page screenshot of the South Coast guide. Needs: pip install playwright (in a venv) + Chrome/Chromium.
Usage: /tmp/pwvenv/bin/python screenshot.py"""
import os, sys
from playwright.sync_api import sync_playwright
ROOT=os.path.dirname(os.path.abspath(__file__))
page_path=os.path.join(ROOT,"dist/guides/south-coast-winter-campsites/index.html")
out=os.path.join(ROOT,"screenshots/south-coast-winter.png")
width=int(sys.argv[1]) if len(sys.argv)>1 else 1280
with sync_playwright() as p:
    exe=next((x for x in ["/usr/bin/google-chrome","/usr/bin/chromium","/usr/bin/chromium-browser"] if os.path.exists(x)),None)
    b=p.chromium.launch(executable_path=exe) if exe else p.chromium.launch()
    pg=b.new_page(viewport={"width":width,"height":900})
    pg.goto("file://"+page_path); pg.screenshot(path=out, full_page=True); b.close()
print("wrote", out)
