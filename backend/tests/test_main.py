"""
Integration tests for the FastAPI app.

These go through the real HTTP layer (routing, Pydantic request
validation, and the global DomainError -> HTTP response handler) via
FastAPI's TestClient, with the service layer mocked out. Business
logic itself is covered by tests/test_services.py - this file verifies
the web layer wires everything together correctly.
"""

import os
import sys
import unittest
from unittest.mock import patch

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from fastapi.testclient import TestClient

import main
from errors import (
    BalanceNotInitializedError,
    InsufficientFundsError,
    InsufficientSharesError,
    InvalidTickerError,
    TickerNotFoundError,
)

client = TestClient(main.app)


class RootAndHealthTests(unittest.TestCase):
    def test_root_endpoint(self):
        response = client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "Portfolio Manager API is running"})

    def test_health_endpoint(self):
        response = client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})


class PortfolioRouteTests(unittest.TestCase):
    def test_get_portfolio_returns_service_data(self):
        with patch("main.services.get_transactions", return_value=[{"id": 1, "ticker": "AAPL"}]):
            response = client.get("/portfolio")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [{"id": 1, "ticker": "AAPL"}])

    def test_get_portfolio_holdings_returns_service_data(self):
        fake_holdings = [{"ticker": "AAPL", "averagePrice": 150.0, "quantity": 10.0, "currentPrice": 160.0}]

        with patch("main.services.get_holdings", return_value=fake_holdings):
            response = client.get("/portfolio/holdings")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), fake_holdings)

    def test_post_portfolio_success_calls_service_with_parsed_fields(self):
        fake_response = {"message": "Holding added", "id": 7, "remainingBalance": 3497.5}

        with patch("main.services.buy_holding", return_value=fake_response) as mock_buy:
            response = client.post(
                "/portfolio",
                json={
                    "ticker": "aapl",
                    "type": "stock",
                    "quantity": 10,
                    "purchasePrice": 150.25,
                    "purchaseDate": "2026-01-15",
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), fake_response)
        mock_buy.assert_called_once_with(
            ticker="AAPL",
            asset_type="stock",
            quantity=10.0,
            purchase_price=150.25,
            purchase_date="2026-01-15",
        )

    def test_post_portfolio_rejects_invalid_request_body(self):
        """
        Verifies Pydantic validation (negative quantity) returns 422
        without ever reaching the service layer.
        """

        with patch("main.services.buy_holding") as mock_buy:
            response = client.post(
                "/portfolio",
                json={
                    "ticker": "AAPL",
                    "type": "stock",
                    "quantity": -5,
                    "purchasePrice": 150.25,
                    "purchaseDate": "2026-01-15",
                },
            )

        self.assertEqual(response.status_code, 422)
        mock_buy.assert_not_called()

    def test_post_portfolio_translates_domain_error_to_400(self):
        with patch(
            "main.services.buy_holding",
            side_effect=InsufficientFundsError("Insufficient funds: this purchase costs $1502.50 but you only have $100.00 available."),
        ):
            response = client.post(
                "/portfolio",
                json={
                    "ticker": "AAPL",
                    "type": "stock",
                    "quantity": 10,
                    "purchasePrice": 150.25,
                    "purchaseDate": "2026-01-15",
                },
            )

        self.assertEqual(response.status_code, 400)
        self.assertIn("Insufficient funds", response.json()["detail"])

    def test_sell_portfolio_translates_domain_error_to_400(self):
        with patch(
            "main.services.sell_holding",
            side_effect=InsufficientSharesError("Insufficient shares: you only own 1.5000 shares of AAPL."),
        ):
            response = client.post("/portfolio/sell", json={"ticker": "AAPL", "quantity": 5})

        self.assertEqual(response.status_code, 400)
        self.assertIn("Insufficient shares", response.json()["detail"])

    def test_get_portfolio_performance_returns_service_data(self):
        fake_performance = {"holdings": [], "summary": {"totalValue": 0.0}}

        with patch("main.services.get_performance", return_value=fake_performance):
            response = client.get("/portfolio/performance")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), fake_performance)


class MarketDataRouteTests(unittest.TestCase):
    def test_get_price_success(self):
        with patch("main.services.lookup_price", return_value={"ticker": "AAPL", "price": 308.91}):
            response = client.get("/stocks/price/AAPL")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"ticker": "AAPL", "price": 308.91})

    def test_get_price_translates_not_found_to_404(self):
        with patch("main.services.lookup_price", side_effect=TickerNotFoundError("'ZZZZZ' doesn't look like a valid, tradeable ticker.")):
            response = client.get("/stocks/price/ZZZZZ")

        self.assertEqual(response.status_code, 404)

    def test_get_trending_returns_service_data(self):
        fake_movers = [{"ticker": "AAPL", "name": "Apple Inc.", "price": 308.91, "changePercent": -7.35}]

        with patch("main.services.trending", return_value=fake_movers):
            response = client.get("/stocks/trending")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), fake_movers)

    def test_search_stocks_requires_query_param(self):
        response = client.get("/stocks/search")
        self.assertEqual(response.status_code, 422)


class BalanceRouteTests(unittest.TestCase):
    def test_get_balance_returns_cash(self):
        with patch("main.services.get_balance", return_value=2500.0):
            response = client.get("/balance")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"cash": 2500.0})

    def test_get_balance_translates_uninitialized_error_to_500(self):
        with patch(
            "main.services.get_balance",
            side_effect=BalanceNotInitializedError("Balance not initialized. Run 'python db_conn.py' to set up the balance table."),
        ):
            response = client.get("/balance")

        self.assertEqual(response.status_code, 500)

    def test_deposit_rejects_non_positive_amount(self):
        with patch("main.services.deposit") as mock_deposit:
            response = client.post("/balance/deposit", json={"amount": 0})

        self.assertEqual(response.status_code, 422)
        mock_deposit.assert_not_called()

    def test_withdraw_translates_domain_error_to_400(self):
        with patch(
            "main.services.withdraw",
            side_effect=InsufficientFundsError("Cannot withdraw $500.00: your balance is only $100.00."),
        ):
            response = client.post("/balance/withdraw", json={"amount": 500})

        self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()
