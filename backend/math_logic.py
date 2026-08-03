"""
Portfolio Math & Calculations

Owner: Person 3 (performance calculations)

Description:
    Pure math functions for evaluating the performance of a portfolio
    holding given its purchase price, quantity, and current market price.
    These functions have no external dependencies (no database, no network
    calls) so they can be tested and reused in isolation.
"""


def calculate_total_value(quantity: float, current_price: float) -> float:
    """
    Calculates the current total value of a holding.

    Args:
        quantity (float): Number of shares/units held.
        current_price (float): Current market price per share/unit.

    Returns:
        float: Total value, rounded to 2 decimal places.
    """

    return round(float(quantity) * float(current_price), 2)


def calculate_total_cost(quantity: float, purchase_price: float) -> float:
    """
    Calculates the total amount originally paid for a holding.

    Args:
        quantity (float): Number of shares/units held.
        purchase_price (float): Price per share/unit at purchase.

    Returns:
        float: Total cost, rounded to 2 decimal places.
    """

    return round(float(quantity) * float(purchase_price), 2)


def calculate_total_gain(quantity: float, purchase_price: float, current_price: float) -> float:
    """
    Calculates the total gain (or loss) in dollars for a holding.

    Args:
        quantity (float): Number of shares/units held.
        purchase_price (float): Price per share/unit at purchase.
        current_price (float): Current market price per share/unit.

    Returns:
        float: Total gain, rounded to 2 decimal places. Negative if a loss.
    """

    total_value = calculate_total_value(quantity, current_price)
    total_cost = calculate_total_cost(quantity, purchase_price)
    return round(total_value - total_cost, 2)


def calculate_gain_percent(purchase_price: float, current_price: float) -> float:
    """
    Calculates the percentage gain (or loss) for a holding.

    Args:
        purchase_price (float): Price per share/unit at purchase.
        current_price (float): Current market price per share/unit.

    Returns:
        float: Percentage gain, rounded to 2 decimal places. Returns 0.0
            if the purchase price is 0 (avoids division by zero).
    """

    purchase_price = float(purchase_price)
    current_price = float(current_price)

    if purchase_price == 0:
        return 0.0

    return round(((current_price - purchase_price) / purchase_price) * 100, 2)


def calculate_holding_performance(quantity: float, purchase_price: float, current_price: float) -> dict:
    """
    Calculates the full performance summary for a single holding.

    Args:
        quantity (float): Number of shares/units held.
        purchase_price (float): Price per share/unit at purchase.
        current_price (float): Current market price per share/unit.

    Returns:
        dict: totalValue, totalCost, totalGain, and gainPercent.
    """

    return {
        "totalValue": calculate_total_value(quantity, current_price),
        "totalCost": calculate_total_cost(quantity, purchase_price),
        "totalGain": calculate_total_gain(quantity, purchase_price, current_price),
        "gainPercent": calculate_gain_percent(purchase_price, current_price),
    }


def calculate_portfolio_performance(holdings: list[dict]) -> dict:
    """
    Calculates the aggregate performance across a list of holdings.

    Args:
        holdings (list[dict]): Each dict must contain "quantity",
            "purchasePrice", and "currentPrice" keys.

    Returns:
        dict: totalValue, totalCost, totalGain, and gainPercent across
            all holdings combined.
    """

    total_value = 0.0
    total_cost = 0.0

    for holding in holdings:
        total_value += calculate_total_value(holding["quantity"], holding["currentPrice"])
        total_cost += calculate_total_cost(holding["quantity"], holding["purchasePrice"])

    total_gain = round(total_value - total_cost, 2)
    gain_percent = round((total_gain / total_cost) * 100, 2) if total_cost else 0.0

    return {
        "totalValue": round(total_value, 2),
        "totalCost": round(total_cost, 2),
        "totalGain": total_gain,
        "gainPercent": gain_percent,
    }


# standalone test execution
if __name__ == "__main__":
    print("---Testing Portfolio Math Logic---")

    result = calculate_holding_performance(quantity=10, purchase_price=100, current_price=150)
    print(f"Single Holding Test: {result}")

    portfolio = [
        {"quantity": 10, "purchasePrice": 100, "currentPrice": 150},
        {"quantity": 5, "purchasePrice": 200, "currentPrice": 180},
    ]
    print(f"Portfolio Test: {calculate_portfolio_performance(portfolio)}")
