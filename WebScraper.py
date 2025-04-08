# Breaking Down the Point
# Author: Kieran Plenn

import requests
import lxml
from bs4 import BeautifulSoup
import pandas as pd

# First let's scrape the list of players
player_list_url = "https://tennisabstract.com/reports/atpRankings.html"
player_list_response = requests.get(player_list_url)
player_list_soup = BeautifulSoup(player_list_response.content, 'lxml')
print(player_list_soup)