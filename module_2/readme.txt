Name: Wendy Eloe
JHED ID: weloe1
Module: Module 2
Assignment: Web Scraping
Due Date: September 13, 2026

Approach

The project processes graduate admissions results from The GradCafe in three
stages: saving survey pages, extracting and cleaning applicant records, and
standardizing program and university names with a local language model.
Applicant records are represented as Python dictionaries and collected in lists.

1.  Collecting survey pages (scrape.py)

The scraper uses urllib3.PoolManager to request survey pages.  The collection
was organized into manually configured chunks, with a saved cursor URL used
to resume pagination.  The current loop covers page numbers 1521 through 1620.
_save_page() saves each HTTP response as scrapedHTML/output_<number>.html,
allowing the cleaning stage to reuse local pages without downloading them again.

_extract_next_url() parses the HTML with BeautifulSoup and Python's built-in
html.parser.  It finds the div with id="app" and reads its data-page attribute.
json.loads() converts this embedded JSON into a dictionary.  The next-page URL
comes from props -> results -> links -> next.  The loop uses that
URL for its next request and prints the page number and continuation URL.
The final scrape_data(url) call starts collection and passes the starting URL
into the function.  Each iteration calls both helper functions.

Responsible Scraping and robots.txt

I checked robots.txt by requesting https://thegradcafe.com/robots.txt with
urllib3.PoolManager and printing the response.  screenshot.jpg contains the
request and returned text.  The saved response shows an Allow: / rule for
User-agent: *, along with separate Disallow: / rules for named crawlers and
a Content-Signal specifying search=yes and ai-train=no.  This describes the
saved response; robots.txt should be checked again before a new collection.

The scraper uses urllib3 as instructed in office hours and requests public
survey pages sequentially, following the next-page links.  It does not include
code to bypass logins, CAPTCHAs, or access restrictions.  Saved HTML allows
cleaning to be repeated without requesting the same pages again.  The local
LLM performs inference to standardize names; this project does not train or
fine-tune a model on the collected records.

The current scraper does not automatically check robots.txt, add a delay
between requests, or handle rate-limit responses.  Manual chunks are not an
automatic throttling mechanism.  These are remaining limitations: a future
revision should check the applicable rules, add a reasonable request delay,
and stop or back off when access is denied or rate limits are returned.

2.  Extracting and cleaning records (clean.py)

scrape_data() uses pathlib.Path to iterate over the saved files in sorted
filename order.  Each file is read as UTF-8 and parsed with BeautifulSoup.
As in the scraper, the data-page attribute is decoded with json.loads().
Applicant records are extracted from props -> results -> data.

wanted_keys defines the source fields to retain, and renamed_keys maps those
fields to descriptive output names. _clean_record() builds a new dictionary
for each applicant.  The output includes Program, University, Comments, Date
Added to Grad Cafe, Applicant Status, Accepted Date, Rejected Date, Term,
Region, GRE Quantitative Score, GRE Verbal Score, Degree, GPA, and GRE Writing
Score.  The original numeric id is replaced with a URL constructed as
https://www.thegradcafe.com/result/<id>.

Fields read with record.get() become JSON null when missing.  Existing values,
including dates and scores, are otherwise preserved rather than converted or
inferred.  clean_data() uses a list comprehension to clean a page of records.
scrape_data() extends one combined list with each page's results.
save_data() writes that list to applicant_data.json as a JSON array, using
four-space indentation and ensure_ascii=False to preserve Unicode text.

3.  Standardizing names (llm_hosting/app.py)

The standardizer uses TinyLlama-1.1B-Chat in GGUF format, downloaded through
huggingface_hub and loaded through llama-cpp-python.  The model is initialized
when first needed and reused for later records.  CPU execution is the default.

Program and university values are passed as separate fields.  The prompt and
example input/output pairs ask the model to return a JSON object containing
standardized_program and standardized_university.  The prompt asks it to
preserve specializations and campuses, correct spelling, expand recognizable
acronyms, and avoid guessing a university from a program name.  Generation uses
temperature=0 and a maximum of 128 output tokens.

The model's output is checked before being accepted.  Canonical program and
university text files support capitalization corrections and name matching.
Explicit mappings handle known spellings and abbreviations.  Program changes
are restricted to small spelling corrections supported by the program
vocabulary.  University corrections use canonical matches, unique acronym
expansions, or character similarity with a margin over the next-best match.
Ambiguous or unsupported changes fall back to the source value.  An empty
university becomes "Unknown".  Invalid model JSON also falls back to the input
before rule-based normalization.

Each record retains its existing fields and receives llm-generated-program
and llm-generated-university.  The command-line interface can write a JSON
array or incremental JSON Lines output; append mode requires JSON Lines.
The Flask interface also provides a POST /standardize endpoint and a GET /
health endpoint.

Changes to the Provided LLM Files

I modified llm_hosting/app.py to read the cleaned Program and University keys
while retaining support for the original lowercase input keys.  I revised
the prompt and examples to process program and school separately and preserve
specializations, campuses, and unfamiliar names.

I added abbreviation mappings for WashU/WUSTL, RISD, UCLA, and CUNY, along with
validation for parenthetical acronyms and preservation of CUNY branch names.
I replaced broad program fuzzy matching and automatic title casing with
canonical capitalization and constrained spelling corrections.  University
matching now checks for unique acronym expansions or a sufficiently strong
similarity match separated from the next-best candidate.  Model responses
must contain the expected string fields, with fallback to source values
when parsing or validation fails.

I changed canonical-file paths to resolve relative to app.py so the program
can run from module_2.  I also changed CLI output to a UTF-8 JSON array by
default, retained JSON Lines support, restricted append mode to JSON Lines,
and delayed opening the JSON destination until normalization completes.
llm_hosting/README.md documents the revised output behavior.  The canonical
program and university text files are unchanged from their initial committed
versions.

The submitted applicant_data.json and llm_extend_applicant_data.json each
contain 32,400 unique applicant records, exceeding the 30,000 minimum.  The
LLM output preserves the original fields and adds the two standardized fields.

Environment

The project requires Python 3.10 or higher.  The local Windows environment
and .venv configuration use Python 3.14.7.  Dependencies are declared in the
root requirements.txt and llm_hosting/requirements.txt.  A fresh installation
of the LLM dependencies has not been verified as part of this documentation
update.

From module_2, create and activate a virtual environment in PowerShell:

python -m venv .venv
.\.venv\Scripts\Activate.ps1

The first LLM run needs internet access to download the GGUF model.  CPU
inference is the default.  Canonical lists are included under llm_hosting.

Running the project

Run these commands from the module_2 directory:

python -m pip install -r requirements.txt

To collect a chunk, first create scrapedHTML if it does not exist and set the
starting url and range in scrape.py.  The current range writes output_1521.html
through output_1620.html, replacing any existing files with those names.
For another chunk, use the last printed continuation URL and a new file-number
range.  Run:

python scrape.py

Once the HTML pages are saved (or to reuse existing pages), run:

python clean.py
python llm_hosting/app.py --file applicant_data.json --out llm_extend_applicant_data.json

The cleaning command requires the saved pages in scrapedHTML.  The first model
run requires downloading the model.  requirements.txt includes BeautifulSoup,
urllib3, and the dependencies listed in llm_hosting/requirements.txt.

Known Bugs

1.  The scraper assumes scrapedHTML already exists and does not check response
status or stop when there is no next-page URL.  Both parsing stages assume the
expected div and JSON structure are present.  Missing directories, error pages,
or unexpected page content can stop processing.  Fix: create the output
directory, check HTTP status and parsed data, and stop pagination when the
next URL is absent.  Log malformed pages so they can be inspected or retried.

2.  clean.py processes every directory entry and does not remove duplicate
records.  Non-HTML entries can cause parsing failures, and overlapping scrape
chunks can produce duplicate applicants.  Fix: select only HTML files and
deduplicate records by the source id or constructed result URL.

3.  LLM normalization is heuristic and may leave unfamiliar names or ambiguous
abbreviations unchanged.  It can also accept an incorrect spelling correction.
Fix: review questionable outputs against the original fields, expand verified
canonical entries and abbreviation mappings, and test those cases before
loosening the validation rules.

