import { getPerformanceData } from "./api.js";
import { formatCurrency, formatNumber } from "./format.js";

const loadingEl = document.getElementById("performance-loading");
const errorEl = document.getElementById("performance-error");
const emptyEl = document.getElementById("performance-empty");
const contentEl = document.getElementById("performance-content");
const tableBodyEl = document.getElementById("holdings-table-body");
const lastUpdatedEl = document.getElementById("last-updated");
const analyticsGridEl = document.getElementById("analytics-grid");

const ALLOCATION_COLORS = ["#012B51", "#0E4C7A", "#1C74A8", "#4A9BC7", "#8FC1DE", "#052647", "#B0C1D1"];

function formatPercent(value) {
    return `${Number(value).toFixed(2)}%`;
}

function renderLastUpdated() {
    lastUpdatedEl.textContent = `Last updated: ${new Date().toLocaleTimeString()}`;
}

function applyGainClass(elementId, value) {
    const el = document.getElementById(elementId);
    el.textContent = formatCurrency(value);
    el.className = `card-value ${value >= 0 ? "gain-positive" : "gain-negative"}`;
}

function renderSummary(summary) {
    document.getElementById("summary-total-value").textContent = formatCurrency(summary.totalValue);
    document.getElementById("summary-total-cost").textContent = formatCurrency(summary.totalCost);

    applyGainClass("summary-realized-gain", summary.totalRealizedGain);
    applyGainClass("summary-unrealized-gain", summary.totalUnrealizedGain);
    applyGainClass("summary-total-pl", summary.totalPL);

    const percentEl = document.getElementById("summary-gain-percent");
    percentEl.textContent = formatPercent(summary.gainPercent);
    percentEl.className = `card-value ${summary.gainPercent >= 0 ? "gain-positive" : "gain-negative"}`;
}

function renderTable(holdings) {
    tableBodyEl.innerHTML = "";

    for (const holding of holdings) {
        const row = document.createElement("tr");
        const realizedClass = holding.realizedGain >= 0 ? "gain-positive" : "gain-negative";
        const unrealizedClass = holding.unrealizedGain >= 0 ? "gain-positive" : "gain-negative";

        row.innerHTML = `
            <td>${holding.ticker}</td>
            <td>${formatNumber(holding.quantity)}</td>
            <td>${formatCurrency(holding.purchasePrice)}</td>
            <td>${formatCurrency(holding.currentPrice)}</td>
            <td>${formatCurrency(holding.totalValue)}</td>
            <td class="${realizedClass}">${formatCurrency(holding.realizedGain)}</td>
            <td class="${unrealizedClass}">${formatCurrency(holding.unrealizedGain)}</td>
            <td class="${unrealizedClass}">${formatPercent(holding.gainPercent)}</td>
        `;
        tableBodyEl.appendChild(row);
    }
}

function renderGainLossChart(holdings) {
    const ctx = document.getElementById("gain-loss-chart");

    new Chart(ctx, {
        type: "bar",
        data: {
            labels: holdings.map((holding) => holding.ticker),
            datasets: [
                {
                    label: "Total Gain ($)",
                    data: holdings.map((holding) => holding.totalGain),
                    backgroundColor: holdings.map((holding) =>
                        holding.totalGain >= 0 ? "#16a34a" : "#dc2626"
                    ),
                },
            ],
        },
        options: {
            responsive: true,
            plugins: {
                legend: { display: false },
            },
        },
    });
}

function renderAllocationChart(holdings) {
    const ctx = document.getElementById("allocation-chart");

    new Chart(ctx, {
        type: "doughnut",
        data: {
            labels: holdings.map((holding) => holding.ticker),
            datasets: [
                {
                    data: holdings.map((holding) => holding.totalValue),
                    backgroundColor: holdings.map((_, index) => ALLOCATION_COLORS[index % ALLOCATION_COLORS.length]),
                },
            ],
        },
        options: {
            responsive: true,
            plugins: {
                legend: { position: "bottom" },
            },
        },
    });
}

async function loadPerformance() {
    try {
        const data = await getPerformanceData();
        loadingEl.classList.add("hidden");

        const hasHoldings = data.holdings && data.holdings.length > 0;
        const hasRealizedHistory = data.summary && data.summary.totalRealizedGain !== 0;

        // Even with no current holdings, past sells may have booked a real
        // realized gain/loss worth showing - only treat this as truly empty
        // if there's neither an open position nor any sell history.
        if (!hasHoldings && !hasRealizedHistory) {
            emptyEl.classList.remove("hidden");
            return;
        }

        renderLastUpdated();
        renderSummary(data.summary);
        renderTable(data.holdings);

        analyticsGridEl.classList.toggle("hidden", !hasHoldings);
        if (hasHoldings) {
            renderGainLossChart(data.holdings);
            renderAllocationChart(data.holdings);
        }

        contentEl.classList.remove("hidden");
    } catch (error) {
        loadingEl.classList.add("hidden");
        errorEl.textContent = "Could not load portfolio performance. Please try again later.";
        errorEl.classList.remove("hidden");
        console.error(error);
    }
}

loadPerformance();
