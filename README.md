# quant finance research scraper

Collects papers, removes duplicates and keeps the source beside each research idea.

<!-- working-example:start -->
## Try it in a minute

**[Live example](https://lolstar123.github.io/quant-research-scraper/)** · [Example code](examples/portfolio/model.mjs) · [Run locally](examples/portfolio/README.md) · [Atul's website](https://atul-kanodia-fieldnotes.atulswaggalicious.chatgpt.site)

Clean and search a small research catalogue; export the reading list.

<img src="examples/portfolio/preview.png" alt="quant finance research scraper example inputs and calculated output" width="760">

<!-- working-example:end -->

## The project

Search for a topic, collect paper metadata, then deduplicate by DOI or title. The reading list keeps titles, dates and source links together so an interesting idea can become a testable strategy.

Less time reopening the same papers. More time checking the idea.

## Find your way around

| Path | What is here |
| --- | --- |
| [examples/portfolio](examples/portfolio) | Runnable browser example and fixtures |
| [model.mjs](examples/portfolio/model.mjs) | Actual calculation or workflow |
| [model.test.mjs](examples/portfolio/model.test.mjs) | Reproducible checks and edge cases |
| [PROVENANCE.md](PROVENANCE.md) | How this example relates to the full project |
| [AGENTS.md](AGENTS.md) | Instructions for extending the example |

## Quick start

```sh
python -m http.server 8000 --directory examples/portfolio
node --test examples/portfolio/model.test.mjs
```

Open http://localhost:8000. No dependencies, accounts or API keys needed.

## What is included

A compact public collection example with authored fixture records. It does not redistribute paper text.

## Collect a saved paper page

The Python collector reads citation metadata from HTML, merges duplicates and saves a reading list.

```sh
python collector/collect.py collector/paper.html --output reading-list.json
```

Use `--url https://...` for a public page that exposes `citation_title` metadata. The included HTML is an authored parser fixture.
