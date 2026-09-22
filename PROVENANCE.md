# Data and project scope

The seeded library contains real journal-article metadata retrieved from the Crossref REST API on the timestamp in data/papers.json. Eight public topic queries return 40 results each. Topic membership means the API returned the paper for that query; it is not an editorial quality judgement. Citation counts are Crossref counts at collection time.

This working public implementation follows the author's research collection workflow: search, collect metadata, deduplicate, retain source links and export a research queue. It adds a browser reading list and a reproducible Crossref collector. The author's local paper strategy and Navier-Stokes research scripts remain the originating workflow, not a claim that these 320 papers were all used in a backtest.

No paper full text, account data, private notes, API credentials or subscription access is bundled. Publisher links may require access. The HTML collector's paper.html remains an explicitly authored parser fixture, separate from the real public library.

Sources: https://www.crossref.org/documentation/retrieve-metadata/rest-api/ and https://api.crossref.org/works.
