import sys
import time
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from Utilities.RobinhoodHandler import RobinhoodHandler
from Utilities.FileUtils import FileUtils
from config.config import (
    CRYPTO_SYMBOLS,
    PRICE_CHECK_INTERVAL
)

class CryptoTracker:
    def __init__(self):
        self.robinhood = RobinhoodHandler()
    
    def get_opening_prices(self):
        """Get the opening prices for each cryptocurrency at the start of the day."""

        print("Getting opening prices...")

        opening_prices = {}

        for symbol in CRYPTO_SYMBOLS:
            
            try:

                historical_data = self.robinhood.get_crypto_historicals(
                    symbol,
                    interval="hour",  # Use 'hour' for detailed data
                    span="day"        # Span for the current day
                )

                opening_price = float(historical_data[0]['open_price'])
                opening_prices[symbol] = float(opening_price)

                print(f"Opening price for {symbol}: ${opening_price}")

            except Exception as e:
                 print(f"Error retrieving historical data for {symbol}: {e}")
    
        return opening_prices

    def monitor_prices(self):

        print("--------------------------------")
        print("Current prices:")

        for symbol in CRYPTO_SYMBOLS:
            price = self.robinhood.get_crypto_price(symbol)
            if price is not None:
                print(f"    {symbol}: ${price}")

        print("--------------------------------")

        print(f"Will refresh prices in {PRICE_CHECK_INTERVAL} seconds...")
        time.sleep(PRICE_CHECK_INTERVAL)
    


if __name__ == "__main__":

    FileUtils.initialize_crypto_output_folder()

    cryptoTracker = CryptoTracker()
    cryptoTracker.get_opening_prices()

    while True:
        try:
            cryptoTracker.monitor_prices()

        except Exception as e:
            print(f"Error while monitoring cryptocurrency prices: {e}")





