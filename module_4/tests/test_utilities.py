"""Exercise report and screenshot orchestration with isolated output."""
from pathlib import Path
import runpy
import sys
from types import ModuleType
from unittest.mock import MagicMock, Mock

import pytest

import config
import query_data

pytestmark = pytest.mark.integration
SOURCE = Path(__file__).resolve().parents[1] / 'src'


def test_connection_uses_environment(monkeypatch):
    monkeypatch.setenv('PGDATABASE', 'test_database')
    monkeypatch.setenv('PGUSER', 'test_user')
    monkeypatch.setenv('PGPASSWORD', 'test-only-placeholder')
    monkeypatch.setenv('PGHOST', 'localhost')
    monkeypatch.setenv('PGPORT', '5433')
    connector = Mock()
    monkeypatch.setattr(config.psycopg, 'connect', connector)
    assert config.connect() is connector.return_value
    assert connector.call_args.kwargs['dbname'] == 'test_database'
    assert config.sqlalchemy_url().port == 5433


def test_reports_generate_both_pdfs(monkeypatch, tmp_path):
    import reportlab.platypus
    results = {i: [(0,)] for i in range(1, 12)}
    results.update({3: [(3.5, 160, 155, 4)], 10: [], 11: []})
    monkeypatch.setattr(query_data, 'run_queries', lambda: results)
    document = reportlab.platypus.SimpleDocTemplate
    monkeypatch.setattr(reportlab.platypus, 'SimpleDocTemplate',
                        lambda path: document(str(tmp_path / Path(path).name)))
    runpy.run_path(str(SOURCE / 'generate_reports.py'), run_name='__main__')
    for filename in ('query_results.pdf', 'limitations.pdf'):
        data = (tmp_path / filename).read_bytes()
        assert data.startswith(b'%PDF')
        assert len(data) > 1000


def test_capture_cli_escapes_output_and_requests_three_images(monkeypatch):
    import subprocess
    api = ModuleType('playwright.sync_api')
    playwright = MagicMock()
    api.sync_playwright = MagicMock()
    api.sync_playwright.return_value.__enter__.return_value = playwright
    package = ModuleType('playwright')
    package.sync_api = api
    monkeypatch.setitem(sys.modules, 'playwright', package)
    monkeypatch.setitem(sys.modules, 'playwright.sync_api', api)
    browser = playwright.chromium.launch.return_value
    page = browser.new_page.return_value
    page.locator.return_value.count.return_value = 11
    monkeypatch.setattr(subprocess, 'check_output', Mock(return_value='<result>'))
    writer = Mock()
    monkeypatch.setattr(Path, 'mkdir', Mock())
    monkeypatch.setattr(Path, 'write_text', writer)
    runpy.run_path(str(SOURCE / 'capture_screenshots.py'), run_name='__main__')
    assert page.screenshot.call_count == 3
    assert writer.call_count == 2
    assert '&lt;result&gt;' in page.set_content.call_args.args[0]
    browser.close.assert_called_once()
