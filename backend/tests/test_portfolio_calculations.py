import os
import sys
import unittest
from unittest.mock import patch

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import services


TICKER = "TEST"


class PortfolioCalculationTests(unittest.TestCase):

    def get_performance(self, transactions, price):
        with patch(
            "services.persistence.fetch_all_transactions",
            return_value=transactions
        ), patch(
            "services.get_multiple_prices",
            return_value={TICKER: price}
        ):
            return services.get_performance()["holdings"][0]


    def print_table_row(self, price, action, cash, holding):
        print("\n--------------------------------")
        print(f"Current Price: ${price}")
        print(f"Action: {action}")
        print(f"Cash in hand: ${cash}")
        print(f"Shares: {holding['quantity']}")
        print(f"Average cost/share: ${holding['purchasePrice']}")
        print(f"Realized P/L: ${holding['realizedGain']}")
        print(f"Unrealized P/L: ${holding['unrealizedGain']}")
        print(f"Total P/L: ${holding['totalPL']}")


    def test_01_buy_100_at_10(self):
        transactions = [
            {
                "ticker": TICKER,
                "side": "buy",
                "quantity": 100,
                "purchasePrice": 10,
                "realizedGain": 0
            }
        ]

        holding = self.get_performance(transactions, 10)

        self.print_table_row(
            10,
            "Buy 100",
            0,
            holding
        )

        self.assertEqual(holding["quantity"], 100)
        self.assertEqual(holding["purchasePrice"], 10)
        self.assertEqual(holding["totalPL"], 0)


    def test_02_sell_50_at_15(self):
        transactions = [
            {"ticker": TICKER, "side": "buy", "quantity": 100, "purchasePrice": 10, "realizedGain": 0},
            {"ticker": TICKER, "side": "sell", "quantity": 50, "purchasePrice": 15, "realizedGain": 250},
        ]

        holding = self.get_performance(transactions, 15)

        self.print_table_row(
            15,
            "Sell 50",
            750,
            holding
        )

        self.assertEqual(holding["quantity"], 50)
        self.assertEqual(holding["realizedGain"], 250)
        self.assertEqual(holding["unrealizedGain"], 250)
        self.assertEqual(holding["totalPL"], 500)


    def test_03_price_check_10(self):
        transactions = [
            {"ticker": TICKER, "side": "buy", "quantity": 100, "purchasePrice": 10, "realizedGain": 0},
            {"ticker": TICKER, "side": "sell", "quantity": 50, "purchasePrice": 15, "realizedGain": 250},
        ]

        holding = self.get_performance(transactions, 10)

        self.print_table_row(
            10,
            "No action",
            750,
            holding
        )

        self.assertEqual(holding["unrealizedGain"], 0)
        self.assertEqual(holding["totalPL"], 250)


    def test_04_price_check_20(self):
        transactions = [
            {"ticker": TICKER, "side": "buy", "quantity": 100, "purchasePrice": 10, "realizedGain": 0},
            {"ticker": TICKER, "side": "sell", "quantity": 50, "purchasePrice": 15, "realizedGain": 250},
        ]

        holding = self.get_performance(transactions, 20)

        self.print_table_row(
            20,
            "No action",
            750,
            holding
        )

        self.assertEqual(holding["unrealizedGain"], 500)
        self.assertEqual(holding["totalPL"], 750)


    def test_05_buy_10_at_25(self):
        transactions = [
            {"ticker": TICKER, "side": "buy", "quantity": 100, "purchasePrice": 10, "realizedGain": 0},
            {"ticker": TICKER, "side": "sell", "quantity": 50, "purchasePrice": 15, "realizedGain": 250},
            {"ticker": TICKER, "side": "buy", "quantity": 10, "purchasePrice": 25, "realizedGain": 0},
        ]

        holding = self.get_performance(transactions, 25)

        self.print_table_row(
            25,
            "Buy 10",
            500,
            holding
        )

        self.assertEqual(holding["quantity"], 60)
        self.assertEqual(holding["purchasePrice"], 12.5)
        self.assertEqual(holding["totalPL"], 1000)


    def test_06_price_check_15(self):
        transactions = [
            {"ticker": TICKER, "side": "buy", "quantity": 100, "purchasePrice": 10, "realizedGain": 0},
            {"ticker": TICKER, "side": "sell", "quantity": 50, "purchasePrice": 15, "realizedGain": 250},
            {"ticker": TICKER, "side": "buy", "quantity": 10, "purchasePrice": 25, "realizedGain": 0},
        ]

        holding = self.get_performance(transactions, 15)

        self.print_table_row(
            15,
            "No action",
            500,
            holding
        )

        self.assertEqual(holding["unrealizedGain"], 150)
        self.assertEqual(holding["totalPL"], 400)


    def test_07_price_check_20_again(self):
        transactions = [
            {"ticker": TICKER, "side": "buy", "quantity": 100, "purchasePrice": 10, "realizedGain": 0},
            {"ticker": TICKER, "side": "sell", "quantity": 50, "purchasePrice": 15, "realizedGain": 250},
            {"ticker": TICKER, "side": "buy", "quantity": 10, "purchasePrice": 25, "realizedGain": 0},
        ]

        holding = self.get_performance(transactions, 20)

        self.print_table_row(
            20,
            "No action",
            500,
            holding
        )

        self.assertEqual(holding["unrealizedGain"], 450)
        self.assertEqual(holding["totalPL"], 700)


    def test_08_sell_20_at_15(self):
        transactions = [
            {"ticker": TICKER, "side": "buy", "quantity": 100, "purchasePrice": 10, "realizedGain": 0},
            {"ticker": TICKER, "side": "sell", "quantity": 50, "purchasePrice": 15, "realizedGain": 250},
            {"ticker": TICKER, "side": "buy", "quantity": 10, "purchasePrice": 25, "realizedGain": 0},
            {"ticker": TICKER, "side": "sell", "quantity": 20, "purchasePrice": 15, "realizedGain": 50},
        ]

        holding = self.get_performance(transactions, 15)

        self.print_table_row(
            15,
            "Sell 20",
            800,
            holding
        )

        self.assertEqual(holding["quantity"], 40)
        self.assertEqual(holding["realizedGain"], 300)
        self.assertEqual(holding["unrealizedGain"], 100)
        self.assertEqual(holding["totalPL"], 400)


    def test_09_final_price_30(self):
        transactions = [
            {"ticker": TICKER, "side": "buy", "quantity": 100, "purchasePrice": 10, "realizedGain": 0},
            {"ticker": TICKER, "side": "sell", "quantity": 50, "purchasePrice": 15, "realizedGain": 250},
            {"ticker": TICKER, "side": "buy", "quantity": 10, "purchasePrice": 25, "realizedGain": 0},
            {"ticker": TICKER, "side": "sell", "quantity": 20, "purchasePrice": 15, "realizedGain": 50},
        ]

        holding = self.get_performance(transactions, 30)

        self.print_table_row(
            30,
            "No action",
            800,
            holding
        )

        self.assertEqual(holding["quantity"], 40)
        self.assertEqual(holding["realizedGain"], 300)
        self.assertEqual(holding["unrealizedGain"], 700)
        self.assertEqual(holding["totalPL"], 1000)


if __name__ == "__main__":
    unittest.main(verbosity=2)