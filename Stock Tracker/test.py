from utilities.robinhood_handler import RobinhoodHandler


if __name__ == "__main__":

    robinhood_handler = RobinhoodHandler()

    stock_prices = robinhood_handler.search_stock_prices(robinhood_handler.tickers)

    stock_price = robinhood_handler.search_stock_prices('CRSP')

    print(stock_prices)
    print(stock_price)

    