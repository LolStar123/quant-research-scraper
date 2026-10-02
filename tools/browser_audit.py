"""Headless checks for paper collection, saved reading lists and the SPY panel."""
import functools
import http.server
import json
import os
import threading
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output/redesign"
OUT.mkdir(parents=True, exist_ok=True)
class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass
server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=str(ROOT / "examples/portfolio")))
threading.Thread(target=server.serve_forever, daemon=True).start()
try:
    with sync_playwright() as p:
        browser = p.chromium.launch(**({"channel": "chrome"} if os.name == "nt" else {}))
        page = browser.new_page(viewport={"width": 1280, "height": 940}, reduced_motion="reduce")
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        url = os.environ.get("AUDIT_URL", f"http://127.0.0.1:{server.server_port}/")
        page.goto(url, wait_until="networkidle")
        page.wait_for_function("window.__research?.ready && window.__research?.forwardReady")
        assert page.evaluate("__research.total") == 320
        assert page.locator(".paper").count() == 8
        assert page.locator("#forward-chart polyline").count() == 2
        assert page.locator("#forward-chart text").first.get_attribute("font-size") == "12"
        original = page.evaluate("__research.forwardResult.stats.total")
        page.locator("#forward-cost").fill("50")
        assert "Settings changed" in page.locator("#forward-state").inner_text()
        assert page.evaluate("__research.forwardResult.stats.total") == original
        page.locator("#run-test").click()
        assert page.evaluate("__research.forwardResult.stats.total") != original
        page.locator("#forward-training").select_option("252")
        page.locator("#forward-testing").select_option("21")
        page.locator("#run-test").click()
        assert page.evaluate("__research.forwardConfig.training") == 252
        page.locator("#forward-cost").fill("-1")
        page.locator("#run-test").click()
        assert "Invalid" in page.locator("#forward-state").inner_text()
        page.locator("#forward-cost").fill("")
        page.locator("#run-test").click()
        assert "including zero" in page.locator("#forward-state").inner_text()
        page.locator("#forward-cost").fill("5")
        page.locator("#forward-training").select_option("504")
        page.locator("#forward-testing").select_option("63")
        page.locator("#run-test").click()
        page.locator("#forward-chart").focus()
        page.keyboard.press("Home")
        first = page.locator("#forward-cursor").inner_text()
        page.keyboard.press("ArrowRight")
        assert page.locator("#forward-cursor").inner_text() != first
        page.keyboard.press("End")
        for topic in ["market microstructure", "options pricing", "momentum investing", ""] * 2:
            page.locator('[data-topic="'+topic+'"]').click()
            assert page.evaluate("__research.filtered") > 0
        page.locator("#next").click()
        assert page.locator("#page-number").inner_text().startswith("2 /")
        page.locator("#previous").click()
        for sort in ["year", "title", "citations"]:
            page.locator("#sort").select_option(sort)
        page.locator("[data-save]").first.click()
        assert page.evaluate("__research.saved") == 1
        page.locator("details.reading-list summary").click()
        with page.expect_download() as dl:
            page.locator("#export-json").click()
        exported = Path(dl.value.path())
        assert len(json.loads(exported.read_text())) == 1
        page.locator("[data-save]").first.click()
        page.locator("#import").set_input_files(exported)
        page.wait_for_function("__research.saved === 1")
        page.locator("#saved-filter").click()
        assert page.locator(".paper").count() == 1
        with page.expect_download() as dl:
            page.locator("#export-bib").click()
        assert "@article" in Path(dl.value.path()).read_text()
        page.reload(wait_until="networkidle")
        page.wait_for_function("__research.saved === 1")
        page.locator("#query").fill("zzzz no matches")
        assert page.evaluate("__research.filtered") == 0
        assert page.locator("#next").is_disabled()
        assert page.locator("#previous").is_disabled()
        page.locator("#query").fill("options")
        assert 0 < page.evaluate("__research.filtered") < 320
        page.locator("#query").fill("")
        page.locator("details.reading-list summary").click()
        page.locator("#import").set_input_files({"name": "bad.json", "mimeType": "application/json", "buffer": b'{"broken":true}'})
        page.wait_for_function('document.querySelector("#status").textContent.includes("Import failed")')
        page.locator("#live").click()
        assert "Enter a topic" in page.locator("#status").inner_text()
        # API fixtures exercise the browser boundary; they are not network evidence.
        fixture = {"message": {"items": [{"DOI": "10.9999/test-metadata", "title": ["Audit paper"], "author": [{"family": "Example"}], "published": {"date-parts": [[2026]]}}]}}
        page.route("https://api.crossref.org/**", lambda route: route.fulfill(json=fixture))
        for _ in range(2):
            page.locator("#query").fill("audit paper")
            page.locator("#live").click()
            page.wait_for_function('document.querySelector("#status").textContent.includes("found")')
            assert page.locator(".paper h2").inner_text() == "Audit paper"
            assert page.evaluate("__research.total") == 321
        page.unroute("https://api.crossref.org/**")
        page.route("https://api.crossref.org/**", lambda route: route.fulfill(status=503, body="unavailable"))
        page.locator("#query").fill("failed query")
        page.locator("#live").click()
        page.wait_for_function('document.querySelector("#status").textContent.includes("unavailable")')
        assert page.evaluate("__research.total") == 321
        assert page.locator("#live").is_enabled()
        page.unroute("https://api.crossref.org/**")
        page.reload(wait_until="networkidle")
        page.wait_for_function("__research.ready && __research.forwardReady")
        page.evaluate("scrollTo(0,0)")
        page.screenshot(path=str(OUT / "library-desktop.png"), full_page=True)
        page.screenshot(path=str(ROOT / "examples/portfolio/preview.png"), full_page=True)
        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(150)
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1")
        assert page.evaluate('Math.abs(document.querySelector("#forward-chart").clientWidth - document.querySelector("#forward-chart svg").viewBox.baseVal.width) <= 1')
        assert page.locator("#papers").bounding_box()["y"] < page.locator(".walk-forward").bounding_box()["y"]
        page.locator("#forward-chart").focus()
        page.keyboard.press("Home")
        page.keyboard.press("ArrowRight")
        page.screenshot(path=str(OUT / "library-mobile.png"), full_page=True)
        page.locator('[data-save]').first.focus()
        assert page.evaluate('getComputedStyle(document.activeElement).outlineStyle') != "none"
        # Independent initial price/library failure: no uncaught exception.
        failed = browser.new_page()
        failed.on("pageerror", lambda e: errors.append(str(e)))
        failed.route("**/data/papers.json", lambda route: route.fulfill(status=500, body="unavailable"))
        failed.route("**/data/spy.json", lambda route: route.fulfill(status=500, body="unavailable"))
        failed.goto(url, wait_until="networkidle")
        assert "could not load" in failed.locator("#status").inner_text()
        assert failed.locator("#run-test").is_disabled()
        assert not errors, errors
        (OUT / "library-checks.json").write_text(json.dumps({"passed": True, "browser_errors": errors, "viewports": [1280,390], "checks": ["saved persistence", "JSON import/export", "BibTeX", "Crossref fixture success/dedup/failure", "topic/search/order/pages", "changed windows/costs", "invalid/blank cost", "keyboard inspector", "actual-width axes", "initial data failure", "focus/reduced motion"]}, indent=2))
        print("PASS: library, saved state, exports, Crossref fixtures, SPY controls, errors and 390px charts")
        browser.close()
finally:
    server.shutdown()
