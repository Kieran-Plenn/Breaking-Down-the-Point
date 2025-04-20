# Breaking Down the Point
# Author: Kieran Plenn

import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

def extract_table(driver, table_id):
    """Extracts and returns a BeautifulSoup object of a table"""
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, table_id))
    )
    print(f"Table with ID '{table_id}' found!")

    # Get page source and parse
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")
    
    # Find the table
    table = soup.find("table", id=table_id)
    return table

def extract_headers(table):
    """Extracts headers (both text and titles) from the table"""
    header_row = table.find("tr")
    headers = header_row.find_all("th")
    
    header_text = []
    header_titles = []
    
    for header in headers:
        # Clean the header text
        header_text.append(header.get_text(strip=True))
        # Get the title attribute (if exists) for header description
        title = header.get("title", "")
        header_titles.append(title)
    
    return header_text, header_titles

def extract_player_stats(table):
    """Extract player stats from a given table, return as a dictionary."""
    players_data = {}
    rows = table.find_all("tr")[1:]  # Skip header row
    for row in rows:
        columns = row.find_all("td")
        if len(columns) < 2:  # Skip if row is too short (invalid data)
            continue
        
        player_name = columns[0].get_text(strip=True)
        stats = [col.get_text(strip=True) for col in columns[1:]]
        
        players_data[player_name] = stats
    
    return players_data

def save_to_csv(file_name, header, rows):
    """Save data to CSV file."""
    with open(file_name, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(header)  # Write the header
        writer.writerows(rows)   # Write the data rows

def setup_driver():
    """Set up and return the Selenium WebDriver."""
    service = Service("C:\\chromedriver-win64\\chromedriver.exe")  # Make sure to adjust path
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Run in headless mode
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def scrape_tournament_data(url, table_ids):
    """Scrape tournament data from multiple tables and return the combined stats."""
    driver = setup_driver()
    driver.get(url)

    all_player_data = {}  # Dictionary to hold all player stats across tables
    all_headers = []      # To hold all headers dynamically

    # Loop through each table
    for table_id in table_ids:
        try:
            # Extract the table content
            table = extract_table(driver, table_id)
            
            if table:
                # Extract header text and titles
                header_text, header_titles = extract_headers(table)
                
                # Combine headers (header_text with titles in parentheses)
                combined_headers = [f"{text} ({title})" if title else text for text, title in zip(header_text, header_titles)]
                
                # Store the headers if it's the first table
                if not all_headers:
                    all_headers = ["Player"] + combined_headers  # Include "Player" as the first column
                
                # Extract player stats from the table
                players_stats = extract_player_stats(table)
                
                # Merge stats with previous data (combine on player name)
                for player, stats in players_stats.items():
                    if player not in all_player_data:
                        all_player_data[player] = []
                    all_player_data[player].extend(stats)  # Add new stats to the player

        except Exception as e:
            print(f"Failed to process table '{table_id}': {e}")

    driver.quit()
    return all_player_data, all_headers

def main():
    url = "https://www.tennisabstract.com/cgi-bin/tourney.cgi?t=2024US_Open"  # Replace with your tournament URL
    table_ids = ["stat-summaries"]  # Replace with your actual table IDs

    # Scrape the data
    all_player_data, all_headers = scrape_tournament_data(url, table_ids)

    # Combine all player stats into rows for CSV
    rows = []
    for player, stats in all_player_data.items():
        rows.append([player] + stats)  # Combine player name with their stats

    # Save combined data to CSV
    save_to_csv("2024_us_open_stats.csv", all_headers, rows)

if __name__ == "__main__":
    main()
