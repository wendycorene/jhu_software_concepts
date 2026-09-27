"""Offline scraping checks: pagination, permissions, and saved-page cleaning."""
import html
import json
from pathlib import Path
import runpy
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

import clean
import scrape
import load_data

pytestmark = pytest.mark.integration


def page(rows, next_url=None):
    data = {'props': {'results': {'data': rows, 'links': {'next': next_url}}}}
    return '<div id="app" data-page="' + html.escape(json.dumps(data), quote=True) + '"></div>'


@pytest.fixture
def network(monkeypatch):
    request = Mock()
    monkeypatch.setattr(scrape.http, 'request', request)
    monkeypatch.setattr(scrape.time, 'sleep', Mock())
    return request


def response(body, status=200):
    return SimpleNamespace(data=body.encode(), status=status)


def test_pagination_cleans_and_deduplicates(network):
    network.side_effect = [response('User-agent: *\nAllow: /'),
                           response(page([{'id': 1, 'program': 'CS'}], '?page=2')),
                           response(page([{'id': 1}, {'id': 2, 'school': 'Example'}]))]
    rows = scrape.scrape_data()
    assert [r['URL'] for r in rows] == ['https://www.thegradcafe.com/result/1',
                                       'https://www.thegradcafe.com/result/2']
    assert rows[0]['Program'] == 'CS'
    assert rows[1]['University'] == 'Example'
    assert network.call_count == 3
    assert network.call_args.args[1] == scrape.BASE_URL + '?page=2'


@pytest.mark.parametrize('rows, known', [([], set()), ([{'id': 1}], {1}), ([{}], set())])
def test_empty_or_known_page_stops(network, rows, known):
    network.side_effect = [response('User-agent: *\nAllow: /'), response(page(rows, '?page=2'))]
    assert scrape.scrape_data(known_ids=known) == []
    assert network.call_count == 2


def test_repeated_page_stops(network):
    network.side_effect = [response('User-agent: *\nAllow: /'),
                           response(page([{'id': 1}], scrape.BASE_URL))]
    assert len(scrape.scrape_data()) == 1
    assert network.call_count == 2


@pytest.mark.parametrize('robots, status, message', [
    ('', 503, 'permissions'), ('User-agent: *\nDisallow: /', 200, 'permit'),
])
def test_robots_failure_prevents_scraping(network, robots, status, message):
    network.return_value = response(robots, status)
    with pytest.raises(RuntimeError, match=message):
        scrape.scrape_data()
    assert network.call_count == 1


def test_http_error_stops_collection(network):
    network.side_effect = [response('User-agent: *\nAllow: /'), response('', 429)]
    with pytest.raises(RuntimeError, match='HTTP 429'):
        scrape.scrape_data()


def test_external_pagination_rejected(network):
    network.side_effect = [response('User-agent: *\nAllow: /'),
                           response(page([{'id': 1}], 'https://example.com/next'))]
    with pytest.raises(ValueError, match='pagination'):
        scrape.scrape_data()
    assert network.call_count == 2


@pytest.mark.parametrize('markup', ['<html></html>', '<div id="app"></div>'])
def test_changed_page_structure_is_reported(markup):
    with pytest.raises(ValueError, match='format has changed'):
        scrape._page_data(markup)


def test_extract_next_url():
    assert scrape._extract_next_url(page([], '?page=2')) == '?page=2'


def test_saved_pages_and_json_output(monkeypatch, tmp_path):
    monkeypatch.setattr(clean, '__file__', str(tmp_path / 'clean.py'))
    folder = tmp_path / 'scrapedHTML'
    folder.mkdir()
    (folder / 'one.html').write_text(page([{'id': 7, 'notes': 'Café'}]), encoding='utf-8')
    rows = clean.scrape_data()
    clean.save_data(rows)
    assert json.loads((tmp_path / 'applicant_data.json').read_text(encoding='utf-8')) == rows
    assert rows[0]['Comments'] == 'Café'
    assert rows[0]['URL'].endswith('/7')


def test_scraper_cli(network, monkeypatch, capsys):
    monkeypatch.setattr(scrape.urllib3, 'PoolManager', Mock(return_value=Mock(request=network)))
    network.side_effect = [response('User-agent: *\nAllow: /'), response(page([{'id': 1}]))]
    loader = Mock(return_value={'inserted': 1})
    monkeypatch.setattr(load_data, 'load_records', loader)
    monkeypatch.setattr('sys.argv', ['scrape.py', '--max-pages', '1'])
    runpy.run_path(str(Path(scrape.__file__)), run_name='__main__')
    assert loader.call_args.args[0][0]['URL'].endswith('/1')
    assert 'inserted' in capsys.readouterr().out


def test_clean_cli(monkeypatch, tmp_path):
    import builtins
    source = tmp_path / 'saved.html'
    source.write_text(page([{'id': 9}]), encoding='utf-8')
    monkeypatch.setattr(Path, 'iterdir', lambda self: iter([source]))
    original_open = builtins.open
    output = tmp_path / 'output.json'

    def isolated_open(path, *args, **kwargs):
        if Path(path).name == 'applicant_data.json':
            path = output
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(builtins, 'open', isolated_open)
    runpy.run_path(clean.__file__, run_name='__main__')
    assert json.loads(output.read_text())[0]['URL'].endswith('/9')
