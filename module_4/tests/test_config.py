"""Connection URL precedence and encoding without a real database."""
from unittest.mock import Mock

import pytest
from psycopg.conninfo import conninfo_to_dict

import config

pytestmark = pytest.mark.db


@pytest.mark.parametrize('scheme', ['postgres', 'postgresql', 'postgresql+psycopg'])
def test_database_url_overrides_pg_settings(monkeypatch, scheme):
    monkeypatch.setenv('PGDATABASE', 'ignored')
    monkeypatch.setenv('PGHOST', 'ignored')
    monkeypatch.setenv('DATABASE_URL',
                       f'{scheme}://reader:p%40ss%3Aword@localhost:5433/analytics?sslmode=require')
    connector = Mock()
    monkeypatch.setattr(config.psycopg, 'connect', connector)
    assert config.connect() is connector.return_value
    supplied = conninfo_to_dict(connector.call_args.args[0])
    assert supplied['dbname'] == 'analytics'
    assert supplied['host'] == 'localhost'
    assert supplied['port'] == '5433'
    assert supplied['password'] == 'p@ss:word'
    assert supplied['sslmode'] == 'require'
    url = config.sqlalchemy_url()
    assert url.drivername == 'postgresql+psycopg'
    assert url.database == supplied['dbname']
    assert url.password == supplied['password']
    assert url.query['sslmode'] == 'require'


def test_empty_database_url_uses_pg_settings(monkeypatch):
    monkeypatch.setenv('DATABASE_URL', '')
    monkeypatch.setenv('PGDATABASE', 'fallback')
    connector = Mock()
    monkeypatch.setattr(config.psycopg, 'connect', connector)
    config.connect()
    assert connector.call_args.kwargs['dbname'] == 'fallback'
    assert config.sqlalchemy_url().database == 'fallback'


@pytest.mark.parametrize('function', [config.connect, config.sqlalchemy_url])
def test_non_postgres_url_is_rejected(monkeypatch, function):
    monkeypatch.setenv('DATABASE_URL', 'sqlite:///local.db')
    with pytest.raises(ValueError, match='must specify PostgreSQL'):
        function()
