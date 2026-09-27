API reference
=============

Flask application and routes
----------------------------

.. automodule:: app
   :members: create_app, PullManager
   :undoc-members:

The factory accepts an optional manager exposing ``running()``, ``start()``,
``state``, and ``message``. Route functions are nested inside the factory.

.. list-table:: HTTP routes
   :header-rows: 1
   :widths: 25 75

   * - Method and path
     - Response and behavior
   * - GET ``/`` or ``/analysis``
     - 200 HTML with eleven answers. Query failures produce an error notice.
   * - POST ``/pull-data``
     - 202 JSON ``{"ok": true}`` when accepted; 409 ``{"busy": true}`` when busy.
   * - POST ``/update-analysis``
     - 200 refreshed HTML when idle; 409 ``{"busy": true}`` without querying when busy.
   * - GET ``/pull-status``
     - 200 JSON with ``running``, ``state``, and ``message``; 503 when the status check fails.

A 202 response acknowledges a job, not successful insertion. Check the progress
endpoint for a later worker failure or completion.

Scraper
-------

.. automodule:: scrape
   :members: scrape_data

Cleaner
-------

``clean_data`` accepts raw dictionaries and returns renamed fields.
``scrape_data`` in this module reads saved HTML, unlike the live scraper.
``save_data`` writes the cleaned JSON beside the cleaner script.

.. automodule:: clean
   :members: clean_data, scrape_data, save_data
   :undoc-members:

Loader
------

``normalize`` returns a tuple in ``COLUMNS`` order and raises ``ValueError``
for an unusable result URL. ``load_records`` returns integer counts named
``inserted``, ``duplicates``, and ``skipped``. Malformed input records are
counted as skipped; database errors propagate to the transaction owner.

.. automodule:: load_data
   :members: normalize, load_records, text, number
   :undoc-members:

Queries
-------

Supply a psycopg connection to the raw SQL function or a SQLAlchemy session
to the ORM function to control connection lifetime. Omitting it opens a
configured connection or session for the call.

.. automodule:: query_data
   :members: run_queries
   :undoc-members:

.. automodule:: orm_queries
   :members: statements, run_queries
   :undoc-members:

Formatting and configuration
----------------------------

``format_result`` converts query tuples into display strings. Percentages
have two decimals; missing values display ``N/A``.

.. automodule:: presentation
   :members: decimal, format_result, print_results
   :undoc-members:

.. automodule:: config
   :members: connection_parameters, connect, sqlalchemy_url
   :undoc-members:
