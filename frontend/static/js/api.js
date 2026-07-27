// The base URL of your FastAPI backend running on port 8000
const API_BASE_URL = "http://127.0.0.1:8000";

// Helper function to fetch performance data
export async function getPerformanceData() {
    const response = await fetch(`${API_BASE_URL}/portfolio/performance`);
    if (!response.ok) {
        throw new Error("Failed to fetch performance data");
    }
    return await response.json();
}

// Helper function to fetch all holdings
export async function getPortfolio() {
    const response = await fetch(`${API_BASE_URL}/portfolio`);
    if (!response.ok) {
        throw new Error("Failed to fetch portfolio");
    }
    return await response.json();
}