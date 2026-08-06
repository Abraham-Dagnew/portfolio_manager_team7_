import os
import sys
import time
import unittest
from unittest.mock import patch

# Allow importing backend modules
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import services


class DatabasePerformanceTests(unittest.TestCase):

    @patch("services.persistence.fetch_all_transactions")
    @patch("services.persistence.transaction")
    @patch("services.get_multiple_prices")
    def test_get_holdings_under_200ms(
        self,
        mock_prices,
        mock_transaction,
        mock_fetch_transactions,
    ):
        """
        Benchmarks local holdings aggregation.
        """

        mock_cursor = object()

        class DummyTransaction:
            def __enter__(self):
                return mock_cursor

            def __exit__(self, exc_type, exc, tb):
                return False

        mock_transaction.return_value = DummyTransaction()

        mock_fetch_transactions.return_value = [
            {
                "ticker": "AAPL",
                "side": "buy",
                "quantity": 10,
                "purchasePrice": 150,
            }
        ] * 500

        mock_prices.return_value = {
            "AAPL": 200
        }

        start = time.perf_counter()

        services.get_holdings()

        elapsed = time.perf_counter() - start

        print(f"Holdings execution: {elapsed*1000:.2f} ms")

        self.assertLess(elapsed, 0.2)


class PortfolioPerformanceTests(unittest.TestCase):

    @patch("services.calculate_portfolio_performance")
    @patch("services.calculate_holding_performance")
    @patch("services._total_realized_gain")
    @patch("services._build_holdings_snapshot")
    @patch("services.persistence.fetch_all_transactions")
    @patch("services.persistence.transaction")
    def test_portfolio_performance_under_200ms(
        self,
        mock_transaction,
        mock_fetch_transactions,
        mock_snapshot,
        mock_total_realized,
        mock_holding_perf,
        mock_portfolio_perf,
    ):

        mock_cursor = object()

        class DummyTransaction:
            def __enter__(self):
                return mock_cursor

            def __exit__(self, exc_type, exc, tb):
                return False

        mock_transaction.return_value = DummyTransaction()
        mock_fetch_transactions.return_value = []

        mock_snapshot.return_value = [
            {
                "ticker": "AAPL",
                "quantity": 10,
                "averagePrice": 150,
                "realizedGain": 0.0,
                "currentPrice": 200,
            }
        ] * 500

        mock_total_realized.return_value = 0.0

        mock_holding_perf.return_value = {
            "totalValue": 2000.0,
            "totalCost": 1500.0,
            "totalGain": 500.0,
            "gainPercent": 33.3,
        }

        mock_portfolio_perf.return_value = {
            "totalValue": 1000000.0,
            "totalCost": 750000.0,
            "totalGain": 250000.0,
            "gainPercent": 33.3,
        }

        start = time.perf_counter()

        services.get_performance()

        elapsed = time.perf_counter() - start

        print(f"Portfolio execution: {elapsed*1000:.2f} ms")

        self.assertLess(elapsed, 0.2)


class PriceLookupPerformanceTests(unittest.TestCase):

    @patch("services.get_stock_price")
    def test_price_lookup_under_2_5_seconds(self, mock_price):

        mock_price.return_value = 215.35

        start = time.perf_counter()

        services.lookup_price("AAPL")

        elapsed = time.perf_counter() - start

        print(f"Price lookup: {elapsed:.3f} sec")

        self.assertLess(elapsed, 2.5)


class TrendingPerformanceTests(unittest.TestCase):

    @patch("services.get_trending_tickers")
    def test_trending_under_2_5_seconds(self, mock_trending):

        mock_trending.return_value = [
            {"symbol": "AAPL"},
            {"symbol": "MSFT"},
            {"symbol": "NVDA"},
        ]

        start = time.perf_counter()

        services.trending()

        elapsed = time.perf_counter() - start

        print(f"Trending execution: {elapsed:.3f} sec")

        self.assertLess(elapsed, 2.5)


class SearchPerformanceTests(unittest.TestCase):

    @patch("services.search_symbols")
    def test_search_under_2_5_seconds(self, mock_search):

        mock_search.return_value = [
            {"symbol": "AAPL"}
        ]

        start = time.perf_counter()

        services.search("apple")

        elapsed = time.perf_counter() - start

        print(f"Search execution: {elapsed:.3f} sec")

        self.assertLess(elapsed, 2.5)


if __name__ == "__main__":
    unittest.main()