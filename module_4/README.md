# Module 4: Testing and documentation

Wendy Eloe

Grad Cafe admissions analytics with Flask, PostgreSQL, Pytest, and Sphinx.
Repository SSH URL: `git@github.com:wendycorene/jhu_software_concepts.git`.

## Setup and application

Run from `module_4` using Python 3.14 and a running PostgreSQL server:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:PGHOST = 'localhost'
$env:PGPORT = '5432'
$env:PGUSER = 'postgres'
$env:PGDATABASE = 'gradcafe_module3'
$dbCredential = Get-Credential -UserName postgres -Message 'PostgreSQL password'
$env:PGPASSWORD = $dbCredential.GetNetworkCredential().Password
```

Create `gradcafe_module3` once in pgAdmin or with `createdb -U postgres gradcafe_module3`.
Then run:

```powershell
python src/load_data.py
python src/app.py
```

Open http://127.0.0.1:5000/analysis. The loader skips duplicate IDs or URLs.
Alternatively, set `DATABASE_URL` to a PostgreSQL connection URL. It takes
precedence over the `PG*` settings for both the loader and ORM queries. Use
`postgresql://USER:PASSWORD@HOST:5432/DATABASE`, URL-encoding special characters
in credentials. Set it before starting the app; do not commit credentials.

## Tests and coverage

```powershell
python -m pytest -q -p no:cacheprovider | Tee-Object -FilePath coverage_summary.txt
```

Tests enforce 100% line coverage of `src`, including the optional standardizer.
Database tests use isolated temporary tables. All tests are marked `web`,
`buttons`, `analysis`, `db`, or `integration`; none requires live scraping.
For the Windows temporary-folder permission workaround, see
[operational notes](docs/operations.rst).

The repository-root `.github/workflows/tests.yml` starts PostgreSQL and runs
the suite. `actions_success.png` records a successful hosted run.

## Documentation

```powershell
python -m sphinx -b html -W --keep-going docs docs/_build/html
```

Open [the generated documentation](docs/_build/html/index.html).
It covers setup, architecture, API reference, testing, and operational notes.
See [publishing instructions](docs/publishing.rst) for Read the Docs.

**Published documentation:** [Grad Cafe Analytics on Read the Docs](https://wendy-eloe-grad-cafe-analytics.readthedocs.io/en/latest/).
