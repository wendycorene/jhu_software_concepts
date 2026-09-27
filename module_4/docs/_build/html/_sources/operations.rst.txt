Operational notes and troubleshooting
======================================

Busy state and uniqueness
-------------------------

Both POST endpoints reject a request with 409 when a pull is observed as busy.
The UI polls progress every 2.5 seconds and disables the two buttons during a
pull. Background errors appear in the progress message. GET requests can still
show committed results while a pull runs.

The worker uses both a local lock and a PostgreSQL advisory lock. The initial
HTTP busy check and worker start are separate operations: a competing process
can acquire the database lock after a request is accepted. In that case the
worker reports that another pull is running and does not scrape.

Duplicate IDs or URLs are skipped with ``ON CONFLICT DO NOTHING``. Existing
records are not overwritten. Missing optional source fields remain NULL.
Live collection stops at a known page or the configured page limit, so a large
historical gap may require a separate larger CLI collection.

Common problems
---------------

**No module named pytest or sphinx:** activate ``.venv`` and install
``requirements.txt``. Alternatively invoke ``.\.venv\Scripts\python.exe``
directly instead of ``python``.

**No password supplied or connection refused:** configure the database variables
in the same terminal used for tests, verify the database exists, and start
PostgreSQL. Credentials set in one terminal do not appear in another process.

**Windows temporary-folder permission error:** choose a fresh temporary folder::

   $pytestTemp = Join-Path $env:TEMP ("pytest-" + [guid]::NewGuid().ToString())
   python -m pytest -q -p no:cacheprovider --basetemp="$pytestTemp" | Tee-Object -FilePath coverage_summary.txt

**Cache warning:** ``-p no:cacheprovider`` disables the optional Pytest cache.

**Coverage below 100%:** resolve setup errors first; tests that cannot start
cannot exercise their code. Then inspect the report's Missing column.

**Documentation import error:** install the root Module 4 requirements and run
the build from ``module_4``. Sphinx imports modules for the API reference but
does not need to connect to PostgreSQL or start a scraper.
