"""Shared environment-based PostgreSQL configuration."""
import os
import psycopg
from sqlalchemy import URL


def connection_parameters():
    return dict(dbname=os.getenv('PGDATABASE', 'gradcafe_module3'),
                user=os.getenv('PGUSER', 'postgres'),
                password=os.getenv('PGPASSWORD'),
                host=os.getenv('PGHOST', 'localhost'),
                port=os.getenv('PGPORT', '5432'))


def connect():
    return psycopg.connect(**connection_parameters())


def sqlalchemy_url():
    p = connection_parameters()
    return URL.create('postgresql+psycopg', username=p['user'], password=p['password'],
                      host=p['host'], port=int(p['port']), database=p['dbname'])
