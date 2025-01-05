import robin_stocks.robinhood as robinhood
import pyotp

from config.config import (
    ROBINHOOD_USERNAME,
    ROBINHOOD_PASSWORD,
    ROBINHOOD_OTP_SECRET
)

class RobinhoodHandler:

    def __init__(self):
        self.stocks = None
        self.tickers = None

        self.login()
        self.build_profile()

    def login(self):

        try:
            # If you have MFA enabled:
            totp  = pyotp.TOTP(ROBINHOOD_OTP_SECRET).now()
            print("Current OTP:", totp)
            login = robinhood.login(
                username=ROBINHOOD_USERNAME,
                password=ROBINHOOD_PASSWORD,
                mfa_code=totp
            )
            
            return login
        except Exception as e:
            print(f"Failed to login to Robinhood: {str(e)}")
            return None
    
    def build_profile(self):

        # store all profile holdings 
        self.stocks = robinhood.build_holdings()

        # store only tickers 
        positions = robinhood.get_open_stock_positions()
        self.tickers = [robinhood.get_symbol_by_url(item["instrument"]) for item in positions] 

    
    def search_stock_price(self, ticker):
        price = robinhood.get_latest_price(ticker,'ask_price')
        return price

    def purchase_stock_shares(self, share_amount, ticker):
        robinhood.order_buy_market(ticker,share_amount)
        
        



            






        

    

    

