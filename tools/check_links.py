#!/usr/bin/env python3
"""Check links in the built site.

  python tools/check_links.py [site_dir]            # internal links and #anchors (fast, offline)
Exit 1 if any internal link or anchor is broken.
"""
import argparse, re, sys, urllib.parse
from pathlib import Path

HREF = re.compile(r'(?:href|src)="([^"]+)"')
ID = re.compile(r'id="([^"]+)"')

def internal(site):
    site = Path(site); ids, n, bad = {}, 0, []
    def anchors(p):
        if p not in ids: ids[p] = set(ID.findall(p.read_text(encoding="utf-8")))
        return ids[p]
    for f in sorted(site.rglob("*.html")):
        for u in HREF.findall(f.read_text(encoding="utf-8")):
            if re.match(r"(https?:|mailto:|data:|javascript:)", u): continue
            n += 1; path, _, frag = u.partition("#")
            tgt = (f.parent / urllib.parse.unquote(path)).resolve() if path else f.resolve()
            if tgt.is_dir(): tgt = tgt / "index.html"
            if not tgt.exists(): bad.append(f"{f}: missing {u}")
            elif frag and tgt.suffix == ".html" and frag not in anchors(tgt): bad.append(f"{f}: bad anchor {u}")
    return n, bad

def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("site", nargs="?", default="site")
    a = ap.parse_args(argv)
    n, bad = internal(a.site)
    for b in bad: print("BROKEN", b)
    print(f"{n} links, {len(bad)} broken")
    return 1 if bad else 0

if __name__ == "__main__":
    sys.exit(main())
