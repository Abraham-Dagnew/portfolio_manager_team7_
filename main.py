"""
FastAPI application for the portfolio manager backend.
"""

from enum import Enum
from datetime import date
from collections import defaultdict
from fastapi import FastAPI, HTTPException, Query
import uvicorn
from db_conn import get_connection
from pydantic import BaseModel, Field, field_validator
from yahoo_service import get_multiple_prices, get_stock_price, get_trending_tickers, search_symbols
from math_logic import calculate_holding_performance, calculate_portfolio_performance
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Portfolio Manager API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5000", "http://localhost:5000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AssetType(str, Enum):
    STOCK = "stock"
    ETF = "etf"
    BOND = "bond"
    CASH = "cash"


class HoldingCreate(BaseModel):
    """
    Request body for creating a new portfolio holding with validation.
    """

    ticker: str
    type: AssetType
    quantity: float = Field(..., gt=0, description="Quantity must be greater than zero")
    purchasePrice: float = Field(..., gt=0, description="Purchase price must be greater than zero")
    purchaseDate: date

    @field_validator("ticker")
    @classmethod
    def validate_ticker(cls, v: str) -> str:
        """
        Validates ticker is 1-5 alphabetic characters and formats to uppercase.
        """
        v = v.strip().upper()
        if not v.isalpha() or not (1 <= len(v) <= 5):
            raise ValueError("Ticker must be 1-5 alphabetic characters")
        return v

    @field_validator("type", mode="before")
    @classmethod
    def normalize_type(cls, v: str) -> str:
        if isinstance(v, str):
            return v.strip().lower()
        return v


class DepositRequest(BaseModel):
    """
    Request body for adding funds to the cash balance.
    """

    amount: float = Field(..., gt=0, description="Deposit amount must be greater than zero")


class WithdrawRequest(BaseModel):
    """
    Request body for removing funds from the cash balance.
    """

    amount: float = Field(..., gt=0, description="Withdrawal amount must be greater than zero")


class SellRequest(BaseModel):
    """
    Request body for selling shares from an existing holding.
    """

    ticker: str
    quantity: float = Field(..., gt=0, description="Quantity must be greater than zero")

    @field_validator("ticker")
    @classmethod
    def validate_ticker(cls, v: str) -> str:
        v = v.strip().upper()
        if not v.isalpha() or not (1 <= len(v) <= 5):
            raise ValueError("Ticker must be 1-5 alphabetic characters")
        return v


def normalize_ticker(ticker: str) -> str:
    return ticker.strip().upper()


def get_portfolio_rows(cursor):
    cursor.execute("SELECT * FROM portfolio ORDER BY purchaseDate ASC, id ASC")
    return cursor.fetchall()


def build_holdings_snapshot(rows):
    grouped = defaultdict(
        lambda: {
            "buyQuantity": 0.0,
            "sellQuantity": 0.0,
            "buyValue": 0.0,
        }
    )

    for row in rows:
        ticker = normalize_ticker(row["ticker"])
        side = (row.get("side") or "buy").lower()
        quantity = float(row["quantity"])
        purchase_price = float(row["purchasePrice"])

        bucket = grouped[ticker]
        if side == "sell":
            bucket["sellQuantity"] += quantity
        else:
            bucket["buyQuantity"] += quantity
            bucket["buyValue"] += quantity * purchase_price

    holdings = []
    for ticker, bucket in grouped.items():
        net_quantity = round(bucket["buyQuantity"] - bucket["sellQuantity"], 4)
        if net_quantity <= 0:
            continue

        average_price = round(bucket["buyValue"] / bucket["buyQuantity"], 2) if bucket["buyQuantity"] else 0.0
        holdings.append(
            {
                "ticker": ticker,
                "averagePrice": average_price,
                "quantity": net_quantity,
            }
        )

    holdings.sort(key=lambda item: item["ticker"])

    if holdings:
        prices = get_multiple_prices([holding["ticker"] for holding in holdings])
        for holding in holdings:
            holding["currentPrice"] = prices.get(holding["ticker"], 0.0)
    else:
        prices = {}

    return holdings


def get_net_quantity_for_ticker(cursor, ticker: str) -> float:
    cursor.execute(
        """
        SELECT COALESCE(SUM(CASE WHEN side = 'buy' THEN quantity ELSE -quantity END), 0) AS quantity
        FROM portfolio
        WHERE ticker = %s
    """,
        (ticker,),
    )
    row = cursor.fetchone()
    return float(row["quantity"] if row and row["quantity"] is not None else 0.0)


def get_buy_type_for_ticker(cursor, ticker: str):
    cursor.execute(
        """
        SELECT type
        FROM portfolio
        WHERE ticker = %s AND side = 'buy'
        ORDER BY purchaseDate ASC, id ASC
        LIMIT 1
    """,
        (ticker,),
    )
    row = cursor.fetchone()
    if row is None:
        raise HTTPException(
            status_code=404,
            detail=f"No buy transactions found for {ticker}.",
        )
    return row["type"]


def get_current_balance(cursor) -> float:
    """
    Reads the single-row cash balance. Raises a 500 with a clear message
    if the balance table hasn't been seeded yet (db_conn.py wasn't run).
    """

    cursor.execute("SELECT cash FROM balance WHERE id = 1")
    row = cursor.fetchone()
    if row is None:
        raise HTTPException(
            status_code=500,
            detail="Balance not initialized. Run 'python db_conn.py' to set up the balance table.",
        )
    return float(row["cash"])


@app.get("/")
def root():
    """
    Returns a simple message that the API is running.
    """

    return {"message": "Portfolio Manager API is running"}


@app.get("/portfolio")
def get_portfolio():
    """
    Returns the raw transaction history from the database.
    """

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        return get_portfolio_rows(cursor)
    finally:
        cursor.close()
        conn.close()


@app.get("/health")
def health_check():
    """
    Returns the API health status.
    """

    return {"status": "ok"}


@app.get("/portfolio/holdings")
def get_portfolio_holdings():
    """
    Returns one aggregated holding per ticker.
    """

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        rows = get_portfolio_rows(cursor)
        return build_holdings_snapshot(rows)
    finally:
        cursor.close()
        conn.close()


@app.get("/stocks/search")
def search_stocks(q: str = Query(..., min_length=1, description="Ticker or company name to search for")):
    """
    Searches for real tickers matching a partial ticker or company name.
    Covers both stocks and bonds so bond holdings aren't invisible to the
    Add Holding autocomplete.
    """

    return search_symbols(q)


@app.get("/stocks/price/{ticker}")
def get_price(ticker: str):
    """
    Looks up the live price for a single ticker. Used by the Add Holding
    form both to verify a ticker is real and to pre-fill the purchase
    price field for the user.
    """

    clean_ticker = ticker.strip().upper()
    price = get_stock_price(clean_ticker)

    if price <= 0.0:
        raise HTTPException(
            status_code=404,
            detail=f"'{clean_ticker}' doesn't look like a valid, tradeable ticker. Please double-check it.",
        )

    return {"ticker": clean_ticker, "price": price}


@app.get("/stocks/trending")
def get_trending():
    """
    Returns a handful of currently most-active real tickers with their
    live price and % change since yesterday's close, for the Buy page's
    popular tickers widget.
    """

    return get_trending_tickers()


@app.get("/balance")
def get_balance():
    """
    Returns the current cash balance available to spend on new holdings.
    """

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cash = get_current_balance(cursor)
    finally:
        cursor.close()
        conn.close()
    return {"cash": cash}


@app.post("/balance/deposit")
def deposit_funds(deposit: DepositRequest):
    """
    Adds funds to the cash balance. This is the only way the balance
    increases, since the app has no income/paycheck modeling.
    """

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        current_balance = get_current_balance(cursor)
        new_balance = round(current_balance + deposit.amount, 2)
        cursor.execute("UPDATE balance SET cash = %s WHERE id = 1", (new_balance,))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

    return {"message": f"Deposited ${deposit.amount:.2f}", "cash": new_balance}


@app.post("/balance/withdraw")
def withdraw_funds(withdrawal: WithdrawRequest):
    """
    Removes funds from the cash balance. Rejected if it would take the
    balance below zero.
    """

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        current_balance = get_current_balance(cursor)
        if withdrawal.amount > current_balance:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Cannot withdraw ${withdrawal.amount:.2f}: your balance is only "
                    f"${current_balance:.2f}."
                ),
            )

        new_balance = round(current_balance - withdrawal.amount, 2)
        cursor.execute("UPDATE balance SET cash = %s WHERE id = 1", (new_balance,))
        conn.commit()
    except HTTPException:
        conn.rollback()
        raise
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

    return {"message": f"Withdrew ${withdrawal.amount:.2f}", "cash": new_balance}


@app.post("/portfolio")
def post_portfolio(holding: HoldingCreate):
    """
    Inserts a new holding into the portfolio table. Rejects the request
    if the ticker doesn't resolve to a real, tradeable price (cash
    positions are exempt since they aren't backed by a market ticker),
    or if the purchase would exceed the available cash balance. On
    success, the purchase cost is deducted from the balance.
    """

    if holding.type != AssetType.CASH:
        price = get_stock_price(holding.ticker)
        if price <= 0.0:
            raise HTTPException(
                status_code=400,
                detail=f"'{holding.ticker}' doesn't look like a valid, tradeable ticker. Please double-check it.",
            )

    cost = round(holding.quantity * holding.purchasePrice, 2)

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        current_balance = get_current_balance(cursor)
        if cost > current_balance:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Insufficient funds: this purchase costs ${cost:.2f} "
                    f"but you only have ${current_balance:.2f} available."
                ),
            )

        cursor.execute(
            """
            INSERT INTO portfolio (ticker, type, side, quantity, purchasePrice, purchaseDate)
            VALUES (%s, %s, 'buy', %s, %s, %s)
        """,
            (
                holding.ticker,
                holding.type.value,
                holding.quantity,
                holding.purchasePrice,
                holding.purchaseDate.strftime("%Y-%m-%d"),
            ),
        )
        new_id = cursor.lastrowid

        new_balance = round(current_balance - cost, 2)
        cursor.execute("UPDATE balance SET cash = %s WHERE id = 1", (new_balance,))

        conn.commit()
    except HTTPException:
        conn.rollback()
        raise
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

    return {"message": "Holding added", "id": new_id, "remainingBalance": new_balance}


@app.post("/portfolio/sell")
def sell_portfolio(sale: SellRequest):
    """
    Records a sell transaction, verifies the user owns enough shares,
    and credits the cash balance with the current market value.
    """

    clean_ticker = normalize_ticker(sale.ticker)
    current_price = get_stock_price(clean_ticker)
    if current_price <= 0.0:
        raise HTTPException(
            status_code=400,
            detail=f"'{clean_ticker}' doesn't look like a valid, tradeable ticker. Please double-check it.",
        )

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        owned_quantity = get_net_quantity_for_ticker(cursor, clean_ticker)
        if sale.quantity > owned_quantity:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Insufficient shares: you only own {owned_quantity:.4f} shares of {clean_ticker}."
                ),
            )

        holding_type = get_buy_type_for_ticker(cursor, clean_ticker)
        sale_value = round(float(sale.quantity) * float(current_price), 2)
        sold_date = date.today().isoformat()

        cursor.execute(
            """
            INSERT INTO portfolio (ticker, type, side, quantity, purchasePrice, purchaseDate)
            VALUES (%s, %s, 'sell', %s, %s, %s)
        """,
            (
                clean_ticker,
                holding_type,
                sale.quantity,
                current_price,
                sold_date,
            ),
        )

        current_balance = get_current_balance(cursor)
        new_balance = round(current_balance + sale_value, 2)
        cursor.execute("UPDATE balance SET cash = %s WHERE id = 1", (new_balance,))

        conn.commit()
    except HTTPException:
        conn.rollback()
        raise
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

    return {
        "message": f"Sold {sale.quantity:.1f} shares of {clean_ticker}",
        "soldValue": sale_value,
        "remainingBalance": new_balance,
    }


@app.get("/portfolio/performance")
def get_portfolio_performance():
    """
    Returns each holding enriched with live price and performance figures,
    plus an aggregate summary across the whole portfolio.
    """

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        holdings = build_holdings_snapshot(get_portfolio_rows(cursor))
    finally:
        cursor.close()
        conn.close()

    enriched_holdings = []
    for holding in holdings:
        performance = calculate_holding_performance(
            quantity=holding["quantity"],
            purchase_price=holding["averagePrice"],
            current_price=holding["currentPrice"],
        )
        enriched_holdings.append(
            {
                **holding,
                "purchasePrice": holding["averagePrice"],
                **performance,
            }
        )

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


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)