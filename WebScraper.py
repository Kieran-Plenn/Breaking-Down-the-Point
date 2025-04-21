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
import json
from urllib.parse import urlparse, parse_qs


# Initialize the Chrome driver
def init_driver(chromedriver_path: str):
    service = Service(chromedriver_path)
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(service=service, options=options)


# Extract table from page
def extract_table(driver, table_id: str):
    WebDriverWait(driver, 4).until(
        EC.presence_of_element_located((By.ID, table_id))
    )
    print(f"✅ Table with ID '{table_id}' found!")
    soup = BeautifulSoup(driver.page_source, "html.parser")
    return soup.find("table", id=table_id)


# Parse table headers and titles
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


# Parse table rows
def parse_table_rows(table):
    rows = []
    for tr in table.find("tbody").find_all("tr"):
        cells = tr.find_all(["td", "th"])
        row = [(cell.get_text(strip=True)) for cell in cells]
        if row:
            rows.append(row)
    return rows


# Write the data to a CSV file
def write_to_csv(filename, headers, descriptions, rows):
    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(headers)       # First row: column names
        writer.writerow(descriptions)  # Second row: tooltips (titles)
        writer.writerows(rows)         # Rest: data rows
    print(f"📁 CSV written to '{filename}'")


# Get tournament name from URL
def get_tournament_name_from_url(url: str) -> str:
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    tourney_param = query.get("t", ["unknown_tournament"])[0]
    return tourney_param


# Cache for storing peak ranks across all tournaments
def load_rank_cache(filename='rank_cache.json'):
    if os.path.exists(filename):
        with open(filename, 'r') as file:
            return json.load(file)
    return {}


def save_rank_cache(rank_cache, filename='rank_cache.json'):
    with open(filename, 'w') as file:
        json.dump(rank_cache, file)
    print("🗄️ Rank cache saved!")


# Scrape a table from the tournament and save it to a CSV
def scrape_table_to_csv(driver, tournament_url, output_dir, table_id, rank_cache):
    driver.get(tournament_url)
    soup = BeautifulSoup(driver.page_source, "html.parser")

    table = soup.find("table", id=table_id)
    if not table:
        print(f"❌ Table with ID '{table_id}' not found at {tournament_url}")
        return

    print(f"✅ Table with ID '{table_id}' found!")

    headers, descriptions = parse_table_headers_and_titles(table)

    # Special handling for singles-results table
    if table_id == "singles-results":
        rows = []
        for row in table.find_all("tr"):
            cells = row.find_all("td")
            if not cells:
                continue

            winner_peak_rank = "N/A"

            # Try to get winner's profile link from the third <td>
            if len(cells) > 2:
                winner_td = cells[2]
                winner_link_tag = winner_td.find("a", href=lambda x: x and "player.cgi?p=" in x)
                if winner_link_tag:
                    player_url = winner_link_tag["href"]
                    full_url = player_url if player_url.startswith("http") else "https://www.tennisabstract.com" + player_url

                    try:
                        # Check if the player's peak rank is in cache
                        player_name = winner_link_tag.get_text(strip=True)
                        if player_name in rank_cache:
                            winner_peak_rank = rank_cache[player_name]
                            print(f"🚀 Using cached peak rank for {player_name}")
                        else:
                            driver.get(full_url)
                            time.sleep(4)
                            player_soup = BeautifulSoup(driver.page_source, "html.parser")
                            script_tag = player_soup.find("script", string=re.compile("var fullname ="))
                            if script_tag:
                                match = re.search(r"var peakrank = (\d+)", script_tag.string)
                                winner_peak_rank = match.group(1) if match else "N/A"

                            # Save the player's peak rank in the cache
                            rank_cache[player_name] = winner_peak_rank

                    except Exception as e:
                        print(f"[ERROR] Failed to get peak rank for {full_url}: {e}")

            # Extract plain text for the row and append peak rank
            row_values = [cell.get_text(strip=True) for cell in cells]
            row_values.append(winner_peak_rank)
            rows.append(row_values)

        # Add extra column for WinnerPeakRank
        headers.append("WinnerPeakRank")
        descriptions.append("Winner's peak ATP rank")
    else:
        # Default parsing for all other tables
        rows = parse_table_rows(table)

    # Prepare output file path
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f"{table_id}.csv")

    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerow(descriptions)
        writer.writerows(rows)

    print(f"📁 CSV written to '{output_file}'")


# Main function to drive the scraping
def main():
    chromedriver_path = "C:\\chromedriver-win64\\chromedriver.exe"
    base_url = "https://www.tennisabstract.com/cgi-bin/tourney.cgi?t="
    base_tourney_names = ["US_Open"]

    start_year = 2020
    end_year = 2020

    table_ids = ["singles-results", "stat-summaries"]  # Add more table IDs here if needed

    driver = init_driver(chromedriver_path)

    # Load cached peak ranks if available
    rank_cache = load_rank_cache()

    for base_tourney_name in base_tourney_names: 
        for year in range(start_year, end_year + 1):
            url = f"{base_url}{year}{base_tourney_name}"
            print(f"\n🌐 Scraping {year} {base_tourney_name.replace('_', ' ')}...")
            driver.get(url)

            output_folder = os.path.join("tennis_data", base_tourney_name, str(year))

            for table_id in table_ids:
                scrape_table_to_csv(driver, url, output_folder, table_id, rank_cache)

            time.sleep(4)

    # Save the rank cache for the next run
    save_rank_cache(rank_cache)

    driver.quit()


if __name__ == "__main__":
    main()
