import sys
import time
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from Utilities.crypto_robinhood_handler import CryptoRobinhoodHandler
from Utilities.file_utils import FileUtils
from config.config import (
    CRYPTO_SYMBOLS,
    PRICE_CHECK_INTERVAL,
    PRICE_THRESHOLD,
    COOLDOWN_PERIOD
)

class CryptoTracker:
    def __init__(self):
        self.robinhood = CryptoRobinhoodHandler()
    
    def get_opening_prices(self):
        """Get the opening prices for each cryptocurrency at the start of the day."""

        print("----------------------------------------------------")
        print("Getting opening price(s)...")

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

                print(f"    • {symbol}: ${opening_price}")

            except Exception as e:
                 print(f"Error retrieving historical data for {symbol}: {e}")
    
        return opening_prices

    def monitor_prices(self):
        last_buy_time = 0

        print("----------------------------------------------------")
        print("Current price(s):")

        for symbol in CRYPTO_SYMBOLS:
            price = self.robinhood.get_crypto_price(symbol)
            if price is not None:
                current_time = time.time()

                # Check if the price is below the threshold
                if price < PRICE_THRESHOLD[symbol]:
                    print(f"    • {symbol}: ${price} (Below the threshold)")

                    # Check if the cooldown period has passed
                    if current_time - last_buy_time >= COOLDOWN_PERIOD:
                        print(f"    Placing buy order...")
                        self.robinhood.place_crypto_buy_order_under_threshold(symbol)
                        last_buy_time = current_time

                    # If the cooldown period has not passed, wait for the remaining time
                    else:
                        remaining_cooldown = COOLDOWN_PERIOD - (current_time - last_buy_time)
                        print(f"    Waiting {remaining_cooldown:.0f} seconds before next buy...")
                else:
                    print(f"    • {symbol}: ${price} (Above the threshold)")

        print("----------------------------------------------------")
        print(f"Will refresh price(s) in {PRICE_CHECK_INTERVAL} seconds...")
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





