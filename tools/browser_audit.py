"""Exercise the research collection and reading-list workflow locally or against its public deployment."""
import functools
import http.server
import os
import threading
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*args): pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(ROOT/'examples/portfolio')))
threading.Thread(target=server.serve_forever,daemon=True).start()
try:
    with sync_playwright() as p:
        browser=p.chromium.launch(**({'channel':'chrome'} if os.name=='nt' else {}))
        page=browser.new_page(viewport={'width':1280,'height':1000},reduced_motion='reduce')
        errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto(os.environ.get('AUDIT_URL',f'http://127.0.0.1:{server.server_port}'),wait_until='networkidle')
        page.wait_for_function('window.__research?.ready')
        assert page.evaluate('__research.total')>=300
        assert page.locator('.paper').count()==15
        page.locator('[data-save]').first.click()
        assert page.evaluate('__research.saved')==1
        with page.expect_download() as dl:page.locator('#export-json').click()
        saved_file=dl.value.path()
        page.locator('[data-save]').first.click()
        page.locator('#import').set_input_files(saved_file)
        page.wait_for_function('__research.saved===1')
        page.locator('#saved-filter').click()
        assert page.locator('.paper').count()==1
        with page.expect_download() as dl:page.locator('#export-bib').click()
        assert '@article' in Path(dl.value.path()).read_text()
        page.locator('#saved-filter').click()
        page.locator('#query').fill('options')
        assert 0<page.evaluate('__research.filtered')<320
        page.locator('#query').fill('')
        page.locator('[data-topic="market microstructure"]').click()
        assert page.evaluate('__research.filtered')>=40
        page.locator('[data-topic=""]').click()
        # Deterministic API interaction, followed by a real network probe separately.
        page.route('https://api.crossref.org/**',lambda route:route.fulfill(json={'message':{'items':[{'DOI':'10.9999/test-metadata','title':['Audit paper'],'author':[{'family':'Example'}],'published':{'date-parts':[[2026]]}}]}}))
        page.locator('#query').fill('audit paper');page.locator('#live').click()
        page.wait_for_function('document.querySelector("#status").textContent.startsWith("Collected")')
        assert page.locator('.paper h2').inner_text()=='Audit paper'
        page.unroute('https://api.crossref.org/**')
        page.locator('[data-topic=""]').click()
        page.reload(wait_until='networkidle')
        page.wait_for_function('window.__research?.ready')
        page.evaluate('window.scrollTo(0,0)')
        page.screenshot(path=str(ROOT/'examples/portfolio/preview.png'))
        page.set_viewport_size({'width':390,'height':844})
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),'mobile overflow'
        assert not errors,errors
        print('PASS: populated library, search, DOI collection, save/import, BibTeX and mobile')
        browser.close()
finally: server.shutdown()
