from bs4 import BeautifulSoup
import json

with open(f"scrapedHTML/output_117.html", "r", encoding="utf-8") as f:
    html = f.read()

soup = BeautifulSoup(html, "html.parser")

app = soup.find("div", id="app")
data_page = app.get("data-page")

page_data = json.loads(data_page)

records = list(page_data["props"]["results"]["data"])

wanted_keys = ["program", "school", "notes", "created_at", "id", "decision", "acceptedDate", "rejectedDate", "season", "status", "greq", "grev", "level", "ugpa", "grew"]

renamed_keys = {
    "program": "Program",
    "school": "University",
    "notes": "Comments",
    "created_at": "Date Added to Grad Cafe",
    "id": "URL",
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

filtered_records = [
    {
        renamed_keys.get(key, key): record.get(key)
        for key in wanted_keys
    }
    for record in records
]

with open ("applicant_data.json", "w", encoding="utf-8") as f:
    f.write(json.dumps(filtered_records, indent=4, ensure_ascii=False))