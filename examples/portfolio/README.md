# Paper library demo

See the [repository guide](../../README.md) for local serving, model tests, browser checks and collection commands.

`app.mjs` connects the citation index to Crossref and browser reading-list storage. `model.mjs` keeps normalization, deduplication, filtering and export logic independently testable. The adjacent `backtesting/` experiment uses a separate market model.
