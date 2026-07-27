const API_BASE_URL = "http://127.0.0.1:8000";

// GET /portfolio/performance (Person B)
export async function getPerformanceData() {
    const response = await fetch(`${API_BASE_URL}/portfolio/performance`);
    if (!response.ok) {
        throw new Error("Failed to fetch performance data");
    }
    return await response.json();
}

// GET /portfolio (Person A)
export async function getPortfolio() {
    const response = await fetch(`${API_BASE_URL}/portfolio`);
    if (!response.ok) {
        throw new Error("Failed to fetch portfolio");
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
        throw new Error("Failed to add holding");
    }
    return await response.json();
}

// DELETE /portfolio/{id} (Person C)
export async function deleteHolding(holdingId) {
    const response = await fetch(`${API_BASE_URL}/portfolio/${holdingId}`, {
        method: "DELETE"
    });
    if (!response.ok) {
        throw new Error("Failed to delete holding");
    }
    return await response.json();
}