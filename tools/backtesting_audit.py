"""Exercise the market backtesting workbench locally or against its public deployment."""
import functools
import http.server
import os
import threading
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*args): pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(ROOT/'examples/portfolio/backtesting')))
threading.Thread(target=server.serve_forever,daemon=True).start()
try:
    with sync_playwright() as p:
        browser=p.chromium.launch(**({'channel':'chrome'} if os.name=='nt' else {}))
        page=browser.new_page(viewport={'width':1280,'height':1000},reduced_motion='reduce')
        errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto(os.environ.get('AUDIT_URL',f'http://127.0.0.1:{server.server_port}'),wait_until='networkidle')
        page.wait_for_function('window.__backtest?.ready')
        before=page.evaluate('__backtest.result.stats.total')
        page.locator('#cost').fill('50');page.locator('#run').click()
        assert page.evaluate('__backtest.result.stats.total')!=before
        baseline = page.evaluate('__backtest.result.stats.total')
        assert page.locator('#chart polyline').count()==2
        assert page.locator('#inspection-equity').count()==1
        assert page.locator('#chart svg').get_attribute('viewBox').split()[2] == '1000'
        assert page.locator('details.method').get_attribute('open') is None
        assert page.locator('details.decisions').get_attribute('open') is None
        assert page.locator('details.data-notes').get_attribute('open') is None
        assert page.locator('#provenance').text_content()
        page.locator('#chart').focus()
        before_cursor = page.locator('#cursor').inner_text()
        page.keyboard.press('ArrowLeft')
        assert page.locator('#cursor').inner_text() != before_cursor
        page.locator('[data-tab="archive"]').click()
        assert page.locator('#strategies tr').count()==50
        page.locator('#search').fill('parity')
        assert 0<page.locator('#strategies tr').count()<50
        page.locator('[data-tab="experiment"]').click()
        with page.expect_download() as dl:page.locator('#download').click()
        assert dl.value.suggested_filename=='walk-forward-returns.csv'
        page.evaluate('window.scrollTo(0,0)')
        mobile_dir = ROOT / 'output' / 'playwright'
        mobile_dir.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(mobile_dir / 'backtesting-desktop-inspection.png'), full_page=True)
        page.screenshot(path=str(ROOT/'examples/portfolio/backtesting/preview.png'))
        page.set_viewport_size({'width':390,'height':844})
        page.wait_for_timeout(150)
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),'mobile overflow'
        mobile_chart = page.evaluate("""() => {
            const chart = document.querySelector('#chart');
            const svg = chart.querySelector('svg');
            const viewBox = svg.getAttribute('viewBox').split(/\s+/).map(Number);
            return {clientWidth: chart.clientWidth, viewBoxWidth: viewBox[2], stats: window.__backtest.result.stats.total, labelSize: svg.querySelector('text').getAttribute('font-size')};
        }""")
        assert abs(mobile_chart['viewBoxWidth'] - mobile_chart['clientWidth']) <= 1
        assert mobile_chart['labelSize'] == '12'
        assert mobile_chart['stats'] == baseline
        page.locator('#chart').focus()
        mobile_cursor = page.locator('#cursor').inner_text()
        page.keyboard.press('ArrowLeft')
        assert page.locator('#cursor').inner_text() != mobile_cursor
        page.screenshot(path=str(mobile_dir / 'backtesting-mobile.png'), full_page=True)
        assert not errors,errors
        print('PASS: historical rerun, changed costs, two equity curves, 50 real strategies, search and export')
        browser.close()
finally: server.shutdown()
