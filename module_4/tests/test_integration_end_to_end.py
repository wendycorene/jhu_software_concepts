"""Pull, update, and render using real PostgreSQL and ORM queries."""

from unittest.mock import Mock, call

from bs4 import BeautifulSoup
import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

import app as app_module
import orm_queries
from config import sqlalchemy_url
from load_data import SCHEMA, load_records


pytestmark = pytest.mark.integration


@pytest.fixture
def workflow(monkeypatch, applicant_records):
    """Share an isolated connection between the real loader and ORM sessions."""
    engine = create_engine(sqlalchemy_url(), poolclass=NullPool)
    try:
        connection = engine.connect()
    except OperationalError:
        engine.dispose()
        pytest.fail('Cannot connect to PostgreSQL. Set the PG connection variables '
                    'and PGPASSWORD in this terminal.', pytrace=False)
    try:
        connection.begin()
        connection.exec_driver_sql('SET LOCAL search_path TO pg_temp')
        connection.exec_driver_sql(SCHEMA.replace(
            'CREATE TABLE IF NOT EXISTS', 'CREATE TEMPORARY TABLE'))
        # Successful application sessions release their savepoints so loader
        # writes remain visible; the outer test transaction is rolled back.
        sessions = sessionmaker(bind=connection, join_transaction_mode='create_savepoint')
        monkeypatch.setattr(app_module, 'Session', sessions.begin)
        monkeypatch.setattr(orm_queries, 'Session', sessions.begin)
        monkeypatch.setattr(app_module, 'load_records', lambda rows: load_records(
            rows, connection=connection.connection.driver_connection))
        scraper = Mock(return_value=applicant_records)
        monkeypatch.setattr(app_module, 'scrape_data', scraper)
        # Execute the worker immediately: deterministic, without sleeps.
        monkeypatch.setattr(app_module.threading, 'Thread',
                            lambda *, target, daemon: Mock(start=target))
        manager = app_module.PullManager()
        application = app_module.create_app(manager=manager)
        application.config['TESTING'] = True
        yield application.test_client(), connection, scraper, manager
    finally:
        connection.rollback()
        connection.close()
        engine.dispose()


def answers(response):
    """Read only answer cards, and reject a database-error page."""
    assert response.status_code == 200
    page = BeautifulSoup(response.data, 'html.parser')
    assert page.select_one('[role="alert"]') is None
    values = [node.get_text(strip=True) for node in page.select('.answer')]
    assert len(values) == 11
    assert all(value.startswith('Answer: ') for value in values)
    return values


def test_pull_update_render(workflow):
    client, connection, scraper, manager = workflow
    before = answers(client.get('/analysis'))
    assert before[0] == 'Answer: 0'
    assert before[1] == 'Answer: N/A'

    response = client.post('/pull-data')
    assert response.status_code == 202
    assert response.get_json() == {'ok': True}
    assert manager.state == 'success'
    assert connection.exec_driver_sql('SELECT count(*) FROM applicants').scalar_one() == 2
    scraper.assert_called_once_with(known_ids=set())

    updated = answers(client.post('/update-analysis'))
    rendered = answers(client.get('/analysis'))
    assert rendered == updated
    assert rendered[0] == 'Answer: 2'
    assert rendered[1] == 'Answer: 50.00%'
    assert rendered[3] == 'Answer: 3.80'


def test_overlapping_pulls_keep_analysis_consistent(workflow, applicant_records):
    client, connection, scraper, manager = workflow
    new_record = dict(applicant_records[1],
                      URL='https://www.thegradcafe.com/result/900003')
    scraper.side_effect = [applicant_records, [applicant_records[1], new_record]]

    assert client.post('/pull-data').status_code == 202
    first = answers(client.post('/update-analysis'))
    assert first[0:2] == ['Answer: 2', 'Answer: 50.00%']

    assert client.post('/pull-data').status_code == 202
    assert manager.state == 'success'
    ids = connection.exec_driver_sql('SELECT p_id FROM applicants ORDER BY p_id').scalars().all()
    assert ids == [900001, 900002, 900003]
    assert scraper.call_args_list == [call(known_ids=set()), call(known_ids={900001, 900002})]

    updated = answers(client.post('/update-analysis'))
    assert updated[0:2] == ['Answer: 3', 'Answer: 66.67%']
    assert answers(client.get('/analysis')) == updated
