# Breaking Down the Point
# Author: Kieran Plenn

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import csv
import os
import re
from urllib.parse import urlparse, parse_qs

def init_driver(chromedriver_path: str):
    service = Service(chromedriver_path)
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(service=service, options=options)

def clean_text(text):
    return re.sub(r"\s+", " ", text.replace('\xa0', ' ')).strip()

def extract_table(driver, table_id: str):
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, table_id))
    )
    print(f"✅ Table with ID '{table_id}' found!")
    soup = BeautifulSoup(driver.page_source, "html.parser")
    return soup.find("table", id=table_id)

def parse_table_headers_and_titles(table):
    header_cells = table.find("thead").find_all("th")
    headers = []
    descriptions = []

    for cell in header_cells:
        text = clean_text(cell.get_text(strip=True))
        title = clean_text(cell.get("title", ""))
        headers.append(text)
        descriptions.append(title if title else "")  # Blank if no title

    return headers, descriptions

def parse_table_rows(table):
    rows = []
    for tr in table.find("tbody").find_all("tr"):
        cells = tr.find_all(["td", "th"])
        row = [clean_text(cell.get_text(strip=True)) for cell in cells]
        if row:
            rows.append(row)
    return rows

def write_to_csv(filename, headers, descriptions, rows):
    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(headers)       # First row: column names
        writer.writerow(descriptions)  # Second row: tooltips (titles)
        writer.writerows(rows)         # Rest: data rows
    print(f"📁 CSV written to '{filename}'")

def get_tournament_name_from_url(url: str) -> str:
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    tourney_param = query.get("t", ["unknown_tournament"])[0]
    return tourney_param

def scrape_table_to_csv(driver, table_id, output_folder="output"):
    try:
        table = extract_table(driver, table_id)
        if not table:
            print(f"⚠️ Table '{table_id}' not found.")
            return

        headers, descriptions = parse_table_headers_and_titles(table)
        rows = parse_table_rows(table)

        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        filename = os.path.join(output_folder, f"{table_id}_with_descriptions.csv")
        write_to_csv(filename, headers, descriptions, rows)

    except Exception as e:
        print(f"❌ Error processing table '{table_id}': {e}")

def main():
    chromedriver_path = "C:\\chromedriver-win64\\chromedriver.exe"
    url = "https://www.tennisabstract.com/cgi-bin/tourney.cgi?t=2023US_Open"
    table_ids = ["stat-summaries"]

    driver = init_driver(chromedriver_path)
    driver.get(url)

    tournament_name = get_tournament_name_from_url(url)
    output_folder = os.path.join("output", tournament_name)

    for table_id in table_ids:
        scrape_table_to_csv(driver, table_id, output_folder=output_folder)

    driver.quit()

if __name__ == "__main__":
    main()
