"""Shared PostgreSQL fixtures with connection-local, temporary tables."""

import psycopg
import pytest

from config import connect
from load_data import SCHEMA


@pytest.fixture
def db_connection():
    """Keep every test isolated from saved applicants and other tests."""
    try:
        connection = connect()
    except psycopg.OperationalError:
        pytest.fail(
            'Cannot connect to PostgreSQL. Set PGHOST, PGPORT, PGUSER, '
            'PGDATABASE and PGPASSWORD in this terminal before running DB tests.',
            pytrace=False,
        )
    try:
        # Only the temporary schema is searched: a missing temporary table
        # must never fall back to the saved public.applicants table.
        connection.execute('SET search_path TO pg_temp')
        connection.execute(SCHEMA.replace(
            'CREATE TABLE IF NOT EXISTS', 'CREATE TEMPORARY TABLE'))
        yield connection
    finally:
        connection.rollback()
        connection.close()


@pytest.fixture
def applicant_records():
    """Complete synthetic records in the scraper's input format."""
    common = {
        'University': 'Example University',
        'Program': 'Computer Science',
        'Comments': 'Synthetic test record',
        'Date Added to Grad Cafe': '2026-09-20',
        'Applicant Status': 'Accepted',
        'Term': 'Fall 2026',
        'Region': 'American',
        'GPA': '3.8',
        'GRE Quantitative Score': '165',
        'GRE Verbal Score': '160',
        'GRE Writing Score': '4.5',
        'Degree': 'Masters',
        'llm-generated-program': 'Computer Science',
        'llm-generated-university': 'Example University',
    }
    return [
        dict(common, URL='https://www.thegradcafe.com/result/900001'),
        dict(common, URL='https://www.thegradcafe.com/result/900002',
             Region='International'),
    ]
