# Breaking Down the Point
# Author: Kieran Plenn

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

def extract_table(table_id):
    # Wait for the table to be present
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, table_id))
    )
    print(f"Table with ID '{table_id}' found!")

    # Get the page source after the table has loaded
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")

    # Find and store the table if it exists
    table = soup.find("table", id=table_id)
        
    # Return the extracted table
    return table

# Point this to your ChromeDriver path
service = Service("C:\\chromedriver-win64\\chromedriver.exe")
options = webdriver.ChromeOptions()
options.add_argument("--headless")  # Optional: Run in headless mode
driver = webdriver.Chrome(service=service, options=options)

url = "https://www.tennisabstract.com/cgi-bin/tourney.cgi?t=2024US_Open"  # Replace with desired player
driver.get(url)

# Table IDs to check
table_ids = [
    "singles-results"
]

# Wait for page to load and try to find each table
for table_id in table_ids:
    try:
        # Extract the table's information
        table = extract_table(table_id)
        
        if table:
            print(f"Contents of '{table_id}' table:")
            print(table.prettify())
        else:
            print(f"'{table_id}' table found but no content.")

    except Exception as e:
        print(f"Failed to find table with ID '{table_id}'. Error: {e}")

# Quit the driver
driver.quit()
