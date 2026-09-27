"""Button requests use fakes instead of PostgreSQL, threads, or live scraping."""

from unittest.mock import MagicMock, Mock

import pytest

import app as app_module


pytestmark = pytest.mark.buttons


@pytest.fixture
def button_app(monkeypatch):
    manager = Mock(state='idle', message='Ready.')
    manager.running.return_value = False
    manager.start.return_value = True
    query = Mock(return_value={1: [(42,)]})
    monkeypatch.setattr(app_module, 'run_queries', query)
    application = app_module.create_app(manager=manager)
    application.config['TESTING'] = True
    return application.test_client(), manager, query


def test_pull_starts_background_work(button_app):
    client, manager, query = button_app
    response = client.post('/pull-data')
    assert response.status_code in (200, 202)
    assert response.get_json() == {'ok': True}
    manager.start.assert_called_once_with()
    query.assert_not_called()


def test_update_refreshes_analysis(button_app):
    client, manager, query = button_app
    response = client.post('/update-analysis')
    assert response.status_code == 200
    assert 'Answer: 42' in response.get_data(as_text=True)
    query.assert_called_once_with()
    manager.start.assert_not_called()


@pytest.mark.parametrize('path', ['/pull-data', '/update-analysis'])
def test_busy_request_does_no_work(button_app, path):
    client, manager, query = button_app
    manager.running.return_value = True
    response = client.post(path)
    assert response.status_code == 409
    assert response.get_json() == {'busy': True}
    manager.start.assert_not_called()
    query.assert_not_called()


def test_pull_handles_another_request_winning_the_lock(button_app):
    client, manager, query = button_app
    manager.start.return_value = False
    response = client.post('/pull-data')
    assert response.status_code == 409
    assert response.get_json() == {'busy': True}
    query.assert_not_called()


def test_pull_passes_scraped_rows_to_loader(monkeypatch):
    """Run the real manager synchronously with fake external dependencies."""
    session = MagicMock()
    session.scalar.return_value = True
    session.scalars.return_value = [101]
    session.__enter__.return_value = session
    monkeypatch.setattr(app_module, 'Session', Mock(return_value=session))
    records = [{'p_id': 102, 'program': 'Computer Science'}]
    scraper = Mock(return_value=records)
    loader = Mock(return_value={'inserted': 1, 'duplicates': 0, 'skipped': 0})
    monkeypatch.setattr(app_module, 'scrape_data', scraper)
    monkeypatch.setattr(app_module, 'load_records', loader)

    def immediate_thread(*, target, daemon):
        return Mock(start=target)

    monkeypatch.setattr(app_module.threading, 'Thread', immediate_thread)
    manager = app_module.PullManager()
    application = app_module.create_app(manager=manager)
    application.config['TESTING'] = True
    response = application.test_client().post('/pull-data')

    assert response.status_code in (200, 202)
    assert response.get_json() == {'ok': True}
    scraper.assert_called_once_with(known_ids={101})
    loader.assert_called_once_with(records)
    assert manager.state == 'success'
    assert not manager.lock.locked()
