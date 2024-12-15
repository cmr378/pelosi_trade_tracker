import requests
from bs4 import BeautifulSoup
from flask import Flask, jsonify
from datetime import datetime
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait  
from selenium.webdriver.support import expected_conditions as EC  
from webdriver_manager.chrome import ChromeDriverManager
import json
import argparse

# Initialize Flask app
app = Flask(__name__)

# URL of the target page
URL = "https://www.quiverquant.com/congresstrading/politician/Nancy%20Pelosi-P000197"

# Initialize Selenium WebDriver
chrome_options = Options()
chrome_options.add_argument("--headless")  # Run in headless mode
chrome_options.add_argument("--disable-gpu")  # Disable GPU acceleration
chrome_options.add_argument("--no-sandbox")  # Overcome limited resource problems
chrome_service = Service(ChromeDriverManager().install())

def output_soup_to_files(soup):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    instances_path = Path("instances")
    instances_path.mkdir(exist_ok=True)
    filename = instances_path / f"page_output_{timestamp}.html"
    with open(filename, "w", encoding="utf-8") as file:
        file.write(soup.prettify())

def save_to_json(data):
    """Save the dictionary to a JSON file."""
    data_file = Path("trade_data.json")
    if data_file.exists():
        with data_file.open("r", encoding="utf-8") as file:
            existing_data = json.load(file)
    else:
        existing_data = {}

    # Update existing data with new data
    existing_data.update(data)

    with data_file.open("w", encoding="utf-8") as file:
        json.dump(existing_data, file, indent=4)

def fetch_data(data_type="trades"):
    """Fetch data from the website and return parsed content based on data type."""
    try:
        # Use Selenium to load the page
        driver = webdriver.Chrome(service=chrome_service, options=chrome_options)
        driver.get(URL)

        # Wait for the specific table to load based on the data type
        if data_type == "holdings":
            WebDriverWait(driver, 40).until(
                EC.presence_of_element_located((By.ID, "holdingsTable"))
            )
        elif data_type == "trades":
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "tradeTable"))
            )

        # Parse the page with BeautifulSoup
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        driver.quit()

        if data_type == "trades":
            trades = soup.select('#tradeTable tbody tr')  # Select all rows in the trade table
            data = {}

            for trade in trades:
                stock_name = trade.select_one('td:nth-child(1)').text.strip() if trade.select_one('td:nth-child(1)') else None
                transaction_type = trade.select_one('td:nth-child(2)').text.strip() if trade.select_one('td:nth-child(2)') else None
                filed_date = trade.select_one('td:nth-child(3)').text.strip() if trade.select_one('td:nth-child(3)') else None
                trade_date = trade.select_one('td:nth-child(4)').text.strip() if trade.select_one('td:nth-child(4)') else None
                description = trade.select_one('td:nth-child(5)').text.strip() if trade.select_one('td:nth-child(5)') else None

                # Store or print data as needed
                data[stock_name] = {
                    "transaction_type": transaction_type,
                    "filed_date": filed_date,
                    "trade_date": trade_date,
                    "description": description,
                }

        elif data_type == "holdings":
            holdings_table = soup.select_one('#holdingsTable')
            print(holdings_table)
            if not holdings_table:
                print("Holdings table not found!")
                return {}

            holdings = holdings_table.select('tbody tr')  # Select all rows in the holdings table
            data = {}

            for holding in holdings:
                stock_name = holding.select_one('td:nth-child(1)').text.strip() if holding.select_one('td:nth-child(1)') else None
                asset_type = holding.select_one('td:nth-child(2)').text.strip() if holding.select_one('td:nth-child(2)') else None
                asset_name = holding.select_one('td:nth-child(3)').text.strip() if holding.select_one('td:nth-child(3)') else None
                amount = holding.select_one('td:nth-child(4)').text.strip() if holding.select_one('td:nth-child(4)') else None
                owner = holding.select_one('td:nth-child(5)').text.strip() if holding.select_one('td:nth-child(5)') else None
                report_year = holding.select_one('td:nth-child(6)').text.strip() if holding.select_one('td:nth-child(6)') else None
                filed_date = holding.select_one('td:nth-child(7)').text.strip() if holding.select_one('td:nth-child(7)') else None

                # Store or print data as needed
                data[stock_name] = {
                    "asset_type": asset_type,
                    "asset_name": asset_name,
                    "amount": amount,
                    "owner": owner,
                    "report_year": report_year,
                    "filed_date": filed_date,
                }

        else:
            raise ValueError("Invalid data type specified. Choose 'trades' or 'holdings'.")

        print(data)
        save_to_json(data)

    except Exception as e:
        print("Error fetching data:", e)  # Print the error to the terminal
        return {"error": str(e)}

def main():
    parser = argparse.ArgumentParser(description="Fetch Nancy Pelosi's trade or holdings data.")
    parser.add_argument("data_type", choices=["trades", "holdings"], help="Specify whether to fetch trades or holdings data.")
    args = parser.parse_args()

    fetch_data(args.data_type)

if __name__ == "__main__":
    main()
