from pathlib import Path
from bs4 import BeautifulSoup
import json

# Only keep fields to save in the final JSON
wanted_keys = ["program", "school", "notes", "created_at", "id", "decision", "acceptedDate", "rejectedDate", "season", "status", "greq", "grev", "level", "ugpa", "grew"]

# Rename raw keys
renamed_keys = {
    "program": "Program",
    "school": "University",
    "notes": "Comments",
    "created_at": "Date Added to Grad Cafe",
    "decision": "Applicant Status",
    "acceptedDate": "Accepted Date",
    "rejectedDate": "Rejected Date",
    "season": "Term",
    "status": "Region",
    "greq": "GRE Quantitative Score",
    "grev": "GRE Verbal Score",
    "level": "Degree",
    "ugpa": "GPA",
    "grew": "GRE Writing Score"
}

def _clean_record(record):
    # Build a cleaned dictionary for a single record
    # Skip the raw ID to replace it with a full URL
    record_data = {
        renamed_keys.get(key, key): record.get(key)
        for key in wanted_keys
        if key != "id"
    }

    # Convert the raw GradCafe ID into a full result URL for each applicant
    record_data["URL"] = "https://www.thegradcafe.com/result/" + str(record["id"])
    return record_data

def clean_data(data_rows):
    # Clean every row in one page before appending to the bigger list
    return [_clean_record(record) for record in data_rows]

def scrape_data():
    # Loop over every saved HTML file in scrapedHTML and process the data
    records = []
    for file in sorted(Path("scrapedHTML").iterdir()):
        # Read each saved page and parse the HTML
        with open(file, "r", encoding="utf-8") as f:
            html = f.read()

        soup = BeautifulSoup(html, "html.parser")
        app = soup.find("div", id="app")

        # The actual applicant data is stored in the data-page attribute
        data_page = app.get("data-page")
        page_data = json.loads(data_page)
        data_rows = page_data["props"]["results"]["data"]

        # Save only the cleaned records from this page
        records.extend(clean_data(data_rows))
    return records

def save_data(records):
    # Write all cleaned records to the output JSON file
    with open("applicant_data.json", "w", encoding="utf-8") as f:
        f.write(json.dumps(records, indent=4, ensure_ascii=False))

records = scrape_data()
save_data(records)