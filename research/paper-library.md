# quant research reading room

**[Open the live library](https://lolstar123.github.io/quant-research-scraper/)**

Collect research metadata, remove duplicate papers and build a reading list for your next market experiment. The library opens with 320 real papers across eight searches, including market microstructure, options pricing and statistical arbitrage.

![Research reading room](examples/portfolio/preview.png)

## Try it

Type to filter the bundled library. Choose a collection, sort by date or citations, and save interesting papers. Use **search live Crossref** to collect up to 40 more results from a public metadata API. Export your saved list as BibTeX or JSON; import it on another browser. Saved lists remain in local browser storage.

No login or API key. If Crossref is unavailable, the bundled library, filtering and exports still work. Full articles remain on the publisher's site; a DOI link may lead to a paywall.

## Run the collectors

```sh
# Refresh all eight topic collections from Crossref.
python collector/refresh_catalogue.py
# Or collect your own topic into a separate list.
python collector/refresh_catalogue.py --query "gamma scalping" --rows 60 --output reading-list.json
# Parse citation meta tags from saved HTML or a public page.
python collector/collect.py collector/paper.html --output citations.json
```

The Python collector records DOI, title, authors, year, journal, citation count, topic and collection time. The browser deduplicates DOI variants and upgrades title-only entries when a DOI arrives. Different DOIs sharing a title are preserved as possible distinct editions.

## Run the app and checks

```sh
python -m http.server 8000 --directory examples/portfolio
node --test examples/portfolio/model.test.mjs
pip install playwright
python -m playwright install chromium
python tools/browser_audit.py
```

Open http://localhost:8000. GitHub Actions checks local and public interactions every four hours. The bundled collection is a dated snapshot; live searches fetch new metadata on demand.

## Find the code

[Collection scripts](collector) / [normalisation and export](examples/portfolio/model.mjs) / [browser interface](examples/portfolio/app.mjs) / [source notes](PROVENANCE.md).

The folder interaction takes inspiration from [Rare UI](https://www.rareui.com/components/foldercomponent). This implementation is original vanilla HTML/CSS/JS; it does not redistribute Rare UI component source.
