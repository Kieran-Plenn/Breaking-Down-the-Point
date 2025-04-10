# Breaking Down the Point
# Author: Kieran Plenn

import os
import csv
import requests
import re
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

# Tracking elapsed time of initial player list scrape
list_scrape_start_time = time.time()

# First let's scrape the page of hyperlinks to players' pages
player_list_link = "https://tennisabstract.com/reports/atpRankings.html"
player_list_response = requests.get(player_list_link)
player_list_soup = BeautifulSoup(player_list_response.content, 'html.parser')

# We'll isolate just the URLs for player pages from the scraped "soup" 
urls = player_list_soup.find_all('a', href=True)
player_urls = [url['href'] for url in urls if '.cgi?p=' in url['href']]

# Calculate and display player list scrape elapsed time
list_scrape_elapsed_time = time.time() - list_scrape_start_time
list_scrape_elapsed_minutes = list_scrape_elapsed_time // 60
list_scrape_elapsed_seconds = list_scrape_elapsed_time % 60
list_scrape_elapsed_milliseconds = (list_scrape_elapsed_time - int(list_scrape_elapsed_time)) * 10000
print(f"Player list scrape elapsed time: {int(list_scrape_elapsed_minutes)}:{int(list_scrape_elapsed_seconds)}:{int(list_scrape_elapsed_milliseconds)}")

# Create a file to save most recently scraped URL as a checkpoint
checkpoint_file = "scraped_players.txt"

# If the file already exists, then load the Set of already scraped URLs
if os.path.exists(checkpoint_file):
    with open(checkpoint_file, "r") as f:
        scraped_urls = set(line.strip() for line in f)
# Else, just initialize the Set
else:
    scraped_urls = set()

# Number of successful scrapes to perform (e.g., 10 or 50)
desired_scrapes = 10

# Counter for successful scrapes
scraped_count = 0

# Tracking elapsed time of consecutive page scrapes
loop_scrape_start_time = time.time()

# Now we scrape each page for our desired stats
for url in player_urls:

    # If current URL is in already scraped URLs, then continue
    if url in scraped_urls:
        continue

    # Parse raw HTML player page for some quick initial variables
    initial_response = requests.get(url)
    initial_soup = BeautifulSoup(initial_response.content, "html.parser")
    
    # Sleep to avoid 429 (too many requests) error code and alert if any errors
    time.sleep(5)
    print("Status code: ", initial_response.status_code)

    # Extract the text inside the script tag where var fullname is found in the HTML
    script_content = initial_soup.find('script', string=re.compile('var fullname =')).string

    # Initializes an empty dictionary to store extracted info
    player_info = {}

    # Use regex to extract the first instance of relevant info
    player_info['name'] = re.search(r"var fullname = '([^']+)'", script_content).group(1)
    player_info['current_rank'] = re.search(r"var currentrank = (\d+)", script_content).group(1)
    player_info['peak_rank'] = re.search(r"var peakrank = (\d+)", script_content).group(1)

    # Write the player info to a CSV file
    csv_filename = 'player_data.csv'

    # Check if the file exists to decide whether to write the header or not
    file_exists = False
    try:
        with open(csv_filename, 'r'):
            file_exists = True
    except FileNotFoundError:
        file_exists = False

    # Open the file in append mode
    with open(csv_filename, mode='a', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=player_info.keys())
        
        # Write the header if the file doesn't exist
        if not file_exists:
            writer.writeheader()

        # Write the player data
        writer.writerow(player_info)
    """
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
                print
                #print(f"Contents of '{table_id}' table:")
                #print(table.prettify())
            else:
                print(f"'{table_id}' table found but no content.")

        except Exception as e:
            print(f"Failed to find table with ID '{table_id}'. Error: {e}")

    # Quit the driver
    driver.quit()
"""
    # Add successfully scraped player page to checkpoint list
    with open(checkpoint_file, "a") as f:
        f.write(url + "\n")

    # Increment the successful scrape counter
    scraped_count += 1

    # If we've reached the desired number of scrapes, then stop the loop
    if scraped_count >= desired_scrapes:
        print(f"Successfully scraped {scraped_count} players. Stopping.")
        break

# Calculate and display consecutive page scrape elapsed time
loop_scrape_elapsed_time = time.time() - loop_scrape_start_time
loop_scrape_elapsed_minutes = loop_scrape_elapsed_time // 60
loop_scrape_elapsed_seconds = loop_scrape_elapsed_time % 60
loop_scrape_elapsed_milliseconds = (loop_scrape_elapsed_time - int(loop_scrape_elapsed_time)) * 10000
print(f"Consecutive page scrape elapsed time: {int(loop_scrape_elapsed_minutes)}:{int(loop_scrape_elapsed_seconds)}:{int(loop_scrape_elapsed_milliseconds)}")

