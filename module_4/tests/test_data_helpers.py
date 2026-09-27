"""Normalization and connection ownership checks without database access."""
import json
import runpy
from unittest.mock import MagicMock, Mock

import pytest

import config
import load_data
import orm_queries
import query_data
from presentation import print_results

pytestmark = pytest.mark.db


@pytest.mark.parametrize('value, expected', [(None, None), (' unknown ', None), (' CS ', 'CS')])
def test_text_normalization(value, expected):
    assert load_data.text(value) == expected


@pytest.mark.parametrize('value, expected', [('3.8', 3.8), ('bad', None), (None, None),
                                            ('nan', None), (5, None), (0, None)])
def test_score_validation(value, expected):
    assert load_data.number(value, 0.01, 4) == expected


def test_normalize_invalid_date_and_missing_id(applicant_records):
    row = dict(applicant_records[0], **{'Date Added to Grad Cafe': 'not-a-date'})
    assert load_data.normalize(row)[3] is None
    with pytest.raises(ValueError, match='result ID'):
        load_data.normalize({'URL': 'invalid'})


@pytest.fixture
def fake_connection(monkeypatch):
    connection = MagicMock()
    connection.__enter__.return_value = connection
    cursor = connection.cursor.return_value.__enter__.return_value
    cursor.rowcount = 1
    cursor.fetchall.return_value = [(1,)]
    monkeypatch.setattr(config, 'connect', Mock(return_value=connection))
    monkeypatch.setattr(load_data, 'connect', Mock(return_value=connection))
    monkeypatch.setattr(query_data, 'connect', Mock(return_value=connection))
    return connection, cursor


def test_loader_counts_bad_inputs_and_owns_connection(fake_connection, applicant_records):
    connection, cursor = fake_connection
    result = load_data.load_records([applicant_records[0], None, {'URL': 'bad'}])
    assert result == {'inserted': 1, 'duplicates': 0, 'skipped': 2}
    assert len(cursor.executemany.call_args.args[1]) == 1
    connection.__exit__.assert_called_once_with(None, None, None)


def test_loader_propagates_database_error_for_rollback(fake_connection, applicant_records):
    connection, cursor = fake_connection
    cursor.executemany.side_effect = RuntimeError('insert failed')
    with pytest.raises(RuntimeError, match='insert failed'):
        load_data.load_records(applicant_records)
    assert connection.__exit__.call_args.args[0] is RuntimeError


def test_supplied_connection_stays_under_callers_control(fake_connection, applicant_records):
    connection, cursor = fake_connection
    result = load_data.load_records(applicant_records[:1], connection=connection)
    assert result == {'inserted': 1, 'duplicates': 0, 'skipped': 0}
    assert len(cursor.executemany.call_args.args[1]) == 1
    connection.commit.assert_not_called()
    connection.rollback.assert_not_called()
    connection.close.assert_not_called()
    connection.__exit__.assert_not_called()


def test_raw_queries_with_owned_and_supplied_connection(fake_connection):
    connection, cursor = fake_connection
    assert set(query_data.run_queries()) == set(range(1, 12))
    assert set(query_data.run_queries(connection)) == set(range(1, 12))
    assert cursor.execute.call_count == 22


def test_orm_queries_with_owned_and_supplied_session(monkeypatch):
    session = MagicMock()
    session.__enter__.return_value = session
    session.execute.return_value = [(1,)]
    monkeypatch.setattr(orm_queries, 'Session', Mock(return_value=session))
    assert set(orm_queries.run_queries()) == set(range(1, 12))
    assert set(orm_queries.run_queries(session)) == set(range(1, 12))
    assert session.execute.call_count == 22


@pytest.mark.analysis
def test_console_labels_and_percentages(capsys):
    print_results({1: [(3,)], 2: [(50,)]})
    text = capsys.readouterr().out
    assert 'Answer: 3' in text
    assert 'Answer: 50.00%' in text


def test_loader_cli_reads_json(monkeypatch, tmp_path, fake_connection, applicant_records, capsys):
    source = tmp_path / 'records.json'
    source.write_text(json.dumps(applicant_records), encoding='utf-8')
    monkeypatch.setattr('sys.argv', ['load_data.py', str(source)])
    runpy.run_path(load_data.__file__, run_name='__main__')
    assert 'inserted' in capsys.readouterr().out
    assert len(fake_connection[1].executemany.call_args.args[1]) == 2


@pytest.mark.parametrize('module', [query_data, orm_queries])
def test_query_cli(monkeypatch, fake_connection, module):
    import models
    import presentation
    session = MagicMock()
    session.__enter__.return_value = session
    session.execute.return_value = [(1,)]
    monkeypatch.setattr(models, 'Session', Mock(return_value=session))
    printer = Mock()
    monkeypatch.setattr(presentation, 'print_results', printer)
    runpy.run_path(module.__file__, run_name='__main__')
    assert set(printer.call_args.args[0]) == set(range(1, 12))


def test_practice_connection_helper(fake_connection, capsys):
    import databasesPractice
    assert databasesPractice.create_connection() is fake_connection[0]
    runpy.run_path(databasesPractice.__file__, run_name='__main__')
    assert 'successful' in capsys.readouterr().out
