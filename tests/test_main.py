"""
Tests for the FastAPI portfolio endpoints.
"""

import os
import sys
import unittest
from unittest.mock import patch

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import main


class FakeCursor:
    """
    Lightweight cursor double for endpoint tests.
    """

    def __init__(self, rows=None, lastrowid=None):
        self.rows = rows or []
        self.lastrowid = lastrowid
        self.executed_queries = []

    def execute(self, query, params=None):
        self.executed_queries.append((query, params))

    def fetchall(self):
        return self.rows

    def close(self):
        return None


class FakeConnection:
    """
    Lightweight connection double for endpoint tests.
    """

    def __init__(self, rows=None, lastrowid=None):
        self.rows = rows or []
        self.lastrowid = lastrowid
        self.committed = False

    def cursor(self, dictionary=False):
        return FakeCursor(rows=self.rows, lastrowid=self.lastrowid)

    def commit(self):
        self.committed = True

    def close(self):
        return None


class PortfolioApiTests(unittest.TestCase):
    def test_root_endpoint(self):
        """
        Verifies the root endpoint returns the running message.
        """

        response = main.root()
        self.assertEqual(response, {"message": "Portfolio Manager API is running"})

    def test_health_endpoint(self):
        """
        Verifies the health endpoint returns ok.
        """

        response = main.health_check()
        self.assertEqual(response, {"status": "ok"})

    def test_get_portfolio_returns_rows(self):
        """
        Verifies portfolio rows are returned from the mocked database.
        """

        fake_connection = FakeConnection(rows=[{"id": 1, "ticker": "AAPL"}])

        with patch("main.get_connection", return_value=fake_connection):
            response = main.get_portfolio()

        self.assertEqual(response, [{"id": 1, "ticker": "AAPL"}])

    def test_post_portfolio_inserts_and_returns_id(self):
        """
        Verifies a holding insert returns the new id.
        """

        fake_connection = FakeConnection(lastrowid=7)

        with patch("main.get_connection", return_value=fake_connection):
            response = main.post_portfolio(
                main.HoldingCreate(
                    ticker="aapl",
                    type="stock",
                    quantity=10,
                    purchasePrice=150.25,
                    purchaseDate="2026-07-24",
                )
            )

        self.assertEqual(response, {"message": "Holding added", "id": 7})
        self.assertTrue(fake_connection.committed)

    def test_get_portfolio_performance_returns_holdings_and_summary(self):
        """
        Verifies performance endpoint enriches holdings with live prices
        and returns an aggregate summary.
        """

        fake_connection = FakeConnection(
            rows=[
                {"id": 1, "ticker": "AAPL", "quantity": 10, "purchasePrice": 100.0},
                {"id": 2, "ticker": "MSFT", "quantity": 5, "purchasePrice": 200.0},
            ]
        )
        fake_prices = {"AAPL": 150.0, "MSFT": 180.0}

        with patch("main.get_connection", return_value=fake_connection), patch(
            "main.get_multiple_prices", return_value=fake_prices
        ):
            response = main.get_portfolio_performance()

        self.assertEqual(len(response["holdings"]), 2)
        self.assertEqual(response["holdings"][0]["currentPrice"], 150.0)
        self.assertEqual(response["holdings"][0]["totalGain"], 500.0)
        self.assertEqual(response["summary"]["totalValue"], 2400.0)
        self.assertEqual(response["summary"]["totalGain"], 400.0)

    def test_delete_portfolio_returns_message(self):
        """
        Verifies deleting a holding returns the confirmation message.
        """

        fake_connection = FakeConnection()

        with patch("main.get_connection", return_value=fake_connection):
            response = main.delete_portfolio(4)

        self.assertEqual(response, {"message": "Holding 4 deleted"})
        self.assertTrue(fake_connection.committed)


if __name__ == "__main__":
    unittest.main()
