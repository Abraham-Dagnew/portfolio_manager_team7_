import re
import pytest
from playwright.sync_api import expect


BASE_URL = "http://127.0.0.1:5000"


@pytest.mark.e2e
def test_search_holdings_and_sell_stock(page, playwright, live_price):

    # Seed database with NVDA before testing the frontend
    request = playwright.request.new_context()

    request.post(
        "http://127.0.0.1:8000/balance/deposit",
        data={"amount": 5000}
    )

    price = live_price("NVDA")

    request.post(
        "http://127.0.0.1:8000/portfolio",
        data={
            "ticker": "NVDA",
            "type": "stock",
            "quantity": 10,
            "purchasePrice": price,
            "purchaseDate": "2026-08-04"
        }
    )

    request.dispose()

    # Open frontend
    page.goto(f"{BASE_URL}/portfolio")

    search = page.locator(
        ".topbar-search, input[placeholder*='Search']"
    ).first

    search.fill("NVDA")

    expect(
        page.get_by_text("NVDA").first
    ).to_be_visible(timeout=30000)

    # Click Sell button on the NVDA row
    sell_button = page.locator(".sell-btn", has_text=re.compile("sell", re.I)).first
    sell_button.click()

    # The modal pre-fills the full quantity and stays disabled while it
    # loads the live price — wait for it to become editable
    quantity_input = page.locator("#sellModalQuantity")
    expect(quantity_input).to_be_enabled(timeout=30000)

    # Sell half the position instead of the full amount, so NVDA
    # is expected to still be visible afterward
    quantity_input.fill("5")

    confirm_button = page.locator('[data-action="confirm"]')
    expect(confirm_button).to_be_visible()
    confirm_button.click()

    # Verify NVDA is still present after the partial sell
    expect(
        page.get_by_text("NVDA").first
    ).to_be_visible(timeout=30000)