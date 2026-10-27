#!/usr/bin/env python3
"""Check links in the built site.

  python tools/check_links.py [site_dir]            # internal links and #anchors (fast, offline)
  python tools/check_links.py --external [dossier ...] [--report linkrot.md]
                                                    # fetch every source url; suggest a Wayback copy for dead ones
Exit 1 if any internal link or anchor is broken, or (with --external) any source url is dead.
Hosts that refuse bots (401/403/429) are reported as "blocked", not dead.
"""
import argparse, re, sys, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor
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

UA = "Mozilla/5.0 (dossier-framework link check)"
BLOCKED = {401, 403, 405, 406, 429, 451, 999}

def status(url, timeout=20):
    """HTTP status for url (HEAD, then GET if HEAD is refused); 0 on network failure."""
    for method in ("HEAD", "GET"):
        try:
            req = urllib.request.Request(url, method=method, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=timeout) as r: return r.status
        except urllib.error.HTTPError as e:
            if method == "GET" or e.code not in BLOCKED | {404, 400, 500, 501}: return e.code
        except Exception:
            if method == "GET": return 0
    return 0

def front(p):
    m = re.match(r"---\n(.*?)\n---", p.read_text(encoding="utf-8"), re.S)
    return dict(re.findall(r"^(\w+):[ \t]*(.*?)\s*$", m.group(1), re.M)) if m else {}

def external(dossiers, check=status, archive=None):
    """Return rows (file, url, status, verdict, suggestion) for every source url."""
    if archive is None:
        sys.path.insert(0, str(Path(__file__).parent)); from add_source import wayback as archive
    srcs = [(f, front(f)) for d in dossiers for f in sorted((Path(d) / "sources").glob("S*.md"))]
    srcs = [(f, m) for f, m in srcs if m.get("url", "").startswith("http")]
    with ThreadPoolExecutor(8) as ex: codes = list(ex.map(lambda fm: check(fm[1]["url"]), srcs))
    rows = []
    for (f, m), c in zip(srcs, codes):
        verdict = "ok" if 200 <= c < 400 else "blocked" if c in BLOCKED else "dead"
        sug = ""
        if verdict == "dead": sug = m.get("archived") or archive(m["url"]) or "no archive found; find a replacement"
        rows.append((f, m["url"], c, verdict, sug))
    return rows

def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("site", nargs="*")
    ap.add_argument("--external", action="store_true", help="check source urls in the given dossiers (default: all)")
    ap.add_argument("--report", help="with --external, also write a markdown report here")
    a = ap.parse_args(argv)
    if a.external:
        ds = a.site or sorted(str(p.parent) for p in Path("dossiers").glob("*/subject.toml"))
        rows = external(ds)
        for f, u, c, v, s in rows:
            if v != "ok": print(f"{v.upper():8}{c:>4}  {f}  {u}" + (f"\n          archived: {s}" if s else ""))
        dead = [r for r in rows if r[3] == "dead"]
        summary = f"{len(rows)} source urls: {len(rows) - len(dead) - sum(r[3] == 'blocked' for r in rows)} ok, {sum(r[3] == 'blocked' for r in rows)} blocked, {len(dead)} dead"
        print(summary)
        if a.report:
            Path(a.report).write_text("# Link rot report\n\n" + summary + "\n\n| Source | URL | Status | Verdict | Archive / fix |\n|---|---|---|---|---|\n"
                + "".join(f"| {f} | {u} | {c} | {v} | {s} |\n" for f, u, c, v, s in rows if v != "ok"), encoding="utf-8")
        return 1 if dead else 0
    n, bad = internal(a.site[0] if a.site else "site")
    for b in bad: print("BROKEN", b)
    print(f"{n} links, {len(bad)} broken")
    return 1 if bad else 0

if __name__ == "__main__":
    sys.exit(main())
