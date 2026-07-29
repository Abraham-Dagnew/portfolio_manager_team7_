"""
FastAPI application for the portfolio manager backend.
"""

from enum import Enum
from datetime import date
from fastapi import FastAPI
import uvicorn
from db_conn import get_connection
from pydantic import BaseModel, Field, field_validator
from yahoo_service import get_multiple_prices
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
    """
    Allowed asset types for portfolio holdings.
    """
    STOCK = "stock"
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


@app.get("/")
def root():
    """
    Returns a simple message that the API is running.
    """

    return {"message": "Portfolio Manager API is running"}


@app.get("/portfolio")
def get_portfolio():
    """
    Returns all portfolio rows from the database.
    """

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM portfolio")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


@app.get("/health")
def health_check():
    """
    Returns the API health status.
    """

    return {"status": "ok"}


@app.post("/portfolio")
def post_portfolio(holding: HoldingCreate):
    """
    Inserts a new holding into the portfolio table.
    """

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO portfolio (ticker, type, quantity, purchasePrice, purchaseDate)
        VALUES (%s, %s, %s, %s, %s)
    """,
        (
            holding.ticker,
            holding.type.value,
            holding.quantity,
            holding.purchasePrice,
            holding.purchaseDate.strftime("%Y-%m-%d"),
        ),
    )
    conn.commit()
    new_id = cursor.lastrowid
    cursor.close()
    conn.close()
    return {"message": "Holding added", "id": new_id}


@app.delete("/portfolio/{holding_id}")
def delete_portfolio(holding_id: int):
    """
    Deletes a holding from the portfolio table by id.
    """

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM portfolio WHERE id = %s", (holding_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return {"message": f"Holding {holding_id} deleted"}


@app.get("/portfolio/performance")
def get_portfolio_performance():
    """
    Returns each holding enriched with live price and performance figures,
    plus an aggregate summary across the whole portfolio.
    """

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM portfolio")
    holdings = cursor.fetchall()
    cursor.close()
    conn.close()

    prices = get_multiple_prices([holding["ticker"] for holding in holdings])

    enriched_holdings = []
    for holding in holdings:
        current_price = prices.get(holding["ticker"].strip().upper(), 0.0)
        performance = calculate_holding_performance(
            quantity=holding["quantity"],
            purchase_price=holding["purchasePrice"],
            current_price=current_price,
        )
        enriched_holdings.append(
            {**holding, "currentPrice": current_price, **performance}
        )

    summary = calculate_portfolio_performance(
        [
            {
                "quantity": holding["quantity"],
                "purchasePrice": holding["purchasePrice"],
                "currentPrice": holding["currentPrice"],
            }
            for holding in enriched_holdings
        ]
    )

    return {"holdings": enriched_holdings, "summary": summary}


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)