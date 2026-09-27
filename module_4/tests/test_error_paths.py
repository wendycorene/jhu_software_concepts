"""Deterministic checks for busy locks, worker failures, and unavailable data."""
from unittest.mock import MagicMock, Mock
import runpy

import pytest
from flask import Flask

import app as app_module

pytestmark = pytest.mark.buttons


@pytest.fixture
def session(monkeypatch):
    session = MagicMock()
    session.__enter__.return_value = session
    session.scalar.return_value = True
    monkeypatch.setattr(app_module, 'Session', Mock(return_value=session))
    return session


def test_local_lock_prevents_new_pull(session):
    manager = app_module.PullManager()
    manager.lock.acquire()
    try:
        assert manager.running()
        assert manager.start() is False
        session.scalar.assert_not_called()
    finally:
        manager.lock.release()


def test_thread_start_failure_releases_lock(monkeypatch, session):
    monkeypatch.setattr(app_module.threading, 'Thread', Mock(
        return_value=Mock(start=Mock(side_effect=RuntimeError('thread failed')))))
    manager = app_module.PullManager()
    with pytest.raises(RuntimeError, match='thread failed'):
        manager.start()
    assert manager.state == 'error'
    assert not manager.lock.locked()


def test_other_process_owns_pull_lock(monkeypatch, session):
    session.scalar.return_value = False
    scraper = Mock()
    monkeypatch.setattr(app_module, 'scrape_data', scraper)
    manager = app_module.PullManager()
    manager.lock.acquire()
    manager._run()
    assert manager.state == 'idle'
    assert not manager.lock.locked()
    scraper.assert_not_called()


def test_loader_failure_is_visible_and_unlocks(monkeypatch, session):
    monkeypatch.setattr(app_module, 'scrape_data', Mock(return_value=[]))
    monkeypatch.setattr(app_module, 'load_records', Mock(side_effect=RuntimeError('load failed')))
    manager = app_module.PullManager()
    manager.lock.acquire()
    manager._run()
    assert manager.state == 'error'
    assert not manager.lock.locked()
    session.execute.assert_called_once()  # Advisory lock released even on error.


@pytest.mark.web
def test_query_failure_displays_error(monkeypatch):
    monkeypatch.setattr(app_module, 'run_queries', Mock(side_effect=RuntimeError('offline')))
    manager = Mock(state='idle', message='Ready')
    response = app_module.create_app(manager).test_client().get('/analysis')
    assert response.status_code == 200
    assert b'The database is unavailable' in response.data
    assert b'role="alert"' in response.data


@pytest.mark.parametrize('running', [True, False])
def test_status_reports_worker_state(running):
    manager = Mock(state='success', message='Finished')
    manager.running.return_value = running
    response = app_module.create_app(manager).test_client().get('/pull-status')
    assert response.status_code == 200
    assert response.json['running'] is running
    assert response.json['state'] == ('running' if running else 'success')
    assert response.headers['Cache-Control'] == 'no-store'


def test_status_failure_returns_503():
    manager = Mock()
    manager.running.side_effect = RuntimeError('offline')
    response = app_module.create_app(manager).test_client().get('/pull-status')
    assert response.status_code == 503
    assert 'Cannot check progress' in response.json['message']


@pytest.mark.web
def test_app_cli_uses_configured_port(monkeypatch):
    run = Mock()
    monkeypatch.setattr(Flask, 'run', run)
    monkeypatch.setenv('PORT', '5055')
    runpy.run_path(app_module.__file__, run_name='__main__')
    run.assert_called_once_with(host='127.0.0.1', port=5055, debug=False)
