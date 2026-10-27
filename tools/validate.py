#!/usr/bin/env python3
"""Validate a dossier: every claim cites existing sources and has a grade,
every [Sxx] in chapters/timeline resolves, sources have url or mirror.

  python tools/validate.py <dossier_dir> [--write-summary] [--write-bibliography] [--strict]
Exit 1 on errors (warnings too with --strict).
"""
import argparse, re, sys, tomllib
from pathlib import Path

GRADES = {"strong": "Strong historical conclusion", "widely-accepted": "Widely accepted",
          "probable": "Probable", "disputed": "Disputed", "unproved": "Unproved hypothesis",
          "unsupported": "Unsupported", "false": "False", "unassessed": "Not yet assessed"}
CITE = re.compile(r"\[(S\d+)\]")

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
        claims.append((f.stem, m, cited))
    used = {s for _, _, c in claims for s in c}
    for f in list((d / "dossier").glob("*.md")) + [d / "timeline.md"]:
        if not f.exists(): continue
        for s in CITE.findall(f.read_text(encoding="utf-8")):
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
    for w in warn: print("WARN ", w)
    for e in err: print("ERROR", e)
    print(f"{len(sources)} sources, {len(claims)} claims, {len(err)} errors, {len(warn)} warnings")
    sys.exit(1 if err or (a.strict and warn) else 0)

if __name__ == "__main__":
    main()
