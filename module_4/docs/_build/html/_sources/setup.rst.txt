Overview and setup
==================

Requirements
------------

Use Python 3.14 (the version used in CI) and PostgreSQL. Run these PowerShell
commands from the repository's ``module_4`` directory::

   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install -r requirements.txt

The requirements include the application, Pytest, coverage, and Sphinx.
The optional local LLM and browser screenshot tools are not required for
running the web application or its tests.

Database configuration
----------------------

Create a database once using pgAdmin or ``createdb -U postgres gradcafe_module3``.
Configure the connection in the terminal that will run the application::

   $env:PGHOST = 'localhost'
   $env:PGPORT = '5432'
   $env:PGUSER = 'postgres'
   $env:PGDATABASE = 'gradcafe_module3'
   $dbCredential = Get-Credential -UserName postgres -Message 'PostgreSQL password'
   $env:PGPASSWORD = $dbCredential.GetNetworkCredential().Password

``config.py`` currently reads these five ``PG*`` environment variables.
Defaults are localhost, port 5432, user postgres, and database
gradcafe_module3. There is no default password. ``PORT`` controls the Flask
port and defaults to 5000.

.. note::

   The assignment also requires ``DATABASE_URL`` support. That is still a
   pending application change; setting that variable alone currently has no
   effect. The instructions here describe the working implementation.

Load and run
------------

Load the included snapshot, then start Flask::

   python src/load_data.py
   python src/app.py

Open http://127.0.0.1:5000/analysis. Stop the server with Ctrl+C.
The loader defaults to the JSON file beside its script. An alternative file
can be supplied as an argument. Repeated loads skip existing IDs or URLs.

``Pull Data`` requests recent live submissions; ``Update Analysis`` refreshes
the displayed database analysis. Both buttons are disabled while a pull runs.
Tests use fake scraper data and do not need live scraping.

To print analyses in the terminal::

   python src/query_data.py
   python src/orm_queries.py

See :doc:`testing` for test commands and :doc:`publishing` for documentation builds.
