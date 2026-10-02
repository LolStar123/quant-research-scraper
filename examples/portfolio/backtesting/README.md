# Walk-forward experiment

See the [repository guide](../../../README.md) for local serving and checks. This folder contains the browser experiment, historical SPY cache and separate 50-strategy archive.

`model.mjs` selects a moving-average period using training returns and evaluates the next unseen window. `chart.mjs` renders equity at the actual container width. `app.mjs` applies settings, renders window decisions and exports daily out-of-sample returns.

The original Python strategies and their provenance are in [research/backtesting](../../../research/backtesting/README.md).
