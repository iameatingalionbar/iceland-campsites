#!/usr/bin/env python3
"""Post-build checks for dist/: internal links resolve, anchors exist, tags balance,
SEO meta present, sitemap entries exist. Exit code 1 on any problem. Stdlib only."""
import os, sys, re, glob
from html.parser import HTMLParser
from urllib.parse import urlparse, unquote

DIST = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dist")
def detect_base():
    """BASE_URL from env, else from the canonical link of dist/index.html."""
    if os.environ.get("BASE_URL"): return os.environ["BASE_URL"].rstrip("/")
    m = re.search(r'<link rel="canonical" href="([^"]+)"', open(os.path.join(DIST, "index.html"), encoding="utf-8").read())
    return m.group(1).rstrip("/") if m else ""
BASE_URL = detect_base()
BASE_PATH = urlparse(BASE_URL).path.rstrip("/")   # e.g. "/iceland-campsites" or ""
def strip_base(path):
    """Map a site-absolute URL path to a path relative to dist/."""
    if BASE_PATH and (path == BASE_PATH or path.startswith(BASE_PATH + "/")):
        path = path[len(BASE_PATH):]
    elif BASE_PATH and path.startswith("/"):
        return None  # absolute path outside the base path -> broken when served under the subpath
    return path.lstrip("/")
VOID = {"area","base","br","col","embed","hr","img","input","link","meta","source","track","wbr"}
problems, ext_links = [], set()

class P(HTMLParser):
    def __init__(s):
        super().__init__(); s.stack=[]; s.links=[]; s.ids=[]; s.meta={}; s.has_title=False; s.h1=0; s.lang=None
    def handle_starttag(s, t, a):
        a=dict(a)
        if t=="html": s.lang=a.get("lang")
        if t not in VOID: s.stack.append((t, s.getpos()))
        if "id" in a: s.ids.append(a["id"])
        if t=="a" and "href" in a: s.links.append(a["href"])
        if t=="link" and a.get("rel")=="stylesheet": s.links.append(a["href"])
        if t=="link" and a.get("rel")=="canonical":
            s.meta["canonical"]=a.get("href")
            if BASE_URL and not a.get("href","").startswith(BASE_URL): problems.append(f"{s.file}: canonical not under BASE_URL")
        if t=="meta" and a.get("name")=="description": s.meta["description"]=a.get("content")
        if t=="meta" and a.get("name")=="viewport": s.meta["viewport"]=1
        if t=="title": s.has_title=True
        if t=="h1": s.h1+=1
        if t=="img" and "alt" not in a: problems.append(f"{s.file}: <img> without alt")
    def handle_startendtag(s,t,a): s.handle_starttag(t,a); (t not in VOID) and s.stack.pop()
    def handle_endtag(s, t):
        if t in VOID: return
        if not s.stack or s.stack[-1][0]!=t:
            problems.append(f"{s.file}: unexpected </{t}> at {s.getpos()} (open: {s.stack[-1] if s.stack else None})")
            for i in range(len(s.stack)-1,-1,-1):
                if s.stack[i][0]==t: del s.stack[i:]; break
        else: s.stack.pop()

pages = {}
for f in glob.glob(os.path.join(DIST, "**", "*.html"), recursive=True):
    p=P(); p.file=os.path.relpath(f,DIST); p.feed(open(f,encoding="utf-8").read()); p.close(); pages[f]=p
    if p.stack: problems.append(f"{p.file}: unclosed tags {[x[0] for x in p.stack]}")
    if not p.has_title: problems.append(f"{p.file}: no <title>")
    if p.h1!=1: problems.append(f"{p.file}: {p.h1} <h1> elements")
    if not p.lang: problems.append(f"{p.file}: no lang attribute")
    for k in ("canonical","description","viewport"):
        if k not in p.meta: problems.append(f"{p.file}: missing {k}")
    dup={i for i in p.ids if p.ids.count(i)>1}
    if dup: problems.append(f"{p.file}: duplicate ids {dup}")

for f,p in pages.items():
    for href in p.links:
        u=urlparse(href)
        if u.scheme in ("http","https","mailto","tel"): ext_links.add(href); continue
        if u.scheme: continue
        path=unquote(u.path)
        if path=="": target=f
        elif path.startswith("/"):
            rel=strip_base(path)
            if rel is None: problems.append(f"{p.file}: absolute link outside base path {href}"); continue
            target=os.path.join(DIST, rel)
        else: target=os.path.normpath(os.path.join(os.path.dirname(f), path))
        if os.path.isdir(target): target=os.path.join(target,"index.html")
        if not os.path.exists(target): problems.append(f"{p.file}: broken link {href}"); continue
        if u.fragment and target in pages and u.fragment not in pages[target].ids:
            problems.append(f"{p.file}: missing anchor #{u.fragment} in {href}")

sm=open(os.path.join(DIST,"sitemap.xml")).read()
for loc in re.findall(r"<loc>([^<]+)</loc>", sm):
    if BASE_URL and not loc.startswith(BASE_URL + "/"): problems.append(f"sitemap: {loc} not under BASE_URL {BASE_URL}"); continue
    path=strip_base(urlparse(loc).path)
    t=os.path.join(DIST, path, "index.html") if (path=="" or path.endswith("/")) else os.path.join(DIST,path)
    if not os.path.exists(t): problems.append(f"sitemap: {loc} has no file")

# llms.txt (llmstxt.org): exists, H1 + blockquote, every link under BASE_URL resolves to a built file, every sitemap URL listed
llms_path=os.path.join(DIST,"llms.txt"); llms_links=[]
if not os.path.exists(llms_path): problems.append("llms.txt: missing from dist/")
else:
    lt=open(llms_path,encoding="utf-8").read(); lines=lt.splitlines()
    if not lines or not lines[0].startswith("# "): problems.append("llms.txt: first line is not an H1")
    if not any(l.startswith("> ") for l in lines[:4]): problems.append("llms.txt: no blockquote summary after the H1")
    if "## Optional" not in lines: problems.append("llms.txt: no '## Optional' section")
    llms_links=re.findall(r"^- \[[^\]]+\]\(([^)\s]+)\)", lt, re.M)
    if not llms_links: problems.append("llms.txt: no links")
    for url in llms_links:
        if BASE_URL and not url.startswith(BASE_URL + "/"): problems.append(f"llms.txt: {url} not under BASE_URL {BASE_URL}"); continue
        path=strip_base(urlparse(url).path)
        t=os.path.join(DIST, path, "index.html") if (path=="" or path.endswith("/")) else os.path.join(DIST,path)
        if path is None or not os.path.exists(t): problems.append(f"llms.txt: {url} has no built page")
    for loc in re.findall(r"<loc>([^<]+)</loc>", sm):
        if loc not in llms_links: problems.append(f"llms.txt: sitemap URL {loc} not listed")
    print(f"llms.txt: {len(llms_links)} links checked.")

# CNAME (GitHub Pages custom domain): must match the BASE_URL host for a root custom domain, absent for github.io builds
_host = urlparse(BASE_URL).hostname or ""; _cn = os.path.join(DIST, "CNAME")
if _host.endswith(".github.io") or not _host:
    if os.path.exists(_cn): problems.append("CNAME present in a github.io build")
else:
    if BASE_PATH: problems.append(f"custom domain BASE_URL must have no path prefix, got {BASE_PATH!r}")
    if not os.path.exists(_cn): problems.append("dist/CNAME missing for custom-domain build")
    elif open(_cn).read().strip() != _host: problems.append(f"dist/CNAME {open(_cn).read().strip()!r} != BASE_URL host {_host!r}")
    else: print(f"CNAME: {_host}")

# robots.txt points at this BASE_URL's sitemap; no stale base URLs/prefixes anywhere in the output
_rb = os.path.join(DIST, "robots.txt")
if not os.path.exists(_rb) or f"Sitemap: {BASE_URL}/sitemap.xml" not in open(_rb).read(): problems.append("robots.txt: Sitemap line missing or not under BASE_URL")
for _f in glob.glob(os.path.join(DIST, "**", "*"), recursive=True):
    if os.path.isfile(_f) and _f.endswith((".html", ".xml", ".txt", ".js", ".css")):
        _t = open(_f, encoding="utf-8").read()
        for _stale in ("iameatingalionbar.github.io", "www.example.com"):
            if _stale in _t and _stale not in BASE_URL: problems.append(f"{os.path.relpath(_f, DIST)}: contains stale base URL {_stale!r}")
        if not BASE_PATH and re.search(r'(href|src|action)="/iceland-campsites', _t): problems.append(f"{os.path.relpath(_f, DIST)}: hard-coded /iceland-campsites prefix")

unc=sum(open(f,encoding="utf-8").read().count('class="unconfirmed"') for f in pages)
print(f"BASE_URL={BASE_URL!r} base path={BASE_PATH!r}")
print(f"Checked {len(pages)} HTML files, {len(ext_links)} distinct external links (not fetched), {unc} visible 'Unconfirmed' markers.")
if problems:
    print("PROBLEMS:"); print("\n".join(problems)); sys.exit(1)
print("OK: no broken internal links, tags balanced, SEO meta present.")
