#!/usr/bin/env python3
"""Scaffold a new dossier, or add a source/claim to one.

  python tools/new_dossier.py --subject "Name" [--out dossiers] [--period ...] [--alias ...]
  python tools/new_dossier.py add-source <dossier_dir> --title "..."
  python tools/new_dossier.py add-claim  <dossier_dir> --claim "..."
"""
import argparse, datetime, re, shutil, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TPL = ROOT / "templates"

def slugify(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-") or "subject"

def fill(text, ctx):
    for k, v in ctx.items():
        text = text.replace("{{%s}}" % k, v)
    return text

def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")

def next_id(folder, prefix):
    nums = [int(m.group(1)) for p in folder.glob(f"{prefix}*.md") if (m := re.match(rf"{prefix}(\d+)", p.stem))]
    return f"{prefix}{(max(nums) + 1 if nums else 1):02d}"

def scaffold(a):
    slug = slugify(a.slug or a.subject)
    dest = Path(a.out) / slug
    if dest.exists() and any(dest.iterdir()) and not a.force:
        sys.exit(f"{dest} exists and is not empty (use --force)")
    ctx = {"NAME": a.subject, "SLUG": slug, "DATE": datetime.date.today().isoformat(),
           "PERIOD": a.period or "TBD", "ALIASES": ", ".join(a.alias) or "none"}
    cfg = fill((TPL / "subject.toml").read_text(encoding="utf-8"), ctx)
    cfg = cfg.replace("aliases = []", "aliases = [%s]" % ", ".join('"%s"' % x for x in a.alias))
    cfg = cfg.replace('period = ""', f'period = "{a.period}"')
    kind = a.kind
    cfg = re.sub(r'^kind = "[^"]*"', f'kind = "{kind}"', cfg, count=1, flags=re.M)
    checklist = TPL / "checklists" / f"{kind}.md"
    if a.question:
        cfg = re.sub(r"(\[questions\][^\[]*?list = )\[.*?\]", lambda m: m.group(1) + "[\n" + "".join(f'  "{q}",\n' for q in a.question) + "]", cfg, flags=re.S)
    if a.collection:
        cfg = re.sub(r"(\[collections\][^\[]*?list = )\[.*?\]", lambda m: m.group(1) + "[" + ", ".join(f'"{c}"' for c in a.collection) + "]", cfg, flags=re.S)
    write(dest / "subject.toml", cfg)
    if checklist.exists():
        write(dest / "checklist.md", checklist.read_text(encoding="utf-8"))
    for f in ["README.md", "timeline.md", "bibliography.md", "contradictions.md"]:
        write(dest / f, fill((TPL / f).read_text(encoding="utf-8"), ctx))
    for f in ["00-executive-findings.md", "00-scope-and-method.md", "99-source-notes.md"]:
        write(dest / "dossier" / f, fill((TPL / "dossier" / f).read_text(encoding="utf-8"), ctx))
    import tomllib
    qs = tomllib.loads(cfg)["questions"]["list"]
    chap = (TPL / "dossier" / "_chapter.md").read_text(encoding="utf-8")
    for i, q in enumerate(qs, 1):
        write(dest / "dossier" / f"{i:02d}-{slugify(q)[:50].rstrip("-")}.md", fill(chap, {**ctx, "NN": f"{i:02d}", "QUESTION": q}))
    for c in tomllib.loads(cfg)["collections"]["list"]:
        (dest / "collections" / c / "_meta").mkdir(parents=True, exist_ok=True)
        (dest / "collections" / c / "_meta" / ".gitkeep").touch()
    for d in ["sources", "claims"]:
        (dest / d).mkdir(parents=True, exist_ok=True)
        shutil.copy(TPL / d / f"_{d[:-1]}.md", dest / d / f"_{d[:-1]}.template.md")
    print(f"Created {dest}\nNext: edit {dest/'subject.toml'}, then follow GUIDE.md")

def add(a, kind):
    d = Path(a.dossier)
    folder, prefix = (d / "sources", "S") if kind == "source" else (d / "claims", "C")
    nid = next_id(folder, prefix)
    text = (TPL / f"{kind}s" / f"_{kind}.md").read_text(encoding="utf-8").replace("{{ID}}", nid)
    if kind == "source":
        text = text.replace("title: \n", f"title: {a.title}\n", 1).replace("— Title", f"— {a.title}")
    else:
        text = text.replace("claim: \n", f"claim: {a.claim}\n", 1).replace("— Claim", f"— {a.claim}")
    write(folder / f"{nid}.md", text)
    print(folder / f"{nid}.md")

def main():
    argv = sys.argv[1:]
    if argv and argv[0] in ("add-source", "add-claim"):
        p = argparse.ArgumentParser(prog=f"new_dossier.py {argv[0]}")
        p.add_argument("dossier")
        p.add_argument("--title" if argv[0] == "add-source" else "--claim", required=True)
        return add(p.parse_args(argv[1:]), argv[0][4:])
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--subject", required=True)
    p.add_argument("--slug"); p.add_argument("--period", default="")
    p.add_argument("--kind", default="person", choices=["person", "event", "place", "object", "movement", "topic"],
                   help="subject type; copies the matching coverage checklist to checklist.md")
    p.add_argument("--alias", action="append", default=[])
    p.add_argument("--question", action="append", default=[], help="research question (repeatable); one chapter each")
    p.add_argument("--collection", action="append", default=[], help="collection folder (repeatable)")
    p.add_argument("--out", default="dossiers"); p.add_argument("--force", action="store_true")
    scaffold(p.parse_args(argv))

if __name__ == "__main__":
    if sys.version_info < (3, 11): sys.exit("Python 3.11+ required")
    main()
