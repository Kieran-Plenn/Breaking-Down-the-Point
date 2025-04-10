# Breaking Down the Point
# Author: Kieran Plenn

import requests
from multiprocessing import Pool
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

def scrape_player_page(url):
    service = Service("C:\\chromedriver-win64\\chromedriver.exe")
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    driver = webdriver.Chrome(service=service, options=options)

    print("Name:", url)
    driver.get(url)

    table_ids = [
        "winners-errors", "serve-speed", "pbp-stats", "mcp-serve",
        "mcp-return", "mcp-rally", "mcp-tactics"
    ]

    for table_id in table_ids:
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, table_id))
            )
            html = driver.page_source
            soup = BeautifulSoup(html, "html.parser")
            table = soup.find("table", id=table_id)
            if table:
                print
                #print(f"Contents of '{table_id}' table from {url}")
            else:
                print(f"'{table_id}' table found but no content.")
        except Exception as e:
            print(f"Failed to find table with ID '{table_id}' in {url}. Error: {e}")

    driver.quit()

if __name__ == "__main__":
    # Setup must be inside this block
    player_list_url = "https://tennisabstract.com/reports/atpRankings.html"
    player_list_response = requests.get(player_list_url)
    player_list_soup = BeautifulSoup(player_list_response.content, 'html.parser')
    links = player_list_soup.find_all('a', href=True)
    player_links = [link['href'] for link in links if '.cgi?p=' in link['href']]
    num_players = len(player_links)

    with Pool(processes=2) as pool:
        pool.map(scrape_player_page, player_links[:10])  # try with a small batch

    print("Does it math? ", num_players * 7)
