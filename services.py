"""
Service layer: business rules and orchestration.

Routes in main.py call these functions instead of touching the
database or third-party APIs directly. Anything here that represents
a business-rule violation (insufficient funds, unknown ticker, ...)
raises a DomainError subclass from errors.py - main.py has one global
handler that turns those into HTTP responses.
"""

from collections import defaultdict
from datetime import date

import persistence
from errors import (
    BalanceNotInitializedError,
    InsufficientFundsError,
    InsufficientSharesError,
    InvalidTickerError,
    NoTransactionsFoundError,
    TickerNotFoundError,
)
from math_logic import calculate_holding_performance, calculate_portfolio_performance
from yahoo_service import get_multiple_prices, get_stock_price, get_trending_tickers, search_symbols


def normalize_ticker(ticker: str) -> str:
    return ticker.strip().upper()


def _require_balance(cursor) -> float:
    balance = persistence.fetch_balance(cursor)
    if balance is None:
        raise BalanceNotInitializedError(
            "Balance not initialized. Run 'python db_conn.py' to set up the balance table."
        )
    return balance


def _build_holdings_snapshot(rows: list[dict]) -> list[dict]:
    """
    Aggregates raw buy/sell transactions into one net position per
    ticker, using average cost basis. A position that's fully closed
    (net quantity reaches zero) resets its cost basis, so a later buy
    starts fresh instead of blending with the closed lot.
    """

    grouped = defaultdict(lambda: {"buyQuantity": 0.0, "buyValue": 0.0})

    for row in rows:
        ticker = normalize_ticker(row["ticker"])
        side = (row.get("side") or "buy").lower()
        quantity = float(row["quantity"])
        purchase_price = float(row["purchasePrice"])

        bucket = grouped[ticker]
        if side == "sell":
            if bucket["buyQuantity"] <= 0:
                continue

            sell_quantity = min(quantity, bucket["buyQuantity"])
            average_cost = bucket["buyValue"] / bucket["buyQuantity"] if bucket["buyQuantity"] else 0.0
            bucket["buyQuantity"] = round(bucket["buyQuantity"] - sell_quantity, 4)
            bucket["buyValue"] = round(bucket["buyValue"] - (sell_quantity * average_cost), 2)

            if bucket["buyQuantity"] <= 0:
                bucket["buyQuantity"] = 0.0
                bucket["buyValue"] = 0.0
        else:
            bucket["buyQuantity"] += quantity
            bucket["buyValue"] += quantity * purchase_price

    holdings = []
    for ticker, bucket in grouped.items():
        net_quantity = round(bucket["buyQuantity"], 4)
        if net_quantity <= 0:
            continue

        average_price = round(bucket["buyValue"] / bucket["buyQuantity"], 2) if bucket["buyQuantity"] else 0.0
        holdings.append({"ticker": ticker, "averagePrice": average_price, "quantity": net_quantity})

    holdings.sort(key=lambda item: item["ticker"])

    if holdings:
        prices = get_multiple_prices([holding["ticker"] for holding in holdings])
        for holding in holdings:
            holding["currentPrice"] = prices.get(holding["ticker"], 0.0)

    return holdings


def get_transactions() -> list[dict]:
    """Returns the raw, ungrouped transaction history."""

    with persistence.transaction() as cursor:
        return persistence.fetch_all_transactions(cursor)


def get_holdings() -> list[dict]:
    """Returns one aggregated holding per ticker, with live prices."""

    with persistence.transaction() as cursor:
        rows = persistence.fetch_all_transactions(cursor)
    return _build_holdings_snapshot(rows)


def get_performance() -> dict:
    """Returns each holding enriched with performance figures, plus a portfolio-wide summary."""

    holdings = get_holdings()

    enriched_holdings = []
    for holding in holdings:
        performance = calculate_holding_performance(
            quantity=holding["quantity"],
            purchase_price=holding["averagePrice"],
            current_price=holding["currentPrice"],
        )
        enriched_holdings.append({**holding, "purchasePrice": holding["averagePrice"], **performance})

    summary = calculate_portfolio_performance(
        [
            {
                "quantity": holding["quantity"],
                "purchasePrice": holding["averagePrice"],
                "currentPrice": holding["currentPrice"],
            }
            for holding in holdings
        ]
    )

    return {"holdings": enriched_holdings, "summary": summary}


def get_balance() -> float:
    with persistence.transaction() as cursor:
        return _require_balance(cursor)


def deposit(amount: float) -> dict:
    with persistence.transaction() as cursor:
        current_balance = _require_balance(cursor)
        new_balance = round(current_balance + amount, 2)
        persistence.update_balance(cursor, new_balance)

    return {"message": f"Deposited ${amount:.2f}", "cash": new_balance}


def withdraw(amount: float) -> dict:
    with persistence.transaction() as cursor:
        current_balance = _require_balance(cursor)
        if amount > current_balance:
            raise InsufficientFundsError(
                f"Cannot withdraw ${amount:.2f}: your balance is only ${current_balance:.2f}."
            )

        new_balance = round(current_balance - amount, 2)
        persistence.update_balance(cursor, new_balance)

    return {"message": f"Withdrew ${amount:.2f}", "cash": new_balance}


def buy_holding(ticker: str, asset_type: str, quantity: float, purchase_price: float, purchase_date: str) -> dict:
    """
    Buys a holding. Rejects tickers that don't resolve to a real,
    tradeable price (cash positions are exempt, since they aren't
    backed by a market ticker), or purchases that would exceed the
    available cash balance.
    """

    clean_ticker = normalize_ticker(ticker)

    if asset_type != "cash":
        price = get_stock_price(clean_ticker)
        if price <= 0.0:
            raise InvalidTickerError(
                f"'{clean_ticker}' doesn't look like a valid, tradeable ticker. Please double-check it."
            )

    cost = round(quantity * purchase_price, 2)

    with persistence.transaction() as cursor:
        current_balance = _require_balance(cursor)
        if cost > current_balance:
            raise InsufficientFundsError(
                f"Insufficient funds: this purchase costs ${cost:.2f} but you only have ${current_balance:.2f} available."
            )

        new_id = persistence.insert_buy(cursor, clean_ticker, asset_type, quantity, purchase_price, purchase_date)

        new_balance = round(current_balance - cost, 2)
        persistence.update_balance(cursor, new_balance)

    return {"message": "Holding added", "id": new_id, "remainingBalance": new_balance}


def sell_holding(ticker: str, quantity: float) -> dict:
    """
    Sells shares of an existing holding at the live market price,
    crediting the cash balance. Rejects sales exceeding the shares
    actually owned.
    """

    clean_ticker = normalize_ticker(ticker)
    current_price = get_stock_price(clean_ticker)
    if current_price <= 0.0:
        raise InvalidTickerError(
            f"'{clean_ticker}' doesn't look like a valid, tradeable ticker. Please double-check it."
        )

    with persistence.transaction() as cursor:
        owned_quantity = persistence.fetch_net_quantity(cursor, clean_ticker)
        if quantity > owned_quantity:
            raise InsufficientSharesError(
                f"Insufficient shares: you only own {owned_quantity:.4f} shares of {clean_ticker}."
            )

        asset_type = persistence.fetch_latest_buy_type(cursor, clean_ticker)
        if asset_type is None:
            raise NoTransactionsFoundError(f"No buy transactions found for {clean_ticker}.")

        sale_value = round(float(quantity) * float(current_price), 2)
        sold_date = date.today().isoformat()
        persistence.insert_sell(cursor, clean_ticker, asset_type, quantity, current_price, sold_date)

        current_balance = _require_balance(cursor)
        new_balance = round(current_balance + sale_value, 2)
        persistence.update_balance(cursor, new_balance)

    return {
        "message": f"Sold {quantity} shares of {clean_ticker}",
        "soldValue": sale_value,
        "remainingBalance": new_balance,
    }


def lookup_price(ticker: str) -> dict:
    clean_ticker = normalize_ticker(ticker)
    price = get_stock_price(clean_ticker)

    if price <= 0.0:
        raise TickerNotFoundError(
            f"'{clean_ticker}' doesn't look like a valid, tradeable ticker. Please double-check it."
        )

    return {"ticker": clean_ticker, "price": price}


def search(query: str) -> list[dict]:
    return search_symbols(query)


def trending() -> list[dict]:
    return get_trending_tickers()
