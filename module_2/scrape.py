import urllib3
from bs4 import BeautifulSoup
import json

http = urllib3.PoolManager()

#I ran this in chunks and put the url from the last run here
url = "https://www.thegradcafe.com/survey?cursor=eyJjcmVhdGVkX2F0IjoiMjAyNi0wMi0xMSAyMTo1ODowNyIsImFkbWl0aWQiOjk5OTk0NywiX3BvaW50c1RvTmV4dEl0ZW1zIjp0cnVlfQ"

for count in range (1021, 1621):
    response = http.request("GET", url)

    with open(f"scrapedHTML/output_{count}.html", "wb") as f:
        f.write(response.data)

    with open(f"scrapedHTML/output_{count}.html", "r", encoding="utf-8") as f:
        html = f.read()

    soup = BeautifulSoup(html, "html.parser")

    app = soup.find("div", id="app")
    data_page = app.get("data-page")

    page_data = json.loads(data_page)

    url = page_data["props"]["results"]["links"]["next"]

    print(count)
    print(url)