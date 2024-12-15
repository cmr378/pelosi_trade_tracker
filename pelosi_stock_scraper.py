import requests
from bs4 import BeautifulSoup
from flask import Flask, jsonify
from datetime import datetime
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

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

def fetch_data():
    """Fetch data from the website and return parsed content."""
    try:
        # Use Selenium to load the page
        driver = webdriver.Chrome(service=chrome_service, options=chrome_options)
        driver.get(URL)

        # Wait for the page to fully load (if needed, add explicit waits here)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        driver.quit()

        # Output a copy of the web page to inspect
        
        #output_soup_to_files(soup)

        # Extract desired data (modify based on the actual structure)
        trades = soup.select('#tradeTable tbody tr')  # Select all rows in the trade table
        new_data = {}

        '''table = soup.select_one('#tradeTable')
        if table:
            print("Table found!")
            print(table.prettify())
        else:
            print("Trade table not found!")'''

        for trade in trades:
            stock_name = trade.select_one('td:nth-child(1)').text.strip()  # Stock name
            print(stock_name)
            transaction_type = trade.select_one('td:nth-child(2)').text.strip()  # Transaction type
            print(transaction_type)
            filed_date = trade.select_one('td:nth-child(3)').text.strip()  # Filed date
            print(filed_date)
            trade_date = trade.select_one('td:nth-child(4)').text.strip()  # Traded date
            print(trade_date)
            description = trade.select_one('td:nth-child(5)').text.strip()  # Description
            print(description)

            # Store or print data as needed
            new_data[stock_name] = {
                "transaction_type": transaction_type,
                "filed_date": filed_date,
                "description": description,
            }

        print(new_data)
        global trade_tracker
        updated_trades = []

        # Compare with existing data in the tracker
        for stock, data in new_data.items():
            if stock not in trade_tracker or trade_tracker[stock] != data["trade_date"]:
                updated_trades.append({"stock": stock, "last_traded_date": data["trade_date"]})
                trade_tracker[stock] = data["trade_date"]  # Update tracker

        print("Updated Trades:", updated_trades)  # Print only new or changed trades
        return updated_trades

    except Exception as e:
        print("Error fetching data:", e)  # Print the error to the terminal
        return {"error": str(e)}

@app.route("/api/trades", methods=["GET"])
def get_trades():
    """API endpoint to fetch the latest trades."""
    data = fetch_data()
    return jsonify(data)

if __name__ == "__main__":
    app.run(debug=True)
