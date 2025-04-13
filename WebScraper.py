# Breaking Down the Point
# Author: Kieran Plenn

import os
import csv
import requests
import re
import time
import unicodedata
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from itertools import chain

# Function to help match span text and title with keys
def clean_span(span):
    if not isinstance(span, str):
        return ''
    span = unicodedata.normalize("NFKD", span)  # Normalize unicode characters
    span = span.replace('\xa0', ' ')            # Replace non-breaking spaces
    span = span.replace('\n', ' ')              # Replace line breaks
    span = re.sub(r'\s+', ' ', span)            # Collapse multiple spaces
    return span.strip()

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
desired_scrapes = 1

# Counter for successful scrapes
scraped_count = 0

# Tracking elapsed time of consecutive page scrapes
loop_scrape_start_time = time.time()

# Now we scrape each page for our desired stats
for url in player_urls:

    # If current URL is in already scraped URLs, then continue
    if url in scraped_urls:
        continue

    # Uncomment to test specific Player
    url = "https://www.tennisabstract.com/cgi-bin/player.cgi?p=PatrickBrady"

    # Parse raw HTML player page for some quick initial variables
    initial_response = requests.get(url)
    initial_soup = BeautifulSoup(initial_response.content, "html.parser")
    
    # Sleep to avoid 429 (too many requests) error code and alert if any errors
    time.sleep(3.5)
    print("Status code: ", initial_response.status_code)

    # Extract the text inside the script tag where var fullname is found in the HTML
    script_content = initial_soup.find('script', string=re.compile('var fullname =')).string

    # Initializes an empty dictionary to store extracted info
    player_info = {}

    # Use regex to extract the first instance of relevant info
    player_info['name'] = re.search(r"var fullname = '([^']+)'", script_content).group(1)
    player_info['current_rank'] = re.search(r"var currentrank = (\d+)", script_content).group(1)
    player_info['peak_rank'] = re.search(r"var peakrank = (\d+)", script_content).group(1)
    
    # Point this to your ChromeDriver path
    service = Service("C:\\chromedriver-win64\\chromedriver.exe")
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Optional: Run in headless mode
    driver = webdriver.Chrome(service=service, options=options)

    driver.get(url)

    # Keep track of how many matches are being used to collect data per player
    num_matches = 0
    scraped_tables_count = 0

    # Store stats with stat names
    all_results = {}

    # Define tables and stats to scrape
    table_stats = {
        "winners-errors": ["Winners", "Wnr/Pt", "UFE/Pt", "FH Wnr/Pt", "BH Wnr/Pt"],
        "serve-speed": ["1st Avg", "1st T Avg", "1st Wide Avg","2nd Avg", "2nd T Avg", "2nd Wide Avg"],
        "pbp-stats": ["Deuce A%", "Deuce SPW%", "Ad A%", "Ad SPW%", "Deuce RPW%", "Ad RPW%"],
        "mcp-serve": {
            "text": [
                "D Wide%",
                "A Wide%"
            ],
            "title": [
                "Percent of first serve points won on either the serve or second shot",
                "Percentage of first serve points won when return was put in play",
                "Percent of second serve points won on either the serve or second shot",
                "Percentage of second serve points won when return was put in play"
            ]
        },
        "mcp-return": {
            "text": [
                "RiP%"
            ],
            "title": [
                "Percent of points won when return was put in play",
                "Return Depth Index (higher = deeper)",
                "Slice/chip returns as a percentage of all in-play first-serve returns",
                "Return winners (and induced forced errors) as a percentage of second-serve return points"
            ]
        },
        "mcp-rally": ["RallyLen", "1-3 W%", "10+ W%", "FH/GS", "BH Slice%", "FHP/100", "BHP/100"],
        
        "mcp-tactics": {
            "text": [
                "SnV Freq", 
                "SnV W%", 
                "Net Freq", 
                "Net W%", 
                "FH: Wnr%", 
                "BH: Wnr%", 
                "Drop: Freq"
            ],
            "title": [
                "Winners (and induced forced errors) per (topspin) down-the-line forehand",
                "Winners (and induced forced errors) per (topspin) inside-out forehand",
                "Winners (and induced forced errors) per (topspin) down-the-line backhand",
                "Winners (and induced forced errors) per (baseline) dropshot"
            ]
        }
    }

    # Generate a consistent list of all possible stat headers
    lookup_map = {
        "player_name": "player_name",
        "current_rank": "current_rank",
        "peak_rank": "peak_rank"
    }

    for table_id, config in table_stats.items():
        text_keys = config.get("text", []) if isinstance(config, dict) else config
        title_keys = config.get("title", []) if isinstance(config, dict) else []

        for key in text_keys:
            header_key = f"{key}"  
            lookup_map[key] = header_key        

        for key in title_keys:
            header_key = f"{key}"
            lookup_map[key] = header_key

    # Loop through tables and columns within tables
    for table_id, config in table_stats.items():
        try:
            # Wait for the table to be present
            WebDriverWait(driver, 4).until(
                EC.presence_of_element_located((By.ID, table_id))
            )

            # Get the page source after the table has loaded
            html = driver.page_source
            soup = BeautifulSoup(html, "html.parser")

            # Find the table by ID
            table = soup.find("table", {"id": table_id})
            if not table:
                print(f"Table {table_id} not found.")
                continue

            # Handle your table extraction logic
            text_keys = config.get("text", []) if isinstance(config, dict) else config
            title_keys = config.get("title", []) if isinstance(config, dict) else []

            header = table.find("thead")
            index_map = {}

            for idx, th in enumerate(header.find_all("th")):
                span = th.find("span")
                if not span:
                    continue

                text_val = clean_span(span.get_text())
                title_val = clean_span(span.get("title", ""))

                if text_val in lookup_map:
                    index_map[lookup_map[text_val]] = idx
                elif title_val in lookup_map:
                    index_map[lookup_map[title_val]] = idx


            # Locate the career row and extract stats
            career_b = table.find("b", string=lambda s: s and "Career" in s)
            career_row = career_b.find_parent("tr") if career_b else None

            if not career_row:
                print(f"Career row not found in {table_id}.")
                raise Exception()

            cols = career_row.find_all("td")
            
            # Keep track of poor match sample size for players
            td_element = cols[0]  # this is a BeautifulSoup tag like <td><b>Career (1 matches)</b></td>

            # extract the inner text
            text = td_element.get_text(strip=True)  # 'Career (1 matches)'

            # use regex to extract the number inside parentheses
            match = re.search(r'\((\d+)\s+matches?\)', text)
            if match:
                num_matches += int(match.group(1))
                scraped_tables_count += 1
            else:
                num_matches += 0  # or None if you prefer

            # Extract the desired statistics from columns
            stat_dict = {}
            for header_key, col_idx in index_map.items():
                if col_idx < len(cols):
                    stat_dict[header_key] = cols[col_idx].get_text(strip=True)
                else:
                    stat_dict[header_key] = "N/A"

            all_results[table_id] = stat_dict

        except Exception as e:
            print(f"Error: could NOT scrape {table_id} table from {player_info['name']}'s page")

            # Create a dict with N/A for each header_key and add it to all_results with table_id as the key
            if isinstance(config, dict):
                missing_table_dict = {header_key: "N/A" for header_key in chain(config.get("text", []), config.get("title", []))}
            else:
                missing_table_dict = {header_key: "N/A" for header_key in config}
            # Add the dictionary to all_results using table_id as the key
            all_results[table_id] = missing_table_dict  

    # Quit the driver
    driver.quit()

    # Flatten the all_results data into a list of rows
    flattened_data = []

    # Define headers (ensure these match your previous header structure)
    headers = ["avg_matches", "player_name", "current_rank", "peak_rank"]  # Add player-specific details as headers first

    # Hard-coded base stats for the player
    base_row = {
        "avg_matches": num_matches/scraped_tables_count,
        "player_name": player_info['name'], 
        "current_rank": player_info['current_rank'],
        "peak_rank": player_info['peak_rank']
    }

    # Iterate through all_results and create rows for each table's stats
    row = base_row.copy()  # Make a copy so we don’t modify the original
    for table_id, stats in all_results.items():
        for stat_name, stat_value in stats.items():
            row[f"{table_id}_{stat_name}"] = stat_value  # Flattened key

    # Append a full copy of the completed row
    flattened_data.append(row.copy())

    # Update headers
    for key in row:
        if key not in headers:
            headers.append(key)

    # Define CSV file path
    csv_filename = 'player_data_test.csv'

    # Check if the file exists to decide whether to write the header or not
    file_exists = os.path.exists(csv_filename)

    # Open the CSV file and append the data
    with open(csv_filename, mode='a', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=headers)
        
        # Write the header if the file doesn't exist
        if not file_exists:
            writer.writeheader()

        # Write all the flattened data to the file (each player as one row)
        for row in flattened_data:
            writer.writerow(row)

    print("Data appended successfully to player_data.csv.")

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

