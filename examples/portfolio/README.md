# quant finance research scraper: working example

Clean and search a small research catalogue; export the reading list.

**[Open the demo](https://lolstar123.github.io/quant-research-scraper/)** · [Calculation / workflow code](model.mjs) · [Checks](model.test.mjs)

![Example output](preview.png)

## Run it

From the repository root, with Python 3 and Node.js 22:

```sh
python -m http.server 8000 --directory examples/portfolio
```

Open http://localhost:8000. Change an input, or edit the JSON fixture, then export the computed result as JSON or CSV.

```sh
node --test examples/portfolio/model.test.mjs
```

## What it does

Search for a topic, collect paper metadata, then deduplicate by DOI or title. The reading list keeps titles, dates and source links together so an interesting idea can become a testable strategy.

## Scope and source

A compact public collection example with authored fixture records. It does not redistribute paper text.

User-described research collection workflow; local quant/paper_strategies_* research and quant/navier_stokes_research/paper_find.py.

`model.mjs` is the small public implementation. `app.mjs` connects its inputs and outputs to the browser. No package install or network key is needed to run the example. GitHub Pages runs the same files after the checks pass.
