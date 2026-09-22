import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import {
    deduplicate,
    normalizeDoi,
    search,
    bibtex,
    cleanPaper,
} from "./model.mjs";
const data = JSON.parse(
    readFileSync(new URL("./data/papers.json", import.meta.url)),
);
test("populated real DOI catalogue", () => {
    assert.ok(data.papers.length >= 300);
    assert.equal(deduplicate(data.papers).length, data.papers.length);
    assert.ok(
        data.papers.every(
            (p) => p.doi && p.title && p.url.startsWith("https://doi.org/"),
        ),
    );
});
test("DOI deduplication upgrades no-DOI records and preserves distinct editions", () => {
    const rows = deduplicate([
        { title: "A Paper" },
        { title: "A paper", doi: "https://doi.org/10.1/X" },
        { title: "A PAPER", doi: "10.1/x" },
        { title: "A paper", doi: "10.1/y" },
    ]);
    assert.equal(rows.length, 2);
    assert.equal(rows[0].doi, "10.1/x");
    assert.equal(normalizeDoi("DOI: 10.1/X"), "10.1/x");
});
test("multiword search, sorting, topic and saved filters", () => {
    const rows = search(data.papers, { query: "market", sort: "year" });
    assert.ok(rows.length > 0);
    assert.ok(
        rows.every((p, i) => !i || (rows[i - 1].year || 0) >= (p.year || 0)),
    );
    const first = data.papers[0];
    assert.equal(
        search(data.papers, { saved: new Set([first.doi]) }).length,
        1,
    );
    assert.ok(search(data.papers, { topic: first.topics[0] }).length >= 40);
});
test("import validation and safe links", () => {
    assert.throws(() => cleanPaper({ title: "" }));
    assert.equal(
        cleanPaper({ title: "<b>Research</b>", url: "javascript:alert(1)" })
            .url,
        "",
    );
    assert.equal(cleanPaper({ title: "<b>Research</b>" }).title, "Research");
    assert.match(bibtex([data.papers[0]]), /@article\{paper1,/);
});
