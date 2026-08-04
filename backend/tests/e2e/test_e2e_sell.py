import pytest

BASE_URL = "http://127.0.0.1:8000"


@pytest.mark.e2e
def test_sell_stock_flow(playwright, live_price):
    """
    E2E:
    Deposit cash -> Buy stock at live price -> Sell stock -> Verify portfolio updates
    """

    request = playwright.request.new_context()

    deposit_response = request.post(
        f"{BASE_URL}/balance/deposit",
        data={"amount": 5000}
    )
    assert deposit_response.status == 200

    price = live_price("NVDA")

    buy_response = request.post(
        f"{BASE_URL}/portfolio",
        data={
            "ticker": "NVDA",
            "type": "stock",
            "quantity": 10,
            "purchasePrice": price,
            "purchaseDate": "2026-08-04"
        }
    )
    assert buy_response.status == 200

    sell_response = request.post(
        f"{BASE_URL}/portfolio/sell",
        data={"ticker": "NVDA", "quantity": 5}
    )
    assert sell_response.status == 200

    holdings_response = request.get(f"{BASE_URL}/portfolio/holdings")
    assert holdings_response.status == 200

    holdings = holdings_response.json()
    found = False
    for holding in holdings:
        if holding["ticker"] == "NVDA":
            found = True
            assert holding["quantity"] >= 5
            break

    request.dispose()
    assert found, "NVDA was not found after selling"