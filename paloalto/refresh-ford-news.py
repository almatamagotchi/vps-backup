#!/usr/bin/env python3
"""Scrape official Ford news from fromtheroad.ford.com and corporate.ford.com."""
import re, json, urllib.request, sys, os
from datetime import datetime

OUT = '/usr/local/www/alma/paloalto/ford-news.json'
CACHE = '/usr/local/www/alma/paloalto/ford-news-cache.json'

SKIP_WORDS = ['featured stories', 'discover more', 'quality comes first', 
              'this week in', 'mustang on a roll']

def extract(html, source, base_url):
    """Extract article titles, URLs, and dates from HTML."""
    headings = list(re.finditer(
        r'<(h[23])[^>]*>((?:[^<]|<(?!/\1>))*?)</\1>', html, re.DOTALL))
    articles = []
    for m in headings:
        text = re.sub(r'<[^>]+>', '', m.group(2)).strip()
        text = text.replace('&#x27;', "'").replace('&amp;', '&')
        if len(text) < 20 or any(s in text.lower() for s in SKIP_WORDS):
            continue
        # Search backwards for href in the preceding 4000 chars
        before = html[:m.start()]
        links = re.findall(r'href="([^"]+)"', before[-4000:])
        url = None
        for l in reversed(links):
            if '/us/en/' in l and len(l) > 10:
                if l not in ('/us/en/home', '/us/en/company-news'):
                    url = l
                    break
        # Try to find a date near the article (up to 2000 chars before heading)
        date = None
        date_area = before[-2000:]
        date_match = re.search(r'(\d{1,2}/\d{1,2}/\d{4})', date_area)
        if date_match:
            date = date_match.group(1)

        articles.append({
            'title': text,
            'url': (base_url + url) if url and not url.startswith('http') else (url or ''),
            'source': source,
            'date': date
        })
    return articles


def load_cache():
    """Load the article cache (title -> first_seen_date)."""
    if os.path.exists(CACHE):
        try:
            with open(CACHE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {}


def save_cache(cache):
    """Save the article cache."""
    with open(CACHE, 'w') as f:
        json.dump(cache, f)


def fetch_page(url):
    """Fetch a page with a browser-like user agent."""
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (compatible; FordNewsBot/1.0)',
        'Accept': 'text/html,application/xhtml+xml'
    })
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.read().decode('utf-8', errors='replace')


def main():
    articles = []

    # 1. From The Road
    try:
        html = fetch_page('https://www.fromtheroad.ford.com/us/en/home')
        articles.extend(extract(html, 'Ford News', 'https://www.fromtheroad.ford.com'))
    except Exception as e:
        print(f'fromtheroad: {e}', file=sys.stderr)

    # 2. Corporate Ford
    try:
        html = fetch_page('https://corporate.ford.com/newsroom.html')
        articles.extend(extract(html, 'Ford Corporate', 'https://corporate.ford.com'))
    except Exception as e:
        print(f'corporate: {e}', file=sys.stderr)

    # Assign dates via cache
    cache = load_cache()
    today = datetime.now().strftime('%-m/%-d')
    for a in articles:
        key = a['source'] + '|' + a['title'][:80]
        if key in cache:
            a['date'] = cache[key]
        elif a['date']:
            cache[key] = a['date']
        else:
            a['date'] = today
            cache[key] = today

    # Take 2 from each source, 4 total
    result = []
    seen_sources = {'Ford News': 0, 'Ford Corporate': 0}
    for a in articles:
        src = a['source']
        if seen_sources.get(src, 0) < 2:
            result.append(a)
            seen_sources[src] = seen_sources.get(src, 0) + 1
    result = result[:4]

    save_cache(cache)

    with open(OUT, 'w') as f:
        json.dump(result, f)
    print(f'Wrote {len(result)} articles to {OUT}')


if __name__ == '__main__':
    main()
