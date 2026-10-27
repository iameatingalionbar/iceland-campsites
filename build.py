#!/usr/bin/env python3
"""Static site builder for Iceland Campsites. Python 3 standard library only.

Usage:  python3 build.py              # builds into dist/
        BASE_URL=https://mysite.is python3 build.py
Reads data/site.json, data/campsites/*.json, data/guides/*.json and templates/base.html.
Fails loudly if any fact has a value without a source, or cites an unknown source key.
"""
import json, os, sys, shutil, glob, datetime, re, math
from html import escape
from string import Template
from urllib.parse import urlparse
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "scripts"))
import gen_llms

ROOT = os.path.dirname(os.path.abspath(__file__))
DIST = os.path.join(ROOT, "dist")
SITE = json.load(open(os.path.join(ROOT, "data", "site.json"), encoding="utf-8"))
BASE_URL = os.environ.get("BASE_URL", SITE["base_url"]).rstrip("/")
TEMPLATE = Template(open(os.path.join(ROOT, "templates", "base.html"), encoding="utf-8").read())
BUILD_DATE = os.environ.get("BUILD_DATE", datetime.date.today().isoformat())
REGIONS = {r["slug"]: r for r in SITE["regions"]}
WINTER = {
    "open": ("Open in winter", "b-open"),
    "partial": ("Shoulder season only", "b-partial"),
    "call-ahead": ("Call ahead", "b-call"),
    "closed": ("Closed in winter", "b-closed"),
    None: ("Unconfirmed", "b-unc"),
    "unconfirmed": ("Unconfirmed", "b-unc"),
}
FACT_LABELS = [
    ("electricity", "Electricity hookup"), ("kitchen", "Kitchen / indoor area"), ("showers", "Showers"),
    ("toilets", "Toilets"), ("dump_station", "Chemical toilet / grey water disposal"), ("wifi", "WiFi"),
    ("laundry", "Laundry"), ("camping_card", "Accepts Camping Card (Útilegukortið)"), ("contact", "Contact / website"),
]
ERRORS = []
PAGES = []  # (path, lastmod)

# ---------- helpers ----------
def load_dir(sub):
    out = []
    for p in sorted(glob.glob(os.path.join(ROOT, "data", sub, "*.json"))):
        d = json.load(open(p, encoding="utf-8"))
        d["_file"] = os.path.relpath(p, ROOT)
        out.append(d)
    return out

class Cites:
    """Per-page numbered source list. Facts cite source keys; we render [n] links."""
    def __init__(self, sources, owner):
        self.sources, self.owner, self.order, self.by_url = sources, owner, [], {}
    def num(self, key):
        if key not in self.sources:
            ERRORS.append(f"{self.owner}: cites unknown source key '{key}'"); return "?"
        url = self.sources[key]["url"]  # de-duplicate identical URLs cited under different keys
        if url not in self.order: self.order.append(url); self.by_url[url] = key
        return self.order.index(url) + 1
    def sup(self, keys):
        if not keys: return ""
        parts, seen = [], set()
        for k in keys:
            n = self.num(k)
            if n == "?" or n in seen: continue
            seen.add(n)
            url = self.sources.get(k, {}).get("url", "#")
            parts.append(f'<a href="{escape(url)}" rel="nofollow noopener" title="{escape(self.sources.get(k,{}).get("title",""))}">[{n}]</a>')
        return '<sup class="cite">' + "".join(parts) + "</sup>"
    def checked(self, keys):
        dates = sorted({self.sources.get(k, {}).get("checked", "") for k in keys if k in self.sources})
        return f' <span class="checked">(checked {", ".join(dates)})</span>' if dates else ""
    def listing(self):
        if not self.order: return ""
        lis = []
        for i, u in enumerate(self.order, 1):
            s = self.sources[self.by_url[u]]
            lis.append(f'<li id="src-{i}"><a href="{escape(s["url"])}" rel="nofollow noopener">{escape(s["title"])}</a> – <span class="meta">{escape(s["url"])}</span> – checked {escape(s["checked"])}</li>')
        return '<ol class="sources">' + "\n".join(lis) + "</ol>"

def fact_html(fact, cites, owner, with_checked=True):
    """Render a fact {value, src[], note?}. Missing value => visible 'Unconfirmed'."""
    if fact is None or fact.get("value") in (None, ""):
        note = (fact or {}).get("note", "")
        return '<span class="unconfirmed">Unconfirmed</span>' + (f'<span class="unc-note">{escape(note)}</span>' if note else "")
    src = fact.get("src") or []
    if not src:
        ERRORS.append(f"{owner}: fact '{fact['value'][:60]}' has a value but no source")
    out = escape(str(fact["value"])) + cites.sup(src)
    if with_checked: out += cites.checked(src)
    return out

def winter_badge(status):
    label, cls = WINTER.get(status, WINTER[None])
    return f'<span class="badge {cls}">{label}</span>'

def map_links(c):
    lat, lon = c["location"].get("lat"), c["location"].get("lon")
    if lat is None or lon is None: return None
    return (f'<a href="https://www.openstreetmap.org/?mlat={lat}&amp;mlon={lon}#map=15/{lat}/{lon}" rel="nofollow noopener">OpenStreetMap</a> · '
            f'<a href="https://www.google.com/maps/search/?api=1&amp;query={lat},{lon}" rel="nofollow noopener">Google Maps</a>')

def write_page(rel, title, description, body, head_extra="", robots="index,follow", root=None, main_cls="page"):
    depth = rel.count("/")
    if root is None: root = "../" * depth  # relative links: work at any host/subpath
    canon_path = rel[:-len("index.html")] if rel.endswith("index.html") else rel
    html = TEMPLATE.substitute(title=escape(title), description=escape(description), canonical=f"{BASE_URL}/{canon_path}",
                               robots=robots, head_extra=head_extra, root=root, body=body, site_name=escape(SITE["site_name"]),
                               build_date=BUILD_DATE, main_cls=main_cls)
    path = os.path.join(DIST, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w", encoding="utf-8").write(html)
    if robots.startswith("index"): PAGES.append(canon_path)

def crumbs(root, items):
    parts = [f'<a href="{root}index.html">Home</a>'] + [f'<a href="{root}{h}">{escape(t)}</a>' if h else escape(t) for t, h in items]
    return '<p class="breadcrumb">' + " › ".join(parts) + "</p>"

def campsite_url(slug, root): return f"{root}campsites/{slug}/index.html"

def dump_has(c): return (c["facts"].get("dump_station") or {}).get("has")

def short_text(fact):
    return fact.get("value") if fact and fact.get("value") else None

# ---------- validation ----------
def validate(c):
    owner = c["_file"]
    for req in ["slug", "name", "region", "sources", "location", "season", "winter", "prices", "facts"]:
        if req not in c: ERRORS.append(f"{owner}: missing '{req}'")
    if c.get("region") not in REGIONS: ERRORS.append(f"{owner}: unknown region '{c.get('region')}'")
    for k, s in c.get("sources", {}).items():
        if not s.get("url", "").startswith("http"): ERRORS.append(f"{owner}: source {k} has no URL")
        if not re.match(r"\d{4}-\d{2}-\d{2}$", s.get("checked", "")): ERRORS.append(f"{owner}: source {k} has no checked date")
    if c.get("winter", {}).get("status") not in WINTER: ERRORS.append(f"{owner}: bad winter.status")
    if c["location"].get("lat") is not None and not c["location"].get("coords_src"):
        ERRORS.append(f"{owner}: coordinates without coords_src")

# ---------- facility flags, cards & map ----------
FACILITIES = [("electricity", "Electricity"), ("showers", "Showers"), ("dump_station", "Dump station"), ("kitchen", "Kitchen")]
FLAG_TXT = {"yes": "yes", "no": "no", "nearby": "nearby, not on site", None: "unconfirmed"}

def has(c, key):
    """Facility flag from the data file ('has'), never guessed: yes|no|nearby|None."""
    f = c["facts"].get(key) or {}
    h = f.get("has")
    if h in ("yes", "no", "nearby"): return h
    return None

def adult_price(c):
    return next((i for i in c["prices"]["items"] if i["label"].lower().startswith(("adult", "per person", "campervan"))), None)

def chips(c):
    out = []
    for key, label in FACILITIES:
        h = has(c, key)
        cls = {"yes": "c-yes", "no": "c-no", "nearby": "c-near", None: "c-unc"}[h]
        mark = {"yes": "✓", "no": "✕", "nearby": "↗", None: "?"}[h]
        out.append(f'<li class="chip {cls}"><span aria-hidden="true">{mark}</span> {label}<span class="sr"> : {FLAG_TXT[h]}</span></li>')
    return '<ul class="chips" aria-label="Facilities">' + "".join(out) + "</ul>"

def card(c, root, heading="h3"):
    reg = REGIONS[c["region"]]
    ap = adult_price(c)
    price = (f'<p class="price"><span class="meta">{escape(ap["label"])}</span> <strong>{escape(ap["value"])}</strong></p>' if ap and ap.get("value")
             else '<p class="price"><span class="meta">Price</span> <span class="unconfirmed">Unconfirmed</span></p>')
    data = (f'data-region="{c["region"]}" data-winter="{c["winter"].get("status") or "unconfirmed"}" '
            + " ".join(f'data-{k.replace("_station","")}="{has(c, k) or "unc"}"' for k, _ in FACILITIES)
            + f' data-name="{escape((c["name"] + " " + c.get("town","") + " " + " ".join(c.get("alt_names", []))).lower())}"')
    return (f'<li class="card camp" {data}><div class="card-top">{winter_badge(c["winter"].get("status"))}'
            + ('<span class="tag">Short entry</span>' if c.get("completeness") == "stub" else '<span class="tag tag-full">Full page</span>') + "</div>"
            + f'<{heading} class="card-title"><a href="{campsite_url(c["slug"], root)}">{escape(c["name"])}</a></{heading}>'
            + f'<p class="meta">{escape(c.get("town",""))} · {escape(reg["name"])}</p>' + chips(c) + price + "</li>")

def cards(cs, root, cls="", heading="h3"):
    if not cs: return '<p><em>No campsites added yet for this list. More pages are added regularly; see the <a href="' + root + 'about/index.html">methodology</a>.</em></p>'
    return f'<ul class="cards camp-cards {cls}">' + "".join(card(c, root, heading) for c in cs) + "</ul>"

OUTLINE = json.load(open(os.path.join(ROOT, "data", "geo", "iceland-outline.json"), encoding="utf-8"))
import math
_LON0, _LAT1 = -24.6, 66.62
_KX = math.cos(math.radians(65)) * 100
_KY = 100 * 1.0
_W = round((-13.45 - _LON0) * _KX + 4); _H = round((_LAT1 - 63.33) * _KY + 2)
def proj(lon, lat): return ((lon - _LON0) * _KX + 2, (_LAT1 - lat) * _KY + 1)
_OUTLINE_D = "M" + " ".join(f"{x:.0f} {y:.0f}" if i == 0 else f"{x:.0f} {y:.0f}" for i, (x, y) in enumerate(proj(*p) for p in OUTLINE["coordinates"])) + "Z"
# collapse duplicate consecutive points produced by rounding
def _dedupe(d):
    pts = d[1:-1].split(" "); out = []; prev = None
    for i in range(0, len(pts), 2):
        pt = (pts[i], pts[i+1])
        if pt != prev: out.append(pt)
        prev = pt
    return "M" + " ".join(f"{a} {b}" for a, b in out) + "Z"
_OUTLINE_D = _dedupe(_OUTLINE_D)

def map_svg(cs, root, label, highlight=None, cls=""):
    """Inline SVG overview of Iceland with one marker per campsite that has sourced coordinates."""
    marks = []
    for c in cs:
        lat, lon = c["location"].get("lat"), c["location"].get("lon")
        if lat is None or lon is None: continue
        x, y = proj(lon, lat)
        st = c["winter"].get("status") or "unconfirmed"
        name = f'{c["name"]} – {WINTER.get(st, WINTER[None])[0]}'
        r = 4 if highlight is None else 7
        marks.append(f'<a href="{campsite_url(c["slug"], root)}" class="mk" data-slug="{c["slug"]}" aria-label="{escape(name)}">'
                     f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" class="m-{st}"/><title>{escape(name)}</title></a>')
    return (f'<svg class="map {cls}" viewBox="0 0 {_W} {_H}" role="img" aria-label="{escape(label)}" xmlns="http://www.w3.org/2000/svg">'
            f'<path class="land" d="{_OUTLINE_D}"/>' + "".join(marks) + "</svg>")

def map_credit():
    return ('<p class="map-credit">Outline: <a href="https://www.naturalearthdata.com/" rel="nofollow noopener">Natural Earth</a> (public domain). '
            'Markers use the GPS coordinates cited on each campsite page; campsites without sourced coordinates are not shown.</p>')

def map_legend():
    return ('<ul class="map-legend" aria-label="Marker colours">' + "".join(
        f'<li><span class="dot m-{s}" aria-hidden="true"></span>{WINTER[s][0]}</li>' for s in ["open", "call-ahead", "partial", "closed"]) + "</ul>")

def unmapped(cs, root):
    miss = [c for c in cs if c["location"].get("lat") is None]
    if not miss: return ""
    return '<p class="meta">Not on the map (no sourced coordinates yet): ' + ", ".join(f'<a href="{campsite_url(c["slug"], root)}">{escape(c["name"])}</a>' for c in miss) + ".</p>"

def page_head(eyebrow, title, lede="", extra=""):
    return (f'<header class="page-head"><p class="eyebrow">{eyebrow}</p><h1>{title}</h1>'
            + (f'<p class="lede">{lede}</p>' if lede else "") + extra + "</header>")

# ---------- page renderers ----------
def render_campsite(c):
    root = "../../"
    cites = Cites(c["sources"], c["_file"])
    o = c["_file"]
    reg = REGIONS[c["region"]]
    loc = c["location"]
    rows = []
    def row(label, html): rows.append(f'<tr><th scope="row">{label}</th><td>{html}</td></tr>')
    row("Region", f'<a href="{root}regions/{reg["slug"]}/index.html">{escape(reg["name"])}</a>' + (f" – {escape(c['town'])}" if c.get("town") else ""))
    row("Address", fact_html(loc.get("address"), cites, o))
    ml = map_links(c)
    if ml:
        row("GPS coordinates", f'{loc["lat"]:.6f}, {loc["lon"]:.6f}' + cites.sup(loc["coords_src"]) + cites.checked(loc["coords_src"]) + f"<br>Map: {ml}")
    else:
        row("GPS coordinates", '<span class="unconfirmed">Unconfirmed</span><span class="unc-note">No coordinates found in the sources checked.</span>')
    row("Opening season", fact_html(c["season"], cites, o))
    w = c["winter"]
    row("Winter opening", winter_badge(w.get("status")) + " " + fact_html(w, cites, o))
    for key, label in FACT_LABELS:
        row(escape(label), fact_html(c["facts"].get(key), cites, o))
    facts_table = '<div class="table-wrap"><table class="facts"><caption>Key facts with sources</caption><tbody>' + "\n".join(rows) + "</tbody></table></div>"

    p = c["prices"]
    prow = [f'<tr><th scope="row">{escape(i["label"])}</th><td>{fact_html(i, cites, o)}</td></tr>' for i in p["items"]]
    prices = (f'<p class="meta">Currency: {escape(p.get("currency","ISK"))}. Applies to: {fact_html(p.get("applies_to"), cites, o)}</p>'
              '<div class="table-wrap"><table class="facts prices"><caption>Prices</caption><tbody>' + "\n".join(prow) + "</tbody></table></div>")
    intro = f'<p class="lede">{fact_html(c.get("intro"), cites, o, with_checked=False)}</p>' if c.get("intro") else ""
    practical = ""
    if c.get("practical"):
        practical = '<h2 id="tips">Practical tips</h2><ul class="tips">' + "".join(f"<li>{fact_html(t, cites, o)}</li>" for t in c["practical"]) + "</ul>"
    stub = ""
    if c.get("completeness") == "stub":
        stub = '<div class="callout warn"><strong>Short entry.</strong> This page covers the basics we could source so far. Anything we have not been able to confirm is marked Unconfirmed.</div>'
    alt = f'<p class="meta">Also known as: {escape(", ".join(c["alt_names"]))}</p>' if c.get("alt_names") else ""
    ap = adult_price(c)
    glance = ('<dl class="glance">'
              f'<div><dt>Winter</dt><dd>{winter_badge(w.get("status"))}</dd></div>'
              f'<div><dt>Season</dt><dd>{escape(short_text(c["season"]) or "Unconfirmed")}</dd></div>'
              + (f'<div><dt>{escape(ap["label"])}</dt><dd>{escape(ap["value"])}</dd></div>' if ap and ap.get("value") else '<div><dt>Price</dt><dd><span class="unconfirmed">Unconfirmed</span></dd></div>')
              + "</dl>")
    side = ('<aside class="side card" aria-label="Location">'
            '<h2 class="side-h">Location</h2>'
            + (map_svg([c], root, f"Map of Iceland showing the location of {c['name']}", highlight=c["slug"], cls="mini") if ml else "")
            + (f'<p class="coords">{loc["lat"]:.5f}, {loc["lon"]:.5f}{cites.sup(loc["coords_src"])}</p><p class="maplinks">'
               f'<a class="btn btn-sm" href="https://www.openstreetmap.org/?mlat={loc["lat"]}&amp;mlon={loc["lon"]}#map=14/{loc["lat"]}/{loc["lon"]}" rel="nofollow noopener">Open in OpenStreetMap</a> '
               f'<a class="btn btn-sm btn-ghost" href="https://www.google.com/maps/search/?api=1&amp;query={loc["lat"]},{loc["lon"]}" rel="nofollow noopener">Google Maps</a></p>'
               if ml else '<p><span class="unconfirmed">Unconfirmed</span><span class="unc-note">No sourced coordinates yet, so no map.</span></p>')
            + '<p class="meta">Seasons and prices change. Check with the campsite before you travel.</p>'
            + '<nav class="toc" aria-label="On this page"><p class="side-h">On this page</p><ul>'
            + '<li><a href="#facts">Key facts</a></li><li><a href="#prices">Prices</a></li>'
            + ('<li><a href="#tips">Practical tips</a></li>' if practical else "") + '<li><a href="#sources">Sources</a></li></ul></nav>'
            + "</aside>")
    head = page_head(f'<a href="{root}regions/{reg["slug"]}/index.html">{escape(reg["name"])}</a> · {escape(c.get("town",""))}', escape(c["name"]),
                     extra=alt + glance + chips(c) + f'<p class="meta">Facts last checked {escape(c["checked"])}. Numbers in brackets link to the source; full list under <a href="#sources">Sources</a>.</p>')
    body = (crumbs(root, [("Regions", "regions/index.html"), (reg["name"], f'regions/{reg["slug"]}/index.html'), (c["name"], None)])
            + head + '<div class="with-side"><div class="main-col">'
            + stub + intro + f'<h2 id="facts">Key facts</h2>{facts_table}'
            + f'<h2 id="prices">Prices</h2>{prices}' + practical
            + f'<h2 id="sources">Sources</h2>{cites.listing()}'
            + '<p class="meta">Spotted something out of date? The campsite\'s own website is always the authority. Prices and seasons change from year to year.</p>'
            + "</div>" + side + "</div>")
    desc = f"{c['name']} in {reg['name']}, Iceland: winter opening, prices, electricity, showers, dump station and more. Every fact sourced, checked {c['checked']}."
    ld = {"@context": "https://schema.org", "@type": "Campground", "name": c["name"], "url": f"{BASE_URL}/campsites/{c['slug']}/"}
    if loc.get("lat") is not None: ld["geo"] = {"@type": "GeoCoordinates", "latitude": loc["lat"], "longitude": loc["lon"]}
    if loc.get("address", {}).get("value"): ld["address"] = loc["address"]["value"]
    head_ld = '<script type="application/ld+json">' + json.dumps(ld, ensure_ascii=False) + "</script>"
    write_page(f"campsites/{c['slug']}/index.html", f"{c['name']} – campsite facts & prices | {SITE['site_name']}", desc, body, head_ld)

def render_region(r, cs):
    root = "../../"
    mine = [c for c in cs if c["region"] == r["slug"]]
    gs = [g for g in GUIDES if g.get("region") == r["slug"] or r["slug"] in g.get("regions", [])]
    guides = ('<h2>Guides</h2><ul class="cards guide-cards">' + "".join(guide_card(g, root) for g in gs) + "</ul>") if gs else ""
    mp = (f'<figure class="map-fig">{map_svg(mine, root, "Map of campsites in " + r["name"])}<figcaption>{map_legend()}{map_credit()}</figcaption></figure>' if any(c["location"].get("lat") for c in mine) else "")
    body = (crumbs(root, [("Regions", "regions/index.html"), (r["name"], None)])
            + page_head(f'Region · {escape(r["is"])}', f'Campsites in {escape(r["name"])}', escape(r["blurb"]))
            + guides + f"<h2>Campsites ({len(mine)})</h2>" + mp + cards(mine, root))
    write_page(f"regions/{r['slug']}/index.html", f"Campsites in {r['name']}, Iceland | {SITE['site_name']}",
               f"Campervan-friendly campsites in {r['name']} ({r['is']}), Iceland, with sourced winter opening, electricity and dump station info.", body)

def render_theme(t, cs):
    root = "../../"
    if t["filter"] == "winter":
        order = ["open", "call-ahead", "partial"]
        sel = sorted([c for c in cs if c["winter"].get("status") in order], key=lambda c: (order.index(c["winter"]["status"]), c["region"], c["name"]))
        content = ('<div class="legend">' + "".join(winter_badge(s) for s in order) + "</div>"
                   + "<p>Sites marked <strong>Call ahead</strong> are listed as open in winter by some source, but the wording is vague (for example 'depending on weather' or 'upon request'), or sources conflict. <strong>Shoulder season only</strong> means open into late autumn or from early spring, but not all winter. Campsites confirmed closed in winter are left off this list.</p>"
                   + f'<figure class="map-fig">{map_svg(sel, root, "Map of campsites open in winter")}<figcaption>{map_legend()}{map_credit()}</figcaption></figure>'
                   + cards(sel, root))
    else:
        content = ""
        for r in SITE["regions"]:
            sel = [c for c in cs if c["region"] == r["slug"] and dump_has(c) in ("yes",)]
            content += f'<h2>{escape(r["name"])}</h2>' + (cards(sel, root) if sel else '<p class="meta"><em>No campsite with a confirmed disposal point added for this region yet.</em></p>')
        near = [c for c in cs if dump_has(c) == "nearby"]
        if near:
            content += "<h2>Campsites without their own disposal point (nearby station)</h2>" + cards(near, root)
        dg = [g for g in GUIDES if g["slug"] == "dump-stations-iceland"]
        if dg: content = f'<p class="callout">Read the full guide: <a href="{root}guides/dump-stations-iceland/index.html">{escape(dg[0]["title"])}</a>.</p>' + content
    body = crumbs(root, [("Themes", "themes/index.html"), (t["name"], None)]) + page_head("Theme", escape(t["name"]), escape(t["blurb"])) + content
    write_page(f"themes/{t['slug']}/index.html", f"{t['name']} – Iceland campsites | {SITE['site_name']}", t["blurb"][:155], body)

GUIDE_COLS = {
    "winter": ["location", "winter", "electricity", "dump", "price", "sources", "checked"],
    "overview": ["location", "winter", "electricity", "dump", "price", "sources", "checked"],
    "dump": ["location", "dump", "winter_badge", "price", "sources", "checked"],
}
COL_HEAD = {"location": "Location", "winter": "Winter status", "winter_badge": "Winter", "electricity": "Electricity", "dump": "Dump station",
            "price": "Price (if confirmed)", "sources": "Sources", "checked": "Checked"}

def render_guide(g, cs_by_slug):
    root = "../../"
    owner = g["_file"]
    sources = dict(g["sources"])
    for slug in g["campsites"]:
        c = cs_by_slug.get(slug)
        if not c: ERRORS.append(f"{owner}: unknown campsite '{slug}'"); continue
        for k, s in c["sources"].items(): sources[f"{slug}:{k}"] = s
    for k, s in sources.items():
        if not re.match(r"\d{4}-\d{2}-\d{2}$", s.get("checked", "")): ERRORS.append(f"{owner}: source {k} has no checked date")
    cites = Cites(sources, owner)
    def ns(slug, keys): return [f"{slug}:{k}" for k in (keys or [])]
    intro = "".join(f'<p{" class=\"lede\"" if i == 0 else ""}>{fact_html(p, cites, owner, with_checked=False)}</p>' for i, p in enumerate(g["intro"]))
    cols = GUIDE_COLS[g.get("table", "winter")]
    rows = []
    listed = []
    for slug in g["campsites"]:
        c = cs_by_slug.get(slug)
        if not c: continue
        listed.append(c)
        w = c["winter"]
        def nf(f):
            if not f or not f.get("value"): return f
            return {**f, "src": ns(slug, f.get("src"))}
        el, dump = nf(c["facts"].get("electricity")), nf(c["facts"].get("dump_station"))
        adult = adult_price(c)
        price = fact_html(nf(adult), cites, owner, with_checked=False) if adult else '<span class="unconfirmed">Unconfirmed</span>'
        if adult and adult.get("value"): price = escape(adult["label"]) + ": " + price
        srcs = sorted({k for f in [nf(w), el, dump, nf(adult), nf(c["season"])] if f and f.get("value") for k in f.get("src", [])})
        loc = c["location"]; ml = map_links(c)
        cell = {
            "location": escape(c.get("town", "")) + (f'<br><span class="meta">{loc["lat"]:.4f}, {loc["lon"]:.4f}</span>' if ml else ""),
            "winter": f'{winter_badge(w.get("status"))}<br>{fact_html(nf(w), cites, owner, with_checked=False)}',
            "winter_badge": winter_badge(w.get("status")),
            "electricity": fact_html(el, cites, owner, with_checked=False),
            "dump": fact_html(dump, cites, owner, with_checked=False),
            "price": price, "sources": cites.sup(srcs) or "–", "checked": f'<span class="checked">{escape(c["checked"])}</span>',
        }
        rows.append(f'<tr><th scope="row"><a href="{campsite_url(slug, root)}">{escape(c["name"])}</a></th>'
                    + "".join(f'<td data-label="{COL_HEAD[k]}" class="col-{k}"><div class="cv">{cell[k]}</div></td>' for k in cols) + "</tr>")
    tkind = g.get("table", "winter")
    table = (f'<div class="table-wrap wide" role="region" aria-label="Campsite comparison table"><table class="guide stack t-{tkind}">'
             f'<caption>{escape(g.get("table_caption", "Listed roughly west to east along the Ring Road. Prices are 2026 rates as published."))}</caption>'
             f'<thead><tr><th scope="col" class="col-name">Campsite</th>' + "".join(f'<th scope="col" class="col-{k}">{COL_HEAD[k]}</th>' for k in cols) + "</tr></thead><tbody>"
             + "\n".join(rows) + "</tbody></table></div>")
    legend = ('<div class="legend">' + "".join(winter_badge(s) for s in ["open", "call-ahead", "partial", "closed"]) + '<span class="unconfirmed">Unconfirmed</span></div>'
              '<p class="meta"><strong>Open in winter</strong>: the campsite or an official listing states it is open through winter. <strong>Call ahead</strong>: listed as open in winter, but the wording is vague or sources conflict. <strong>Shoulder season only</strong>: open into late autumn or from early spring, not all winter. <strong>Closed in winter</strong>: published season ends before winter.</p>')
    sections = ""
    for s in g.get("sections", []):
        sid = s.get("id", "")
        sections += f'<h2{f" id=\"{sid}\"" if sid else ""}>{escape(s["title"])}</h2>' + "".join(f"<p>{fact_html(p, cites, owner)}</p>" for p in s.get("paras", []))
        if s.get("items"): sections += '<ul class="tips">' + "".join(f"<li>{fact_html(t, cites, owner)}</li>" for t in s["items"]) + "</ul>"
    tips = (f"<h2 id=\"tips\">{escape(g.get('tips_title', 'Practical winter tips'))}</h2><ul class='tips'>" + "".join(f"<li>{fact_html(t, cites, owner)}</li>" for t in g["tips"]) + "</ul>") if g.get("tips") else ""
    demand = f'<h2>What travellers ask</h2><p>{fact_html(g["demand"], cites, owner)}</p>' if g.get("demand") else ""
    mp = (f'<figure class="map-fig guide-map">{map_svg(listed, root, "Map of the campsites in this guide")}<figcaption>{map_legend()}{map_credit()}{unmapped(listed, root)}</figcaption></figure>')
    body = (crumbs(root, [("Guides", "guides/index.html"), (g["title"], None)])
            + page_head(f'Guide · checked {escape(g["checked"])}', escape(g["title"]), extra=intro)
            + f'<p class="callout">{escape(g["scope_note"])}</p>'
            + f'<h2 id="glance">{escape(g.get("glance_title", "At a glance"))}</h2>' + legend + mp + table + sections + tips + demand
            + f'<div class="callout warn">{escape(g.get("warning", "Winter seasons, prices and facilities can change at short notice. Contact the campsite before relying on it, especially sites marked Call ahead."))}</div>'
            + f'<h2 id="sources">Sources</h2>{cites.listing()}')
    ld = {"@context": "https://schema.org", "@type": "Article", "headline": g["title"], "description": g["description"],
          "dateModified": g["checked"], "url": f"{BASE_URL}/guides/{g['slug']}/", "inLanguage": "en"}
    write_page(f"guides/{g['slug']}/index.html", f"{g['title']} | {SITE['site_name']}", g["description"], body,
               '<script type="application/ld+json">' + json.dumps(ld, ensure_ascii=False) + "</script>")

def guide_card(g, root):
    return (f'<li class="card guide-card"><p class="eyebrow">Guide · {len(g["campsites"])} campsites</p>'
            f'<h3 class="card-title"><a href="{root}guides/{g["slug"]}/index.html">{escape(g["title"])}</a></h3>'
            f'<p class="meta">{escape(g["description"])}</p></li>')

def filter_form(root, action=None, hero=False):
    """Filter controls. On the index (action=None) JS filters cards live; on the home page it submits to the index."""
    regs = "".join(f'<option value="{r["slug"]}">{escape(r["name"])}</option>' for r in SITE["regions"])
    pre = "h-" if hero else "f-"
    boxes = "".join(f'<label class="check"><input type="checkbox" name="{k}" value="yes" id="{pre}{k}"> {l}</label>'
                    for k, l in [("electricity", "Electricity"), ("showers", "Showers"), ("dump", "Dump station"), ("kitchen", "Kitchen")])
    return (f'<form class="filters{" hero-form" if hero else ""}" role="search" action="{action or ""}" method="get"'
            + ("" if hero else ' id="filters" hidden') + ">"
            + f'<div class="f-row"><label class="field grow"><span>Search by name or town</span><input type="search" name="q" id="{pre}q" placeholder="e.g. Skaftafell, Vík, Selfoss" autocomplete="off"></label>'
            + f'<label class="field"><span>Region</span><select name="region" id="{pre}region"><option value="">All regions</option>{regs}</select></label>'
            + f'<label class="field"><span>Winter</span><select name="winter" id="{pre}winter"><option value="">Any season</option><option value="open">Open in winter</option><option value="open,call-ahead">Open or call ahead</option><option value="open,call-ahead,partial">Open, call ahead or shoulder season</option></select></label></div>'
            + f'<fieldset class="f-row checks"><legend>Must have (confirmed)</legend>{boxes}</fieldset>'
            + ('<div class="f-row"><button class="btn" type="submit">Find campsites</button></div>' if hero else
               '<div class="f-row f-foot"><p class="count" id="count" aria-live="polite"></p><button class="btn btn-ghost" type="reset" id="f-reset">Clear filters</button></div>')
            + "</form>")

def render_static_pages(cs):
    root = ""
    ordered = sorted(cs, key=lambda c: (list(REGIONS).index(c["region"]), c["name"]))
    n_open = sum(1 for c in cs if c["winter"].get("status") == "open")
    n_dump = sum(1 for c in cs if dump_has(c) == "yes")
    n_full = sum(1 for c in cs if c.get("completeness") == "full")
    regions = "".join(f'<li class="card region-card"><h3 class="card-title"><a href="regions/{r["slug"]}/index.html">{escape(r["name"])}</a></h3><p class="meta">{escape(r["is"])} · {sum(1 for c in cs if c["region"]==r["slug"])} campsite(s)</p></li>' for r in SITE["regions"])
    themes = "".join(f'<li class="card"><h3 class="card-title"><a href="themes/{t["slug"]}/index.html">{escape(t["name"])}</a></h3><p class="meta">{escape(t["blurb"][:120])}…</p></li>' for t in SITE["themes"])
    guides = "".join(guide_card(g, root) for g in GUIDES)
    featured = [c for c in ordered if c.get("completeness") == "full"]
    hero = ('<section class="hero" aria-labelledby="hero-h">'
            '<div class="hero-text"><p class="eyebrow">Campervan &amp; motorhome campsites · Iceland</p>'
            f'<h1 id="hero-h">Find a campsite in Iceland you can actually rely on</h1>'
            '<p class="lede">Winter opening, prices, electricity, showers, kitchens and dump stations – every fact linked to its source and dated. If we can\'t confirm it, we say <span class="unconfirmed">Unconfirmed</span> instead of guessing.</p>'
            + filter_form(root, action="campsites/index.html", hero=True)
            + '<ul class="quick" aria-label="Popular searches">'
              '<li><a href="themes/open-in-winter/index.html">Open in winter</a></li>'
              '<li><a href="themes/dump-stations/index.html">Dump stations</a></li>'
              + "".join(f'<li><a href="guides/{g["slug"]}/index.html">{escape(g.get("short", g["title"]))}</a></li>' for g in GUIDES[:3])
            + "</ul></div>"
            f'<div class="hero-map"><figure class="map-fig on-dark">{map_svg(cs, root, "Map of Iceland with all campsites on this site")}<figcaption>{map_legend()}</figcaption></figure></div>'
            "</section>")
    stats = (f'<ul class="stats" aria-label="Site at a glance"><li><strong>{len(cs)}</strong> campsites</li><li><strong>{n_open}</strong> confirmed open in winter</li>'
             f'<li><strong>{n_dump}</strong> with a dump station</li><li><strong>{len(GUIDES)}</strong> guides</li></ul>')
    how = ('<section class="how"><h2>How this site works</h2><ol class="steps">'
           '<li><strong>Sourced.</strong> Every fact links to the campsite\'s own site or an official listing.</li>'
           '<li><strong>Dated.</strong> Each fact shows when we last checked it.</li>'
           '<li><strong>Honest.</strong> Vague or conflicting information is marked Call ahead or Unconfirmed.</li></ol>'
           '<p><a href="about/index.html">Read our methodology</a></p></section>')
    body = (hero + stats
            + f'<h2>Guides</h2><ul class="cards guide-cards">{guides}</ul>'
            + f'<h2>Campsites with full pages</h2>{cards(featured, root)}<p><a class="btn" href="campsites/index.html">Browse and filter all {len(cs)} campsites</a></p>'
            + f'<h2>Browse by region</h2><ul class="cards region-cards">{regions}</ul>'
            + f'<h2>Browse by theme</h2><ul class="cards">{themes}</ul>' + how)
    ld = {"@context": "https://schema.org", "@type": "WebSite", "name": SITE["site_name"], "url": f"{BASE_URL}/", "inLanguage": "en"}
    write_page("index.html", f"{SITE['site_name']} – sourced campsite facts for Iceland", SITE["tagline"], body,
               '<script type="application/ld+json">' + json.dumps(ld, ensure_ascii=False) + "</script>", main_cls="home")
    # Campsites index with client-side filters (works without JS: all cards are listed)
    idx = (crumbs("../", [("All campsites", None)])
           + page_head("Directory", f"All campsites ({len(cs)})", "Filter by region, winter opening and facilities. Filters only match facilities a source confirms, so a site with an Unconfirmed facility is hidden when you tick that box.")
           + filter_form("../")
           + '<noscript><p class="callout">Filters need JavaScript. All campsites are listed below, grouped by region.</p></noscript>'
           + f'<div class="dir"><figure class="map-fig dir-map">{map_svg(cs, "../", "Map of all campsites on this site")}<figcaption>{map_legend()}{map_credit()}{unmapped(cs, "../")}</figcaption></figure>'
           + f'<div class="dir-list">{cards(ordered, "../", "filterable", heading="h2")}<p class="empty" id="empty" hidden>No campsite matches all of these filters. Try removing one.</p></div></div>'
           + '<script src="../static/filter.js" defer></script>')
    write_page("campsites/index.html", f"All campsites – filter by winter, electricity & dump station | {SITE['site_name']}",
               "All Iceland campsites on this site. Filter by region, open in winter, electricity, showers, dump station and kitchen.", idx)
    write_page("regions/index.html", f"Regions | {SITE['site_name']}", "Iceland campsites by region.",
               crumbs("../", [("Regions", None)]) + page_head("Browse", "Regions") + "<ul class='cards region-cards'>" + "".join(f'<li class="card"><h2 class="card-title"><a href="{r["slug"]}/index.html">{escape(r["name"])}</a></h2><p class="meta">{escape(r["is"])} · {sum(1 for c in cs if c["region"]==r["slug"])} campsite(s)</p><p class="meta">{escape(r["blurb"])}</p></li>' for r in SITE["regions"]) + "</ul>")
    write_page("themes/index.html", f"Themes | {SITE['site_name']}", "Iceland campsites by theme: winter opening, dump stations.",
               crumbs("../", [("Themes", None)]) + page_head("Browse", "Themes") + "<ul class='cards'>" + "".join(f'<li class="card"><h2 class="card-title"><a href="{t["slug"]}/index.html">{escape(t["name"])}</a></h2><p class="meta">{escape(t["blurb"])}</p></li>' for t in SITE["themes"]) + "</ul>")
    write_page("guides/index.html", f"Guides | {SITE['site_name']}", "Guides to camping in Iceland by campervan.",
               crumbs("../", [("Guides", None)]) + page_head("Read", "Guides") + "<ul class='cards guide-cards'>" + "".join(guide_card(g, "../").replace("<h3", "<h2").replace("</h3>", "</h2>") for g in GUIDES) + "</ul>")
    # About
    write_page("about/index.html", f"About, sources & methodology | {SITE['site_name']}", "How this site researches Iceland campsites: sources, check dates and the Unconfirmed rule.",
        crumbs("../", [("About, sources & methodology", None)]) + """<header class="page-head"><p class="eyebrow">About</p><h1>About, sources &amp; methodology</h1>
<p class="lede">An independent, English-language reference for campervan and motorhome travellers in Iceland. We are not affiliated with any campsite or with the official tourist board.</p></header><div class="prose">
<h2>Who runs this site</h2>
<p>This is an independent information site for motorhome and campervan travellers in Iceland. Facts are cited and dated from the campsites' own websites, <a href="https://tjalda.is/en" rel="nofollow noopener">tjalda.is</a>, <a href="https://www.ferdalag.is/en" rel="nofollow noopener">ferdalag.is</a> and municipality websites; anything we could not confirm is marked <span class="unconfirmed">Unconfirmed</span>. Content is prepared with AI assistance (see the <a href="../ai-disclosure/index.html">AI disclosure</a>), and the site may earn commissions from travel partners (see the <a href="../affiliate-disclosure/index.html">affiliate disclosure</a>).</p>
<h2>Our rules</h2>
<ul>
<li><strong>Every fact has a source.</strong> Each fact on a campsite page links to the page it came from and shows the date we checked it. The site's build script will not publish a fact without a source.</li>
<li><strong>Nothing is guessed.</strong> If we cannot confirm a price, opening date or facility from a real source, the page says <span class="unconfirmed">Unconfirmed</span>.</li>
<li><strong>Vague is labelled as vague.</strong> Official listings sometimes say a site is open in winter 'depending on weather' or 'upon request'. We mark those sites <em>Call ahead</em>, not <em>Open</em>. When sources contradict each other, we say so.</li>
<li><strong>Prices carry a year.</strong> Prices are shown in ISK with the year or season they apply to, exactly as the source publishes them.</li>
</ul>
<h2>Preferred sources, in order</h2>
<ol>
<li>The campsite's own website.</li>
<li><a href="https://tjalda.is/en" rel="nofollow noopener">Tjalda.is</a>, Iceland's national campsite directory (operated by Parka Lausnir ehf.).</li>
<li><a href="https://www.ferdalag.is/en" rel="nofollow noopener">Ferdalag.is</a> / <a href="https://www.visiticeland.com/" rel="nofollow noopener">Visit Iceland</a> (Icelandic Tourist Board listings).</li>
<li>Municipality and national park websites, e.g. <a href="https://www.vatnajokulsthjodgardur.is/en" rel="nofollow noopener">Vatnajökull National Park</a>.</li>
<li>Government guidance, e.g. <a href="https://uos.is/en/environment/ocean-water/emptying-portable-toilets" rel="nofollow noopener">Umhverfis- og orkustofnun on emptying portable toilets</a>.</li>
</ol>
<p>Traveller forums such as Reddit are used only as evidence of what travellers ask or report, and are always labelled as such. We never treat them as a source for a campsite's facts.</p>
<h2>Corrections</h2>
<p>Seasons and prices change every year. If you run a campsite and something here is out of date, the campsite's own website is always the authority. A corrections contact will be added here.</p></div>""")
    write_page("affiliate-disclosure/index.html", f"Affiliate disclosure | {SITE['site_name']}", "Affiliate and referral link disclosure.",
        crumbs("../", [("Affiliate disclosure", None)]) + """<header class="page-head"><p class="eyebrow">About</p><h1>Affiliate disclosure</h1></header><div class="prose">
<p>This site may in future contain referral (affiliate) links to campervan and motorhome rental companies in Iceland. If you book through one of those links, we may earn a commission at no extra cost to you.</p>
<p>Referral links will never affect which campsites we list or what we say about them. Campsite facts come only from the sources cited on each page.</p>
<p>We may also earn commissions from other travel partners in the same way, always at no extra cost to you.</p>
<p><strong>Current status:</strong> the site has no affiliate links yet. When we add any, we will label them clearly where they appear.</p></div>""")
    write_page("ai-disclosure/index.html", f"AI disclosure | {SITE['site_name']}", "How AI assistance is used to prepare this site, and why you should verify hours and prices with the campsite.",
        crumbs("../", [("AI disclosure", None)]) + """<header class="page-head"><p class="eyebrow">About</p><h1>AI disclosure</h1></header><div class="prose">
<p>Content on this site is prepared with the help of AI tools: researching public sources, extracting facts, and drafting and checking pages.</p>
<p>Facts about campsites come only from the public sources cited on each page (campsite websites, <a href="https://tjalda.is/en" rel="nofollow noopener">tjalda.is</a>, <a href="https://www.ferdalag.is/en" rel="nofollow noopener">ferdalag.is</a>, municipalities and national parks), each with the date it was checked. If a fact could not be confirmed from a source, it is marked <span class="unconfirmed">Unconfirmed</span> rather than filled in.</p>
<p>AI-assisted research can still make mistakes, and campsites change their seasons and prices. Please verify opening hours, winter access and prices with the campsite before you travel.</p>
<p>See <a href="../about/index.html">About, sources &amp; methodology</a> for how sources are chosen.</p></div>""")
    # 404.html is served for any missing URL at any depth, so it must use base-path-absolute links.
    base_path = urlparse(BASE_URL).path.rstrip("/") + "/"
    write_page("404.html", f"Page not found | {SITE['site_name']}", "Page not found.",
               f'<h1>Page not found</h1><p><a href="{base_path}index.html">Go to the home page</a>.</p>', robots="noindex", root=base_path)

def write_sitemap():
    urls = "\n".join(f"  <url><loc>{BASE_URL}/{p}</loc><lastmod>{BUILD_DATE}</lastmod></url>" for p in sorted(set(PAGES)))
    open(os.path.join(DIST, "sitemap.xml"), "w").write(f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urls}\n</urlset>\n')
    open(os.path.join(DIST, "robots.txt"), "w").write(f"User-agent: *\nAllow: /\nSitemap: {BASE_URL}/sitemap.xml\n")

def main():
    global GUIDES
    cs = load_dir("campsites"); GUIDES = load_dir("guides")
    for c in cs: validate(c)
    if ERRORS: sys.exit("VALIDATION FAILED:\n" + "\n".join(ERRORS))
    if os.path.isdir(DIST): shutil.rmtree(DIST)
    os.makedirs(DIST)
    shutil.copytree(os.path.join(ROOT, "static"), os.path.join(DIST, "static"))
    by_slug = {c["slug"]: c for c in cs}
    for c in cs: render_campsite(c)
    for r in SITE["regions"]: render_region(r, cs)
    for t in SITE["themes"]: render_theme(t, cs)
    for g in GUIDES: render_guide(g, by_slug)
    render_static_pages(cs)
    write_sitemap()
    gen_llms.write(DIST, BASE_URL, SITE, cs, GUIDES)   # dist/llms.txt (llmstxt.org), from data + built pages
    if ERRORS: sys.exit("BUILD FAILED:\n" + "\n".join(ERRORS))
    print(f"Built {len(PAGES)} indexable pages ({len(cs)} campsites, {len(GUIDES)} guides) into dist/  base_url={BASE_URL}")

GUIDES = []
if __name__ == "__main__":
    main()
