# Module 3: Database queries and admissions analysis

Wendy Eloe

This project loads the included 32,400 Module 2 records into one PostgreSQL
`applicants` table, answers 11 questions in raw SQL and SQLAlchemy, and displays
all answers on a Flask webpage. All reused source and data are local copies;
there are no imports or runtime paths to module_1 or module_2.

## Setup (PowerShell, Python 3.10+ and PostgreSQL)

From this module_3 folder:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:PGHOST = 'localhost'
$env:PGPORT = '5432'
$env:PGUSER = 'postgres'
$env:PGDATABASE = 'gradcafe_module3'
$credential = Get-Credential -UserName postgres -Message 'Local PostgreSQL credentials'
$env:PGPASSWORD = $credential.GetNetworkCredential().Password
```

Create `gradcafe_module3` once in pgAdmin or with `createdb -U postgres gradcafe_module3`.
PostgreSQL's bin directory must be on PATH to use createdb. The local development
database has already been created and loaded. Passwords come from the process
environment or PostgreSQL's password file, never source code. No .env file is required.

```powershell
python load_data.py
python query_data.py
python orm_queries.py
python app.py
```

Open http://127.0.0.1:5000. Keep the terminal running; Ctrl+C stops the server.
The loader resolves its default JSON beside its script, and ignores duplicate
source IDs/URLs on later runs. An alternate JSON path can be passed as an argument.
The Flask model maps the same table; it does not create or copy another table.

## Data cleaning choices

The source stores nationality `0` and many score values `0`/`0.00` as placeholders.
These become SQL NULL. Blank, null, unknown, and N/A text is also treated as missing.
Only finite GPA values on the (0, 4] scale, GRE Quantitative/Verbal scores from
130 through 170, and positive GRE Writing values up to 6 are included. In particular,
GRE totals such as 328 are not treated as Quantitative scores. We do not guess a
component score or convert an unknown GPA scale. This policy may exclude genuine
zero GPA/writing scores and non-US GPA scales; it is an explicit analytical
assumption, not a claim that those source entries are false. Original JSON is
preserved so another policy can be evaluated. Missing optional values never
prevent otherwise usable entries from loading. Entries without a usable source
result ID are skipped and counted.

University and program are combined into the required original `program` field;
LLM fields are loaded separately from the enriched JSON. Queries ignore case and
surrounding spaces. JHU/MIT/CMU acronym matching uses word boundaries. Master and
PhD spelling variants are accepted. Computer Science matching includes programs
such as Electrical Engineering and Computer Science, but does not infer CS from
unrelated department names. Statistics describe submissions, not distinct people.
Each average independently excludes its missing metric; N/A means the denominator
or eligible metric set is empty. Counts are integers and averages/percentages use
two decimals throughout the console, reports, and page.

## Results from the included data

- Fall 2026 entries: 31914.
- International among classified entries: 45.70%.
- Average GPA: 3.77; GRE Quantitative: 165.79; GRE Verbal: 160.73; GRE Writing: 4.35.
- American Fall 2026 average GPA: 3.79.
- Fall 2025 acceptance percentage: 47.23%.
- Accepted Fall 2026 average GPA: 3.76.
- Johns Hopkins Computer Science master's entries: 8.
- Q8 original-field count: 30; Q9 LLM-field count: 30; difference: +0.
- Original question 10: Top five programs by average GRE Quantitative score,
  with at least 10 valid scores per program across all terms: finance: 168.39 (23 scores); economics: 167.91 (400 scores); mechanical engineering: 167.39 (23 scores); chemistry: 167.39 (18 scores); statistics: 165.65 (17 scores).
- Original question 11: Top five universities by reported rejection count across
  all terms: stanford university: 528 rejections; yale university: 451 rejections; princeton university: 413 rejections; university of california, berkeley: 395 rejections; massachusetts institute of technology: 373 rejections.

Both rankings use standardized LLM names, grouped without case or surrounding
whitespace. Missing names are excluded. Alphabetical order breaks ties at the
five-row cutoff. Rejection counts reflect reporting volume, not rejection rates.

`query_results.pdf` contains all questions, executable SQL, results, and explanations.
`limitations.pdf` contains the two-paragraph reflection. Regenerate with
`python generate_reports.py`; the narrative describes the included snapshot and
should be reviewed if newly pulled data change it.

## SQL and SQLAlchemy comparison: Question 4

Raw SQL:

```sql
SELECT AVG(gpa) FROM applicants
WHERE lower(trim(term)) = 'fall 2026'
  AND lower(trim(us_or_international)) = 'american';
```

Corresponding SQLAlchemy query:

```python
select(func.avg(Applicant.gpa)).where(
    func.lower(func.trim(Applicant.term)) == 'fall 2026',
    func.lower(func.trim(Applicant.us_or_international)) == 'american',
)
```

The SQL directly exposes the database operation and is easy to run independently
in a database client. SQLAlchemy expresses the same operation using mapped Python
attributes, which helps reuse query logic throughout the Flask application.
An ORM also handles connection/session integration and makes many queries easier
to adapt across database backends. Raw SQL offers more direct control over the
exact query and can be easier to inspect when debugging complex database-specific
operations; neither approach removes the need to understand filtering and NULLs.

## Pull Data and Update Analysis

Pull Data runs the copied Module 2 urllib3/BeautifulSoup scraper in a background
thread. It checks robots.txt, waits at least two seconds between requests, follows
recent-page links, and stops after a fully known page or ten pages. It validates
responses and stops on denied/rate-limited requests rather than bypassing access
controls. Data is cleaned with the copied `clean.py` and inserted in one transaction;
existing records are not overwritten. A local thread lock and PostgreSQL advisory
lock prevent simultaneous scraping even across multiple Flask processes. Status
messages describe running, completed, and failed pulls. Update Analysis only
re-queries the committed database through SQLAlchemy; it never starts a scrape.
Refresh while a pull is active to see current committed results and a running notice.

The ten-page cap means a large historical gap may require a larger CLI collection:
`python scrape.py --max-pages 100`. The first fully known page is a practical
incremental stopping rule, not a guarantee that every historical late entry was
collected. The site can change layout or availability. A real one-page scrape
returned 20 cleaned records during verification; those records were not added to
the submitted snapshot. New pulls leave LLM fields NULL rather than labeling raw
text as model output. The optional copied `llm_hosting` source and canonical files
are included for a separate local LLM workflow; its dependencies are listed in
`llm_hosting/requirements.txt`. Its model download is not required to run this project.
Imports of the copied scraper/cleaner no longer start network or disk work.

## Verification and submission

```powershell
python -m unittest -v test_project
python generate_reports.py
```

Integration tests create temporary tables that shadow applicants and roll back;
they do not delete or change the saved dataset. Checks cover SQL/ORM agreement,
case/degree/university filters, independent missing metrics, zero denominators,
repeated insertion, background pull completion/failure, and refreshing during a pull.
A repeat load inserted 0 rows and identified all 32,400 records as duplicates.

`screenshots/raw_sql.png` and `screenshots/orm.png` show actual captured command
stdout rendered in a browser for legibility; their matching .txt files retain
exact output. `screenshots/flask.png` is a browser screenshot of the running Flask
page. To regenerate: install optional `playwright`, ensure Chrome is installed,
and run `python capture_screenshots.py` with the server running.

`github.txt` contains this repository's configured SSH remote. Repository privacy
has not been independently verified. Review the work and reflection before
submitting, then commit/push the final files to your private repository and upload
`module_3.zip` to Canvas. The archive contains a module_3 folder and excludes
credentials, environments, caches, and the archive itself. No remote commit,
push, or Canvas submission is performed by the application.


### Live webpage feedback

The page checks `/pull-status` every 2.5 seconds without starting a scrape.
A spinner and disabled Pull Data button indicate retrieval is running; completion
and error messages appear automatically. Connection failures show a retry message.
Update Analysis shows Refreshing while loading, then displays the successful
analysis refresh time in your browser timezone. Restart Flask after code changes.
Status messages are held in the serving process; this local development app uses
one process. The database lock still prevents simultaneous scrapes across processes.
