"""
Yahoo Finance Market Data Service
    
Owner: Person 2 (market data integration)
    
Description:
    This module fetches live stock price data using the 'yfinance' library. 
    It includes error handling for invalid or missing ticker symbols. 
    
Usage / Testing:
    Run directly in terminal:
    $ python yahoo_service.py   
"""
    
    
import yfinance as yf

def get_stock_price(ticker: str) -> float:
    """
    Fetches the current live market price for a given stock ticker symbol.

    Args:
        ticker (str): Stock symbol (e.g., 'AAPL', 'MSFT', 'NVDA').

    Returns:
        float: Live price rounded to 2 decimal places, or 0.0 if invalid.
    """
    try: 
        # ensure ticker is a valid string
        if not isinstance(ticker, str):
            ticker = str(ticker)
            
        # clean ticker string (remove spaces, convert to uppercase)
        clean_ticker = ticker.strip().upper()
        
        # connect to Yahoo Finance
        stock = yf.Ticker(clean_ticker)
        
        # Extract the fast current market price
        price = stock.fast_info['lastPrice']
        
        if price is None:
            return 0.0
        
        return round(float(price), 2)
    
    except Exception as e:
        print(f"[ERROR] Could not fetch price for '{ticker}': {e}")
        return 0.0
    
def get_multiple_prices(tickers: list[str]) -> dict[str, float]:
    """ 
    Fetches current price for a list of stock tickers at once.

    Args:
        tickers (list[str]): List of ticker strings (e.g., ['AAPL', 'MSFT'])

    Returns:
        dict[str, float]: Dictionary mapping each ticker to its live price.
    """
    prices = {}
    for symbol in tickers:
        if isinstance(symbol, str):
            clean_sym = symbol.strip().upper()
            prices[clean_sym] = get_stock_price(clean_sym)
    return prices

# standalone test execution 
if __name__ == "__main__":
    print("---Testing Yahoo Market Data Service---")
    
    # test 1: single ticker 
    test_symbol = "AAPL"
    price = get_stock_price(test_symbol)
    print(f"Single Ticker Test: {test_symbol} -> ${price}")
    
    # test 2: multiple tickers
    test_list = ["AAPL", "MSFT", "NVDA", "INVALID_TICKER_123"]
    print("\nMultiple Tickers Test:")
    results = get_multiple_prices(test_list)
    for symbol, val in results.items():
        print(f" -{symbol}: ${val}")
    