"""Check page rendering without a live database or scraper."""

from unittest.mock import Mock

from bs4 import BeautifulSoup
import pytest

import app as app_module


pytestmark = pytest.mark.web


@pytest.fixture
def app(monkeypatch):
    """Supply predictable analysis data and an idle pull manager."""
    monkeypatch.setattr(app_module, 'run_queries', lambda: {1: [(42,)]})
    manager = Mock(state='idle', message='Ready to check for new entries.')
    manager.running.return_value = False
    application = app_module.create_app(manager=manager)
    application.config.update(TESTING=True)
    return application


def test_factory_registers_required_routes(app):
    routes = {rule.rule: rule.methods for rule in app.url_map.iter_rules()}
    for path in ('/', '/analysis', '/pull-status'):
        assert 'GET' in routes.get(path, set())
    for path in ('/pull-data', '/update-analysis'):
        assert 'POST' in routes.get(path, set())


@pytest.mark.parametrize('path', ['/analysis', '/'])
def test_analysis_page_renders_required_components(app, path):
    response = app.test_client().get(path)

    assert response.status_code == 200
    page = BeautifulSoup(response.data, 'html.parser')
    assert 'Analysis' in page.get_text()
    assert 'Answer: 42' in page.get_text(' ', strip=True)
    for test_id, label, action in (
        ('pull-data-btn', 'Pull Data', '/pull-data'),
        ('update-analysis-btn', 'Update Analysis', '/update-analysis'),
    ):
        button = page.select_one(f'button[data-testid="{test_id}"]')
        assert button is not None
        assert button.get_text(strip=True) == label
        form = button.find_parent('form')
        assert form['method'].lower() == 'post'
        assert form['action'] == action
