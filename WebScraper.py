# Breaking Down the Point
# Author: Kieran Plenn

import os
import csv
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

# First let's scrape the page featuring hyperlinks to players' pages
player_list_link = "https://tennisabstract.com/reports/atpRankings.html"
player_list_response = requests.get(player_list_link)
player_list_soup = BeautifulSoup(player_list_response.content, 'html.parser')

# We'll isolate just the URLs for player pages from the scraped "soup" 
urls = player_list_soup.find_all('a', href=True)
player_urls = [url['href'] for url in urls if '.cgi?p=' in url['href']]

# Track completed URLs
checkpoint_file = "scraped_players.txt"
if os.path.exists(checkpoint_file):
    with open(checkpoint_file, "r") as f:
        scraped_urls = set(line.strip() for line in f)
else:
    scraped_urls = set()

# Now we scrape each page for our desired stats
for url in player_urls[:1]:
    if url in scraped_urls:
        continue

    # Get easy initial stats
    initial_response = requests.get(url)
    initial_soup = BeautifulSoup(initial_response, "html.parser")
    print(initial_soup)
    
    # Point this to your ChromeDriver path
    service = Service("C:\\chromedriver-win64\\chromedriver.exe")
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Optional: Run in headless mode
    driver = webdriver.Chrome(service=service, options=options)

    driver.get(url)

    # Table IDs to check
    table_ids = [
        "winners-errors", "serve-speed", "pbp-stats", "mcp-serve",
        "mcp-return", "mcp-rally", "mcp-tactics"
    ]

    # Wait for page to load and try to find each table
    for table_id in table_ids:
        try:
            # Wait for the table to be present
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, table_id))
            )

            # Get the page source after the table has loaded
            html = driver.page_source
            soup = BeautifulSoup(html, "html.parser")

            # Find and print the table if it exists
            table = soup.find("table", id=table_id)
            if table:
                print(f"Contents of '{table_id}' table:")
                #print(table.prettify())
            else:
                print(f"'{table_id}' table found but no content.")

        except Exception as e:
            print(f"Failed to find table with ID '{table_id}'. Error: {e}")

    # Quit the driver
    driver.quit()

    # Add successfully scraped player page to checkpoint list
    with open(checkpoint_file, "a") as f:
        f.write(url + "\n")
