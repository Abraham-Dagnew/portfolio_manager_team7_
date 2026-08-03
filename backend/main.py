"""
FastAPI application for the portfolio manager backend.

This is the web layer only: request/response schemas, routes, and
translating domain errors into HTTP responses. Business rules live in
services.py; raw SQL lives in persistence.py.
"""

from datetime import date
from enum import Enum

import uvicorn
from fastapi import FastAPI, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator

import services
from errors import DomainError

app = FastAPI(title="Portfolio Manager API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5000", "http://localhost:5000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(DomainError)
def handle_domain_error(request: Request, exc: DomainError):
    """
    Single place where business-rule violations raised anywhere in the
    service layer become HTTP responses, in the same {"detail": "..."}
    shape FastAPI's own HTTPException uses, so the frontend's error
    handling doesn't need to know the difference.
    """

    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


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


@app.get("/")
def root():
    """
    Returns a simple message that the API is running.
    """

    return {"message": "Portfolio Manager API is running"}


@app.get("/health")
def health_check():
    """
    Returns the API health status.
    """

    return {"status": "ok"}


@app.get("/portfolio")
def get_portfolio():
    """
    Returns the raw transaction history from the database.
    """

    return services.get_transactions()


@app.get("/portfolio/holdings")
def get_portfolio_holdings():
    """
    Returns one aggregated holding per ticker.
    """

    return services.get_holdings()


@app.get("/stocks/search")
def search_stocks(q: str = Query(..., min_length=1, description="Ticker or company name to search for")):
    """
    Searches for real tickers matching a partial ticker or company name.
    Covers both stocks and bonds so bond holdings aren't invisible to the
    Add Holding autocomplete.
    """

    return services.search(q)


@app.get("/stocks/price/{ticker}")
def get_price(ticker: str):
    """
    Looks up the live price for a single ticker. Used by the Add Holding
    form both to verify a ticker is real and to pre-fill the purchase
    price field for the user.
    """

    return services.lookup_price(ticker)


@app.get("/stocks/trending")
def get_trending():
    """
    Returns a handful of currently most-active real tickers with their
    live price and % change since yesterday's close, for the Buy page's
    popular tickers widget.
    """

    return services.trending()


@app.get("/balance")
def get_balance():
    """
    Returns the current cash balance available to spend on new holdings.
    """

    return {"cash": services.get_balance()}


@app.post("/balance/deposit")
def deposit_funds(deposit: DepositRequest):
    """
    Adds funds to the cash balance. This is the only way the balance
    increases, since the app has no income/paycheck modeling.
    """

    return services.deposit(deposit.amount)


@app.post("/balance/withdraw")
def withdraw_funds(withdrawal: WithdrawRequest):
    """
    Removes funds from the cash balance. Rejected if it would take the
    balance below zero.
    """

    return services.withdraw(withdrawal.amount)


@app.post("/portfolio")
def post_portfolio(holding: HoldingCreate):
    """
    Buys a new holding. Rejects the request if the ticker doesn't
    resolve to a real, tradeable price, or if the purchase would
    exceed the available cash balance.
    """

    return services.buy_holding(
        ticker=holding.ticker,
        asset_type=holding.type.value,
        quantity=holding.quantity,
        purchase_price=holding.purchasePrice,
        purchase_date=holding.purchaseDate.strftime("%Y-%m-%d"),
    )


@app.post("/portfolio/sell")
def sell_portfolio(sale: SellRequest):
    """
    Records a sell transaction, verifies the user owns enough shares,
    and credits the cash balance with the current market value.
    """

    return services.sell_holding(ticker=sale.ticker, quantity=sale.quantity)


@app.get("/portfolio/performance")
def get_portfolio_performance():
    """
    Returns each holding enriched with live price and performance figures,
    plus an aggregate summary across the whole portfolio.
    """

    return services.get_performance()


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
