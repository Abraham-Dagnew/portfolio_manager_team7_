"""
Tests for the FastAPI portfolio endpoints.
"""

import os
import sys
import unittest
from unittest.mock import patch

from fastapi import HTTPException

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import main


class FakeCursor:
    """
    Lightweight cursor double for endpoint tests.
    """

    def __init__(self, rows=None, lastrowid=None, fetchone_results=None):
        self.rows = rows or []
        self.lastrowid = lastrowid
        self.executed_queries = []
        self.fetchone_results = list(fetchone_results) if fetchone_results else []

    def execute(self, query, params=None):
        self.executed_queries.append((query, params))

    def fetchall(self):
        return self.rows

    def fetchone(self):
        if self.fetchone_results:
            return self.fetchone_results.pop(0)
        return None

    def close(self):
        return None


class FakeConnection:
    """
    Lightweight connection double for endpoint tests.

    fetchone_results is a queue consumed in the order the endpoint under
    test calls fetchone() (e.g. balance lookup, then holding lookup).
    """

    def __init__(self, rows=None, lastrowid=None, fetchone_results=None):
        self.rows = rows or []
        self.lastrowid = lastrowid
        self.fetchone_results = fetchone_results
        self.committed = False
        self.rolled_back = False

    def cursor(self, dictionary=False):
        return FakeCursor(rows=self.rows, lastrowid=self.lastrowid, fetchone_results=self.fetchone_results)

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

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
        Verifies a holding insert returns the new id and deducts its
        cost from the cash balance.
        """

        fake_connection = FakeConnection(lastrowid=7, fetchone_results=[{"cash": 5000.0}])

        with patch("main.get_connection", return_value=fake_connection), patch(
            "main.get_stock_price", return_value=150.25
        ):
            response = main.post_portfolio(
                main.HoldingCreate(
                    ticker="aapl",
                    type="stock",
                    quantity=10,
                    purchasePrice=150.25,
                    purchaseDate="2026-07-24",
                )
            )

        self.assertEqual(
            response,
            {"message": "Holding added", "id": 7, "remainingBalance": 3497.5},
        )
        self.assertTrue(fake_connection.committed)

    def test_post_portfolio_rejects_insufficient_funds(self):
        """
        Verifies a purchase costing more than the available balance is
        rejected with a clear 400 error and nothing is committed.
        """

        fake_connection = FakeConnection(fetchone_results=[{"cash": 100.0}])

        with patch("main.get_connection", return_value=fake_connection), patch(
            "main.get_stock_price", return_value=150.25
        ):
            with self.assertRaises(HTTPException) as ctx:
                main.post_portfolio(
                    main.HoldingCreate(
                        ticker="aapl",
                        type="stock",
                        quantity=10,
                        purchasePrice=150.25,
                        purchaseDate="2026-07-24",
                    )
                )

        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("Insufficient funds", ctx.exception.detail)
        self.assertFalse(fake_connection.committed)
        self.assertTrue(fake_connection.rolled_back)

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
        Verifies deleting a holding returns the confirmation message and
        refunds its cost basis to the cash balance.
        """

        fake_connection = FakeConnection(
            fetchone_results=[
                {"quantity": 10, "purchasePrice": 100.0},
                {"cash": 500.0},
            ]
        )

        with patch("main.get_connection", return_value=fake_connection):
            response = main.delete_portfolio(4)

        self.assertEqual(
            response,
            {"message": "Holding 4 deleted", "refunded": 1000.0, "remainingBalance": 1500.0},
        )
        self.assertTrue(fake_connection.committed)

    def test_delete_portfolio_not_found(self):
        """
        Verifies deleting a non-existent holding returns a clear 404
        instead of a silent no-op.
        """

        fake_connection = FakeConnection(fetchone_results=[None])

        with patch("main.get_connection", return_value=fake_connection):
            with self.assertRaises(HTTPException) as ctx:
                main.delete_portfolio(999)

        self.assertEqual(ctx.exception.status_code, 404)
        self.assertIn("999", ctx.exception.detail)
        self.assertFalse(fake_connection.committed)

    def test_get_balance_returns_cash(self):
        """
        Verifies the balance endpoint returns the current cash amount.
        """

        fake_connection = FakeConnection(fetchone_results=[{"cash": 2500.0}])

        with patch("main.get_connection", return_value=fake_connection):
            response = main.get_balance()

        self.assertEqual(response, {"cash": 2500.0})

    def test_get_balance_uninitialized_raises_clear_error(self):
        """
        Verifies a missing balance row (table not seeded) raises a
        descriptive 500 instead of a raw KeyError/None crash.
        """

        fake_connection = FakeConnection(fetchone_results=[None])

        with patch("main.get_connection", return_value=fake_connection):
            with self.assertRaises(HTTPException) as ctx:
                main.get_balance()

        self.assertEqual(ctx.exception.status_code, 500)
        self.assertIn("not initialized", ctx.exception.detail)

    def test_deposit_funds_adds_to_balance(self):
        """
        Verifies a deposit increases the cash balance by the given amount.
        """

        fake_connection = FakeConnection(fetchone_results=[{"cash": 1000.0}])

        with patch("main.get_connection", return_value=fake_connection):
            response = main.deposit_funds(main.DepositRequest(amount=500.0))

        self.assertEqual(response, {"message": "Deposited $500.00", "cash": 1500.0})
        self.assertTrue(fake_connection.committed)

    def test_withdraw_funds_subtracts_from_balance(self):
        """
        Verifies a withdrawal decreases the cash balance by the given amount.
        """

        fake_connection = FakeConnection(fetchone_results=[{"cash": 1000.0}])

        with patch("main.get_connection", return_value=fake_connection):
            response = main.withdraw_funds(main.WithdrawRequest(amount=500.0))

        self.assertEqual(response, {"message": "Withdrew $500.00", "cash": 500.0})
        self.assertTrue(fake_connection.committed)

    def test_withdraw_funds_rejects_amount_exceeding_balance(self):
        """
        Verifies a withdrawal larger than the balance is rejected with a
        clear 400 and the balance is left unchanged.
        """

        fake_connection = FakeConnection(fetchone_results=[{"cash": 100.0}])

        with patch("main.get_connection", return_value=fake_connection):
            with self.assertRaises(HTTPException) as ctx:
                main.withdraw_funds(main.WithdrawRequest(amount=500.0))

        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("Cannot withdraw", ctx.exception.detail)
        self.assertFalse(fake_connection.committed)
        self.assertTrue(fake_connection.rolled_back)

    def test_withdraw_funds_allows_exact_balance(self):
        """
        Verifies withdrawing exactly the full balance is allowed and
        leaves the balance at zero, not negative.
        """

        fake_connection = FakeConnection(fetchone_results=[{"cash": 250.0}])

        with patch("main.get_connection", return_value=fake_connection):
            response = main.withdraw_funds(main.WithdrawRequest(amount=250.0))

        self.assertEqual(response, {"message": "Withdrew $250.00", "cash": 0.0})


if __name__ == "__main__":
    unittest.main()
