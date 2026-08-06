import os
import sys
from unittest.mock import patch

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import services


TICKER = "TEST"


class DummyTransaction:
    def __enter__(self):
        return None

    def __exit__(self, exc_type, exc, tb):
        return False


def get_result(transactions, price):
    with patch(
        "services.persistence.transaction",
        return_value=DummyTransaction()
    ), patch(
        "services.persistence.fetch_all_transactions",
        return_value=transactions
    ), patch(
        "services.get_multiple_prices",
        return_value={TICKER: price}
    ):
        return services.get_performance()["holdings"][0]


def print_calculation(price, action, holding):
    print("\n--------------------------------")
    print(f"Current Price: ${price}")
    print(f"Action: {action}")
    print(f"Shares: {holding['quantity']}")
    print(f"Average Cost/Share: ${holding['purchasePrice']}")
    print(f"Realized P/L: ${holding['realizedGain']}")
    print(f"Unrealized P/L: ${holding['unrealizedGain']}")
    print(f"Total P/L: ${holding['totalPL']}")


@pytest.fixture
def buy_100():
    return [
        {
            "ticker": TICKER,
            "side": "buy",
            "quantity": 100,
            "purchasePrice": 10,
            "realizedGain": 0,
        }
    ]


@pytest.fixture
def after_sell_50():
    return [
        {
            "ticker": TICKER,
            "side": "buy",
            "quantity": 100,
            "purchasePrice": 10,
            "realizedGain": 0,
        },
        {
            "ticker": TICKER,
            "side": "sell",
            "quantity": 50,
            "purchasePrice": 15,
            "realizedGain": 250,
        }
    ]


@pytest.fixture
def after_second_buy():
    return [
        {
            "ticker": TICKER,
            "side": "buy",
            "quantity": 100,
            "purchasePrice": 10,
            "realizedGain": 0,
        },
        {
            "ticker": TICKER,
            "side": "sell",
            "quantity": 50,
            "purchasePrice": 15,
            "realizedGain": 250,
        },
        {
            "ticker": TICKER,
            "side": "buy",
            "quantity": 10,
            "purchasePrice": 25,
            "realizedGain": 0,
        }
    ]


@pytest.fixture
def after_sell_20():
    return [
        {
            "ticker": TICKER,
            "side": "buy",
            "quantity": 100,
            "purchasePrice": 10,
            "realizedGain": 0,
        },
        {
            "ticker": TICKER,
            "side": "sell",
            "quantity": 50,
            "purchasePrice": 15,
            "realizedGain": 250,
        },
        {
            "ticker": TICKER,
            "side": "buy",
            "quantity": 10,
            "purchasePrice": 25,
            "realizedGain": 0,
        },
        {
            "ticker": TICKER,
            "side": "sell",
            "quantity": 20,
            "purchasePrice": 15,
            "realizedGain": 50,
        }
    ]


def test_buy_100_at_10(buy_100):

    holding = get_result(buy_100, 10)

    print_calculation(10, "Buy 100", holding)

    assert holding["quantity"] == 100
    assert holding["purchasePrice"] == 10
    assert holding["realizedGain"] == 0
    assert holding["unrealizedGain"] == 0
    assert holding["totalPL"] == 0


def test_sell_50_at_15(after_sell_50):

    holding = get_result(after_sell_50, 15)

    print_calculation(15, "Sell 50", holding)

    assert holding["quantity"] == 50
    assert holding["purchasePrice"] == 10
    assert holding["realizedGain"] == 250
    assert holding["unrealizedGain"] == 250
    assert holding["totalPL"] == 500


def test_price_drop_to_10(after_sell_50):

    holding = get_result(after_sell_50, 10)

    print_calculation(10, "No Action", holding)

    assert holding["unrealizedGain"] == 0
    assert holding["totalPL"] == 250


def test_price_increase_to_20(after_sell_50):

    holding = get_result(after_sell_50, 20)

    print_calculation(20, "No Action", holding)

    assert holding["unrealizedGain"] == 500
    assert holding["totalPL"] == 750


def test_buy_10_at_25(after_second_buy):

    holding = get_result(after_second_buy, 25)

    print_calculation(25, "Buy 10", holding)

    assert holding["quantity"] == 60
    assert holding["purchasePrice"] == 12.5
    assert holding["realizedGain"] == 250
    assert holding["unrealizedGain"] == 750
    assert holding["totalPL"] == 1000


def test_price_drop_to_15(after_second_buy):

    holding = get_result(after_second_buy, 15)

    print_calculation(15, "No Action", holding)

    assert holding["unrealizedGain"] == 150
    assert holding["totalPL"] == 400


def test_price_increase_to_20_again(after_second_buy):

    holding = get_result(after_second_buy, 20)

    print_calculation(20, "No Action", holding)

    assert holding["unrealizedGain"] == 450
    assert holding["totalPL"] == 700


def test_sell_20_at_15(after_sell_20):

    holding = get_result(after_sell_20, 15)

    print_calculation(15, "Sell 20", holding)

    assert holding["quantity"] == 40
    assert holding["purchasePrice"] == 12.5
    assert holding["realizedGain"] == 300
    assert holding["unrealizedGain"] == 100
    assert holding["totalPL"] == 400


def test_final_price_at_30(after_sell_20):

    holding = get_result(after_sell_20, 30)

    print_calculation(30, "No Action", holding)

    assert holding["quantity"] == 40
    assert holding["realizedGain"] == 300
    assert holding["unrealizedGain"] == 700
    assert holding["totalPL"] == 1000


def test_final_portfolio_summary(after_sell_20):

    holding = get_result(after_sell_20, 30)

    print("\n--------------------------------")
    print("Final Portfolio Summary")
    print(f"Realized P/L: ${holding['realizedGain']}")
    print(f"Unrealized P/L: ${holding['unrealizedGain']}")
    print(f"Total P/L: ${holding['totalPL']}")

    assert holding["totalPL"] == 1000