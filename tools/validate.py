#!/usr/bin/env python3
"""Validate a dossier: every claim cites existing sources and has a grade,
every [Sxx] in chapters/timeline resolves, sources have url or mirror.

  python tools/validate.py <dossier_dir> [--write-summary] [--write-bibliography] [--report] [--strict]
--report writes coverage.md: per-chapter claims, grade mix, single-source claims,
source reliability, and checklist gaps.
Exit 1 on errors (warnings too with --strict).
"""
import argparse, re, sys, tomllib
from pathlib import Path

GRADES = {"strong": "Strong historical conclusion", "widely-accepted": "Widely accepted",
          "probable": "Probable", "disputed": "Disputed", "unproved": "Unproved hypothesis",
          "unsupported": "Unsupported", "false": "False", "unassessed": "Not yet assessed"}
CITE = re.compile(r"\[(S\d+)\]")
RELIABILITY = {"A": "major outlet, scholarly or primary record", "B": "reputable but limited or self-reported", "C": "tertiary, fan-maintained or anonymous"}
TYPES = {"primary", "secondary", "archaeological", "reference", "media"}
CONFIDENT = {"strong", "widely-accepted"}
# Hosts that paywall or block fetching; sources from them need an `archived:` copy.
PAYWALLED = ("nytimes.com", "wsj.com", "washingtonpost.com", "theglobeandmail.com", "latimes.com", "newyorker.com",
             "ft.com", "economist.com", "theatlantic.com", "bloomberg.com", "thetimes.co.uk", "telegraph.co.uk", "thehendonmob.com")

def is_paywalled(url):
    host = re.sub(r"^https?://(www\.)?", "", url or "").split("/")[0]
    return any(host == h or host.endswith("." + h) for h in PAYWALLED)

def weak(src):
    """Tertiary or low-reliability: can't carry a strong grade alone."""
    return src.get("reliability") == "C" or src.get("type") == "reference"

def front(path):
    t = path.read_text(encoding="utf-8")
    m = re.match(r"---\n(.*?)\n---\n", t, re.S)
    meta = {}
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.split("#")[0].strip()
    return meta

def ids(v):
    return re.findall(r"S\d+", v or "")

def replace_block(path, tag, body):
    t = path.read_text(encoding="utf-8")
    new = re.sub(rf"(<!-- {tag}:start -->\n).*?(<!-- {tag}:end -->)", lambda m: m.group(1) + body + "\n" + m.group(2), t, flags=re.S)
    path.write_text(new, encoding="utf-8")

def main():
    p = argparse.ArgumentParser()
    p.add_argument("dossier"); p.add_argument("--write-summary", action="store_true")
    p.add_argument("--write-bibliography", action="store_true"); p.add_argument("--strict", action="store_true")
    p.add_argument("--report", action="store_true", help="write coverage.md")
    a = p.parse_args(); d = Path(a.dossier)
    err, warn = [], []
    try:
        cfg = tomllib.loads((d / "subject.toml").read_text(encoding="utf-8"))
        if not cfg["scope"].get("public_subject_confirmed"):
            warn.append("subject.toml: public_subject_confirmed is false (see ETHICS.md)")
    except Exception as e:
        err.append(f"subject.toml: {e}")
    sources = {}
    for f in sorted((d / "sources").glob("S*.md")):
        m = front(f); sid = m.get("id")
        if sid != f.stem: err.append(f"{f.name}: id '{sid}' does not match filename")
        if not m.get("title"): err.append(f"{f.name}: missing title")
        if not (m.get("url") or m.get("mirrored")): err.append(f"{f.name}: needs url or mirrored path")
        if m.get("mirrored") and not (d / "collections" / m["mirrored"]).exists():
            err.append(f"{f.name}: mirrored file collections/{m['mirrored']} not found")
        if m.get("mirrored") and m.get("license") == "linked-only":
            err.append(f"{f.name}: linked-only sources must not be mirrored")
        if m.get("reliability") not in RELIABILITY:
            err.append(f"{f.name}: reliability must be one of A/B/C (got '{m.get('reliability', '')}')")
        if m.get("type") not in TYPES: err.append(f"{f.name}: type must be one of {sorted(TYPES)}")
        if is_paywalled(m.get("url")) and not m.get("archived"):
            warn.append(f"{f.name}: paywalled host with no archived: copy (run tools/add_source.py --archive-only {f})")
        sources[f.stem] = m
    claims = []
    for f in sorted((d / "claims").glob("C*.md")):
        m = front(f); cited = ids(m.get("sources"))
        if not m.get("claim"): err.append(f"{f.name}: missing claim text")
        g = m.get("grade", "")
        if g not in GRADES: err.append(f"{f.name}: invalid grade '{g}'")
        elif g == "unassessed": warn.append(f"{f.name}: grade unassessed")
        if not cited: err.append(f"{f.name}: cites no source")
        for s in cited:
            if s not in sources: err.append(f"{f.name}: cites unknown source {s}")
        known = [sources[s] for s in cited if s in sources]
        if g in CONFIDENT and len(set(cited)) < 2:
            warn.append(f"{f.name}: graded {g} on a single source; add an independent source or lower the grade")
        if g == "strong" and known and all(weak(s) for s in known):
            err.append(f"{f.name}: graded strong but cites only tertiary/C sources")
        claims.append((f.stem, m, cited))
    nums = sorted(int(c[1:]) for c, _, _ in claims)
    gaps = sorted(set(range(1, nums[-1] + 1)) - set(nums)) if nums else []
    if gaps: warn.append("claims: ID gap(s) at " + ", ".join(f"C{n:02d}" for n in gaps) + " (renumber with tools/renumber.py)")
    used = {s for _, _, c in claims for s in c}
    for f in list((d / "dossier").glob("*.md")) + [d / "timeline.md"]:
        if not f.exists(): continue
        txt = f.read_text(encoding="utf-8")
        for c in re.findall(r"\((C\d+)\)", txt):
            if c not in {cid for cid, _, _ in claims}: err.append(f"{f.relative_to(d)}: refers to unknown claim {c}")
        for s in CITE.findall(txt):
            used.add(s)
            if s not in sources: err.append(f"{f.relative_to(d)}: cites unknown source {s}")
    for s in sources:
        if s not in used: warn.append(f"sources/{s}.md: never cited")
    if a.write_summary and (d / "dossier/00-executive-findings.md").exists():
        rows = ["| Claim | Best assessment | Sources |", "|---|---|---|"] + [
            f"| {m.get('claim')} ({cid}) | {GRADES.get(m.get('grade'), '?')} | {' '.join('['+s+']' for s in c)} |" for cid, m, c in claims]
        replace_block(d / "dossier/00-executive-findings.md", "claims", "\n".join(rows))
    if a.write_bibliography:
        lines = [f"- **{s}** — {m.get('author') + ', ' if m.get('author') else ''}*{m.get('title')}*"
                 f"{' (' + m['date'] + ')' if m.get('date') else ''}{', ' + m['locator'] if m.get('locator') else ''}."
                 f"{' <' + m['url'] + '>' if m.get('url') else ''} License: {m.get('license')}." for s, m in sources.items()]
        replace_block(d / "bibliography.md", "bibliography", "\n".join(lines))
    chapters = {f.stem[:2]: f for f in sorted((d / "dossier").glob("[0-9][0-9]-*.md"))}
    gaps, cl = [], d / "checklist.md"
    if cl.exists():
        for row in re.findall(r"^\|(?!\s*Item\b)(?!-)([^|]+)\|([^|]*)\|([^|]*)\|$", cl.read_text(encoding="utf-8"), re.M):
            item, cov, note = (x.strip() for x in row)
            if set(item) <= set("-: "): continue
            if not cov: gaps.append(item); continue
            if cov.lower() == "n/a":
                if not note: warn.append(f"checklist.md: '{item}' is n/a without a note")
                continue
            for c in re.split(r"[,\s]+", cov):
                if c and c not in chapters: err.append(f"checklist.md: '{item}' points to missing chapter {c}")
        for g in gaps: warn.append(f"checklist.md: not covered: {g}")
    if a.report:
        write_report(d, sources, claims, chapters, gaps)
    for w in warn: print("WARN ", w)
    for e in err: print("ERROR", e)
    print(f"{len(sources)} sources, {len(claims)} claims, {len(err)} errors, {len(warn)} warnings")
    sys.exit(1 if err or (a.strict and warn) else 0)

def write_report(d, sources, claims, chapters, gaps):
    def mix(cs):
        n = {}
        for _, m, _ in cs: n[m.get("grade")] = n.get(m.get("grade"), 0) + 1
        return ", ".join(f"{g} {n[g]}" for g in GRADES if g in n) or "—"
    rel = lambda ss: sum(sources.get(s, {}).get("reliability") == "A" for s in ss)
    rows = ["| Chapter | Claims | Grades | Single-source | Distinct sources | A-grade share |", "|---|---|---|---|---|---|"]
    for num, f in chapters.items():
        cs = [c for c in claims if (c[1].get("chapter") or "").startswith(num)]
        txt = f.read_text(encoding="utf-8"); cited = set(CITE.findall(txt)) | {s for c in cs for s in c[2]}
        share = f"{100 * rel(cited) // len(cited)}%" if cited else "—"
        rows.append(f"| {f.stem} | {len(cs)} | {mix(cs)} | {sum(len(set(c[2])) == 1 for c in cs)} | {len(cited)} | {share} |")
    single = [f"- {cid} ({m.get('grade')}): {m.get('claim')} — {', '.join(c)}" for cid, m, c in claims if len(set(c)) == 1]
    by_rel = {}
    for s, m in sources.items(): by_rel.setdefault(m.get("reliability") or "?", []).append(s)
    out = [f"# Coverage report", "", "Generated by `tools/validate.py --report`. Do not edit by hand.", "",
           f"**{len(sources)} sources** (" + ", ".join(f"{k}: {len(v)}" for k, v in sorted(by_rel.items())) + f") · **{len(claims)} claims** ({mix(claims)})", "",
           "## By chapter", "", *rows, "", "## Single-source claims", "", *(single or ["None."]), "",
           "## Checklist gaps", "", *([f"- {g}" for g in gaps] or ["None." if (d / "checklist.md").exists() else "No checklist.md."]), ""]
    (d / "coverage.md").write_text("\n".join(out), encoding="utf-8")

if __name__ == "__main__":
    main()
