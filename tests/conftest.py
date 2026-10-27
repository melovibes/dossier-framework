import shutil, subprocess, sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
PY = sys.executable

def run(*args, cwd=ROOT):
    return subprocess.run([PY, *map(str, args)], cwd=cwd, capture_output=True, text=True)

SRC = """---
id: {id}
title: Title {id}
author: A
date: 2020-01-01
type: {type}
url: {url}
locator: p. 1
license: linked-only
mirrored:
accessed: 2026-01-01
reliability: {rel}
archived: {arch}
---

# {id}
"""
CLAIM = """---
id: {id}
claim: Claim {id}
grade: {grade}
sources: [{src}]
chapter: 01
---

# {id}
"""

@pytest.fixture
def dossier(tmp_path):
    """A minimal valid dossier scaffolded by new_dossier.py, with two sources and one claim."""
    r = run(ROOT / "tools/new_dossier.py", "--subject", "Test Person", "--kind", "person", "--out", tmp_path,
            "--question", "Early life")
    assert r.returncode == 0, r.stderr
    d = tmp_path / "test-person"
    (d / "subject.toml").write_text((d / "subject.toml").read_text().replace("public_subject_confirmed = false", "public_subject_confirmed = true"))
    for f in (d / "sources").glob("_*"): f.unlink()
    for f in (d / "claims").glob("_*"): f.unlink()
    (d / "checklist.md").unlink()
    add_source(d, "S01"); add_source(d, "S02")
    add_claim(d, "C01", "strong", "S01, S02")
    (d / "dossier/01-early-life.md").write_text("# 01 — Early life\n\nBorn [S01] [S02] (C01).\n")
    (d / "timeline.md").write_text("# Timeline\n\n| Date | Event | Certainty | Sources |\n|---|---|---|---|\n| 1990-05 | Born | strong | [S01] |\n| c. 2001 | School | probable | [S02] |\n")
    return d

def add_source(d, sid, type="secondary", rel="A", url="https://example.org/a", arch=""):
    (d / "sources" / f"{sid}.md").write_text(SRC.format(id=sid, type=type, rel=rel, url=url + sid, arch=arch))

def add_claim(d, cid, grade, src):
    (d / "claims" / f"{cid}.md").write_text(CLAIM.format(id=cid, grade=grade, src=src))
