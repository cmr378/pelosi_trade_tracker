import robin_stocks.robinhood as robinhood
from Utilities.robinhood_handler import RobinhoodHandler
from config.config import (
    PRICE_THRESHOLD,
    DIP_THRESHOLD,
    BUY_ORDER_AMOUNT
)

class CryptoRobinhoodHandler(RobinhoodHandler):
    def __init__(self):
        super().__init__()
        self.last_prices = {}

    def get_crypto_price(self, symbol):
            """Get current price for a cryptocurrency"""

            try:
                quote = robinhood.crypto.get_crypto_quote(symbol)
                current_price = float(quote['mark_price'])
                return current_price
            
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

    def check_and_handle_dip(self, symbol, current_price, last_prices):
        """Check for price dip and execute buy if threshold met"""

        last_price = last_prices[symbol]
        price_change = (current_price - last_price) / last_price        

        if price_change <= -DIP_THRESHOLD[symbol]:
            print(f"Dip detected for {symbol}! Price dropped {abs(price_change)*100:.2f}%")
            print(f"Last price: ${last_price:.2f} -> Current price: ${current_price:.2f}")
         #   self.place_crypto_buy_order(symbol)

    def place_crypto_buy_order(self, symbol):
        """Place a market buy order for crypto"""

        try:

            order = robinhood.orders.order_buy_crypto_by_quantity(
                symbol=symbol,
                quantity=BUY_ORDER_AMOUNT,
                timeInForce='gtc',
                jsonify=True
            )

            print(f"Buy order placed for {BUY_ORDER_AMOUNT} {symbol}")
            return order
        
        except Exception as e:

            print(f"Failed to place buy order for {symbol}: {e}")
            return None

    def place_crypto_buy_order_under_threshold(self, symbol):
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