// SVG follows rendered pixel dimensions so labels stay readable on phones.
export function mountEquityChart(container, curve, cursor, { height = 320 } = {}) {
    let index = curve.length - 1;
    const colors = { equity: "#acbadf", benchmark: "#77b6bd" };
    const redraw = () => {
        const width = Math.max(240, Math.round(container.clientWidth));
        const compact = width < 500, h = compact ? 250 : height;
        const left = 44, right = width - 13, top = 16, bottom = h - 40;
        const values = curve.flatMap(p => [p.equity, p.benchmark]);
        const ceiling = Math.max(1, ...values) * 1.06;
        const step = niceStep(ceiling / 4), max = Math.ceil(ceiling / step) * step;
        const x = i => left + i / Math.max(1, curve.length - 1) * (right - left);
        const y = value => bottom - value / max * (bottom - top);
        const ticks = Array.from({length: Math.round(max / step) + 1}, (_, i) => i * step);
        const dates = compact ? [0, curve.length - 1] : [0, Math.floor(curve.length / 2), curve.length - 1];
        container.classList.add("equity-plot");
        container.innerHTML = `<svg viewBox="0 0 ${width} ${h}" role="img" aria-label="Historical compounded equity: moving-average rule and SPY buy and hold">
            ${ticks.map(v => `<line x1="${left}" x2="${right}" y1="${y(v)}" y2="${y(v)}" stroke="#343d50"/><text x="${left - 9}" y="${y(v)+4}" text-anchor="end" fill="#aab5c9" font-family="Consolas,monospace" font-size="12">${v.toFixed(step < 1 ? 1 : 0)}</text>`).join("")}
            <line x1="${left}" x2="${right}" y1="${y(1)}" y2="${y(1)}" stroke="#aab5c9" opacity=".4" stroke-dasharray="2 4"/>
            ${["benchmark", "equity"].map(k => `<polyline fill="none" stroke="${colors[k]}" stroke-width="1.8" stroke-linejoin="round" points="${curve.map((p,i) => `${x(i).toFixed(1)},${y(p[k]).toFixed(1)}`).join(" ")}"/>`).join("")}
            <g aria-hidden="true"><line data-inspection="line" y1="${top}" y2="${bottom}" stroke="#edf0f5" opacity=".55" stroke-dasharray="3 4"/><circle data-inspection="equity" r="4" fill="${colors.equity}" stroke="#191e29" stroke-width="2"/><circle data-inspection="benchmark" r="4" fill="${colors.benchmark}" stroke="#191e29" stroke-width="2"/></g>
            ${dates.map((i,n) => `<line x1="${x(i)}" x2="${x(i)}" y1="${bottom}" y2="${bottom+5}" stroke="#aab5c9"/><text x="${x(i)}" y="${h-14}" text-anchor="${n === 0 ? 'start' : n === dates.length-1 ? 'end' : 'middle'}" fill="#aab5c9" font-size="12" font-family="Consolas,monospace">${compact ? curve[i].date.slice(0,7) : curve[i].date}</text>`).join("")}
        </svg>`;
        const inspect = () => {
            const point = curve[index], px = x(index);
            const line = container.querySelector('[data-inspection="line"]');
            line.setAttribute("x1",px); line.setAttribute("x2",px);
            for (const k of ["equity","benchmark"]) {
                const dot = container.querySelector(`[data-inspection="${k}"]`);
                dot.setAttribute("cx",px); dot.setAttribute("cy",y(point[k]));
            }
            cursor.textContent = `${point.date} \u00b7 rule ${point.equity.toFixed(3)} \u00b7 buy & hold ${point.benchmark.toFixed(3)} \u00b7 ${point.position ? 'invested' : 'cash'} \u00b7 SMA ${point.period}`;
        };
        inspect();
        container.onpointermove = e => {
            const rect = container.getBoundingClientRect();
            index = Math.max(0,Math.min(curve.length-1,Math.round((e.clientX-rect.left-left)/(right-left)*(curve.length-1))));
            inspect();
        };
        container.onkeydown = e => {
            if (!["ArrowLeft","ArrowRight","Home","End"].includes(e.key)) return;
            e.preventDefault();
            index = e.key === "Home" ? 0 : e.key === "End" ? curve.length-1 : Math.max(0,Math.min(curve.length-1,index+(e.key === "ArrowRight" ? 1 : -1)));
            inspect();
        };
    };
    const observer = new ResizeObserver(redraw);
    observer.observe(container); redraw();
    return () => { observer.disconnect(); container.onpointermove = null; container.onkeydown = null; };
}
function niceStep(value) {
    const magnitude = 10 ** Math.floor(Math.log10(value));
    const fraction = value / magnitude;
    return (fraction <= 1 ? 1 : fraction <= 2 ? 2 : fraction <= 5 ? 5 : 10) * magnitude;
}
