#!/usr/bin/env python3
"""Render a dossier into a static, mobile-friendly HTML site (stdlib only).

  python tools/build_site.py dossiers/<slug> [--out site/<slug>]

Pages: index (executive findings + contents), one per chapter, claims, sources,
timeline. [Sxx] and (Cxx) become links; grades become badges; a small search
box filters pages client-side. Open site/<slug>/index.html directly, no server needed.
"""
import argparse, html, json, re, sys, tomllib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate import front, GRADES  # noqa: E402

def esc(s): return html.escape(s, quote=True)

def inline(t, ctx):
    t = esc(t)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<![\w*])\*(?!\s)(.+?)\*(?!\w)", r"<em>\1</em>", t)
    t = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)", r'<a href="\2" rel="noopener">\1</a>', t)
    t = re.sub(r"&lt;(https?://[^&\s]+)&gt;", r'<a href="\1" rel="noopener">\1</a>', t)
    def s(m):
        sid = m.group(1); src = ctx["sources"].get(sid)
        if not src: return m.group(0)
        return f'<a class="cite" href="sources.html#{sid}" title="{esc(src.get("title",""))}">{sid}</a>'
    t = re.sub(r"\[(S\d+)\]", s, t)
    def c(m):
        cid = m.group(1); cl = ctx["claims"].get(cid)
        if not cl: return m.group(0)
        return f'<a class="cref g-{esc(cl.get("grade",""))}" href="claims.html#{cid}" title="{esc(cl.get("claim",""))}">{cid}</a>'
    t = re.sub(r"\((C\d+)\)", c, t)
    t = re.sub(r"(?<![\w>#\"])(C\d{2,})\b", lambda m: c(m) if m.group(1) in ctx["claims"] else m.group(0), t)
    return t

def md(text, ctx):
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    text = re.sub(r"\A---\n.*?\n---\n", "", text, flags=re.S)
    out, lines, i = [], text.splitlines(), 0
    while i < len(lines):
        ln = lines[i]
        if not ln.strip(): i += 1; continue
        if m := re.match(r"(#{1,4})\s+(.*)", ln):
            lvl = len(m.group(1)); body = m.group(2)
            hid = re.sub(r"[^a-z0-9]+", "-", body.lower()).strip("-")
            out.append(f'<h{lvl} id="{hid}">{inline(body, ctx)}</h{lvl}>'); i += 1; continue
        if ln.lstrip().startswith("|"):
            rows = []
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")]); i += 1
            rows = [r for r in rows if not all(re.fullmatch(r":?-{2,}:?", c) for c in r)]
            h, *b = rows
            out.append('<div class="tablewrap"><table><thead><tr>' + "".join(f'<th scope="col">{inline(c, ctx)}</th>' for c in h) + "</tr></thead><tbody>"
                       + "".join("<tr>" + "".join(f"<td>{inline(c, ctx)}</td>" for c in r) + "</tr>" for r in b) + "</tbody></table></div>")
            continue
        if re.match(r"\s*[-*]\s+", ln):
            items = []
            while i < len(lines) and re.match(r"\s*[-*]\s+", lines[i]):
                items.append(re.sub(r"^\s*[-*]\s+", "", lines[i])); i += 1
            out.append("<ul>" + "".join(f"<li>{inline(x, ctx)}</li>" for x in items) + "</ul>"); continue
        if ln.startswith(">"):
            q = []
            while i < len(lines) and lines[i].startswith(">"):
                q.append(lines[i].lstrip("> ")); i += 1
            out.append(f"<blockquote>{inline(' '.join(q), ctx)}</blockquote>"); continue
        para = []
        while i < len(lines) and lines[i].strip() and not re.match(r"(#{1,4}\s|\s*[-*]\s|\||>)", lines[i]):
            para.append(lines[i]); i += 1
        out.append(f"<p>{inline(' '.join(para), ctx)}</p>")
    return "\n".join(out)

def badge(g): return f'<span class="badge g-{esc(g)}">{esc(GRADES.get(g, g))}</span>'

CSS = """
:root{--bg:#fdfdfb;--alt:#f5f4ef;--fg:#1b1b19;--muted:#6b6b63;--rule:#e2e0d8;--accent:#7a2e12;--soft:#f0e6df;--panel:#fff;
--serif:ui-serif,"Iowan Old Style","Palatino Linotype",Georgia,serif;--sans:ui-sans-serif,-apple-system,"Segoe UI",Roboto,Arial,sans-serif}
@media(prefers-color-scheme:dark){:root{--bg:#161614;--alt:#1f1f1c;--fg:#e8e6df;--muted:#a09d92;--rule:#33322d;--accent:#e39a74;--soft:#3a2a22;--panel:#1c1c19}}
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%}body{margin:0;background:var(--bg);color:var(--fg);font:17px/1.65 var(--serif)}
a{color:var(--accent)}a:hover{text-decoration-thickness:2px}
.top{position:sticky;top:0;z-index:5;display:flex;gap:1rem;align-items:center;padding:.6rem 1rem;background:var(--bg);border-bottom:1px solid var(--rule);font-family:var(--sans)}
.brand{font-weight:600;text-decoration:none;color:var(--fg);white-space:nowrap}.brand b{color:var(--accent)}.brand span{color:var(--muted);font-weight:400}
#q{flex:1;max-width:26rem;padding:.4rem .7rem;border:1px solid var(--rule);border-radius:6px;background:var(--panel);color:var(--fg);font:inherit}
#navbtn{display:none;background:none;border:1px solid var(--rule);border-radius:6px;color:var(--fg);padding:.3rem .6rem;font:inherit}
.wrap{display:grid;grid-template-columns:17rem minmax(0,1fr);max-width:78rem;margin:0 auto}
nav.side{position:sticky;top:3.2rem;align-self:start;height:calc(100vh - 3.2rem);overflow:auto;padding:1rem;border-right:1px solid var(--rule);font:14px/1.45 var(--sans)}
nav.side h4{margin:1rem 0 .3rem;font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
nav.side a{display:block;padding:.25rem .5rem;border-radius:5px;color:var(--fg);text-decoration:none}nav.side a:hover{background:var(--alt)}nav.side a.on{background:var(--soft);color:var(--accent);font-weight:600}
main{padding:1.5rem 2rem 4rem;max-width:72ch;width:100%}
h1{font-size:1.9rem;line-height:1.2;margin:.2rem 0 1rem}h2{margin-top:2rem;font-size:1.35rem}h1,h2,h3{font-family:var(--serif)}
.kicker{font:13px var(--sans);color:var(--muted);text-transform:uppercase;letter-spacing:.08em}
.tablewrap{overflow-x:auto}table{border-collapse:collapse;width:100%;font:15px/1.45 var(--sans);margin:1rem 0}th,td{border-bottom:1px solid var(--rule);padding:.45rem .5rem;text-align:left;vertical-align:top}th{background:var(--alt)}
a.cite,a.cref{font:600 12px var(--sans);text-decoration:none;padding:0 .3rem;border-radius:4px;background:var(--soft);vertical-align:1px;white-space:nowrap}
.badge{display:inline-block;font:600 12px var(--sans);padding:.1rem .5rem;border-radius:999px;border:1px solid currentColor;white-space:nowrap}
.g-strong{color:#1d6b3a}.g-widely-accepted{color:#2f7d6b}.g-probable{color:#6a6a12}.g-disputed{color:#a8560b}.g-unproved{color:#7a4fa0}.g-unsupported{color:#a33a3a}.g-false{color:#b0172b}.g-unassessed{color:var(--muted)}
@media(prefers-color-scheme:dark){.g-strong{color:#6fd39a}.g-widely-accepted{color:#6cc9b4}.g-probable{color:#d6d36a}.g-disputed{color:#f0a35d}.g-unproved{color:#c39ae6}.g-unsupported{color:#f08a8a}.g-false{color:#ff7a8a}}
.card{background:var(--panel);border:1px solid var(--rule);border-radius:8px;padding:.9rem 1rem;margin:1rem 0;scroll-margin-top:4rem}
.card:target{outline:2px solid var(--accent)}.card h3{margin:.1rem 0 .4rem;font-size:1.05rem}.meta{font:13px/1.5 var(--sans);color:var(--muted)}
.meta a{word-break:break-all}.grades{display:flex;flex-wrap:wrap;gap:.4rem;margin:.6rem 0}
.pager{display:flex;justify-content:space-between;gap:1rem;margin-top:3rem;font:14px var(--sans)}
footer{font:13px var(--sans);color:var(--muted);border-top:1px solid var(--rule);margin-top:3rem;padding-top:1rem}
.hide{display:none!important}
.skip{position:absolute;left:-999px;top:0;z-index:9;background:var(--accent);color:#fff;padding:.5rem 1rem}.skip:focus{left:0}
:focus-visible{outline:3px solid var(--accent);outline-offset:2px}main:focus{outline:none}
.vh{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)}
@media print{.top,nav.side,.pager,.skip,#q{display:none!important}.wrap{display:block}main{max-width:none;padding:0}body{font-size:11pt;background:#fff;color:#000}
a{color:#000}a.cite,a.cref{background:none;border:1px solid #999}.card{break-inside:avoid;border-color:#999}h1,h2,h3{break-after:avoid}.printpage section{break-before:page}}
@media(max-width:820px){.wrap{display:block}#navbtn{display:block}nav.side{display:none;position:static;height:auto;border-right:0;border-bottom:1px solid var(--rule)}nav.side.open{display:block}main{padding:1rem 1.1rem 3rem}.brand span{display:none}}
"""

JS = """
const b=document.getElementById('navbtn'),n=document.querySelector('nav.side');b&&b.addEventListener('click',()=>n.classList.toggle('open'));
// Filter targets: explicit [data-s] cards (claims, sources); otherwise table rows and text blocks in <main> (timeline, chapters).
const q=document.getElementById('q');
const items=()=>{const m=document.querySelector('main')||document.body,c=m.querySelectorAll('[data-s]');
return c.length?[...c]:[...m.querySelectorAll('tbody tr, li, p, blockquote, pre, dl')].filter(e=>!e.parentElement.closest('li, p, blockquote, pre, dl')&&!e.classList.contains('kicker')&&!e.classList.contains('meta'));};
q&&q.addEventListener('input',()=>{const v=q.value.toLowerCase().trim();
items().forEach(e=>e.classList.toggle('hide',!!v&&!e.textContent.toLowerCase().includes(v)));});
document.addEventListener('keydown',e=>{if(e.key==='/'&&document.activeElement!==q){e.preventDefault();q.focus();}});
"""

def describe(body, fallback):
    """First real paragraph as plain text, for <meta name=description> and Open Graph."""
    for para in re.findall(r"<p(?: [^>]*)?>(.*?)</p>", body, re.S):
        txt = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", para))).strip()
        txt = re.sub(r"\s*\(?\b[SC]\d{2,}\b(?:[,;][^)]*)?\)?", "", txt).strip()
        if len(txt) > 40: return txt if len(txt) <= 160 else txt[:157].rsplit(" ", 1)[0] + "…"
    return fallback

def page(ctx, fname, title, body, kicker=""):
    on = lambda f: ' class=on aria-current="page"' if f == fname else ""
    nav = ['<h4>Dossier</h4>'] + [f'<a href="{f}"{on(f)}>{esc(t)}</a>' for f, t in ctx["nav"]]
    nav += ['<h4>Reference</h4>'] + [f'<a href="{f}"{on(f)}>{t}</a>' for f, t in
            [("claims.html", f"Claims ({len(ctx['claims'])})"), ("sources.html", f"Sources ({len(ctx['sources'])})"), ("timeline.html", "Timeline"), ("print.html", "Print / PDF")]]
    order = [f for f, _ in ctx["nav"]] + ["claims.html", "sources.html", "timeline.html"]
    k = order.index(fname) if fname in order else -1
    titles = dict(ctx["nav"] + [("claims.html", "Claims"), ("sources.html", "Sources"), ("timeline.html", "Timeline")])
    prev = f'<a href="{order[k-1]}">← {esc(titles[order[k-1]])}</a>' if k > 0 else "<span></span>"
    nxt = f'<a href="{order[k+1]}">{esc(titles[order[k+1]])} →</a>' if 0 <= k < len(order) - 1 else "<span></span>"
    name = esc(ctx["name"])
    desc = esc(describe(body, f"Sourced, graded evidence dossier on {ctx['name']}."))
    full = f"{esc(title)} — {name} dossier"
    base = ctx.get("base_url", "")
    url = base + ("" if fname == "index.html" else fname) if base else ""
    ctx.setdefault("pages", []).append(fname)
    head = (f'<meta name="description" content="{desc}"><meta property="og:type" content="article">'
            f'<meta property="og:title" content="{full}"><meta property="og:description" content="{desc}">'
            f'<meta property="og:site_name" content="{name} — evidence dossier"><meta name="twitter:card" content="summary">'
            + (f'<link rel="canonical" href="{esc(url)}"><meta property="og:url" content="{esc(url)}">' if url else ""))
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{full}</title>{head}<link rel="stylesheet" href="assets/site.css"></head><body>
<a class="skip" href="#main">Skip to content</a>
<header class="top"><button id="navbtn" aria-label="Contents">☰</button><a class="brand" href="index.html"><b>✦</b> {name} <span>— evidence dossier</span></a>
<label class="vh" for="q">Filter this page</label><input id="q" type="search" placeholder="Filter this page   /"></header>
<div class="wrap"><nav class="side" aria-label="Contents">{''.join(nav)}</nav>
<main id="main" tabindex="-1">{f'<div class="kicker">{esc(kicker)}</div>' if kicker else ''}{body}
<div class="pager">{prev}{nxt}</div>
<footer>Research cutoff {esc(ctx['cutoff'])}. Generated by dossier-framework. Copyrighted sources are linked, not copied.</footer></main></div>
<script src="assets/site.js"></script></body></html>"""

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("dossier"); ap.add_argument("--out")
    ap.add_argument("--base-url", help="public URL of the built site, for canonical/Open Graph links and sitemap.xml (default: [site] base_url in subject.toml)")
    a = ap.parse_args(); d = Path(a.dossier)
    cfg = tomllib.loads((d / "subject.toml").read_text(encoding="utf-8"))["subject"]
    out = Path(a.out or Path("site") / cfg["slug"]); (out / "assets").mkdir(parents=True, exist_ok=True)
    sources = {f.stem: front(f) for f in sorted((d / "sources").glob("S*.md"))}
    claims = {f.stem: {**front(f), "_body": f.read_text(encoding="utf-8")} for f in sorted((d / "claims").glob("C*.md"))}
    chapters = sorted(f for f in (d / "dossier").glob("*.md") if f.stem != "00-executive-findings")
    def htitle(f):
        m = re.search(r"^#\s+(.*)", f.read_text(encoding="utf-8"), re.M); return m.group(1) if m else f.stem
    site_cfg = tomllib.loads((d / "subject.toml").read_text(encoding="utf-8")).get("site", {})
    base_url = (a.base_url or site_cfg.get("base_url", "")).rstrip("/") + "/" if (a.base_url or site_cfg.get("base_url")) else ""
    ctx = {"name": cfg["name"], "cutoff": cfg.get("research_cutoff", ""), "sources": sources, "claims": claims, "base_url": base_url,
           "nav": [("index.html", "Executive findings")] + [(f.stem + ".html", htitle(f)) for f in chapters]}
    (out / "assets/site.css").write_text(CSS, encoding="utf-8"); (out / "assets/site.js").write_text(JS, encoding="utf-8")
    counts = {}
    for c in claims.values(): counts[c.get("grade")] = counts.get(c.get("grade"), 0) + 1
    meta = (f'<p class="meta">{len(sources)} sources · {len(claims)} graded claims · period {esc(cfg.get("period",""))}'
            + (f' · also known as {esc(", ".join(cfg.get("aliases", [])))}' if cfg.get("aliases") else "") + "</p>"
            '<div class="grades">' + "".join(f'<a href="claims.html" style="text-decoration:none">{badge(g)} <span class="meta">×{n}</span></a>' for g, n in sorted(counts.items(), key=lambda x: list(GRADES).index(x[0]) if x[0] in GRADES else 99)) + "</div>")
    ef = d / "dossier/00-executive-findings.md"
    body = md(ef.read_text(encoding="utf-8"), ctx) if ef.exists() else f"<h1>{esc(cfg['name'])}</h1>"
    body = body.replace("</h1>", "</h1>" + meta, 1)
    toc = "<h2>Contents</h2><ol>" + "".join(f'<li><a href="{f}">{esc(t)}</a></li>' for f, t in ctx["nav"][1:]) + "</ol>"
    (out / "index.html").write_text(page(ctx, "index.html", "Executive findings", body + toc, "Research dossier"), encoding="utf-8")
    for f in chapters:
        (out / (f.stem + ".html")).write_text(page(ctx, f.stem + ".html", htitle(f), md(f.read_text(encoding="utf-8"), ctx), "Chapter"), encoding="utf-8")
    cards = []
    for cid, c in claims.items():
        body_md = re.sub(r"^#.*\n", "", re.sub(r"\A---\n.*?\n---\n", "", c["_body"], flags=re.S), count=1, flags=re.M)
        ch = c.get("chapter", ""); chf = next((f.stem for f in chapters if ch and f.stem.startswith(ch)), None)
        cards.append(f'<div class="card" id="{cid}" data-s><h3>{cid} · {inline(c.get("claim",""), ctx)}</h3>{badge(c.get("grade",""))}'
                     + (f' <span class="meta">argued in <a href="{chf}.html">{esc(htitle(d/"dossier"/(chf+".md")))}</a></span>' if chf else "")
                     + md(body_md, ctx) + "</div>")
    (out / "claims.html").write_text(page(ctx, "claims.html", "Claims", "<h1>Claims</h1><p class=meta>Each claim is graded on the scale in GUIDE.md and cites its sources.</p>" + "".join(cards), "Reference"), encoding="utf-8")
    used = {}
    for cid, c in claims.items():
        for s in re.findall(r"S\d+", c.get("sources", "")): used.setdefault(s, []).append(cid)
    scards = []
    for sid, s in sources.items():
        rows = " · ".join(esc(x) for x in [s.get("author"), s.get("date"), s.get("type"), s.get("locator")] if x)
        link = f'<a href="{esc(s["url"])}" rel="noopener">{esc(s["url"])}</a>' if s.get("url") else ""
        cb = " ".join(f'<a class="cref" href="claims.html#{c}">{c}</a>' for c in used.get(sid, []))
        scards.append(f'<div class="card" id="{sid}" data-s><h3>{sid} · {esc(s.get("title",""))}</h3><div class="meta">{rows}<br>{link}<br>'
                      f'License: {esc(s.get("license",""))}{" · supports " + cb if cb else ""}</div></div>')
    (out / "sources.html").write_text(page(ctx, "sources.html", "Sources", "<h1>Sources</h1>" + "".join(scards), "Reference"), encoding="utf-8")
    tl = d / "timeline.md"
    (out / "timeline.html").write_text(page(ctx, "timeline.html", "Timeline", md(tl.read_text(encoding="utf-8"), ctx) if tl.exists() else "<h1>Timeline</h1>", "Reference"), encoding="utf-8")
    # Print / PDF: every chapter, the timeline, claims and sources on one page.
    parts = [f'<section><h1>{esc(cfg["name"])} — evidence dossier</h1><p class="meta">Research cutoff {esc(ctx["cutoff"])}. Use your browser\'s Print → Save as PDF.</p></section>']
    parts += [f"<section>{md(f.read_text(encoding='utf-8'), ctx)}</section>" for f in chapters]
    if tl.exists(): parts.append(f"<section>{md(tl.read_text(encoding='utf-8'), ctx)}</section>")
    parts.append("<section><h1>Claims</h1>" + "".join(cards).replace(' id="C', ' data-id="C') + "</section>")
    parts.append("<section><h1>Sources</h1>" + "".join(scards).replace(' id="S', ' data-id="S') + "</section>")
    (out / "print.html").write_text(page(ctx, "print.html", "Print / PDF", '<div class="printpage">' + "".join(parts) + "</div>", "Full dossier"), encoding="utf-8")
    if base_url:
        urls = "".join(f"<url><loc>{esc(base_url + ('' if p == 'index.html' else p))}</loc></url>" for p in ctx["pages"])
        (out / "sitemap.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>\n', encoding="utf-8")
    print(f"Built {out}/index.html ({len(ctx['pages'])} pages)")

if __name__ == "__main__":
    main()
