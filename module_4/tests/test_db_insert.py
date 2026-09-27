"""Exercise real PostgreSQL inserts, uniqueness, schema, and analysis queries."""

from datetime import date
from unittest.mock import MagicMock, Mock

from psycopg.rows import dict_row
import pytest

import app as app_module
from load_data import load_records
from query_data import run_queries


pytestmark = pytest.mark.db


@pytest.fixture
def pull_client(monkeypatch, db_connection, applicant_records):
    """Use the real pull manager and loader, with a fake scraper and no thread."""
    # Coordination is tested separately; writes use real PostgreSQL here.
    session = MagicMock()
    session.__enter__.return_value = session
    session.scalar.return_value = True
    session.scalars.return_value = []
    monkeypatch.setattr(app_module, 'Session', Mock(return_value=session))
    monkeypatch.setattr(app_module, 'scrape_data', Mock(return_value=applicant_records))
    monkeypatch.setattr(app_module, 'load_records',
                        lambda rows: load_records(rows, connection=db_connection))
    monkeypatch.setattr(app_module.threading, 'Thread',
                        lambda *, target, daemon: Mock(start=target))
    application = app_module.create_app(manager=app_module.PullManager())
    application.config['TESTING'] = True
    return application.test_client()


def test_pull_inserts_required_fields(pull_client, db_connection):
    assert db_connection.execute('SELECT count(*) FROM applicants').fetchone()[0] == 0
    response = pull_client.post('/pull-data')
    assert response.status_code == 202
    assert response.get_json() == {'ok': True}

    with db_connection.cursor(row_factory=dict_row) as cursor:
        cursor.execute('SELECT * FROM applicants ORDER BY p_id')
        rows = cursor.fetchall()
    assert len(rows) == 2
    expected_fields = {
        'p_id', 'program', 'comments', 'date_added', 'url', 'status', 'term',
        'us_or_international', 'gpa', 'gre', 'gre_v', 'gre_aw', 'degree',
        'llm_generated_program', 'llm_generated_university',
    }
    for row in rows:
        assert set(row) == expected_fields
        # These complete inputs should preserve even the optional fields.
        assert all(row[field] is not None for field in expected_fields)
    assert rows[0]['p_id'] == 900001
    assert rows[0]['program'] == 'Example University, Computer Science'
    assert rows[0]['date_added'] == date(2026, 9, 20)
    assert rows[0]['gpa'] == pytest.approx(3.8)


def test_repeated_pull_does_not_duplicate_rows(pull_client, db_connection):
    for _ in range(2):
        assert pull_client.post('/pull-data').status_code == 202
    assert db_connection.execute('SELECT count(*) FROM applicants').fetchone()[0] == 2


def test_overlapping_load_keeps_existing_records(db_connection, applicant_records):
    assert load_records(applicant_records, db_connection)['inserted'] == 2
    duplicate = dict(applicant_records[0], Comments='Should not overwrite')
    new_record = dict(applicant_records[1],
                      URL='https://www.thegradcafe.com/result/900003')
    result = load_records([duplicate, new_record], db_connection)
    assert result == {'inserted': 1, 'duplicates': 1, 'skipped': 0}
    assert db_connection.execute('SELECT count(*) FROM applicants').fetchone()[0] == 3
    assert db_connection.execute(
        'SELECT comments FROM applicants WHERE p_id = %s', (900001,)
    ).fetchone()[0] == 'Synthetic test record'


def test_query_returns_expected_analysis_keys(db_connection, applicant_records):
    load_records(applicant_records, db_connection)
    results = run_queries(connection=db_connection)
    assert isinstance(results, dict)
    assert set(results) == set(range(1, 12))
    assert results[1] == [(2,)]
    assert float(results[2][0][0]) == pytest.approx(50.0)
    assert results[3][0] == pytest.approx((3.8, 165, 160, 4.5))
    assert results[5] == [(None,)]  # No Fall 2025 records: undefined percentage.
