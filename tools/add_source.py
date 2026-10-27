#!/usr/bin/env python3
"""Capture a web source into a dossier: next free S-number, metadata from the page, Wayback copy.

  python tools/add_source.py <dossier> <url> [--reliability A|B|C] [--type secondary] [--title ...]
                             [--author ...] [--date YYYY-MM-DD] [--locator ...] [--no-fetch] [--save]
  python tools/add_source.py --archive-only <source.md> [...] [--save]

Metadata comes from og:/article: meta tags or <title>; anything given on the command line wins.
`archived:` is filled from the Wayback availability API; --save asks Save Page Now to archive
pages that have no copy yet. Stdlib only. Review the generated file before committing.
"""
import argparse, datetime, html, json, re, sys, urllib.parse, urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate import front, is_paywalled  # noqa: E402

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36 dossier-framework"

def get(url, timeout=20, tries=4):
    import time, urllib.error
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "en"})
    for i in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read(2_000_000).decode(r.headers.get_content_charset() or "utf-8", "replace")
        except urllib.error.HTTPError as e:
            if e.code not in (429, 503) or i == tries - 1: raise
            time.sleep(5 * 2 ** i)  # archive.org rate-limits bursts

def meta(page):
    """Pull title/author/date/site from HTML. Pure function, tested offline."""
    def tag(*names):
        for n in names:
            m = re.search(rf'<meta[^>]+(?:property|name)=["\']{re.escape(n)}["\'][^>]*content=["\']([^"\']+)', page, re.I) \
                or re.search(rf'<meta[^>]+content=["\']([^"\']+)["\'][^>]*(?:property|name)=["\']{re.escape(n)}["\']', page, re.I)
            if m: return html.unescape(m.group(1)).strip()
        return ""
    title = tag("og:title", "twitter:title") or html.unescape((re.search(r"<title[^>]*>(.*?)</title>", page, re.S | re.I) or [None, ""])[1]).strip()
    date = tag("article:published_time", "datePublished", "date", "pubdate", "parsely-pub-date")
    if not date and (m := re.search(r'"datePublished"\s*:\s*"([^"]+)"', page)): date = m.group(1)
    author = tag("author", "article:author", "parsely-author", "byl")
    if author.startswith("http"): author = ""
    return {"title": re.sub(r"\s+", " ", title), "author": re.sub(r"^By\s+", "", author), "date": date[:10], "site": tag("og:site_name")}

def wayback(url, save=False):
    api = "https://archive.org/wayback/available?url=" + urllib.parse.quote(url, safe="")
    cdx = "https://web.archive.org/cdx/search/cdx?output=json&limit=-1&filter=statuscode:200&url=" + urllib.parse.quote(url, safe="")
    try:
        try:
            snap = json.loads(get(api)).get("archived_snapshots", {}).get("closest", {})
            if snap.get("available"): return snap["url"].replace("http://", "https://", 1)
        except Exception:
            rows = json.loads(get(cdx) or "[]")  # fallback endpoint: newest 200 capture
            if len(rows) > 1: return f"https://web.archive.org/web/{rows[-1][1]}/{rows[-1][2]}"
        if save:
            get("https://web.archive.org/save/" + url, timeout=90)
            return wayback(url, save=False)
    except Exception as e:
        print(f"  wayback lookup failed: {e}", file=sys.stderr)
    return ""

def next_id(folder):
    nums = [int(m.group(1)) for p in folder.glob("S*.md") if (m := re.fullmatch(r"S(\d+)", p.stem))]
    return f"S{(max(nums) + 1 if nums else 1):02d}"

def render(sid, f):
    title = f["title"] or "TODO title"
    return f"""---
id: {sid}
title: {title}
author: {f.get('author', '')}
date: {f.get('date', '')}
type: {f['type']}
url: {f['url']}
locator: {f.get('locator', '')}
license: linked-only
mirrored:
accessed: {datetime.date.today().isoformat()}
reliability: {f['reliability']}
archived: {f.get('archived', '')}
---

# {sid} — {title}

**What it is:** TODO one or two sentences{' (' + f['site'] + ')' if f.get('site') else ''}.

**Reliability:** {f['reliability']} — TODO why.

**License:** copyrighted; linked, not copied.
"""

def set_field(path, key, value):
    t = path.read_text(encoding="utf-8")
    if re.search(rf"^{key}:.*$", t, re.M):
        t = re.sub(rf"^{key}:.*$", f"{key}: {value}", t, count=1, flags=re.M)
    else:
        t = t.replace("\n---\n", f"\n{key}: {value}\n---\n", 1)
    path.write_text(t, encoding="utf-8")

def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if argv and argv[0] == "--archive-only":
        ap = argparse.ArgumentParser(); ap.add_argument("files", nargs="+"); ap.add_argument("--save", action="store_true")
        a = ap.parse_args(argv[1:]); rc = 0
        for f in map(Path, a.files):
            m = front(f)
            if m.get("archived"): print(f"{f.name}: already archived"); continue
            arch = wayback(m.get("url", ""), a.save)
            if arch: set_field(f, "archived", arch); print(f"{f.name}: {arch}")
            else: print(f"{f.name}: no archive found{' (try --save)' if not a.save else ''}"); rc = 1
        return rc
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dossier"); ap.add_argument("url")
    ap.add_argument("--reliability", choices="ABC", default="B"); ap.add_argument("--type", default="secondary")
    for k in ("title", "author", "date", "locator"): ap.add_argument("--" + k, default="")
    ap.add_argument("--no-fetch", action="store_true"); ap.add_argument("--no-archive", action="store_true")
    ap.add_argument("--save", action="store_true")
    a = ap.parse_args(argv); d = Path(a.dossier); folder = d / "sources"
    for p in folder.glob("S*.md"):
        if front(p).get("url") == a.url: print(f"already captured as {p.stem}"); return 1
    f = {"url": a.url, "type": a.type, "reliability": a.reliability, "title": "", "author": "", "date": "", "site": ""}
    if not a.no_fetch:
        try: f.update({k: v for k, v in meta(get(a.url)).items() if v})
        except Exception as e: print(f"  fetch failed ({e}); fill metadata by hand", file=sys.stderr)
    f.update({k: getattr(a, k) for k in ("title", "author", "date", "locator") if getattr(a, k)})
    if not a.no_archive: f["archived"] = wayback(a.url, a.save or is_paywalled(a.url))
    sid = next_id(folder); out = folder / f"{sid}.md"
    out.write_text(render(sid, f), encoding="utf-8")
    print(out); [print(f"  {k}: {f.get(k) or '(missing)'}") for k in ("title", "author", "date", "archived")]
    return 0

if __name__ == "__main__":
    sys.exit(main())
