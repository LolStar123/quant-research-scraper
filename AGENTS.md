# Working on quant finance research scraper

Read PROVENANCE.md and examples/portfolio/README.md first.
Keep calculation and decision logic in model.mjs, independently runnable in Node.
Run `node --test examples/portfolio/model.test.mjs` after changes.
Keep generated fixtures labelled; never present sample outcomes as measured production results.
Preserve the project's workflow: Search for a topic, collect paper metadata, then deduplicate by DOI or title. The reading list keeps titles, dates and source links together so an interesting idea can become a testable strategy.
Add regression checks for changed decisions, including missing or invalid inputs.
Do not add credentials, user records or runtime account integrations to the demo.
