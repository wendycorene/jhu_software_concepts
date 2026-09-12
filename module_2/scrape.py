import urllib3
from bs4 import BeautifulSoup
import json
from pathlib import Path

http = urllib3.PoolManager()

#I ran this in chunks and put the url from the last run here manually.
url = "https://www.thegradcafe.com/survey?cursor=eyJjcmVhdGVkX2F0IjoiMjAyNi0wMi0xMSAyMTo1ODowNyIsImFkbWl0aWQiOjk5OTk0NywiX3BvaW50c1RvTmV4dEl0ZW1zIjp0cnVlfQ"

def _save_page(count, response_data):
    # Save the page HTML to a numbered file
    with open(f"scrapedHTML/output_{count}.html", "wb") as f:
        f.write(response_data)

def _extract_next_url(html):
    # Pull the next page URL from the JSON embedded in the page
    soup = BeautifulSoup(html, "html.parser")
    app = soup.find("div", id="app")
    data_page = app.get("data-page")
    page_data = json.loads(data_page)
    return page_data["props"]["results"]["links"]["next"]

def scrape_data(url):
    # Loop through the saved chunk range and continue following pagination
    for count in range(1521, 1621):
        response = http.request("GET", url)

        _save_page(count, response.data)

        with open(f"scrapedHTML/output_{count}.html", "r", encoding="utf-8") as f:
            html = f.read()

        url = _extract_next_url(html)

        print(count)
        print(url)

scrape_data(url)