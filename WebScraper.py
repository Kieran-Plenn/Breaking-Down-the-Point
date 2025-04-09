# Breaking Down the Point
# Author: Kieran Plenn

import requests
import lxml
from bs4 import BeautifulSoup
import pandas as pd

# First let's scrape the page featuring hyperlinks to players' pages
player_list_url = "https://tennisabstract.com/reports/atpRankings.html"
player_list_response = requests.get(player_list_url)
player_list_soup = BeautifulSoup(player_list_response.content, 'lxml')

# We'll isolate just the URLs for player pages from the scraped "soup" 
links = player_list_soup.find_all('a', href=True)
player_links = [link['href'] for link in links if '.cgi?p=' in link['href']]

# Now we scrape each page for our desired stats
for player_url in player_links:
    individual_player_response = requests.get(player_url)
    individual_player_soup = BeautifulSoup(individual_player_response.content, 'lxml')
    break
print(individual_player_soup)