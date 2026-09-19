"""Module 2 scraper, adapted to fetch recent pages safely when requested."""
import json
import time
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
import urllib3
from bs4 import BeautifulSoup
from clean import clean_data

BASE_URL = 'https://www.thegradcafe.com/survey'
USER_AGENT = 'GradCafeCourseProject/1.0'
http = urllib3.PoolManager(timeout=urllib3.Timeout(connect=10, read=30))


def _page_data(html):
    app = BeautifulSoup(html, 'html.parser').find('div', id='app')
    if app is None or not app.get('data-page'):
        raise ValueError('The survey page format has changed or access is unavailable.')
    return json.loads(app['data-page'])['props']['results']


def _extract_next_url(html):
    return _page_data(html)['links'].get('next')


def scrape_data(known_ids=None, max_pages=10):
    """Return cleaned recent records; cap each pull at ten sequential pages.

    Stop after an entirely known page. A bounded pull can leave a large backlog;
    use the CLI with a larger max_pages value when collecting historical data.
    """
    known_ids = set(known_ids or ())
    robots_url = 'https://www.thegradcafe.com/robots.txt'
    response = http.request('GET', robots_url, headers={'User-Agent': USER_AGENT}, retries=False)
    if response.status != 200:
        raise RuntimeError('Unable to check site scraping permissions. Try again later.')
    robots = RobotFileParser()
    robots.parse(response.data.decode('utf-8').splitlines())
    records, seen, url = [], set(), BASE_URL
    delay = max(2, robots.crawl_delay(USER_AGENT) or robots.crawl_delay('*') or 0)
    for _ in range(max_pages):
        if not url or url in seen:
            break
        parsed = urlparse(url)
        if parsed.scheme != 'https' or parsed.hostname not in ('www.thegradcafe.com', 'thegradcafe.com'):
            raise ValueError('Unexpected pagination address.')
        if not robots.can_fetch(USER_AGENT, url):
            raise RuntimeError('The site does not currently permit this survey request.')
        seen.add(url)
        time.sleep(delay)
        response = http.request('GET', url, headers={'User-Agent': USER_AGENT}, retries=False)
        if response.status != 200:
            raise RuntimeError(f'The survey returned HTTP {response.status}; collection stopped.')
        page = _page_data(response.data.decode('utf-8'))
        rows = page['data']
        if not rows:
            break
        fresh = [row for row in rows if row.get('id') is not None and int(row['id']) not in known_ids]
        records.extend(clean_data(fresh))
        known_ids.update(int(row['id']) for row in fresh)
        if not fresh:
            break
        next_url = page.get('links', {}).get('next')
        url = urljoin(BASE_URL, next_url) if next_url else None
    return records


if __name__ == '__main__':
    import argparse
    from load_data import load_records
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--max-pages', type=int, default=10)
    args = parser.parse_args()
    print(load_records(scrape_data(max_pages=args.max_pages)))
