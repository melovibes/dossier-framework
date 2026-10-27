from conftest import ROOT, run, add_source, add_claim

def validate(d, *extra):
    return run(ROOT / "tools/validate.py", d, "--strict", *extra)

def test_fixture_is_clean(dossier):
    r = validate(dossier); assert r.returncode == 0, r.stdout

def test_missing_reliability_is_error(dossier):
    add_source(dossier, "S01", rel="")
    r = validate(dossier); assert "S01.md: reliability" in r.stdout and r.returncode == 1

def test_single_source_confident_grade_warns(dossier):
    add_claim(dossier, "C01", "widely-accepted", "S01")
    r = validate(dossier); assert "single source" in r.stdout and r.returncode == 1

def test_single_source_probable_is_fine(dossier):
    add_claim(dossier, "C01", "probable", "S01")
    assert validate(dossier).returncode == 0

def test_strong_on_tertiary_only_is_error(dossier):
    add_source(dossier, "S01", type="reference", rel="B"); add_source(dossier, "S02", rel="C")
    r = validate(dossier); assert "only tertiary" in r.stdout and "ERROR" in r.stdout

def test_claim_id_gap_warns(dossier):
    add_claim(dossier, "C03", "probable", "S01")
    r = validate(dossier); assert "ID gap(s) at C02" in r.stdout

def test_paywalled_needs_archive(dossier):
    add_source(dossier, "S02", url="https://www.nytimes.com/x")
    assert "paywalled" in validate(dossier).stdout
    add_source(dossier, "S02", url="https://www.nytimes.com/x", arch="https://web.archive.org/web/2020/https://www.nytimes.com/xS02")
    assert validate(dossier).returncode == 0

def test_checklist_gaps_and_bad_chapter(dossier):
    (dossier / "checklist.md").write_text("| Item | Covered in | Notes |\n|---|---|---|\n| Education | | |\n| Death | 07 | |\n| Faith | n/a | |\n")
    out = validate(dossier).stdout
    assert "not covered: Education" in out and "missing chapter 07" in out and "n/a without a note" in out

def test_report_written(dossier):
    validate(dossier, "--report")
    rep = (dossier / "coverage.md").read_text()
    assert "## By chapter" in rep and "01-early-life" in rep

def test_real_dossiers_pass_strict():
    for d in sorted((ROOT / "dossiers").iterdir()):
        r = validate(d); assert r.returncode == 0, f"{d.name}:\n{r.stdout}"

from validate import parse_date

def test_parse_date_precisions():
    assert parse_date("2018-09-11")[1] == "day" and parse_date("2018-09")[1] == "month"
    assert parse_date("2018")[1] == "year" and parse_date("c. 1992–93")[1] == "circa"
    assert parse_date("mid-2010s")[1] == "decade" and parse_date("355 BCE")[0] < parse_date("415")[0]
    assert parse_date("banana") is None

def test_timeline_rules(dossier):
    tl = dossier / "timeline.md"
    tl.write_text(tl.read_text() + "| 1980 | Earlier | strong | [S01] |\n| someday | ? | probable | [S01] |\n| 2005 | Uncited | probable | |\n")
    out = validate(dossier).stdout
    assert "out of chronological order" in out and "unparseable date 'someday'" in out and "cites no source" in out
