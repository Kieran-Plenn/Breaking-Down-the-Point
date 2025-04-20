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
import time
from urllib.parse import urlparse, parse_qs

def init_driver(chromedriver_path: str):
    service = Service(chromedriver_path)
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(service=service, options=options)

def extract_table(driver, table_id: str):
    WebDriverWait(driver, 4).until(
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
        span = cell.find("span")
        if span and span.has_attr("title"):
            headers.append(span.get_text(strip=True))         # Visible label
            descriptions.append(span["title"].strip())        # Tooltip/description
        else:
            headers.append(cell.get_text(strip=True))         # Fallback for no span
            descriptions.append("")                           # Blank if no title

    return headers, descriptions


def parse_table_rows(table):
    rows = []
    for tr in table.find("tbody").find_all("tr"):
        cells = tr.find_all(["td", "th"])
        row = [(cell.get_text(strip=True)) for cell in cells]
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

        if table_id == "singles-results":
            headers.append("WinnerPeakRank")  # Add new column

            peak_rank_cache = {}

            for row in rows:
                try:
                    winner_cell = row[0]  # Adjust index if winner isn't at 0
                    winner_soup = BeautifulSoup(winner_cell, "html.parser")
                    winner_link = winner_soup.find('a', href=True)

                    if winner_link and "player" in winner_link['href']:
                        winner_url = "https://www.tennisabstract.com" + winner_link['href']
                        winner_name = winner_link.text.strip()

                        if winner_url in peak_rank_cache:
                            peak_rank = peak_rank_cache[winner_url]
                        else:
                            driver.get(winner_url)
                            time.sleep(4)  # Consider tuning this for speed/throttling
                            profile_soup = BeautifulSoup(driver.page_source, "html.parser")
                            script_tag = profile_soup.find('script', string=re.compile("var fullname ="))

                            if script_tag:
                                match = re.search(r"var peakrank = (\d+)", script_tag.string)
                                peak_rank = match.group(1) if match else "N/A"
                            else:
                                peak_rank = "N/A"

                            peak_rank_cache[winner_url] = peak_rank
                    else:
                        peak_rank = "N/A"

                    row.append(peak_rank)

                except Exception as e:
                    print(f"❌ Error extracting winner peak rank for row: {e}")
                    row.append("N/A")

        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        filename = os.path.join(output_folder, f"{table_id}.csv")
        write_to_csv(filename, headers, descriptions, rows)

    except Exception as e:
        print(f"❌ Error processing table '{table_id}': {e}")

def main():
    chromedriver_path = "C:\\chromedriver-win64\\chromedriver.exe"
    base_url = "https://www.tennisabstract.com/cgi-bin/tourney.cgi?t="
    base_tourney_names = ["US_Open"]

    start_year = 2022
    end_year = 2022

    table_ids = ["singles-results", "stat-summaries"]  # Add more table IDs here if needed

    driver = init_driver(chromedriver_path)

    for base_tourney_name in base_tourney_names: 
        for year in range(start_year, end_year + 1):
            url = f"{base_url}{year}{base_tourney_name}"
            print(f"\n🌐 Scraping {year} {base_tourney_name.replace('_', ' ')}...")
            driver.get(url)

            output_folder = os.path.join("tennis_data", base_tourney_name, str(year))

            for table_id in table_ids:
                scrape_table_to_csv(driver, table_id, output_folder)

            time.sleep(4)

    driver.quit()


if __name__ == "__main__":
    main()
