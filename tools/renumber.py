#!/usr/bin/env python3
"""Close gaps in claim (C) or source (S) IDs and rewrite every reference.

  python tools/renumber.py <dossier_dir> [--kind C|S] [--dry-run]

C01, C02, C04 -> C01, C02, C03, updating front matter, (Cxx) / [Sxx] references,
timeline, chapters and claim files. Generated files are refreshed by validate.py.
"""
import argparse, re, sys
from pathlib import Path

def plan(folder, prefix):
    old = sorted(int(m.group(1)) for p in folder.glob(f"{prefix}*.md") if (m := re.fullmatch(rf"{prefix}(\d+)", p.stem)))
    return {f"{prefix}{o:02d}": f"{prefix}{n:02d}" for n, o in enumerate(old, 1) if o != n}

def rewrite(text, mapping, prefix):
    # Two-phase so C51->C50 can't collide with an existing C50.
    pat = re.compile(rf"\b({prefix}\d+)\b")
    text = pat.sub(lambda m: "\x00" + mapping[m.group(1)] if m.group(1) in mapping else m.group(1), text)
    return text.replace("\x00", "")

def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("dossier"); ap.add_argument("--kind", default="C", choices="CS")
    ap.add_argument("--dry-run", action="store_true"); a = ap.parse_args(argv)
    d = Path(a.dossier); folder = d / ("claims" if a.kind == "C" else "sources")
    mapping = plan(folder, a.kind)
    if not mapping: print("no gaps"); return 0
    for k, v in mapping.items(): print(f"{k} -> {v}")
    if a.dry_run: return 0
    files = [p for p in d.rglob("*.md") if "collections" not in p.parts]
    for p in files:
        t = p.read_text(encoding="utf-8"); n = rewrite(t, mapping, a.kind)
        if n != t: p.write_text(n, encoding="utf-8")
    for old, new in sorted(mapping.items()):  # ascending: targets are always free
        (folder / f"{old}.md").rename(folder / f"{new}.md")
    return 0

if __name__ == "__main__":
    sys.exit(main())
