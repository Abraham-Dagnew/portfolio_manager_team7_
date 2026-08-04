import pytest

FRONTEND_URL = "http://127.0.0.1:5000"
API_URL = "http://127.0.0.1:8000"


@pytest.fixture(autouse=True)
def clean_database(playwright):
    request = playwright.request.new_context()

    response = request.delete(
        f"{API_URL}/test/reset"
    )

    assert response.status == 200

    yield

    request.delete(
        f"{API_URL}/test/reset"
    )

    request.dispose()


@pytest.fixture
def live_price(playwright):
    """
    Returns a helper that fetches the current live price for a ticker,
    so buy tests use real market prices instead of hardcoded values.
    """

    request = playwright.request.new_context()

    def _get(ticker):
        response = request.get(f"{API_URL}/stocks/price/{ticker}")
        assert response.status == 200, f"Could not fetch live price for {ticker}"
        return response.json()["price"]

    yield _get

    request.dispose()