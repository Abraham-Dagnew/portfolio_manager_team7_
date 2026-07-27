"""
Tests for the portfolio math and calculation functions.
"""

import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import math_logic


class MathLogicTests(unittest.TestCase):
    def test_calculate_total_value(self):
        self.assertEqual(math_logic.calculate_total_value(10, 150), 1500.0)

    def test_calculate_total_cost(self):
        self.assertEqual(math_logic.calculate_total_cost(10, 100), 1000.0)

    def test_calculate_total_gain_positive(self):
        self.assertEqual(math_logic.calculate_total_gain(10, 100, 150), 500.0)

    def test_calculate_total_gain_negative(self):
        self.assertEqual(math_logic.calculate_total_gain(10, 150, 100), -500.0)

    def test_calculate_gain_percent(self):
        self.assertEqual(math_logic.calculate_gain_percent(100, 150), 50.0)

    def test_calculate_gain_percent_zero_purchase_price(self):
        self.assertEqual(math_logic.calculate_gain_percent(0, 150), 0.0)

    def test_calculate_holding_performance(self):
        result = math_logic.calculate_holding_performance(
            quantity=10, purchase_price=100, current_price=150
        )
        self.assertEqual(
            result,
            {
                "totalValue": 1500.0,
                "totalCost": 1000.0,
                "totalGain": 500.0,
                "gainPercent": 50.0,
            },
        )

    def test_calculate_portfolio_performance(self):
        holdings = [
            {"quantity": 10, "purchasePrice": 100, "currentPrice": 150},
            {"quantity": 5, "purchasePrice": 200, "currentPrice": 180},
        ]
        result = math_logic.calculate_portfolio_performance(holdings)

        self.assertEqual(result["totalValue"], 2400.0)
        self.assertEqual(result["totalCost"], 2000.0)
        self.assertEqual(result["totalGain"], 400.0)
        self.assertEqual(result["gainPercent"], 20.0)

    def test_calculate_portfolio_performance_empty(self):
        result = math_logic.calculate_portfolio_performance([])
        self.assertEqual(
            result,
            {"totalValue": 0.0, "totalCost": 0.0, "totalGain": 0.0, "gainPercent": 0.0},
        )


if __name__ == "__main__":
    unittest.main()
