Architecture
============

Web layer
---------

``app.py`` exposes ``create_app(manager=None)``. The factory registers page,
button, and progress routes. ``templates/analysis.html`` renders the answers;
``static/status.js`` polls progress and updates button availability.
``presentation.py`` holds question text and common answer formatting.

Data collection and loading
---------------------------

``scrape.py`` checks robots.txt, fetches bounded recent pages, and passes raw
records to ``clean.clean_data``. The cleaner renames source fields and creates
result URLs. ``load_data.normalize`` converts dates and numeric values and
extracts the result ID. ``load_records`` inserts normalized rows in PostgreSQL.

The production pull manager runs collection in a background thread. A thread
lock prevents overlapping local workers; a PostgreSQL advisory lock coordinates
pulls across processes. The loader owns a separate transaction in production.
When passed a connection, its caller owns commit and rollback.

Database and analysis
---------------------

``models.py`` maps the existing ``applicants`` table with SQLAlchemy.
``orm_queries.py`` computes the web page's eleven analyses; ``query_data.py``
provides their raw SQL counterparts. Both return dictionaries keyed by question
numbers 1 through 11, with lists of result tuples as values.

The table preserves the Module 3 fields: ID, program, comments, date, URL,
status, term, nationality, GPA, GRE scores, degree, and standardized program
and university names. ID is the primary key; URL is unique. Other columns
can be NULL when the source omits information.

Request flow
------------

1. POST ``/pull-data`` starts a background pull and acknowledges acceptance.
2. The worker scrapes, cleans, and loads records; progress is exposed separately.
3. After completion, POST ``/update-analysis`` queries and renders results.
4. GET ``/analysis`` also queries and renders current committed data.

The optional ``llm_hosting`` service standardizes names separately. Normal
web pulls do not run an LLM. Its tests substitute model inference and downloads.
