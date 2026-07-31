import { getPerformanceData } from "./api.js";
import { formatCurrency, formatNumber } from "./format.js";

const loadingEl = document.getElementById("performance-loading");
const errorEl = document.getElementById("performance-error");
const emptyEl = document.getElementById("performance-empty");
const contentEl = document.getElementById("performance-content");
const tableBodyEl = document.getElementById("holdings-table-body");
const lastUpdatedEl = document.getElementById("last-updated");

const ALLOCATION_COLORS = ["#7c3aed", "#4f46e5", "#16a34a", "#f59e0b", "#dc2626", "#0ea5e9", "#db2777"];

function formatPercent(value) {
    return `${Number(value).toFixed(2)}%`;
}

function renderLastUpdated() {
    lastUpdatedEl.textContent = `Last updated: ${new Date().toLocaleTimeString()}`;
}

function renderSummary(summary) {
    document.getElementById("summary-total-value").textContent = formatCurrency(summary.totalValue);
    document.getElementById("summary-total-cost").textContent = formatCurrency(summary.totalCost);
    document.getElementById("summary-total-gain").textContent = formatCurrency(summary.totalGain);
    document.getElementById("summary-gain-percent").textContent = formatPercent(summary.gainPercent);

    const gainEl = document.getElementById("summary-total-gain");
    const percentEl = document.getElementById("summary-gain-percent");
    const gainClass = summary.totalGain >= 0 ? "gain-positive" : "gain-negative";
    gainEl.className = `card-value ${gainClass}`;
    percentEl.className = `card-value ${gainClass}`;
}

function renderTable(holdings) {
    tableBodyEl.innerHTML = "";

    for (const holding of holdings) {
        const row = document.createElement("tr");
        const gainClass = holding.totalGain >= 0 ? "gain-positive" : "gain-negative";

        row.innerHTML = `
            <td>${holding.ticker}</td>
            <td>${formatNumber(holding.quantity)}</td>
            <td>${formatCurrency(holding.purchasePrice)}</td>
            <td>${formatCurrency(holding.currentPrice)}</td>
            <td>${formatCurrency(holding.totalValue)}</td>
            <td class="${gainClass}">${formatCurrency(holding.totalGain)}</td>
            <td class="${gainClass}">${formatPercent(holding.gainPercent)}</td>
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

        if (!data.holdings || data.holdings.length === 0) {
            emptyEl.classList.remove("hidden");
            return;
        }

        renderLastUpdated();
        renderSummary(data.summary);
        renderTable(data.holdings);
        renderGainLossChart(data.holdings);
        renderAllocationChart(data.holdings);
        contentEl.classList.remove("hidden");
    } catch (error) {
        loadingEl.classList.add("hidden");
        errorEl.textContent = "Could not load portfolio performance. Please try again later.";
        errorEl.classList.remove("hidden");
        console.error(error);
    }
}

loadPerformance();
