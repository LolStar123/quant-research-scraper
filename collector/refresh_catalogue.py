"""Collect public Crossref metadata into the ready-to-use research library."""
import argparse
import json
import time
from urllib.error import HTTPError
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

TOPICS = ['market microstructure', 'momentum investing', 'options pricing', 'portfolio optimisation', 'volatility forecasting', 'fluid mechanics finance', 'statistical arbitrage', 'machine learning asset pricing']

def collect(topics=TOPICS, rows=40):
    papers = {}
    for topic in topics:
        url = 'https://api.crossref.org/works?' + urlencode({'query.title': topic, 'rows': rows, 'filter': 'type:journal-article'})
        request = Request(url, headers={'User-Agent': 'QuantResearchLibrary/1.0 (https://github.com/LolStar123/quant-research-scraper)'})
        for attempt in range(4):
            try:
                with urlopen(request, timeout=45) as response:
                    items = json.load(response)['message']['items']
                break
            except HTTPError as error:
                if error.code not in (429, 502, 503, 504) or attempt == 3:
                    raise
                retry = error.headers.get('Retry-After', '')
                delay = min(60, max(5 * (attempt + 1), int(retry) if retry.isdigit() else 0))
                print('Rate limit/service retry in', delay, 'seconds', flush=True)
                time.sleep(delay)
        time.sleep(2)
        for item in items:
            doi = item.get('DOI', '').lower()
            if not doi or not item.get('title'):
                continue
            if doi in papers:
                papers[doi]['topics'].append(topic)
                continue
            date = (item.get('published', {}).get('date-parts') or [[]])[0]
            papers[doi] = {'doi': doi, 'title': item['title'][0], 'authors': [' '.join(filter(None, [a.get('given'), a.get('family')])) for a in item.get('author', [])], 'year': date[0] if date else None, 'journal': (item.get('container-title') or [''])[0], 'url': 'https://doi.org/' + doi, 'citations': item.get('is-referenced-by-count', 0), 'topics': [topic]}
        print(topic, len(items), flush=True)
    return {'collected': datetime.now(timezone.utc).isoformat(), 'source': 'Crossref REST API', 'topics': topics, 'papers': list(papers.values())}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--query', action='append')
    parser.add_argument('--rows', type=int, default=40)
    parser.add_argument('--output', type=Path, default=Path(__file__).resolve().parents[1] / 'examples/portfolio/data/papers.json')
    args = parser.parse_args()
    if not 1 <= args.rows <= 1000: parser.error('rows must be between 1 and 1000')
    result = collect(args.query or TOPICS, args.rows)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print('Collected', len(result['papers']), 'unique papers')
