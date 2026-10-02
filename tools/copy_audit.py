"""Record rendered UI copy, excluding paper/row/chart data and numeric outputs."""
import argparse
import functools
import http.server
import json
import os
import re
import threading
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument("phase", choices=["before", "after"])
args = parser.parse_args()
out = ROOT / "output/copy-cull" / args.phase
out.mkdir(parents=True, exist_ok=True)
quant = (ROOT / "examples/portfolio/backtesting").is_dir()
cases = [
    ("library", "", "__research?.ready && __research?.forwardReady", None),
    ("backtesting", "backtesting/", "__backtest?.ready", None),
    ("strategy-archive", "backtesting/#archive", "__backtest?.ready", None),
] if quant else [
    ("ledger", "", "__datasets?.ready && !__datasets.refreshing", None),
    ("original-calculator", "archive.html", "__poe?.ready", None),
    ("original-workbook", "archive.html", "__poe?.ready", "archive"),
    ("variants", "archive.html", "__poe?.ready", "variants"),
    ("workflow", "archive.html", "__poe?.ready", "pipeline"),
]
excluded = ".paper>div, tbody, #pairs, svg, #forward-chart, #chart, #forward-cursor, #cursor, #forward-stats strong, #stats strong, #metrics strong, #sheet-kpis strong, #coverage-value, #risk-summary, #formula"
class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass
server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=str(ROOT / "examples/portfolio")))
threading.Thread(target=server.serve_forever, daemon=True).start()
records = []
try:
    with sync_playwright() as p:
        browser = p.chromium.launch(**({"channel": "chrome"} if os.name == "nt" else {}))
        for width, height in [(1280, 940), (390, 844)]:
            for name, path, ready, tab in cases:
                page = browser.new_page(viewport={"width": width, "height": height}, reduced_motion="reduce")
                page.goto(f"http://127.0.0.1:{server.server_port}/{path}", wait_until="networkidle")
                page.wait_for_function("window." + ready)
                if tab:
                    page.locator('[data-tab="'+tab+'"]').click()
                page.evaluate("scrollTo(0,0)")
                text = page.evaluate("""excluded => {
                    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
                    const parts = [];
                    while (walker.nextNode()) {
                        const node = walker.currentNode, el = node.parentElement;
                        if (!el || el.closest(excluded) || el.closest('script,style,option') || !el.getClientRects().length) continue;
                        const style = getComputedStyle(el);
                        if (style.visibility === 'hidden' || style.display === 'none') continue;
                        parts.push(node.textContent.trim());
                    }
                    return parts.filter(Boolean).join(' ');
                }""", excluded)
                words = re.findall(r"\b[\w]+(?:[-'/][\w]+)*\b", text)
                record = {"view": name, "viewport": width, "chrome_words": len(words), "chrome_text": text,
                          "overflow": page.evaluate("document.documentElement.scrollWidth > innerWidth + 1")}
                assert not record["overflow"], record
                records.append(record)
                page.screenshot(path=str(out / f"{name}-{width}.png"), full_page=True)
                page.close()
        browser.close()
    (out / "wordcounts.json").write_text(json.dumps({"phase": args.phase, "excluded": excluded, "records": records}, indent=2), encoding="utf-8")
    print(json.dumps([{"view": r["view"], "viewport": r["viewport"], "chrome_words": r["chrome_words"]} for r in records]))
finally:
    server.shutdown()

