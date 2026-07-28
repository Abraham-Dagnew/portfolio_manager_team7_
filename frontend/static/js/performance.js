import { getPerformanceData } from "./api.js";

const loadingEl = document.getElementById("performance-loading");
const errorEl = document.getElementById("performance-error");
const emptyEl = document.getElementById("performance-empty");
const contentEl = document.getElementById("performance-content");
const tableBodyEl = document.getElementById("holdings-table-body");

function formatCurrency(value) {
    return `$${Number(value).toFixed(2)}`;
}

function formatPercent(value) {
    return `${Number(value).toFixed(2)}%`;
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
            <td>${holding.quantity}</td>
            <td>${formatCurrency(holding.purchasePrice)}</td>
            <td>${formatCurrency(holding.currentPrice)}</td>
            <td>${formatCurrency(holding.totalValue)}</td>
            <td class="${gainClass}">${formatCurrency(holding.totalGain)}</td>
            <td class="${gainClass}">${formatPercent(holding.gainPercent)}</td>
        `;
        tableBodyEl.appendChild(row);
    }
}

function renderChart(holdings) {
    const ctx = document.getElementById("performance-chart");

    new Chart(ctx, {
        type: "bar",
        data: {
            labels: holdings.map((holding) => holding.ticker),
            datasets: [
                {
                    label: "Total Gain ($)",
                    data: holdings.map((holding) => holding.totalGain),
                    backgroundColor: holdings.map((holding) =>
                        holding.totalGain >= 0 ? "#2e7d32" : "#c62828"
                    ),
                },
            ],
        },
        options: {
            responsive: true,
            plugins: {
                legend: { display: false },
                title: { display: true, text: "Gain / Loss by Holding" },
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

        renderSummary(data.summary);
        renderTable(data.holdings);
        renderChart(data.holdings);
        contentEl.classList.remove("hidden");
    } catch (error) {
        loadingEl.classList.add("hidden");
        errorEl.textContent = "Could not load portfolio performance. Please try again later.";
        errorEl.classList.remove("hidden");
        console.error(error);
    }
}

loadPerformance();
