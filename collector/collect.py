"""Collect citation metadata from saved HTML or a supplied public paper page."""
import argparse
import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request, urlopen


class Citations(HTMLParser):
    def __init__(self):
        super().__init__()
        self.metadata = {}

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'meta':
            key = attrs.get('name', '').lower()
            if key.startswith('citation_'):
                self.metadata.setdefault(key, []).append(attrs.get('content', ''))


def parse(html, source):
    parser = Citations()
    parser.feed(html)
    fields = parser.metadata
    def first(key):
        return fields.get('citation_' + key, [''])[0].strip()
    if not first('title'):
        raise ValueError(f'No citation_title found in {source}')
    return {'title': first('title'), 'authors': fields.get('citation_author', []),
            'doi': first('doi').lower().removeprefix('https://doi.org/'),
            'date': first('publication_date'), 'url': source}


def collect(pages):
    unique = {}
    for source, html in pages:
        paper = parse(html, source)
        key = paper['doi'] or ''.join(c for c in paper['title'].casefold() if c.isalnum())
        if key in unique:
            unique[key]['sources'].append(source)
        else:
            unique[key] = {**paper, 'sources': [source]}
    return list(unique.values())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('files', nargs='*', help='Saved HTML pages')
    parser.add_argument('--url', action='append', default=[], help='Public page to read once')
    parser.add_argument('--output', default='reading-list.json')
    args = parser.parse_args()
    pages = [(str(p), Path(p).read_text(encoding='utf-8')) for p in args.files]
    for url in args.url:
        if not url.startswith(('https://', 'http://')):
            parser.error('Only http(s) pages are supported')
        request = Request(url, headers={'User-Agent': 'ResearchReadingList/1.0'})
        with urlopen(request, timeout=20) as response:
            pages.append((url, response.read(2_000_000).decode('utf-8', errors='replace')))
    if not pages:
        parser.error('Supply a saved HTML file or --url')
    records = collect(pages)
    Path(args.output).write_text(json.dumps(records, indent=2), encoding='utf-8')
    print(f'{len(pages)} pages -> {len(records)} unique papers -> {args.output}')


if __name__ == '__main__':
    main()
