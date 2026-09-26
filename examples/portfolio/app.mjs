import { deduplicate, fromCrossref, key, search, bibtex } from "./model.mjs";
import { backtest } from "./backtesting/model.mjs";
const $ = (s) => document.querySelector(s);
const esc = (s) =>
    String(s ?? "").replace(
        /[&<>"']/g,
        (c) =>
            ({
                "&": "&amp;",
                "<": "&lt;",
                ">": "&gt;",
                '"': "&quot;",
                "'": "&#39;",
            })[c],
    );
let papers = [],
    topic = "",
    savedOnly = false,
    page = 0,
    saved = new Set(),
    collected = "";
const size = 8;
const forwardRuns = [
    { training: 504, testing: 63, costBps: 5 },
    { training: 252, testing: 21, costBps: 5 },
    { training: 756, testing: 126, costBps: 8 },
];
let forwardPrices = [], forwardRun = 0;
const pct = (value) => (value * 100).toFixed(1) + "%";
function renderForward() {
    if (!forwardPrices.length) return;
    const config = forwardRuns[forwardRun++ % forwardRuns.length];
    const result = backtest(forwardPrices, config);
    const stats = [
        [pct(result.stats.cagr), "oos return"],
        [result.stats.sharpe.toFixed(2), "sharpe"],
        [pct(result.stats.drawdown), "drawdown"],
    ];
    $("#forward-stats").innerHTML = stats.map(([value, label]) => `<span><strong>${value}</strong><small>${label}</small></span>`).join("");
    const curves = result.curve.flatMap((point) => [point.equity, point.benchmark]);
    const min = Math.min(...curves), max = Math.max(...curves), range = Math.max(.01, max - min);
    const x = (index) => 2 + index / (result.curve.length - 1) * 756;
    const y = (value) => 96 - (value - min) / range * 90;
    const path = (key) => result.curve.map((point, index) => `${index ? "L" : "M"}${x(index).toFixed(1)} ${y(point[key]).toFixed(1)}`).join(" ");
    $("#forward-chart").innerHTML = `<svg viewBox="0 0 760 102" preserveAspectRatio="none"><path d="${path("benchmark")}" class="benchmark"/><path d="${path("equity")}" class="strategy"/></svg>`;
    $("#forward-window").textContent = `${config.training / 252}y train · ${config.testing} unseen sessions · ${config.costBps}bp costs`;
    window.__research = { ...(window.__research || {}), forwardReady: true, forwardWindows: result.windows.length };
}
async function loadForward() {
    try {
        const response = await fetch("backtesting/data/spy.json");
        if (!response.ok) throw Error("prices unavailable");
        forwardPrices = (await response.json()).prices;
        renderForward();
    } catch (error) {
        $("#forward-window").textContent = error.message;
    }
}
$("#run-test").onclick = renderForward;
loadForward();
function store() {
    try {
        localStorage.setItem(
            "quant-reading-room",
            JSON.stringify(papers.filter((p) => saved.has(key(p)))),
        );
    } catch {
        $("#status").textContent =
            "Browser storage is full. Export your reading list to keep it.";
    }
}
function render() {
    const topics = [...new Set(papers.flatMap((p) => p.topics))];
    $("#topics").innerHTML = [["", "all papers"], ...topics.map((t) => [t, t])]
        .map(
            ([k, t]) =>
                `<button class="folder" data-topic="${esc(k)}" aria-pressed="${topic === k}">${esc(t)}</button>`,
        )
        .join("");
    $("#saved-count").textContent = saved.size;
    $("#saved-filter").setAttribute("aria-pressed", savedOnly);
    const results = search(papers, {
        query: $("#query").value,
        topic,
        sort: $("#sort").value,
        saved: savedOnly ? saved : null,
    });
    page = Math.min(page, Math.max(0, Math.ceil(results.length / size) - 1));
    $("#count").textContent =
        `${results.length} papers${savedOnly ? " in your reading list" : ""}`;
    $("#papers").innerHTML =
        results
            .slice(page * size, (page + 1) * size)
            .map(
                (p) =>
                    `<article class="paper"><div><p class="meta">${p.year || "undated"} · ${p.citations.toLocaleString()} citations</p><h2>${p.url ? `<a href="${esc(p.url)}" target="_blank" rel="noopener noreferrer">${esc(p.title)}</a>` : esc(p.title)}</h2><p>${esc(p.authors.slice(0, 3).join(", "))}${p.authors.length > 3 ? " et al." : ""}</p></div><button data-save="${esc(key(p))}" aria-pressed="${saved.has(key(p))}">${saved.has(key(p)) ? "saved" : "save"}</button></article>`,
            )
            .join("") ||
        "<p>No papers match. Clear the search, choose another collection, or search Crossref.</p>";
    $("#page-number").textContent =
        `${results.length ? page + 1 : 0} / ${Math.ceil(results.length / size)}`;
    $("#previous").disabled = page === 0;
    $("#next").disabled = (page + 1) * size >= results.length;
    $("#export-bib").disabled = $("#export-json").disabled = !saved.size;
    window.__research = {
        ...(window.__research || {}),
        ready: true,
        total: papers.length,
        filtered: results.length,
        saved: saved.size,
    };
}
$("#query").oninput = () => {
    page = 0;
    render();
};
$("#sort").onchange = () => {
    page = 0;
    render();
};
$("#topics").onclick = (e) => {
    const b = e.target.closest("[data-topic]");
    if (!b) return;
    topic = b.dataset.topic;
    page = 0;
    render();
};
$("#saved-filter").onclick = () => {
    savedOnly = !savedOnly;
    page = 0;
    render();
};
$("#papers").onclick = (e) => {
    const b = e.target.closest("[data-save]");
    if (!b) return;
    const id = b.dataset.save;
    saved.has(id) ? saved.delete(id) : saved.add(id);
    store();
    render();
};
$("#previous").onclick = () => {
    page--;
    render();
};
$("#next").onclick = () => {
    page++;
    render();
};
function download(content, name, type) {
    const url = URL.createObjectURL(new Blob([content], { type }));
    const a = document.createElement("a");
    a.href = url;
    a.download = name;
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
}
$("#export-bib").onclick = () =>
    download(
        bibtex(papers.filter((p) => saved.has(key(p)))),
        "reading-list.bib",
        "text/plain",
    );
$("#export-json").onclick = () =>
    download(
        JSON.stringify(
            papers.filter((p) => saved.has(key(p))),
            null,
            2,
        ),
        "reading-list.json",
        "application/json",
    );
$("#import").onchange = async (e) => {
    try {
        const file = e.target.files[0];
        if (!file) return;
        if (file.size > 5000000) throw Error("Choose a JSON file under 5 MB.");
        const value = JSON.parse(await file.text());
        const rows = deduplicate(Array.isArray(value) ? value : value.papers);
        papers = deduplicate([...papers, ...rows]);
        for (const r of rows)
            saved.add(
                key(
                    papers.find(
                        (p) =>
                            (p.doi === r.doi && r.doi) || p.title === r.title,
                    ) || r,
                ),
            );
        store();
        render();
        $("#status").textContent = `${rows.length} imported.`;
    } catch (e) {
        $("#status").textContent = "Import failed: " + e.message;
    }
};
$("#search-form").onsubmit = async (e) => {
    e.preventDefault();
    const q = $("#query").value.trim();
    if (!q) {
        $("#status").textContent = "Enter a topic or paper title first.";
        return;
    }
    $("#live").disabled = true;
    $("#status").textContent = "searching Crossref…";
    try {
        const r = await fetch(
            "https://api.crossref.org/works?" +
                new URLSearchParams({
                    "query.bibliographic": q,
                    rows: "40",
                    filter: "type:journal-article",
                }),
            { signal: AbortSignal.timeout(25000) },
        );
        if (!r.ok) throw Error(`Crossref returned ${r.status}`);
        const data = await r.json();
        const incoming = data.message.items
            .filter((i) => i.title?.[0])
            .map((i) => fromCrossref(i, q));
        const before = papers.length;
        papers = deduplicate([...papers, ...incoming]);
        topic = q;
        $("#query").value = "";
        savedOnly = false;
        page = 0;
        render();
        $("#status").textContent = `${incoming.length} found · ${papers.length - before} new.`;
    } catch (e) {
        $("#status").textContent = `Live search unavailable: ${e.message}`;
    } finally {
        $("#live").disabled = false;
    }
};
try {
    const r = await fetch("data/papers.json");
    if (!r.ok) throw Error("Bundled library could not load");
    const data = await r.json();
    papers = deduplicate(data.papers);
    collected = data.collected;
    try {
        const cached = JSON.parse(
            localStorage.getItem("quant-reading-room") || "[]",
        );
        const rows = deduplicate(cached);
        papers = deduplicate([...papers, ...rows]);
        saved = new Set(rows.map(key));
    } catch {}
    $("#provenance").textContent = `Crossref · ${new Date(collected).toLocaleDateString()}`;
    $("#status").textContent = `${papers.length} papers ready.`;
    render();
} catch (e) {
    $("#status").textContent = e.message;
    throw e;
}
