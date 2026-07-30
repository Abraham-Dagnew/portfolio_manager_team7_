const API_BASE_URL = "http://127.0.0.1:8000";

// Pulls a usable error message out of a failed fetch response.
// Handles both FastAPI's 422 validation array format and the plain
// string "detail" used by our HTTPException calls (e.g. bad ticker).
async function extractErrorMessage(response, fallback) {
    try {
        const data = await response.json();

        if (!data || !data.detail) {
            return fallback;
        }

        if (Array.isArray(data.detail)) {
            return data.detail
                .map((item) => item.msg || fallback)
                .join(", ");
        }

        return data.detail;

    } catch (_) {
        return fallback;
    }
}

// GET /portfolio/performance (Person B)
export async function getPerformanceData() {
    const response = await fetch(`${API_BASE_URL}/portfolio/performance`);
    if (!response.ok) {
        throw new Error(await extractErrorMessage(response, "Failed to fetch performance data"));
    }
    return await response.json();
}

// GET /portfolio (Person A)
export async function getPortfolio() {
    const response = await fetch(`${API_BASE_URL}/portfolio`);
    if (!response.ok) {
        throw new Error(await extractErrorMessage(response, "Failed to fetch portfolio"));
    }
    return await response.json();
}

// POST /portfolio (Person C)
export async function addHolding(holdingData) {
    const response = await fetch(`${API_BASE_URL}/portfolio`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(holdingData)
    });
    if (!response.ok) {
        throw new Error(await extractErrorMessage(response, "Failed to add holding"));
    }
    return await response.json();
}

// DELETE /portfolio/{id} (Person C)
export async function deleteHolding(holdingId) {
    const response = await fetch(`${API_BASE_URL}/portfolio/${holdingId}`, {
        method: "DELETE"
    });
    if (!response.ok) {
        throw new Error(await extractErrorMessage(response, "Failed to delete holding"));
    }
    return await response.json();
}

// GET /stocks/search?q= (Person C)
// Returns real matching tickers - both stocks and bonds - for the
// Add Holding autocomplete dropdown.
export async function searchStocks(query) {
    const response = await fetch(`${API_BASE_URL}/stocks/search?q=${encodeURIComponent(query)}`);
    if (!response.ok) {
        throw new Error(await extractErrorMessage(response, "Failed to search stocks"));
    }
    return await response.json();
}

// GET /balance
export async function getBalance() {
    const response = await fetch(`${API_BASE_URL}/balance`);
    if (!response.ok) {
        throw new Error(await extractErrorMessage(response, "Failed to fetch balance"));
    }
    return await response.json();
}

// POST /balance/deposit
export async function depositFunds(amount) {
    const response = await fetch(`${API_BASE_URL}/balance/deposit`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ amount })
    });
    if (!response.ok) {
        throw new Error(await extractErrorMessage(response, "Failed to deposit funds"));
    }
    return await response.json();
}

// POST /balance/withdraw
export async function withdrawFunds(amount) {
    const response = await fetch(`${API_BASE_URL}/balance/withdraw`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ amount })
    });
    if (!response.ok) {
        throw new Error(await extractErrorMessage(response, "Failed to withdraw funds"));
    }
    return await response.json();
}

// GET /stocks/price/{ticker} (Person C)
// Confirms a ticker actually exists and returns its live price so the
// Add Holding form can reject bad tickers and pre-fill purchase price.
export async function getStockPrice(ticker) {
    const response = await fetch(`${API_BASE_URL}/stocks/price/${encodeURIComponent(ticker)}`);
    if (!response.ok) {
        throw new Error(await extractErrorMessage(response, `Could not verify ticker '${ticker}'`));
    }
    return await response.json();
}