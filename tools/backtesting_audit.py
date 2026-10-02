"""Headless checks for the historical walk-forward and 50-strategy archive."""
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
server = http.server.ThreadingHTTPServer(("127.0.0.1",0), functools.partial(Quiet,directory=str(ROOT / "examples/portfolio")))
threading.Thread(target=server.serve_forever,daemon=True).start()
try:
    with sync_playwright() as p:
        browser=p.chromium.launch(**({"channel":"chrome"} if os.name == "nt" else {}))
        page=browser.new_page(viewport={"width":1280,"height":940},reduced_motion="reduce")
        errors=[]
        page.on("pageerror",lambda e:errors.append(str(e)))
        url=os.environ.get("AUDIT_URL",f"http://127.0.0.1:{server.server_port}/backtesting/")
        page.goto(url,wait_until="networkidle")
        page.wait_for_function("window.__backtest?.ready")
        baseline=page.evaluate("__backtest.result.stats.total")
        assert page.evaluate("__backtest.prices") == 5351
        for training,testing,cost in [(252,21,0),(756,126,50),(504,63,5)]:
            page.locator("#training").select_option(str(training))
            page.locator("#testing").select_option(str(testing))
            page.locator("#cost").fill(str(cost))
            assert page.locator("#download").is_disabled()
            page.locator("#run").click()
            assert page.locator("#download").is_enabled()
            assert page.evaluate("__backtest.result.costBps") == cost
        assert page.evaluate("__backtest.result.stats.total") == baseline
        for invalid in ["-1", "", "1001"]:
            page.locator("#cost").fill(invalid)
            page.locator("#run").click()
            assert page.locator("#download").is_disabled()
            assert page.evaluate("__backtest.result.stats.total") == baseline
        page.locator("#cost").fill("5")
        page.locator("#run").click()
        assert page.locator("#chart polyline").count()==2
        page.locator("#chart").focus()
        page.keyboard.press("Home")
        first=page.locator("#cursor").inner_text()
        page.keyboard.press("ArrowRight")
        assert first != page.locator("#cursor").inner_text()
        page.keyboard.press("End")
        page.locator("details.decisions summary").click()
        assert page.locator("#windows tr").count() == page.evaluate("__backtest.result.windows.length")
        page.locator("details.decisions summary").click()
        with page.expect_download() as dl:
            page.locator("#download").click()
        content=Path(dl.value.path()).read_text().splitlines()
        assert len(content)==page.evaluate("__backtest.result.curve.length")+1
        assert content[0]=="date,equity,benchmark,position,period,return"
        page.locator('[data-tab="archive"]').click()
        assert page.locator("#strategies tr").count()==50
        for query in ["parity","holiday","zzzz",""]*2:
            page.locator("#search").fill(query)
            count=page.locator("#strategies tr").count()
            assert count==0 if query=="zzzz" else count>0
        for sort in ["wf1_sharpe","wf2_ret","combined_rank"]:
            page.locator("#sort").select_option(sort)
        page.screenshot(path=str(OUT/"strategy-archive-desktop.png"),full_page=True)
        page.locator('[data-tab="experiment"]').click()
        page.evaluate("scrollTo(0,0)")
        page.screenshot(path=str(OUT/"backtesting-desktop.png"),full_page=True)
        page.screenshot(path=str(ROOT/"examples/portfolio/backtesting/preview.png"),full_page=True)
        page.set_viewport_size({"width":390,"height":844})
        page.wait_for_timeout(150)
        assert page.evaluate("document.documentElement.scrollWidth<=innerWidth+1")
        assert page.evaluate('Math.abs(document.querySelector("#chart").clientWidth-document.querySelector("#chart svg").viewBox.baseVal.width)<=1')
        assert page.locator("#chart text").first.get_attribute("font-size")=="12"
        assert page.evaluate("__backtest.result.stats.total")==baseline
        page.locator("#chart").focus()
        page.keyboard.press("Home")
        page.keyboard.press("ArrowRight")
        page.screenshot(path=str(OUT/"backtesting-mobile.png"),full_page=True)
        page.locator('[data-tab="archive"]').click()
        assert page.evaluate("document.documentElement.scrollWidth<=innerWidth+1")
        page.screenshot(path=str(OUT/"strategy-archive-mobile.png"),full_page=True)
        failed=browser.new_page()
        failed.on("pageerror",lambda e:errors.append(str(e)))
        failed.route("**/data/spy.json",lambda route:route.fulfill(status=500,body="unavailable"))
        failed.goto(url,wait_until="networkidle")
        assert failed.locator("#download").is_disabled()
        assert failed.locator("#run").is_disabled()
        assert not errors,errors
        (OUT/"backtesting-checks.json").write_text(json.dumps({"passed":True,"browser_errors":errors,"checks":["three window/cost configs","invalid/blank cost protects export","unchanged output after resize","daily CSV rows","all 50 strategies","repeated search/order","keyboard inspection","desktop/mobile axes","initial data failure"]},indent=2))
        print("PASS: walk-forward controls, daily CSV, archive filters, invalid costs and desktop/mobile plots")
        browser.close()
finally:
    server.shutdown()
