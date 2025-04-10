# Breaking Down the Point
# Author: Kieran Plenn

import requests
import threading
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import concurrent.futures

# First let's scrape the page featuring hyperlinks to players' pages
player_list_url = "https://tennisabstract.com/reports/atpRankings.html"
player_list_response = requests.get(player_list_url)
player_list_soup = BeautifulSoup(player_list_response.content, 'html.parser')

# We'll isolate just the URLs for player pages from the scraped "soup" 
links = player_list_soup.find_all('a', href=True)
player_links = [link['href'] for link in links if '.cgi?p=' in link['href']]

num_players = len(player_links)
table_count_lock = threading.Lock()
table_count = 0

# Function for scraping player page
def scrape_player_page(url):
    global table_count
    # Point this to your ChromeDriver path
    service = Service("C:\\chromedriver-win64\\chromedriver.exe")
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")  # Optional: Run in headless mode
    driver = webdriver.Chrome(service=service, options=options)

    #url = "https://www.tennisabstract.com/cgi-bin/player.cgi?p=NovakDjokovic"  # Replace with desired player
    print("Name: ", url)
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
            WebDriverWait(driver, 2).until(
                EC.presence_of_element_located((By.ID, table_id))
            )
            #print(f"Table with ID '{table_id}' found!")

            # Get the page source after the table has loaded
            html = driver.page_source
            soup = BeautifulSoup(html, "html.parser")

            # Find and print the table if it exists
            table = soup.find("table", id=table_id)
            if table:
                #print(f"Contents of '{table_id}' table:")
                #print(table.prettify())
                with table_count_lock:
                    table_count+=1
            else:
                print(f"'{table_id}' table found but no content.")

        except Exception as e:
            print(f"Failed to find table with ID '{table_id}' in ", url,". Error: {e}")

    # Quit the driver
    driver.quit()

# Now we scrape each page for our desired stats
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
    executor.map(scrape_player_page, player_links[:100])
print("Table Count: ", table_count)
print("Does it math? ", num_players*7)
