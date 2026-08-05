"""
Unit tests for the service layer (business rules).

Persistence is faked out with a simple cursor double and a fake
`transaction()` context manager, so these tests exercise real business
logic (balance checks, share-ownership checks, cost-basis aggregation)
without touching a database.
"""

import os
import sys
import unittest
from contextlib import contextmanager
from unittest.mock import patch

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import services
from errors import (
    BalanceNotInitializedError,
    InsufficientFundsError,
    InsufficientSharesError,
    InvalidTickerError,
    NoTransactionsFoundError,
    TickerNotFoundError,
)


class FakeCursor:
    def __init__(self, fetchone_results=None, fetchall_result=None, lastrowid=None):
        self.fetchone_results = list(fetchone_results) if fetchone_results else []
        self.fetchall_result = fetchall_result or []
        self.lastrowid = lastrowid
        self.executed = []

    def execute(self, query, params=None):
        self.executed.append((query, params))

    def fetchone(self):
        if self.fetchone_results:
            return self.fetchone_results.pop(0)
        return None

    def fetchall(self):
        return self.fetchall_result


def fake_transaction(cursor):
    @contextmanager
    def _transaction():
        yield cursor

    return _transaction


class TransactionsAndHoldingsTests(unittest.TestCase):
    def test_get_transactions_returns_raw_rows(self):
        cursor = FakeCursor(fetchall_result=[{"id": 1, "ticker": "AAPL"}])

        with patch("services.persistence.transaction", fake_transaction(cursor)):
            result = services.get_transactions()

        self.assertEqual(result, [{"id": 1, "ticker": "AAPL"}])

    def test_get_holdings_aggregates_buys_and_sells(self):
        cursor = FakeCursor(
            fetchall_result=[
                {"id": 1, "ticker": "AAPL", "side": "buy", "quantity": 10, "purchasePrice": 100.0, "purchaseDate": "2026-07-20"},
                {"id": 2, "ticker": "AAPL", "side": "buy", "quantity": 5, "purchasePrice": 120.0, "purchaseDate": "2026-07-21"},
                {"id": 3, "ticker": "AAPL", "side": "sell", "quantity": 3, "purchasePrice": 130.0, "purchaseDate": "2026-07-22"},
                {"id": 4, "ticker": "MSFT", "side": "buy", "quantity": 2, "purchasePrice": 200.0, "purchaseDate": "2026-07-22"},
            ]
        )

        with patch("services.persistence.transaction", fake_transaction(cursor)), patch(
            "services.get_multiple_prices", return_value={"AAPL": 150.0, "MSFT": 250.0}
        ):
            result = services.get_holdings()

        self.assertEqual(
            result,
            [
                {"ticker": "AAPL", "averagePrice": 106.67, "quantity": 12.0, "realizedGain": 0.0, "currentPrice": 150.0},
                {"ticker": "MSFT", "averagePrice": 200.0, "quantity": 2.0, "realizedGain": 0.0, "currentPrice": 250.0},
            ],
        )

    def test_get_holdings_resets_cost_basis_after_full_close(self):
        cursor = FakeCursor(
            fetchall_result=[
                {"id": 1, "ticker": "INTC", "side": "buy", "quantity": 10, "purchasePrice": 80.0, "purchaseDate": "2026-07-20"},
                {"id": 2, "ticker": "INTC", "side": "sell", "quantity": 10, "purchasePrice": 95.0, "purchaseDate": "2026-07-21"},
                {"id": 3, "ticker": "INTC", "side": "buy", "quantity": 4, "purchasePrice": 90.71, "purchaseDate": "2026-07-22"},
            ]
        )

        with patch("services.persistence.transaction", fake_transaction(cursor)), patch(
            "services.get_multiple_prices", return_value={"INTC": 92.0}
        ):
            result = services.get_holdings()

        self.assertEqual(
            result,
            [{"ticker": "INTC", "averagePrice": 90.71, "quantity": 4.0, "realizedGain": 0.0, "currentPrice": 92.0}],
        )

    def test_get_holdings_carries_realized_gain_from_past_sells(self):
        cursor = FakeCursor(
            fetchall_result=[
                {"id": 1, "ticker": "AAPL", "side": "buy", "quantity": 10, "purchasePrice": 100.0, "purchaseDate": "2026-07-20", "realizedGain": None},
                {"id": 2, "ticker": "AAPL", "side": "sell", "quantity": 4, "purchasePrice": 120.0, "purchaseDate": "2026-07-21", "realizedGain": 80.0},
            ]
        )

        with patch("services.persistence.transaction", fake_transaction(cursor)), patch(
            "services.get_multiple_prices", return_value={"AAPL": 130.0}
        ):
            result = services.get_holdings()

        self.assertEqual(
            result,
            [{"ticker": "AAPL", "averagePrice": 100.0, "quantity": 6.0, "realizedGain": 80.0, "currentPrice": 130.0}],
        )

    def test_get_performance_returns_holdings_and_summary(self):
        cursor = FakeCursor(
            fetchall_result=[
                {"id": 1, "ticker": "AAPL", "side": "buy", "quantity": 10, "purchasePrice": 100.0, "purchaseDate": "2026-07-20", "realizedGain": None},
                {"id": 2, "ticker": "MSFT", "side": "buy", "quantity": 5, "purchasePrice": 200.0, "purchaseDate": "2026-07-21", "realizedGain": None},
            ]
        )

        with patch("services.persistence.transaction", fake_transaction(cursor)), patch(
            "services.get_multiple_prices", return_value={"AAPL": 150.0, "MSFT": 180.0}
        ):
            response = services.get_performance()

        self.assertEqual(len(response["holdings"]), 2)
        self.assertEqual(response["holdings"][0]["currentPrice"], 150.0)
        self.assertEqual(response["holdings"][0]["totalGain"], 500.0)
        self.assertEqual(response["holdings"][0]["unrealizedGain"], 500.0)
        self.assertEqual(response["holdings"][0]["totalPL"], 500.0)
        self.assertEqual(response["summary"]["totalValue"], 2400.0)
        self.assertEqual(response["summary"]["totalGain"], 400.0)
        self.assertEqual(response["summary"]["totalRealizedGain"], 0.0)
        self.assertEqual(response["summary"]["totalUnrealizedGain"], 400.0)
        self.assertEqual(response["summary"]["totalPL"], 400.0)

    def test_get_performance_includes_realized_gain_from_closed_positions(self):
        """
        A fully-closed position (net quantity 0) shouldn't appear in
        holdings, but its realized gain must still count toward the
        portfolio-wide total.
        """

        cursor = FakeCursor(
            fetchall_result=[
                {"id": 1, "ticker": "TSLA", "side": "buy", "quantity": 5, "purchasePrice": 200.0, "purchaseDate": "2026-07-20", "realizedGain": None},
                {"id": 2, "ticker": "TSLA", "side": "sell", "quantity": 5, "purchasePrice": 250.0, "purchaseDate": "2026-07-21", "realizedGain": 250.0},
            ]
        )

        with patch("services.persistence.transaction", fake_transaction(cursor)), patch(
            "services.get_multiple_prices", return_value={}
        ):
            response = services.get_performance()

        self.assertEqual(response["holdings"], [])
        self.assertEqual(response["summary"]["totalRealizedGain"], 250.0)
        self.assertEqual(response["summary"]["totalPL"], 250.0)


class BalanceServiceTests(unittest.TestCase):
    def test_get_balance_returns_cash(self):
        cursor = FakeCursor(fetchone_results=[{"cash": 2500.0}])

        with patch("services.persistence.transaction", fake_transaction(cursor)):
            self.assertEqual(services.get_balance(), 2500.0)

    def test_get_balance_uninitialized_raises_clear_error(self):
        cursor = FakeCursor(fetchone_results=[None])

        with patch("services.persistence.transaction", fake_transaction(cursor)):
            with self.assertRaises(BalanceNotInitializedError) as ctx:
                services.get_balance()

        self.assertEqual(ctx.exception.status_code, 500)
        self.assertIn("not initialized", ctx.exception.message)

    def test_deposit_adds_to_balance(self):
        cursor = FakeCursor(fetchone_results=[{"cash": 1000.0}])

        with patch("services.persistence.transaction", fake_transaction(cursor)):
            response = services.deposit(500.0)

        self.assertEqual(response, {"message": "Deposited $500.00", "cash": 1500.0})

    def test_withdraw_subtracts_from_balance(self):
        cursor = FakeCursor(fetchone_results=[{"cash": 1000.0}])

        with patch("services.persistence.transaction", fake_transaction(cursor)):
            response = services.withdraw(500.0)

        self.assertEqual(response, {"message": "Withdrew $500.00", "cash": 500.0})

    def test_withdraw_rejects_amount_exceeding_balance(self):
        cursor = FakeCursor(fetchone_results=[{"cash": 100.0}])

        with patch("services.persistence.transaction", fake_transaction(cursor)):
            with self.assertRaises(InsufficientFundsError) as ctx:
                services.withdraw(500.0)

        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("Cannot withdraw", ctx.exception.message)

    def test_withdraw_allows_exact_balance(self):
        cursor = FakeCursor(fetchone_results=[{"cash": 250.0}])

        with patch("services.persistence.transaction", fake_transaction(cursor)):
            response = services.withdraw(250.0)

        self.assertEqual(response, {"message": "Withdrew $250.00", "cash": 0.0})


class BuySellServiceTests(unittest.TestCase):
    def test_buy_holding_inserts_and_deducts_balance(self):
        cursor = FakeCursor(fetchone_results=[{"cash": 5000.0}], lastrowid=7)

        with patch("services.persistence.transaction", fake_transaction(cursor)), patch(
            "services.get_stock_price", return_value=150.25
        ):
            response = services.buy_holding("aapl", "stock", 10, 150.25, "2026-07-24")

        self.assertEqual(
            response,
            {"message": "Holding added", "id": 7, "remainingBalance": 3497.5},
        )

    def test_buy_holding_rejects_invalid_ticker(self):
        with patch("services.get_stock_price", return_value=0.0):
            with self.assertRaises(InvalidTickerError):
                services.buy_holding("zzzzz", "stock", 10, 150.25, "2026-07-24")

    def test_buy_holding_rejects_insufficient_funds(self):
        cursor = FakeCursor(fetchone_results=[{"cash": 100.0}])

        with patch("services.persistence.transaction", fake_transaction(cursor)), patch(
            "services.get_stock_price", return_value=150.25
        ):
            with self.assertRaises(InsufficientFundsError) as ctx:
                services.buy_holding("aapl", "stock", 10, 150.25, "2026-07-24")

        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("Insufficient funds", ctx.exception.message)

    def test_sell_holding_records_sale_and_credits_balance(self):
        cursor = FakeCursor(
            fetchall_result=[
                {"side": "buy", "quantity": 10, "purchasePrice": 100.0},
            ],
            fetchone_results=[
                {"cash": 500.0},
            ],
        )
        # fetch_ticker_history uses fetchall() to compute owned quantity and
        # average cost; fetch_latest_buy_type is patched directly below since
        # it isn't exercised through the fake cursor in this test.

        with patch("services.persistence.transaction", fake_transaction(cursor)), patch(
            "services.get_stock_price", return_value=120.0
        ), patch("services.persistence.fetch_latest_buy_type", return_value="stock"):
            response = services.sell_holding("aapl", 3)

        self.assertEqual(
            response,
            {
                "message": "Sold 3 shares of AAPL",
                "soldValue": 360.0,
                "realizedGain": 60.0,
                "remainingBalance": 860.0,
            },
        )

    def test_sell_holding_rejects_insufficient_shares(self):
        cursor = FakeCursor(
            fetchall_result=[
                {"side": "buy", "quantity": 1.5, "purchasePrice": 100.0},
            ]
        )

        with patch("services.persistence.transaction", fake_transaction(cursor)), patch(
            "services.get_stock_price", return_value=120.0
        ):
            with self.assertRaises(InsufficientSharesError) as ctx:
                services.sell_holding("AAPL", 5)

        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("Insufficient shares", ctx.exception.message)

    def test_sell_holding_rejects_invalid_ticker(self):
        with patch("services.get_stock_price", return_value=0.0):
            with self.assertRaises(InvalidTickerError):
                services.sell_holding("zzzzz", 1)

    def test_sell_holding_rejects_ticker_with_no_buy_history(self):
        cursor = FakeCursor(
            fetchall_result=[
                {"side": "buy", "quantity": 10, "purchasePrice": 100.0},
            ]
        )

        with patch("services.persistence.transaction", fake_transaction(cursor)), patch(
            "services.get_stock_price", return_value=120.0
        ), patch("services.persistence.fetch_latest_buy_type", return_value=None):
            with self.assertRaises(NoTransactionsFoundError):
                services.sell_holding("AAPL", 3)


class MarketDataServiceTests(unittest.TestCase):
    def test_lookup_price_returns_ticker_and_price(self):
        with patch("services.get_stock_price", return_value=308.91):
            self.assertEqual(services.lookup_price("aapl"), {"ticker": "AAPL", "price": 308.91})

    def test_lookup_price_raises_not_found_for_invalid_ticker(self):
        with patch("services.get_stock_price", return_value=0.0):
            with self.assertRaises(TickerNotFoundError) as ctx:
                services.lookup_price("zzzzz")

        self.assertEqual(ctx.exception.status_code, 404)

    def test_search_delegates_to_yahoo_service(self):
        fake_results = [{"ticker": "AAPL", "name": "Apple Inc.", "type": "stock"}]

        with patch("services.search_symbols", return_value=fake_results) as mock_search:
            result = services.search("aap")

        mock_search.assert_called_once_with("aap")
        self.assertEqual(result, fake_results)

    def test_trending_delegates_to_yahoo_service(self):
        fake_movers = [{"ticker": "AAPL", "name": "Apple Inc.", "price": 308.91, "changePercent": -7.35}]

        with patch("services.get_trending_tickers", return_value=fake_movers):
            self.assertEqual(services.trending(), fake_movers)


if __name__ == "__main__":
    unittest.main()
