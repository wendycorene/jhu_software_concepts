"""Shared environment-based PostgreSQL configuration."""
import os
import psycopg
from sqlalchemy import URL, make_url


def _database_url():
    value = os.getenv('DATABASE_URL')
    if not value:
        return None
    url = make_url(value)
    if url.drivername not in ('postgres', 'postgresql', 'postgresql+psycopg'):
        raise ValueError('DATABASE_URL must specify PostgreSQL')
    return url.set(drivername='postgresql+psycopg')


def connection_parameters():
    return dict(dbname=os.getenv('PGDATABASE', 'gradcafe_module3'),
                user=os.getenv('PGUSER', 'postgres'),
                password=os.getenv('PGPASSWORD'),
                host=os.getenv('PGHOST', 'localhost'),
                port=os.getenv('PGPORT', '5432'))


def connect():
    url = _database_url()
    if url is not None:
        return psycopg.connect(url.set(drivername='postgresql').render_as_string(hide_password=False))
    return psycopg.connect(**connection_parameters())


def sqlalchemy_url():
    url = _database_url()
    if url is not None:
        return url
    p = connection_parameters()
    return URL.create('postgresql+psycopg', username=p['user'], password=p['password'],
                      host=p['host'], port=int(p['port']), database=p['dbname'])
