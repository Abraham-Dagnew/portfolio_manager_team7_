import re
import pytest
from playwright.sync_api import expect

API_URL = "http://127.0.0.1:8000"
FRONTEND_URL = "http://127.0.0.1:5000"


@pytest.mark.e2e
def test_buy_stock_flow(page, playwright):
    """
    E2E:
    Deposit cash -> Buy stock through the Buy page UI -> Verify holdings
    """

    # Add cash via API (the balance widget itself isn't what this test covers)
    request = playwright.request.new_context()

    deposit_response = request.post(
        f"{API_URL}/balance/deposit",
        data={"amount": 5000}
    )
    assert deposit_response.status == 200
    request.dispose()

    # Open the Buy page
    page.goto(f"{FRONTEND_URL}/add")

    # Search for the ticker
    page.locator("#ticker").fill("AAPL")

    # Wait for the autocomplete suggestion and select it
    suggestion = page.locator("#stockSuggestions .stock-option", has_text="AAPL").first
    expect(suggestion).to_be_visible(timeout=10000)
    suggestion.click()

    # Wait for the price to auto-populate from the live market price
    price_hint = page.locator("#purchasePriceHint")
    expect(price_hint).to_contain_text("Auto-filled", timeout=10000)

    # Enter quantity and submit
    page.locator("#quantity").fill("1")
    page.locator("#submitBtn").click()

    # Wait for the success toast
    expect(
        page.get_by_text(re.compile("holding added|purchased successfully", re.I))
    ).to_be_visible(timeout=15000)

    # Verify the holding shows up on the Holdings page
    page.goto(f"{FRONTEND_URL}/portfolio")

    search = page.locator(".topbar-search, input[placeholder*='Search']").first
    search.fill("AAPL")

    expect(page.get_by_text("AAPL").first).to_be_visible(timeout=30000)