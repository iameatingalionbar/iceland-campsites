#!/usr/bin/env python3
"""Serve dist/ under its BASE_URL path (e.g. /iceland-campsites/) on localhost and crawl every
internal href/src/stylesheet from the home page, plus every sitemap URL and a missing URL (404 page assets).
Exit 1 on any non-200. Stdlib only."""
import os, sys, re, shutil, tempfile, threading, functools, http.server, urllib.request, urllib.error
from urllib.parse import urlparse, urljoin, urldefrag
from html.parser import HTMLParser
ROOT=os.path.dirname(os.path.abspath(__file__)); DIST=os.path.join(ROOT,"dist")
m=re.search(r'<link rel="canonical" href="([^"]+)"', open(os.path.join(DIST,"index.html"),encoding="utf-8").read())
BASE_URL=os.environ.get("BASE_URL", m.group(1) if m else "").rstrip("/")
BASE_PATH=urlparse(BASE_URL).path.rstrip("/")
tmp=tempfile.mkdtemp(); site=os.path.join(tmp, BASE_PATH.lstrip("/")) if BASE_PATH else tmp
if BASE_PATH: shutil.copytree(DIST, site)
else: shutil.rmtree(tmp); shutil.copytree(DIST, tmp)
class H(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*a): pass
    def send_error(self, code, message=None, explain=None):
        if code==404:  # mimic GitHub Pages: serve <base>/404.html with status 404
            body=open(os.path.join(site,"404.html"),"rb").read()
            self.send_response(404); self.send_header("Content-Type","text/html"); self.send_header("Content-Length",str(len(body))); self.end_headers(); self.wfile.write(body); return
        super().send_error(code,message,explain)
srv=http.server.ThreadingHTTPServer(("127.0.0.1",0), functools.partial(H, directory=tmp))
threading.Thread(target=srv.serve_forever,daemon=True).start()
origin=f"http://127.0.0.1:{srv.server_address[1]}"; start=f"{origin}{BASE_PATH}/"
class L(HTMLParser):
    def __init__(s): super().__init__(); s.l=[]
    def handle_starttag(s,t,a):
        a=dict(a)
        for k in ("href","src"):
            if a.get(k): s.l.append(a[k])
def get(u):
    try:
        r=urllib.request.urlopen(u); return r.status, r.read().decode("utf-8","replace"), r.headers.get("Content-Type","")
    except urllib.error.HTTPError as e: return e.code, e.read().decode("utf-8","replace"), ""
seen,bad,queue=set(),[],[start]
sm=open(os.path.join(DIST,"sitemap.xml")).read()
queue+= [origin+urlparse(x).path for x in re.findall(r"<loc>([^<]+)</loc>",sm)]
queue.append(f"{start}llms.txt")  # llms.txt itself, plus every page it links to
if os.path.exists(os.path.join(DIST,"llms.txt")):
    queue+= [origin+urlparse(x).path for x in re.findall(r"^- \[[^\]]+\]\(([^)\s]+)\)", open(os.path.join(DIST,"llms.txt"),encoding="utf-8").read(), re.M)]
while queue:
    u=urldefrag(queue.pop())[0]
    if u in seen: continue
    seen.add(u); st,body,ct=get(u)
    if st!=200: bad.append(f"{st} {u}"); continue
    if u.endswith("/") or u.endswith(".html"):
        p=L(); p.feed(body)
        for h in p.l:
            if h.startswith("#"): continue
            nu=urljoin(u,h)
            if nu.startswith(origin): queue.append(nu)
# 404 page from a deep missing path: its assets/links must resolve
missing=f"{start}no/such/page/"
st,body,_=get(missing)
p=L(); p.feed(body)
for h in p.l:
    if h.startswith("#"): continue
    nu=urljoin(missing,h)
    if nu.startswith(origin):
        s2=get(nu)[0]; seen.add(nu)
        if s2!=200: bad.append(f"{s2} {nu} (linked from 404 page)")
if st!=404: bad.append(f"missing page returned {st}, expected 404")
srv.shutdown(); shutil.rmtree(tmp, ignore_errors=True)
print(f"Served dist at {BASE_PATH or '/'}; crawled {len(seen)} URLs.")
if bad: print("BROKEN:\n"+"\n".join(bad)); sys.exit(1)
print("OK: every internal link, stylesheet and sitemap URL returned 200 under the subpath.")
