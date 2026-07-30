"""
Yahoo Finance Market Data Service

Owner: Person 2 (market data integration)

Description:
    This module fetches live stock price data using the yfinance library.
    It supports stocks, ETFs, and bonds.
"""

import yfinance as yf


def get_stock_price(ticker: str) -> float:
    """
    Fetch current market price for a ticker.

    Returns:
        float: Current price rounded to 2 decimals.
        0.0 if ticker is invalid.
    """

    try:
        if not isinstance(ticker, str):
            ticker = str(ticker)

        clean_ticker = ticker.strip().upper()

        stock = yf.Ticker(clean_ticker)


        # First try fast_info
        try:
            price = stock.fast_info["lastPrice"]

        except Exception:

            # Fallback for ETFs / leveraged ETFs
            history = stock.history(period="1d")

            if history.empty:
                return 0.0

            price = history["Close"].iloc[-1]


        if price is None:
            return 0.0


        return round(float(price), 2)


    except Exception as e:

        print(
            f"[ERROR] Could not fetch price for '{ticker}': {e}"
        )

        return 0.0



def get_multiple_prices(tickers: list[str]) -> dict[str, float]:
    """
    Fetch current prices for multiple tickers.
    """

    prices = {}


    for symbol in tickers:

        if isinstance(symbol, str):

            clean_symbol = symbol.strip().upper()

            prices[clean_symbol] = get_stock_price(
                clean_symbol
            )


    return prices




def search_symbols(query: str, max_results: int = 8) -> list[dict]:
    """
    Search Yahoo Finance for stocks, ETFs, and bonds.

    Returns:

    [
        {
            "ticker": "LQD",
            "name": "iShares iBoxx $ Investment Grade Corporate Bond ETF",
            "type": "bond"
        }
    ]
    """


    if not isinstance(query, str):
        return []


    query = query.strip()


    if len(query) < 1:
        return []



    try:

        search_result = yf.Search(
            query,
            max_results=max_results
        )

        quotes = getattr(
            search_result,
            "quotes",
            []
        ) or []


    except Exception as e:

        print(
            f"[ERROR] Symbol search failed for '{query}': {e}"
        )

        return []



    results = []



    bond_keywords = [

        "bond",
        "treasury",
        "fixed income",
        "corporate",
        "credit",
        "aggregate",
        "high yield",
        "investment grade"

    ]



    for quote in quotes:


        symbol = quote.get("symbol")


        if not symbol:
            continue



        quote_type = (
            quote.get("quoteType")
            or ""
        ).upper()



        name = (

            quote.get("shortname")
            or quote.get("longname")
            or symbol

        ).lower()



        #
        # Convert Yahoo types into our app types
        #

        if quote_type == "ETF":


            # Detect bond ETFs
            if any(
                word in name
                for word in bond_keywords
            ):

                asset_type = "bond"

            else:

                asset_type = "etf"



        elif quote_type == "BOND":

            asset_type = "bond"



        elif quote_type == "EQUITY":

            asset_type = "stock"



        else:

            continue




        results.append({

            "ticker": symbol.strip().upper(),

            "name": (
                quote.get("shortname")
                or quote.get("longname")
                or symbol
            ),

            "type": asset_type

        })



    return results





# Standalone test

if __name__ == "__main__":


    print(
        "--- Testing Yahoo Market Data Service ---"
    )



    print("\nSingle Price Test:")

    for symbol in [
        "AAPL",
        "NVDA",
        "SOXL",
        "LQD"
    ]:

        print(
            symbol,
            "->",
            get_stock_price(symbol)
        )



    print("\nSearch Test:")


    for match in search_symbols("LQD"):

        print(
            match["ticker"],
            match["type"],
            match["name"]
        )