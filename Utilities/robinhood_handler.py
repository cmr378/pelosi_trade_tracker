import robin_stocks.robinhood as robinhood
import pyotp

from config.config import (
    ROBINHOOD_USERNAME,
    ROBINHOOD_PASSWORD,
    ROBINHOOD_OTP_SECRET,
)

class RobinhoodHandler:
    def __init__(self):
        self.login()

    def login(self):
        """Login to Robinhood"""

        try:

            totp = pyotp.TOTP(ROBINHOOD_OTP_SECRET).now()
            robinhood.login(ROBINHOOD_USERNAME, ROBINHOOD_PASSWORD, mfa_code=totp)
            print("----------------------------------------------------")
            print("Successfully logged into Robinhood!")

        except Exception as e:
            print(f"Failed to login to Robinhood: {e}")
            raise
    
    def logout(self):
        """Logout from Robinhood"""

        try:
            robinhood.logout()
            print("Successfully logged out of Robinhood")
        except Exception as e:
            print(f"Failed to logout from Robinhood: {e}")

    
    

