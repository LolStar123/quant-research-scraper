export const defaults = {
  query: "",
  records: [
    {
      title: "Momentum after costs",
      doi: "10.example/momentum",
      year: 2023,
      url: "https://example.org/momentum",
      source: "catalogue A",
      tags: ["momentum", "execution"],
    },
    {
      title: "MOMENTUM AFTER COSTS",
      doi: "https://doi.org/10.example/momentum",
      year: 2023,
      url: "https://example.org/momentum",
      source: "catalogue B",
      tags: ["trend"],
    },
    {
      title: "Options under rough volatility",
      doi: "",
      year: 2024,
      url: "https://example.org/rough-volatility",
      source: "catalogue A",
      tags: ["options", "volatility"],
    },
    {
      title: "Order flow and market impact",
      doi: "10.example/orderflow",
      year: 2022,
      url: "https://example.org/orderflow",
      source: "catalogue C",
      tags: ["execution", "liquidity"],
    },
    {
      title: "A test of gamma scalping",
      doi: "",
      year: 2025,
      url: "https://example.org/gamma",
      source: "catalogue B",
      tags: ["options", "hedging"],
    },
    {
      title: "Order flow and market impact",
      doi: "10.example/orderflow",
      year: 2022,
      url: "https://example.org/orderflow",
      source: "catalogue A",
      tags: ["microstructure"],
    },
  ],
};
export const controls = [{ key: "query", label: "Find a topic", type: "text" }];
export function collect(records, query = "") {
  const unique = new Map();
  for (const r of records) {
    if (!r.title?.trim() || !/^https?:\/\//.test(r.url))
      throw Error("Each paper needs a title and an http(s) source URL.");
    const doi = (r.doi || "")
      .toLowerCase()
      .replace(/^https?:\/\/(?:dx\.)?doi.org\//, "")
      .trim();
    const key = doi || r.title.toLowerCase().replace(/[^\p{L}\p{N}]/gu, "");
    const old = unique.get(key);
    unique.set(key, {
      ...r,
      doi,
      sources: [...new Set([...(old?.sources || []), r.source])],
      tags: [...new Set([...(old?.tags || []), ...(r.tags || [])])],
    });
  }
  const terms = query.toLowerCase().trim().split(/\s+/).filter(Boolean);
  return [...unique.values()]
    .filter((r) =>
      terms.every((t) =>
        (r.title + " " + r.tags.join(" ")).toLowerCase().includes(t),
      ),
    )
    .sort((a, b) => b.year - a.year);
}
export function run(input) {
  const rows = collect(input.records, input.query);
  return {
    summary: `${rows.length} papers in the reading list`,
    metrics: {
      "source records": input.records.length,
      "duplicates removed":
        input.records.length - collect(input.records).length,
      matches: rows.length,
    },
    columns: ["paper", "year", "topics", "found in", "source"],
    rows: rows.map((r) => [
      r.title,
      r.year,
      r.tags.join(", "),
      r.sources.join(" + "),
      r.url,
    ]),
    steps: [
      "Import metadata from source listings",
      "Normalise DOI and title; merge duplicate records",
      "Search topics and retain provenance",
      "Export the shortlist for research",
    ],
    artifact: { reading_list: rows },
  };
}
