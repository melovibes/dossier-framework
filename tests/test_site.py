import shutil, subprocess, threading, functools, http.server
import pytest
from conftest import ROOT, run

def build(d, out):
    r = run(ROOT / "tools/build_site.py", d, "--out", out); assert r.returncode == 0, r.stderr

def test_build_and_links(dossier, tmp_path):
    out = tmp_path / "site" / "test-person"; build(dossier, out)
    for p in ["index.html", "claims.html", "sources.html", "timeline.html", "contradictions.html", "print.html", "01-early-life.html"]:
        assert (out / p).exists()
    r = run(ROOT / "tools/check_links.py", tmp_path / "site"); assert r.returncode == 0, r.stdout

def test_committed_site_links():
    assert run(ROOT / "tools/check_links.py", ROOT / "site").returncode == 0

@pytest.fixture
def server():
    pw = pytest.importorskip("playwright.sync_api")
    h = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(ROOT / "site"))
    h.log_message = lambda *a: None
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(ROOT / "site")))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_port}/norm-macdonald"
    srv.shutdown()

CASES = [("timeline.html", "poker"), ("claims.html", "gambl"), ("sources.html", "variety"), ("11-gambling-and-poker.html", "bravo"), ("contradictions.html", "ohlmeyer")]

@pytest.mark.parametrize("page,term", CASES)
def test_filter_hides_and_restores(server, page, term):
    from playwright.sync_api import sync_playwright
    exe = shutil.which("google-chrome") or shutil.which("chromium")
    with sync_playwright() as p:
        b = p.chromium.launch(**({"executable_path": exe} if exe else {}))
        pg = b.new_page(); pg.goto(f"{server}/{page}")
        vis = "()=>[...document.querySelectorAll('main tbody tr, main [data-s], main p, main li')].filter(e=>e.offsetParent!==null).length"
        before = pg.evaluate(vis); pg.fill("#q", term); during = pg.evaluate(vis); pg.fill("#q", ""); after = pg.evaluate(vis)
        b.close()
    assert 0 < during < before and after == before

def test_meta_a11y_print(dossier, tmp_path):
    t = (dossier / "subject.toml"); t.write_text(t.read_text().replace('base_url = ""', 'base_url = "https://example.org/d/"'))
    out = tmp_path / "s"; build(dossier, out)
    h = (out / "01-early-life.html").read_text()
    for needle in ['<a class="skip" href="#main">', 'name="description"', 'property="og:title"',
                   '<link rel="canonical" href="https://example.org/d/01-early-life.html">', 'aria-current="page"']:
        assert needle in h, needle
    assert 'scope="col"' in (out / "timeline.html").read_text()
    assert "01-early-life.html" in (out / "sitemap.xml").read_text()
    assert "Early life" in (out / "print.html").read_text()

def test_full_text_search(server):
    from playwright.sync_api import sync_playwright
    exe = shutil.which("google-chrome") or shutil.which("chromium")
    with sync_playwright() as p:
        b = p.chromium.launch(**({"executable_path": exe} if exe else {}))
        pg = b.new_page(); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto(f"{server}/search.html?q=ohlmeyer%20espys")
        hrefs = pg.eval_on_selector_all(".result h3 a", "es=>es.map(e=>e.getAttribute('href'))")
        assert "claims.html#C09" in hrefs and pg.locator(".result mark").count() > 0
        pg.fill("#sq", "zzzz-nothing"); assert pg.locator(".result").count() == 0
        pg.goto(f"{server}/timeline.html"); pg.fill("#q", "moth joke"); pg.press("#q", "Enter"); pg.wait_for_load_state()
        assert "search.html?q=moth%20joke" in pg.url and pg.locator(".result").count() > 0
        b.close()
    assert not errs, errs

def test_search_index_covers_every_page(dossier, tmp_path):
    out = tmp_path / "s"; build(dossier, out)
    idx = (out / "assets/search-index.js").read_text()
    for u in ['"u":"claims.html#C01"', '"u":"sources.html#S01"', '"u":"timeline.html', '"u":"01-early-life.html']:
        assert u in idx, u
    assert "print.html" not in idx and "search.html" not in idx
