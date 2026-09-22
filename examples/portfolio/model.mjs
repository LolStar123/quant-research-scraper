export const normalizeDoi = value => String(value || '').trim().replace(/^https?:\/\/(dx\.)?doi\.org\//i, '').replace(/^doi:\s*/i, '').toLowerCase();
const titleKey = value => String(value || '').toLowerCase().replace(/[^\p{L}\p{N}]/gu, '');
export function cleanPaper(raw) {
    if (!raw || typeof raw.title !== 'string' || !raw.title.trim()) throw Error('Every paper needs a title.');
    const doi = normalizeDoi(raw.doi);
    const url = doi ? 'https://doi.org/' + doi : String(raw.url || '');
    return {
        doi, title: raw.title.replace(/<[^>]*>/g, '').trim(),
        authors: Array.isArray(raw.authors) ? raw.authors.map(String) : [],
        year: Number.isInteger(Number(raw.year)) && Number(raw.year) > 0 ? Number(raw.year) : null,
        journal: String(raw.journal || ''), url: /^https?:\/\//i.test(url) ? url : '',
        citations: Math.max(0, Number(raw.citations) || 0),
        topics: Array.isArray(raw.topics) ? raw.topics.map(String) : [],
    };
}
export const key = paper => paper.doi || titleKey(paper.title);
export function deduplicate(records) {
    const result = [], dois = new Map(), titles = new Map();
    for (const raw of records) {
        const p = cleanPaper(raw), title = titleKey(p.title);
        // Equal titles with two different DOIs may be distinct editions: preserve both.
        let existing = p.doi ? dois.get(p.doi) : titles.get(title);
        if (!existing) {
            const sameTitle = titles.get(title);
            if (sameTitle && (!p.doi || !sameTitle.doi)) existing = sameTitle;
        }
        if (existing) {
            existing.topics = [...new Set([...existing.topics, ...p.topics])];
            if (!existing.doi && p.doi) { existing.doi = p.doi; existing.url = p.url; dois.set(p.doi, existing); }
        } else {
            result.push(p); if (p.doi) dois.set(p.doi, p); titles.set(title, p);
        }
    }
    return result;
}
export function fromCrossref(item, topic) {
    return cleanPaper({doi:item.DOI, title:(item.title || [])[0], authors:(item.author || []).map(a=>[a.given,a.family].filter(Boolean).join(' ')), year:item.published?.['date-parts']?.[0]?.[0], journal:item['container-title']?.[0], citations:item['is-referenced-by-count'], topics:[topic]});
}
export function search(papers, {query='', topic='', sort='citations', saved=null}={}) {
    const terms=query.toLowerCase().trim().split(/\s+/).filter(Boolean);
    const rows=papers.filter(p=>(!topic||p.topics.includes(topic))&&(!saved||saved.has(key(p)))&&terms.every(t=>[p.title,p.doi,p.journal,...p.authors].join(' ').toLowerCase().includes(t)));
    return rows.sort(sort==='year'?(a,b)=>(b.year||0)-(a.year||0):sort==='title'?(a,b)=>a.title.localeCompare(b.title):(a,b)=>b.citations-a.citations);
}
const tex = value => String(value).replace(/[{}\\]/g, '');
export function bibtex(papers) {
    return papers.map((p,i)=>`@article{paper${i+1},\n  title = {${tex(p.title)}},\n  author = {${p.authors.map(tex).join(' and ')}},\n  year = {${p.year||''}},\n  journal = {${tex(p.journal)}},\n  doi = {${tex(p.doi)}},\n  url = {${tex(p.url)}}\n}`).join('\n\n');
}
