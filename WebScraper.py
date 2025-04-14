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

# Custom exception names for readability
class CareerRowNotFoundException(Exception):
    pass

# Function to help match span text and title with keys
def clean_span(span):
    if not isinstance(span, str):
        return ''
    span = unicodedata.normalize("NFKD", span)  # Normalize unicode characters
    span = span.replace('\xa0', ' ')            # Replace non-breaking spaces
    span = span.replace('\n', ' ')              # Replace line breaks
    span = re.sub(r'\s+', ' ', span)            # Collapse multiple spaces
    return span.strip()

# Function to return formatted elapsed time (min:sec:milli)
def format_time(elapsed_time):
    elapsed_minutes = elapsed_time // 60
    elapsed_seconds = elapsed_time % 60
    elapsed_milliseconds = (elapsed_time - int(elapsed_time)) * 10000
    return f"{int(elapsed_minutes):02d}:{int(elapsed_seconds):02d}:{int(elapsed_milliseconds)}"


# Tracking elapsed time of initial player list scrape
list_scrape_start_time = time.time()

# First let's scrape the page of hyperlinks to players' pages
player_list_link = "https://tennisabstract.com/reports/atpRankings.html"
player_list_response = requests.get(player_list_link)
player_list_soup = BeautifulSoup(player_list_response.content, 'html.parser')

# We'll isolate just the URLs for player pages from the scraped "soup" 
urls = player_list_soup.find_all('a', href=True)
player_urls = [url['href'] for url in urls if 'player' in url['href']]

# Display player list scrape elapsed time
print(f"Successfully scraped {len(player_urls)} player url(s) (time: {format_time(time.time() - list_scrape_start_time)})")

# Create a file to save most recently scraped URL as a checkpoint
checkpoint_file = "scraped_players.txt"

# Define CSV file path
csv_filename = 'player_data.csv'

# Identify if we are testing so we ignore checkpoint_file
test = False

# If the file already exists, then load the Set of already scraped URLs
if os.path.exists(checkpoint_file):
    with open(checkpoint_file, "r") as f:
        scraped_urls = set(line.strip() for line in f)
# Else, just initialize the Set
else:
    scraped_urls = set()

# Determines size of .csv (number of players/rows we want)
desired_scrapes = 1000

# Counter for successful scrapes
scraped_count = 0

# Tracking elapsed time of consecutive page scrapes
total_loop_start_time = time.time()

# Define tables and stats to scrape
table_stats = {
    "tour-years": ["A%", "DF%", "1stIn", "1st%", "2nd%"],
    "winners-errors": ["Wnr/Pt", "UFE/Pt", "FH Wnr/Pt", "BH Wnr/Pt"],
    "serve-speed": ["1st Avg", "1st T Avg", "1st Wide Avg","2nd Avg", "2nd T Avg", "2nd Wide Avg"],
    "pbp-stats": ["Deuce A%", "Deuce SPW%", "Ad A%", "Ad SPW%", "Deuce RPW%", "Ad RPW%"],
    "mcp-serve": {
        "text": [
            "1st: Unret%",
            "2nd: Unret%",
            "D Wide%",
            "A Wide%",
            "2ndAgg"
        ],
        "title": [
            "Serve Impact: Advanced stat estimating how many service points won due to the serve",
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
    "mcp-rally": ["RallyLen", "1-3 W%", "4-6 W%", "7-9 W%", "10+ W%", "FH/GS", "BH Slice%", "FHP/100", "BHP/100"],
        
    "mcp-tactics": {
        "text": [
            "SnV Freq", 
            "SnV W%", 
            "Net Freq", 
            "Net W%", 
            "FH: Wnr%", 
            "IO Wnr%",
            "BH: Wnr%", 
            "Drop: Freq",
            "RallyAgg",
            "ReturnAgg"
        ],
        "title": [
            "Winners (and induced forced errors) per (topspin) down-the-line forehand",
            "Winners (and induced forced errors) per (topspin) down-the-line backhand",
            "Winners (and induced forced errors) per (baseline) dropshot"
        ]
    }
}

# Uncomment to test specific list of players
'''
test = True
# Define your desired indices (can mix ranges and specific values)
target_indices = (
    list(range(373, 386))      # Rank 374 to Rank 386
    #list(range(100, 111)) +    # 100 to 110
    #[373]                # specific indices
)
player_urls = [player_urls[i] for i in target_indices if i < len(player_urls)]
desired_scrapes = len(player_urls)
csv_filename = 'player_data_test.csv'
'''

# Uncomment to test specific Player
'''
test = True
player_urls = ["https://www.tennisabstract.com/cgi-bin/player.cgi?p=GiovanniFonio"
               ]
desired_scrapes = len(player_urls)
csv_filename = 'player_data_test.csv'
'''

# Confirm before running real scrapes
if not test:
    confirm = input("\nNOT A TEST: This will change saved files. Are you sure you want to proceed? (y/n): ")
    if confirm.lower() not in ['y', 'yes']:
        print("Scraping cancelled. Exiting program.")
        exit()

# Now we scrape each page for our desired stats
for url_total, url in enumerate(player_urls):
    # Track scrape time for each page
    player_scrape_start_time = time.time()

    # If we've reached the desired number of scrapes, then stop the loop
    if scraped_count >= desired_scrapes:
        print(f"Successfully scraped {scraped_count} players. Stopping.")
        break

    # If current URL is in already scraped URLs (and we aren't just testing), then continue
    if url in scraped_urls and not test:
        continue

    # Parse raw HTML player page for some quick initial variables
    initial_response = requests.get(url)
    initial_soup = BeautifulSoup(initial_response.content, "html.parser")
    
    # Sleep to avoid 429 (too many requests) error code and alert if any errors
    time.sleep(4)
    print(f"\n\nStatus code: {initial_response.status_code} ({url})")

    # Extract the text inside the script tag where var fullname is found in the HTML
    script_content = initial_soup.find('script', string=re.compile('var fullname =')).string

    # Initializes an empty dictionary to store extracted info
    player_info = {}

    # Keep track of missing tables
    error_tables = []

    # Use regex to extract the first instance of relevant info
    # Extract full name safely
    try:
        match = re.search(r"var fullname = '([^']+)'", script_content)
        player_info['name'] = match.group(1) if match else 'N/A'
        if not match:
            print(f"[WARN] Missing name on {url}")
    except Exception as e:
        print(f"[ERROR] Failed to extract name from {url}: {e}")
        player_info['name'] = 'N/A'

    # Extract current rank (with UNR handling)
    try:
        match = re.search(r"var currentrank = (\d+)", script_content)
        if match:
            player_info['current_rank'] = match.group(1)
        elif 'UNR' in script_content:
            player_info['current_rank'] = 'UNR'
        else:
            player_info['current_rank'] = 'N/A'
            print(f"[WARN] No current rank found on {url}")
    except Exception as e:
        print(f"[ERROR] Failed to extract current rank from {url}: {e}")
        player_info['current_rank'] = 'N/A'

    # Extract peak rank
    try:
        match = re.search(r"var peakrank = (\d+)", script_content)
        player_info['peak_rank'] = match.group(1) if match else 'N/A'
        if not match:
            print(f"[WARN] Missing peak rank on {url}")
    except Exception as e:
        print(f"[ERROR] Failed to extract peak rank from {url}: {e}")
        player_info['peak_rank'] = 'N/A'

    # Point this to your ChromeDriver path
    service = Service("C:\\chromedriver-win64\\chromedriver.exe")
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Optional: Run in headless mode
    driver = webdriver.Chrome(service=service, options=options)

    # Navigate the browser to the specified URL
    driver.get(url)
    
    # Grab all table elements and their IDs
    tables_on_page = driver.find_elements(By.TAG_NAME, "table")
    table_ids_found = {table.get_attribute("id") for table in tables_on_page if table.get_attribute("id")}
    
    # Check if page contains any desired tables
    if not table_stats.keys() & table_ids_found:
        print(f"Skipping {player_info.get("name")}'s page - no desired tables available")
        driver.quit()
        continue  # if page features no desired tables continue and skip player

    # Store stats with stat names
    all_results = {}
    
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

    # We want the median of this
    num_matches_list = []
    # Loop through tables and columns within tables
    for table_id, config in table_stats.items():
        # Keep track of how many matches are being used to collect data per player
        num_matches = 0

        try:
            # Wait for the table to be present
            WebDriverWait(driver, 1).until(EC.presence_of_element_located((By.ID, table_id)))

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
                elif text_val == "MS":  # special case where we might be scraping a career row where # of matches is in table
                    num_matches_idx = idx

            # Locate the career row and extract stats
            career_b = table.find("b", string=lambda s: s and "Career" in s)
            career_row = career_b.find_parent("tr") if career_b else None

            if not career_row:
                print(f"Career row not found in {table_id}.")
                raise CareerRowNotFoundException()

            cols = career_row.find_all("td")
            
            # Keep track of poor match sample size for players
            td_element = cols[0]  # this is a BeautifulSoup tag like <td><b>Career (1 matches)</b></td>

            # extract the inner text
            text = td_element.get_text(strip=True)  # 'Career (1 matches)'

            # use regex to extract the number inside parentheses
            match = re.search(r'\((\d+)\s+matches?\)', text)
            if match:
                num_matches += int(match.group(1))
            elif num_matches_idx:
                try:
                    num_matches = int(cols[num_matches_idx].get_text(strip=True))
                except ValueError:
                    continue
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

        except CareerRowNotFoundException as e:
            stat_dict = {}
            col_total_tracker = {}
            percent_tracker = {}
            # For each row in our whole table
            for row in table.find("tbody").find_all("tr"):
                cols = row.find_all("td")
                if num_matches_idx:
                    try:
                        num_matches += int(cols[num_matches_idx].get_text(strip=True))
                    except ValueError:
                        continue
                else:
                    num_matches += 1
                for header_key, col_idx in index_map.items():
                    if col_idx < len(cols):
                        try:
                            if "%" in cols[col_idx].text:
                                percent_tracker[header_key] = True
                            value = cols[col_idx].text.strip('%')
                            stat_dict[header_key] = stat_dict.get(header_key, 0.0) + float(value)
                            col_total_tracker[header_key] = col_total_tracker.get(header_key, 0) + 1
                        except ValueError:
                            continue
                    else:
                        stat_dict[header_key] = "N/A"
            
            for header_key, total in stat_dict.items():
                try:
                    stat_dict[header_key] = "{:.2f}".format(stat_dict[header_key]/col_total_tracker[header_key])
                    if percent_tracker[header_key]:
                        stat_dict[header_key] = f"{stat_dict[header_key]}%"
                except Exception:
                    continue
            all_results[table_id] = stat_dict
        
        except Exception as e:
            # Add table_id to list of missing tables
            error_tables.append(table_id)

            # Create a dict with N/A for each header_key and add it to all_results with table_id as the key
            if isinstance(config, dict):
                missing_table_dict = {header_key: "N/A" for header_key in chain(config.get("text", []), config.get("title", []))}
            else:
                missing_table_dict = {header_key: "N/A" for header_key in config}
            # Add the dictionary to all_results using table_id as the key
            all_results[table_id] = missing_table_dict  
        if table_id not in error_tables:
            num_matches_list.append(num_matches)

    # Quick calc
    num_matches_list.sort()
    median_index = len(num_matches_list) // 2
    try:
        median_num_matches = num_matches_list[median_index]
    except IndexError:
        median_num_matches = 0

    # Quit the driver
    driver.quit()

    # Flatten the all_results data into a list of rows
    flattened_data = []

    # Define hard coded headers (ensure these match your previous header structure)
    headers = ["median_matches", "player_name", "current_rank", "peak_rank"]  # Add player-specific details as headers first

    # Create a mapping from header names to values
    player_info_map = {
        "url": url,
        "median_matches": median_num_matches,
        "player_name": player_info.get("name", "N/A"),
        "current_rank": player_info.get("current_rank", "N/A"),
        "peak_rank": player_info.get("peak_rank", "N/A")
    }

    # Build the base row dynamically
    base_row = {header: player_info_map.get(header, "N/A") for header in headers}

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

    # Add successfully scraped player page to checkpoint list (unless we're testing)
    if not test:
        with open(checkpoint_file, "a") as f:
            f.write(url + "\n")

    # Increment the successful scrape counter
    scraped_count += 1
    
    # Output info and confirmation message
    print(f"{player_info.get("name")}'s page data appended successfully in time: {format_time(time.time() - player_scrape_start_time)} (missing {len(error_tables)} tables).")

# Completion message
print("\nSCRAPE COMPLETE...")
total_time = time.time() - total_loop_start_time
print(f"Total elapsed time ({scraped_count} pages): {format_time(total_time)}")

