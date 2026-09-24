# Quant research & backtesting

Collect research papers, keep their sources, and test market ideas on unseen periods after costs.

- [Paper library](https://lolstar123.github.io/quant-research-scraper/): search 320 real paper records, fetch Crossref metadata, deduplicate and export a reading list.
- [Backtesting workbench](https://lolstar123.github.io/quant-research-scraper/backtesting/): change training windows and costs, run walk-forward tests on 5,351 SPY observations, export returns and explore 50 archived strategy results.

The library and market workbench are two stages of the research workflow. Collecting a paper does not automatically implement its strategy. The runnable browser backtest is separate from the original 50-strategy archive.

## Code map

| Path | Contents |
| --- | --- |
| `examples/portfolio/` | Paper library, Crossref collection and deduplication |
| `examples/portfolio/backtesting/` | Walk-forward model, charts, historical data and archive |
| `research/backtesting/` | Original Python research, requirements, results and source documentation |
| `tools/` | Browser audits for both workbenches |

## Run

```sh
python -m http.server 8000 --directory examples/portfolio
node --test examples/portfolio/model.test.mjs examples/portfolio/backtesting/model.test.mjs
```

Open localhost:8000 and use the papers / backtesting tabs. For the original Python research, see [its README](research/backtesting/README.md).

## Data and provenance

See [paper provenance](PROVENANCE.md) and [market-data provenance](research/backtesting/PROVENANCE.md). Historical observations and archived results are preserved as supplied; data adjustment provenance is not independently verified. Source references stay attached to the research.
