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
    @patch("services.get_holdings")
    def test_portfolio_performance_under_200ms(
        self,
        mock_holdings,
        mock_holding_perf,
        mock_portfolio_perf,
    ):

        mock_holdings.return_value = [
            {
                "ticker": "AAPL",
                "quantity": 10,
                "averagePrice": 150,
                "currentPrice": 200,
            }
        ] * 500

        mock_holding_perf.return_value = {
            "gainLoss": 500,
            "gainLossPercent": 33.3,
        }

        mock_portfolio_perf.return_value = {
            "totalGainLoss": 5000,
            "totalGainLossPercent": 20,
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