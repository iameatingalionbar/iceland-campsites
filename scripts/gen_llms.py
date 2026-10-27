#!/usr/bin/env python3
"""Generate dist/llms.txt (https://llmstxt.org) from the site data and the built pages. Stdlib only.

Called by build.py after the sitemap is written, so every build regenerates it:
    gen_llms.write(DIST, BASE_URL, SITE, campsites, guides)
Standalone (regenerates from an existing dist/; BASE_URL from env, else from dist/index.html's canonical):
    python3 scripts/gen_llms.py

Link titles/descriptions come only from each built page's <title>/<meta name="description"> or from data fields
(region, town, winter status, completeness, check date). Every URL in sitemap.xml is listed: pages not placed in a
named section fall through to "## Optional", so new page types are never silently left out.
"""
import os, re, sys, json, glob
from html import unescape
from urllib.parse import urlparse

WINTER = {"open": "Open in winter", "partial": "Shoulder season only", "call-ahead": "Call ahead",
          "closed": "Closed in winter", "unconfirmed": "Unconfirmed", None: "Unconfirmed"}

def page_meta(dist, base_url, url):
    """(title, description) from the built HTML for an absolute site URL; site-name suffix stripped from the title."""
    path = urlparse(url).path
    bp = urlparse(base_url).path.rstrip("/")
    if bp and path.startswith(bp): path = path[len(bp):]
    f = os.path.join(dist, path.lstrip("/"))
    if f.endswith("/") or os.path.isdir(f): f = os.path.join(f, "index.html")
    html = open(f, encoding="utf-8").read()
    head = html.split("</head>", 1)[0]
    t = re.search(r"<title>(.*?)</title>", head, re.S)
    d = re.search(r'<meta name="description" content="([^"]*)"', head)
    return (unescape(t.group(1)).strip() if t else url), (unescape(d.group(1)).strip() if d else "")

def clean_title(title, site_name):
    return re.sub(r"\s*\|\s*" + re.escape(site_name) + r"$", "", title)

def md(text):
    """Keep link text/descriptions on one line and free of markdown link brackets."""
    return re.sub(r"\s+", " ", text).replace("[", "(").replace("]", ")").strip()

def build_text(dist, base_url, site, campsites, guides):
    base_url = base_url.rstrip("/"); name = site["site_name"]
    sm = open(os.path.join(dist, "sitemap.xml"), encoding="utf-8").read()
    all_urls = re.findall(r"<loc>([^<]+)</loc>", sm)
    used = set()
    def u(rel): return f"{base_url}/{rel}"
    def item(url, desc=None, title=None):
        used.add(url)
        t, d = page_meta(dist, base_url, url)
        return f"- [{md(title or clean_title(t, name))}]({url}): {md(desc if desc is not None else d)}"
    regions = {r["slug"]: r for r in site["regions"]}
    out = [f"# {name}", "", f"> {site['tagline']}.", "",
           "Static English reference site. Every campsite fact links to its source and shows the date it was checked; "
           "facts that could not be confirmed are marked Unconfirmed. Confirm seasons and prices with the campsite before travelling.", ""]
    # Guides
    if guides:
        out += ["## Guides", ""] + [item(u(f"guides/{g['slug']}/"), g["description"], g["title"]) for g in guides] + [""]
    # Campsites, grouped by region (site.json order), only regions that have campsites
    for r in site["regions"]:
        cs = sorted((c for c in campsites if c["region"] == r["slug"]), key=lambda c: c["name"])
        if not cs: continue
        out += [f"## Campsites: {r['name']}", ""]
        for c in cs:
            st = (c.get("winter") or {}).get("status")
            bits = [c.get("town"), r["name"]]
            desc = (", ".join(b for b in bits if b) + f". Winter: {WINTER.get(st, st)}. "
                    + ("Full page" if c.get("completeness") == "full" else "Short entry (stub)")
                    + f"; facts sourced, checked {c.get('checked')}.")
            out.append(item(u(f"campsites/{c['slug']}/"), desc, c["name"]))
        out.append("")
    # Hubs: directory, region hubs with campsites, theme hubs
    hubs = [item(u("campsites/"))]
    for r in site["regions"]:
        n = sum(1 for c in campsites if c["region"] == r["slug"])
        if n: hubs.append(item(u(f"regions/{r['slug']}/"), f"{n} campsite(s). {r['blurb']}"))
    for t in site["themes"]:
        hubs.append(item(u(f"themes/{t['slug']}/"), t["blurb"]))
    out += ["## Hubs", ""] + hubs + [""]
    # About and disclosures
    info = [item(u(p)) for p in ("about/", "affiliate-disclosure/", "ai-disclosure/") if u(p) in all_urls]
    if info: out += ["## About this site", ""] + info + [""]
    # Optional: everything else in the sitemap (home, list indexes, empty region hubs, any new page types)
    empty = {u(f"regions/{r['slug']}/"): f"No campsites added yet. {r['blurb']}" for r in site["regions"]
             if not any(c["region"] == r["slug"] for c in campsites)}
    rest = [x for x in all_urls if x not in used]
    out += ["## Optional", ""] + [item(x, empty.get(x)) for x in rest]
    out.append(f"- [Sitemap]({base_url}/sitemap.xml): XML sitemap of all indexable pages")
    return "\n".join(out) + "\n"

def write(dist, base_url, site, campsites, guides):
    txt = build_text(dist, base_url, site, campsites, guides)
    open(os.path.join(dist, "llms.txt"), "w", encoding="utf-8").write(txt)
    return txt

if __name__ == "__main__":
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); dist = os.path.join(root, "dist")
    site = json.load(open(os.path.join(root, "data", "site.json"), encoding="utf-8"))
    load = lambda sub: [json.load(open(p, encoding="utf-8")) for p in sorted(glob.glob(os.path.join(root, "data", sub, "*.json")))]
    base = os.environ.get("BASE_URL")
    if not base:
        m = re.search(r'<link rel="canonical" href="([^"]+)"', open(os.path.join(dist, "index.html"), encoding="utf-8").read())
        base = m.group(1) if m else site["base_url"]
    txt = write(dist, base.rstrip("/"), site, load("campsites"), load("guides"))
    print(f"Wrote dist/llms.txt ({txt.count(chr(10))} lines)")
