#!/usr/bin/env python3
"""Static site builder for Iceland Campsites. Python 3 standard library only.

Usage:  python3 build.py              # builds into dist/
        BASE_URL=https://mysite.is python3 build.py
Reads data/site.json, data/campsites/*.json, data/guides/*.json and templates/base.html.
Fails loudly if any fact has a value without a source, or cites an unknown source key.
"""
import json, os, sys, shutil, glob, datetime, re
from html import escape
from string import Template

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

def write_page(rel, title, description, body, head_extra="", robots="index,follow"):
    depth = rel.count("/")
    root = "../" * depth
    canon_path = rel[:-len("index.html")] if rel.endswith("index.html") else rel
    html = TEMPLATE.substitute(title=escape(title), description=escape(description), canonical=f"{BASE_URL}/{canon_path}",
                               robots=robots, head_extra=head_extra, root=root, body=body, site_name=escape(SITE["site_name"]),
                               build_date=BUILD_DATE)
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
        f = c["facts"].get(key)
        row(escape(label), fact_html(f, cites, o))
    facts_table = '<div class="table-wrap"><table class="facts"><caption class="meta" style="text-align:left;padding:.5rem .65rem">Key facts</caption><tbody>' + "\n".join(rows) + "</tbody></table></div>"

    p = c["prices"]
    prow = [f'<tr><th scope="row">{escape(i["label"])}</th><td>{fact_html(i, cites, o)}</td></tr>' for i in p["items"]]
    prices = (f'<p>Currency: {escape(p.get("currency","ISK"))}. Applies to: {fact_html(p.get("applies_to"), cites, o)}</p>'
              '<div class="table-wrap"><table class="facts"><tbody>' + "\n".join(prow) + "</tbody></table></div>")
    intro = f'<p class="lede">{fact_html(c.get("intro"), cites, o, with_checked=False)}</p>' if c.get("intro") else ""
    practical = ""
    if c.get("practical"):
        practical = '<h2 id="tips">Practical tips</h2><ul class="tips">' + "".join(f"<li>{fact_html(t, cites, o)}</li>" for t in c["practical"]) + "</ul>"
    stub = ""
    if c.get("completeness") == "stub":
        stub = '<div class="callout warn"><strong>Short entry.</strong> This page covers the basics we could source so far. Anything we have not been able to confirm is marked Unconfirmed.</div>'
    alt = f'<p class="meta">Also known as: {escape(", ".join(c["alt_names"]))}</p>' if c.get("alt_names") else ""
    body = (crumbs(root, [("Regions", "regions/index.html"), (reg["name"], f'regions/{reg["slug"]}/index.html'), (c["name"], None)])
            + f"<h1>{escape(c['name'])}</h1>{alt}"
            + f'<p class="meta">Facts last checked {escape(c["checked"])}. Each fact shows its source number and check date; full list under <a href="#sources">Sources</a>.</p>'
            + stub + intro + facts_table
            + f'<h2 id="prices">Prices</h2>{prices}' + practical
            + f'<h2 id="sources">Sources</h2>{cites.listing()}'
            + '<p class="meta">Spotted something out of date? Please check the campsite\'s own website. Prices and seasons change from year to year.</p>')
    desc = f"{c['name']} in {reg['name']}, Iceland: winter opening, prices, electricity, showers, dump station and more. Every fact sourced, checked {c['checked']}."
    ld = {"@context": "https://schema.org", "@type": "Campground", "name": c["name"], "url": f"{BASE_URL}/campsites/{c['slug']}/"}
    if loc.get("lat") is not None: ld["geo"] = {"@type": "GeoCoordinates", "latitude": loc["lat"], "longitude": loc["lon"]}
    if loc.get("address", {}).get("value"): ld["address"] = loc["address"]["value"]
    head = '<script type="application/ld+json">' + json.dumps(ld, ensure_ascii=False) + "</script>"
    write_page(f"campsites/{c['slug']}/index.html", f"{c['name']} – campsite facts & prices | {SITE['site_name']}", desc, body, head)

def campsite_list_table(cs, root, cites=None):
    if not cs: return '<p><em>No campsites added yet for this list. See the <a href="' + root + 'about/index.html">methodology</a>; more pages are added regularly.</em></p>'
    rows = []
    for c in cs:
        el = short_text(c["facts"].get("electricity")) or "Unconfirmed"
        dh = {"yes": "Yes", "nearby": "Not on site (nearby)", "no": "No", None: "Unconfirmed"}[dump_has(c)]
        rows.append(f'<tr><th scope="row"><a href="{campsite_url(c["slug"], root)}">{escape(c["name"])}</a></th>'
                    f'<td>{escape(REGIONS[c["region"]]["name"])}</td><td>{winter_badge(c["winter"].get("status"))}</td>'
                    f'<td>{escape(el)}</td><td>{escape(dh)}</td></tr>')
    return ('<div class="table-wrap"><table><thead><tr><th scope="col">Campsite</th><th scope="col">Region</th><th scope="col">Winter</th>'
            '<th scope="col">Electricity</th><th scope="col">Dump station</th></tr></thead><tbody>' + "\n".join(rows) + "</tbody></table></div>"
            '<p class="meta">Summary only. Open each campsite page for sources, check dates and details.</p>')

def render_region(r, cs):
    root = "../../"
    mine = [c for c in cs if c["region"] == r["slug"]]
    gs = [g for g in GUIDES if g.get("region") == r["slug"]]
    guides = ("<h2>Guides</h2><ul>" + "".join(f'<li><a href="{root}guides/{g["slug"]}/index.html">{escape(g["title"])}</a></li>' for g in gs) + "</ul>") if gs else ""
    body = (crumbs(root, [("Regions", "regions/index.html"), (r["name"], None)])
            + f'<h1>Campsites in {escape(r["name"])} <span class="meta">({escape(r["is"])})</span></h1><p class="lede">{escape(r["blurb"])}</p>'
            + guides + f"<h2>Campsites ({len(mine)})</h2>" + campsite_list_table(mine, root))
    write_page(f"regions/{r['slug']}/index.html", f"Campsites in {r['name']}, Iceland | {SITE['site_name']}",
               f"Campervan-friendly campsites in {r['name']} ({r['is']}), Iceland, with sourced winter opening, electricity and dump station info.", body)

def render_theme(t, cs):
    root = "../../"
    if t["filter"] == "winter":
        order = ["open", "call-ahead", "partial"]
        sel = sorted([c for c in cs if c["winter"].get("status") in order], key=lambda c: (order.index(c["winter"]["status"]), c["region"], c["name"]))
        content = ('<div class="legend">' + "".join(winter_badge(s) for s in ["open", "call-ahead", "partial"]) + "</div>"
                   + "<p>Sites marked <strong>Call ahead</strong> are listed as open in winter by some source, but the wording is vague (for example 'depending on weather' or 'upon request'), or sources conflict. <strong>Shoulder season only</strong> means open into late autumn or from early spring, but not all winter. Campsites confirmed closed in winter are left off this list.</p>"
                   + campsite_list_table(sel, root))
    else:
        content = ""
        for r in SITE["regions"]:
            sel = [c for c in cs if c["region"] == r["slug"] and dump_has(c) in ("yes",)]
            content += f'<h2>{escape(r["name"])}</h2>' + (campsite_list_table(sel, root) if sel else '<p><em>No campsite with a confirmed disposal point added for this region yet.</em></p>')
        near = [c for c in cs if dump_has(c) == "nearby"]
        if near:
            content += "<h2>Campsites without their own disposal point (nearby station)</h2>" + campsite_list_table(near, root)
    body = crumbs(root, [("Themes", "themes/index.html"), (t["name"], None)]) + f'<h1>{escape(t["name"])}</h1><p class="lede">{escape(t["blurb"])}</p>' + content
    write_page(f"themes/{t['slug']}/index.html", f"{t['name']} – Iceland campsites | {SITE['site_name']}", t["blurb"][:155], body)

def render_guide(g, cs_by_slug):
    root = "../../"
    owner = g["_file"]
    # merge sources: guide sources + each listed campsite's sources (namespaced)
    sources = dict(g["sources"])
    for slug in g["campsites"]:
        c = cs_by_slug.get(slug)
        if not c: ERRORS.append(f"{owner}: unknown campsite '{slug}'"); continue
        for k, s in c["sources"].items(): sources[f"{slug}:{k}"] = s
    cites = Cites(sources, owner)
    def ns(slug, keys): return [f"{slug}:{k}" for k in (keys or [])]
    intro = "".join(f"<p>{fact_html(p, cites, owner, with_checked=False)}</p>" for p in g["intro"])
    rows = []
    for slug in g["campsites"]:
        c = cs_by_slug.get(slug)
        if not c: continue
        w = c["winter"]
        def nf(f):
            if not f or not f.get("value"): return f
            return {**f, "src": ns(slug, f.get("src"))}
        el, dump = nf(c["facts"].get("electricity")), nf(c["facts"].get("dump_station"))
        adult = next((i for i in c["prices"]["items"] if i["label"].lower().startswith(("adult", "per person"))), None)
        price = fact_html(nf(adult), cites, owner, with_checked=False) if adult else '<span class="unconfirmed">Unconfirmed</span>'
        if adult and adult.get("value"): price = escape(adult["label"]) + ": " + price
        srcs = sorted({k for f in [nf(w), el, dump, nf(adult), nf(c["season"])] if f and f.get("value") for k in f.get("src", [])})
        loc = c["location"]; ml = map_links(c)
        loc_html = escape(c.get("town", "")) + (f'<br><span class="meta">{loc["lat"]:.4f}, {loc["lon"]:.4f}</span>' if ml else "")
        rows.append(f'<tr><th scope="row"><a href="{campsite_url(slug, root)}">{escape(c["name"])}</a></th><td>{loc_html}</td>'
                    f'<td class="wcol">{winter_badge(w.get("status"))}<br>{fact_html(nf(w), cites, owner, with_checked=False)}</td>'
                    f'<td>{fact_html(el, cites, owner, with_checked=False)}</td><td>{fact_html(dump, cites, owner, with_checked=False)}</td>'
                    f'<td>{price}</td><td>{cites.sup(srcs)}</td><td class="checked">{escape(c["checked"])}</td></tr>')
    table = ('<div class="table-wrap" tabindex="0" role="region" aria-label="Winter campsite table (scrolls sideways on small screens)"><table class="guide"><caption class="meta" style="text-align:left;padding:.5rem .65rem">Listed roughly west to east along the Ring Road. Prices are 2026 rates as published.</caption>'
             '<thead><tr><th scope="col">Campsite</th><th scope="col">Location</th><th scope="col">Winter status</th><th scope="col">Electricity</th>'
             '<th scope="col">Dump station</th><th scope="col">Price (if confirmed)</th><th scope="col">Sources</th><th scope="col">Checked</th></tr></thead><tbody>'
             + "\n".join(rows) + "</tbody></table></div>")
    legend = ('<div class="legend">' + "".join(winter_badge(s) for s in ["open", "call-ahead", "partial", "closed"]) + '<span class="unconfirmed">Unconfirmed</span></div>'
              '<p class="meta"><strong>Open in winter</strong>: the campsite or an official listing states it is open through winter. <strong>Call ahead</strong>: listed as open in winter, but the wording is vague or sources conflict. <strong>Shoulder season only</strong>: open into late autumn or from early spring, not all winter. <strong>Closed in winter</strong>: published season ends before winter.</p>')
    tips = "<h2>Practical winter tips</h2><ul class='tips'>" + "".join(f"<li>{fact_html(t, cites, owner)}</li>" for t in g["tips"]) + "</ul>"
    demand = f'<h2>What travellers ask</h2><p>{fact_html(g["demand"], cites, owner)}</p>' if g.get("demand") else ""
    body = (crumbs(root, [("Guides", "guides/index.html"), (g["title"], None)]) + f"<h1>{escape(g['title'])}</h1>"
            + f'<p class="meta">All facts checked {escape(g["checked"])}. Source numbers link to the original page; see the full list under <a href="#sources">Sources</a>.</p>'
            + intro + f'<p class="callout">{escape(g["scope_note"])}</p>'
            + "<h2>At a glance</h2>" + legend + table + tips + demand
            + '<div class="callout warn">Winter seasons, prices and facilities can change at short notice. Contact the campsite before relying on it, especially sites marked Call ahead.</div>'
            + f'<h2 id="sources">Sources</h2>{cites.listing()}')
    write_page(f"guides/{g['slug']}/index.html", f"{g['title']} | {SITE['site_name']}", g["description"], body)

def render_static_pages(cs):
    # Home
    root = ""
    regions = "".join(f'<li><h3><a href="regions/{r["slug"]}/index.html">{escape(r["name"])}</a></h3><p class="meta">{escape(r["is"])} · {sum(1 for c in cs if c["region"]==r["slug"])} campsite(s)</p></li>' for r in SITE["regions"])
    themes = "".join(f'<li><h3><a href="themes/{t["slug"]}/index.html">{escape(t["name"])}</a></h3><p class="meta">{escape(t["blurb"][:120])}…</p></li>' for t in SITE["themes"])
    guides = "".join(f'<li><h3><a href="guides/{g["slug"]}/index.html">{escape(g["title"])}</a></h3><p class="meta">{escape(g["description"])}</p></li>' for g in GUIDES)
    body = (f"<h1>{escape(SITE['site_name'])}</h1>"
            f'<p class="lede">An English guide to campsites in Iceland for people travelling by campervan or motorhome. For each site we list winter opening, prices, electricity, showers, kitchens and dump stations. Every fact links to its source and shows when it was checked; if we can\'t confirm something, we mark it <span class="unconfirmed">Unconfirmed</span> instead of guessing.</p>'
            f'<h2>Guides</h2><ul class="cards">{guides}</ul><h2>Browse by region</h2><ul class="cards">{regions}</ul>'
            f'<h2>Browse by theme</h2><ul class="cards">{themes}</ul>'
            f'<p><a href="campsites/index.html">See all {len(cs)} campsites</a> · <a href="about/index.html">How we research</a></p>')
    write_page("index.html", f"{SITE['site_name']} – sourced campsite facts for Iceland", SITE["tagline"], body)
    # Indexes
    write_page("campsites/index.html", f"All campsites | {SITE['site_name']}", "All Iceland campsites on this site with winter status, electricity and dump station summary.",
               crumbs("../", [("All campsites", None)]) + "<h1>All campsites</h1>" + campsite_list_table(sorted(cs, key=lambda c: (list(REGIONS).index(c["region"]), c["name"])), "../"))
    write_page("regions/index.html", f"Regions | {SITE['site_name']}", "Iceland campsites by region.",
               crumbs("../", [("Regions", None)]) + "<h1>Regions</h1><ul class='cards'>" + "".join(f'<li><h3><a href="{r["slug"]}/index.html">{escape(r["name"])}</a></h3><p class="meta">{escape(r["blurb"])}</p></li>' for r in SITE["regions"]) + "</ul>")
    write_page("themes/index.html", f"Themes | {SITE['site_name']}", "Iceland campsites by theme: winter opening, dump stations.",
               crumbs("../", [("Themes", None)]) + "<h1>Themes</h1><ul class='cards'>" + "".join(f'<li><h3><a href="{t["slug"]}/index.html">{escape(t["name"])}</a></h3><p class="meta">{escape(t["blurb"])}</p></li>' for t in SITE["themes"]) + "</ul>")
    write_page("guides/index.html", f"Guides | {SITE['site_name']}", "Guides to camping in Iceland by campervan.",
               crumbs("../", [("Guides", None)]) + "<h1>Guides</h1><ul class='cards'>" + "".join(f'<li><h3><a href="{g["slug"]}/index.html">{escape(g["title"])}</a></h3><p class="meta">{escape(g["description"])}</p></li>' for g in GUIDES) + "</ul>")
    # About
    write_page("about/index.html", f"About, sources & methodology | {SITE['site_name']}", "How this site researches Iceland campsites: sources, check dates and the Unconfirmed rule.",
        crumbs("../", [("About, sources & methodology", None)]) + """<h1>About, sources &amp; methodology</h1>
<p class="lede">An independent, English-language reference for campervan and motorhome travellers in Iceland. We are not affiliated with any campsite or with the official tourist board.</p>
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
<p>Seasons and prices change every year. If you run a campsite and something here is out of date, the campsite's own website is always the authority. A corrections contact will be added here.</p>""")
    write_page("affiliate-disclosure/index.html", f"Affiliate disclosure | {SITE['site_name']}", "Affiliate and referral link disclosure.",
        crumbs("../", [("Affiliate disclosure", None)]) + """<h1>Affiliate disclosure</h1>
<p>This site may in future contain referral (affiliate) links to campervan and motorhome rental companies in Iceland. If you book through one of those links, we may earn a commission at no extra cost to you.</p>
<p>Referral links will never affect which campsites we list or what we say about them. Campsite facts come only from the sources cited on each page.</p>
<p><strong>Current status:</strong> the site has no affiliate links yet. When we add any, we will label them clearly where they appear.</p>""")
    write_page("404.html", f"Page not found | {SITE['site_name']}", "Page not found.",
               '<h1>Page not found</h1><p><a href="/index.html">Go to the home page</a>.</p>', robots="noindex")

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
    if ERRORS: sys.exit("BUILD FAILED:\n" + "\n".join(ERRORS))
    print(f"Built {len(PAGES)} indexable pages ({len(cs)} campsites, {len(GUIDES)} guides) into dist/  base_url={BASE_URL}")

GUIDES = []
if __name__ == "__main__":
    main()
