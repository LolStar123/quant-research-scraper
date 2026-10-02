import { backtest } from "./model.mjs";
import { mountEquityChart } from "./chart.mjs";
const $ = (s) => document.querySelector(s),
    esc = (s) =>
        String(s).replace(
            /[&<>"']/g,
            (c) =>
                ({
                    "&": "&amp;",
                    "<": "&lt;",
                    ">": "&gt;",
                    '"': "&quot;",
                    "'": "&#39;",
                })[c],
        ),
    pct = (x) => (x * 100).toFixed(1) + "%";
let data, research, result, disposeChart;
function run() {
    try {
        if (!data) return;
        if ($("#cost").value === "") throw Error("Enter a cost per side, including zero.");
        result = backtest(data.prices, {
            training: +$("#training").value,
            testing: +$("#testing").value,
            costBps: +$("#cost").value,
        });
        const s = result.stats;
        $("#stats").innerHTML = [
            [pct(s.cagr), "out-of-sample CAGR"],
            [s.sharpe.toFixed(2), "daily-return Sharpe"],
            [pct(s.drawdown), "maximum drawdown"],
            [result.trades, "exposure changes"],
        ]
            .map(
                ([v, k]) =>
                    `<span><strong>${v}</strong><small>${k}</small></span>`,
            )
            .join("");
        disposeChart?.();
        disposeChart = mountEquityChart($("#chart"), result.curve, $("#cursor"), {height: 360});
        $("#run-state").textContent = `${$("#training").value} training / ${$("#testing").value} test sessions / ${result.costBps} bp per exposure change.`;
        $("#download").disabled = false;
        $("#windows").innerHTML = result.windows
            .slice()
            .reverse()
            .map(
                (r) =>
                    `<tr><td>${r.trainTo}</td><td>${r.testFrom} to ${r.testTo}</td><td>SMA ${r.period}</td><td>${r.trainingSharpe.toFixed(2)}</td></tr>`,
            )
            .join("");
        window.__backtest = { ready: true, result, prices: data.prices.length };
    } catch (e) {
        $("#run-state").textContent = e.message + " The chart shows the last successful run.";
        $("#download").disabled = true;
    }
}
function archive() {
    const q = $("#search").value.toLowerCase(),
        key = $("#sort").value,
        rows = research
            .filter((r) => (r.name + " " + r.paper).toLowerCase().includes(q))
            .sort((a, b) =>
                key === "combined_rank" ? +a[key] - b[key] : +b[key] - a[key],
            );
    $("#archive-count").textContent =
        rows.length + " of 50 original research runs";
    $("#strategies").innerHTML = rows
        .map(
            (r) =>
                `<tr><td>${esc(r.name)}<small>${esc(r.paper)}</small></td><td>${pct(+r.wf1_cagr)}</td><td>${(+r.wf1_sharpe).toFixed(2)}</td><td>${pct(+r.wf1_mdd)}</td><td>${pct(+r.wf2_ret)}</td></tr>`,
        )
        .join("");
}
for (const b of document.querySelectorAll("nav button"))
    b.onclick = () => {
        for (const s of ["experiment", "archive"])
            $("#" + s).hidden = s !== b.dataset.tab;
        for (const n of document.querySelectorAll("nav button"))
            { n.classList.toggle("active", n === b); n.setAttribute("aria-pressed", n === b); }
    };
$("#run").onclick = run;
for (const id of ["training","testing","cost"]) $("#"+id).addEventListener("input",() => { $("#run-state").textContent = "Settings changed. Run test to apply them; the chart shows the last run."; $("#download").disabled = true; });
$("#search").oninput = archive;
$("#sort").onchange = archive;
$("#download").onclick = () => {
    const keys = [
            "date",
            "equity",
            "benchmark",
            "position",
            "period",
            "return",
        ],
        text = [
            keys.join(","),
            ...result.curve.map((p) => keys.map((k) => p[k]).join(",")),
        ].join("\n"),
        url = URL.createObjectURL(new Blob([text], { type: "text/csv" })),
        a = document.createElement("a");
    a.href = url;
    a.download = "walk-forward-returns.csv";
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
};
try {
    [data, research] = await Promise.all(
        ["data/spy.json", "data/research.json"].map(async (u) => {
            const r = await fetch(u);
            if (!r.ok) throw Error("Historical data could not load");
            return r.json();
        }),
    );
    $("#source").textContent =
        `SPY / ${data.prices.length.toLocaleString()} daily closes / ${data.prices[0].date} to ${data.prices.at(-1).date}`;
    $("#provenance").textContent =
        data.note +
        " The browser experiment is a separate transparent moving-average walk-forward test; it does not reproduce all fifty Python strategies. Positions are marked to close, with no leverage, interest on cash or taxes.";
    $("#run").disabled = false;
    $('[data-tab="archive"]').disabled = false;
    run();
    archive();
    if (location.hash === "#archive") $('[data-tab="archive"]').click();
} catch (e) {
    $("#source").textContent = e.message;

}
