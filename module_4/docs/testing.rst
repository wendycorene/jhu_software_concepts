Testing guide
=============

Running tests
-------------

From ``module_4``, activate the environment and configure PostgreSQL as in
:doc:`setup`. Then run::

   python -m pytest -q -p no:cacheprovider

``pytest.ini`` measures all source code under ``src`` and fails below 100%
line coverage. ``.coveragerc`` includes directories without ``__init__.py``,
including the copied LLM service. Full line coverage does not imply that every
possible input or concurrent execution has been tested.

All tests have at least one registered marker:

* ``web``: routes and page structure.
* ``buttons``: pull/update behavior, progress, and busy handling.
* ``analysis``: formatting and standardization.
* ``db``: database writes, query results, and data helpers.
* ``integration``: complete workflows and supporting utilities.

Run the complete marked suite and save the assignment evidence in PowerShell::

   python -m pytest -m "web or buttons or analysis or db or integration" -q -p no:cacheprovider | Tee-Object -FilePath coverage_summary.txt

For focused development, select a marker and disable the full-suite coverage
gate for that invocation only::

   python -m pytest -m web --no-cov -p no:cacheprovider

Fixtures and isolation
----------------------

``tests/conftest.py`` provides ``applicant_records`` (complete synthetic data)
and ``db_connection`` (a PostgreSQL connection with a temporary applicants
table). The search path is limited to ``pg_temp`` and the connection is rolled
back and closed after each test. No saved public table is cleared.

Integration tests share an isolated connection between the real loader and
real ORM sessions, using savepoints. They replace the scraper with deterministic
records and run the background worker immediately, without sleeps.

Other tests patch database access for page rendering, HTTP requests for scraper
tests, and model calls for the optional standardizer. File-producing tests use
Pytest temporary directories. Screenshot orchestration uses a fake browser.
These substitutes exercise application behavior without live internet access,
model downloads, or manual browser clicks.

HTML selectors
--------------

Tests use Flask's test client and BeautifulSoup. Stable button selectors are
``[data-testid="pull-data-btn"]`` and ``[data-testid="update-analysis-btn"]``.
Answer cards are ``.grid article`` and ``.answer``; error notices have
``role="alert"``. Percentage assertions require exactly two digits after the
decimal point.

Continuous integration
----------------------

The repository-root ``.github/workflows/tests.yml`` runs on pushes, pull
requests, and manual dispatch. It installs requirements on Ubuntu with Python
3.14, starts PostgreSQL 16, waits for its health check, and runs all marked
tests. The database credentials are disposable CI-only values.

The workflow logs the coverage summary. The assignment evidence files are
``module_4/coverage_summary.txt`` and ``module_4/actions_success.png``.
