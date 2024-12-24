import robin_stocks.robinhood as robinhood
import pyotp

from config.config import (
    ROBINHOOD_USERNAME,
    ROBINHOOD_PASSWORD,
    ROBINHOOD_OTP_SECRET,
    PRICE_THRESHOLD,
    BUY_ORDER_AMOUNT
)

class RobinhoodHandler:
    def __init__(self):
        self.login()

    def login(self):
        """Login to Robinhood"""

        try:
            totp = pyotp.TOTP(ROBINHOOD_OTP_SECRET).now()
            robinhood.login(ROBINHOOD_USERNAME, ROBINHOOD_PASSWORD, mfa_code=totp)
            print("Successfully logged into Robinhood!")

        except Exception as e:
            print(f"Failed to login to Robinhood: {e}")
            raise

    def get_crypto_price(self, symbol):
        """Get current price for a cryptocurrency"""

        try:
            crypto_info = robinhood.crypto.get_crypto_quote(symbol)
            return float(crypto_info['mark_price'])
        
        except Exception as e:
            print(f"Error getting price for {symbol}: {e}")
            return None
    
    def get_crypto_historicals(self, symbol, interval="hour", span="day"):
        """Get historical data for a cryptocurrency"""

        try:
            historicals = robinhood.crypto.get_crypto_historicals(
                symbol,
                interval=interval,
                span=span
            )

            return historicals
        
        except Exception as e:
            print(f"Error getting historical data for {symbol}: {e}")
            return None
    
    def trigger_buy_order_under_threshold(self, symbol):
        """Trigger a buy order if the price is below the threshold"""

        try:

            current_price = self.get_crypto_price(symbol)

            if current_price is not None and current_price < PRICE_THRESHOLD[symbol]:
                print(f"Current price of {symbol} is below the threshold. Placing buy order...")

                robinhood.orders.order_buy_crypto_by_price(symbol, BUY_ORDER_AMOUNT)
                print(f"Buy order placed for {symbol} at ${current_price}")
           
            else:
                print(f"Current price of {symbol} is above the threshold. No action taken.")
        
        except Exception as e:
            print(f"Error getting price for {symbol}: {e}")
    

    

