"""Load the local Module 2 JSON into PostgreSQL; repeat loads are safe."""
import argparse
from datetime import date
import json
import math
from pathlib import Path
import re
from config import connect

# Keep this column order consistent with the tuple returned by normalize().
COLUMNS = ('p_id', 'program', 'comments', 'date_added', 'url', 'status', 'term',
           'us_or_international', 'gpa', 'gre', 'gre_v', 'gre_aw', 'degree',
           'llm_generated_program', 'llm_generated_university')
# Create the table only if it does not already exist. The primary key and
# unique URL prevent the same source entry from being inserted twice.
SCHEMA = '''CREATE TABLE IF NOT EXISTS applicants (
    p_id INTEGER PRIMARY KEY, program TEXT, comments TEXT, date_added DATE,
    url TEXT UNIQUE, status TEXT, term TEXT, us_or_international TEXT,
    gpa DOUBLE PRECISION, gre DOUBLE PRECISION, gre_v DOUBLE PRECISION,
    gre_aw DOUBLE PRECISION, degree TEXT,
    llm_generated_program TEXT, llm_generated_university TEXT
)'''
# Each %s is a placeholder: psycopg supplies the values separately from SQL.
# ON CONFLICT DO NOTHING skips entries with an existing ID or URL.
INSERT = ('INSERT INTO applicants (' + ', '.join(COLUMNS) + ') VALUES ('
          + ', '.join(['%s'] * len(COLUMNS)) + ') ON CONFLICT DO NOTHING')


def text(value):
    # Trim whitespace and convert missing-value markers to Python None.
    # psycopg stores None as SQL NULL (a missing database value).
    if value is None:
        return None
    value = str(value).strip()
    return None if value.lower() in ('', 'none', 'null', 'n/a', 'unknown', '0') else value


def number(value, minimum, maximum):
    # Convert numeric strings to floats; reject invalid values, infinity,
    # NaN (not a number), and scores outside the chosen metric's range.
    try:
        result = float(value)
        return result if math.isfinite(result) and minimum <= result <= maximum else None
    except (TypeError, ValueError):
        return None


def normalize(record):
    # Extract the numeric source ID from a URL ending in /result/12345.
    # record.get() returns None when an optional JSON field is absent.
    url = text(record.get('URL'))
    match = re.search(r'/result/(\d+)/?$', url or '')
    if not match:
        raise ValueError('Record has no usable Grad Cafe result ID')
    # Use the YYYY-MM-DD portion of the date, ignoring any time suffix.
    # An invalid or missing date becomes NULL rather than rejecting the entry.
    added = text(record.get('Date Added to Grad Cafe'))
    try:
        added = date.fromisoformat(added[:10]) if added else None
    except ValueError:
        added = None
    # The assignment stores university and department together in program.
    # filter(None, ...) leaves out either component when it is missing.
    program = ', '.join(filter(None, (text(record.get('University')), text(record.get('Program')))))
    # Return values in COLUMNS order. Keep LLM fields separate from originals.
    # These score ranges assume a 4-point GPA and current GRE component scales.
    # Zero placeholders and incompatible scales are treated as missing; this
    # policy can also exclude genuine zero scores (see README.md).
    return (int(match[1]), program or None, text(record.get('Comments')), added, url,
            text(record.get('Applicant Status')), text(record.get('Term')),
            text(record.get('Region')), number(record.get('GPA'), 0.01, 4.0),
            number(record.get('GRE Quantitative Score'), 130, 170), number(record.get('GRE Verbal Score'), 130, 170),
            number(record.get('GRE Writing Score'), 0.5, 6.0), text(record.get('Degree')),
            text(record.get('llm-generated-program')), text(record.get('llm-generated-university')))


def load_records(records, connection=None):
    # Prepare usable entries and count malformed records without stopping
    # the entire batch. Missing optional fields are handled by normalize().
    rows, skipped = [], 0
    for record in records:
        try:
            rows.append(normalize(record))
        except (ValueError, TypeError, AttributeError):
            skipped += 1
    # A cursor sends SQL to PostgreSQL. executemany runs the same INSERT
    # for each prepared row; rowcount counts the rows actually inserted.
    def insert(conn):
        with conn.cursor() as cursor:
            cursor.execute(SCHEMA)
            cursor.executemany(INSERT, rows)
            return {'inserted': cursor.rowcount, 'duplicates': len(rows) - cursor.rowcount,
                    'skipped': skipped}
    # A caller-supplied connection lets the caller control commit/rollback.
    if connection is not None:
        return insert(connection)
    # Otherwise, open our own connection using config.py settings.
    # This context commits on success, rolls back on error, and closes it.
    with connect() as conn:
        return insert(conn)


# Run this section only when launched directly, not when imported by Flask.
if __name__ == '__main__':
    # argparse reads command-line arguments and supplies a --help option.
    parser = argparse.ArgumentParser(description=__doc__)
    # Example: python load_data.py applicant_data.json
    # nargs='?' makes the filename optional; type=Path creates a Path object.
    # Without a filename, use the enriched JSON beside this script.
    parser.add_argument('file', nargs='?', type=Path,
                        default=Path(__file__).parent / 'llm_extend_applicant_data.json')
    # Store the selected filename in args.file.
    args = parser.parse_args()
    # Read UTF-8 JSON (allowing a byte-order mark), convert it to Python
    # records, load them, and print inserted/duplicate/skipped counts.
    print(load_records(json.loads(args.file.read_text(encoding='utf-8-sig'))))

