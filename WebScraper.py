# Breaking Down the Point
# Author: Kieran Plenn

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time

# Point this to your ChromeDriver path
service = Service("C:\\chromedriver-win64\\chromedriver.exe")
options = webdriver.ChromeOptions()
options.add_argument("--headless")  # Optional: Run in headless mode
driver = webdriver.Chrome(service=service, options=options)

url = "https://www.tennisabstract.com/cgi-bin/player.cgi?p=NovakDjokovic"  # Replace with desired player
driver.get(url)

# Wait for a key table (like #titles-finals) to load
try:
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "mcp-serve"))
    )
except:
    print("Table didn't load in time")

# Now get the page source
html = driver.page_source
soup = BeautifulSoup(html, "html.parser")

# Find all tables by ID or just all <table> tags
tables = soup.find_all("table")
print(f"Found {len(tables)} tables")

# Optionally, grab a specific table
titles_table = soup.find("table", id="mcp-serve")
if titles_table:
    print("MCP Serve Table Found")
    print(titles_table.prettify())
else:
    print("No 'mcp-serve' table found")

driver.quit()
