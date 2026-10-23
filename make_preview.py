#!/usr/bin/env python3
"""Make a standalone single-file copy of the South Coast winter guide (CSS inlined)."""
import os, re
ROOT=os.path.dirname(os.path.abspath(__file__))
src=os.path.join(ROOT,"dist/guides/south-coast-winter-campsites/index.html")
css=open(os.path.join(ROOT,"dist/static/style.css"),encoding="utf-8").read()
html=open(src,encoding="utf-8").read()
html=re.sub(r'<link rel="stylesheet" href="[^"]+">', "<style>\n"+css+"\n</style>", html)
open(os.path.join(ROOT,"south-coast-winter-preview.html"),"w",encoding="utf-8").write(html)
print("wrote south-coast-winter-preview.html")
