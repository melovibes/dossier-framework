from conftest import ROOT, run, add_claim
import add_source as cap, renumber

def test_renumber_closes_gaps_and_rewrites_refs(dossier):
    add_claim(dossier, "C03", "probable", "S01")
    ch = dossier / "dossier/01-early-life.md"
    ch.write_text(ch.read_text() + "\nLater (C03).\n")
    assert renumber.main([str(dossier)]) == 0
    assert (dossier / "claims/C02.md").exists() and not (dossier / "claims/C03.md").exists()
    assert "(C02)" in ch.read_text() and "id: C02" in (dossier / "claims/C02.md").read_text()

def test_meta_parsing_offline():
    page = ('<html><head><title>Fallback</title><meta property="og:title" content="Real &amp; Title">'
            '<meta name="author" content="By Jane Doe"><meta property="article:published_time" content="2021-09-14T10:00:00Z">'
            '<meta property="og:site_name" content="Example News"></head></html>')
    assert cap.meta(page) == {"title": "Real & Title", "author": "Jane Doe", "date": "2021-09-14", "site": "Example News"}

def test_add_source_offline(dossier):
    r = run(ROOT / "tools/add_source.py", dossier, "https://example.org/new", "--no-fetch", "--no-archive",
            "--title", "New piece", "--reliability", "A")
    assert r.returncode == 0, r.stderr
    t = (dossier / "sources/S03.md").read_text()
    assert "title: New piece" in t and "reliability: A" in t
    dup = run(ROOT / "tools/add_source.py", dossier, "https://example.org/new", "--no-fetch", "--no-archive")
    assert dup.returncode == 1 and "already captured as S03" in dup.stdout

def test_paywall_detection():
    assert cap.is_paywalled("https://www.nytimes.com/2018/x") and cap.is_paywalled("https://pokerdb.thehendonmob.com/p")
    assert not cap.is_paywalled("https://variety.com/x")
