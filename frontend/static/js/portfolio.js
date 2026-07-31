import { getPortfolio, deleteHolding, getStockPrice } from './api.js';
import { showToast } from './toast.js';
import { refreshBalance } from './balance.js';
import { formatCurrency, formatNumber } from './format.js';

document.addEventListener("DOMContentLoaded", async () => {

    const container = document.getElementById("holdings-container");

    // Prevent crash if JS loads on another page
    if (!container) {
        console.error("holdings-container not found");
        return;
    }

    try {

        const holdings = await getPortfolio();

        if (!holdings || holdings.length === 0) {

            container.innerHTML = `
                <div class="empty-state card p-4 text-center">
                    <h3>No holdings found</h3>
                    <p class="text-muted mb-0">
                        Click "Buy" to start building your portfolio.
                    </p>
                </div>
            `;

            return;
        }


        let html = `
            <div class="card shadow-sm border-0">
                <div class="table-responsive">

                    <table class="table align-middle mb-0">

                        <thead>
                            <tr>
                                <th>Ticker</th>
                                <th>Type</th>
                                <th>Quantity</th>
                                <th>Purchase Price</th>
                                <th>Purchase Date</th>
                                <th>Actions</th>
                            </tr>
                        </thead>

                        <tbody>
        `;


        holdings.forEach(item => {

            html += `
                <tr data-ticker="${item.ticker.toLowerCase()}">

                    <td>
                        <strong>${item.ticker}</strong>
                    </td>

                    <td>
                        <span class="badge bg-light text-dark">
                            ${item.type}
                        </span>
                    </td>

                    <td>${formatNumber(item.quantity)}</td>

                    <td>
                        ${formatCurrency(item.purchasePrice)}
                    </td>

                    <td>
                        ${item.purchaseDate}
                    </td>

                    <td>

                        <button
                            class="sell-btn btn btn-sm btn-outline-danger"
                            data-id="${item.id}"
                            data-ticker="${item.ticker}"
                            data-type="${item.type}"
                            data-quantity="${item.quantity}"
                            data-price="${item.purchasePrice}">
                            Sell
                        </button>

                    </td>

                </tr>
            `;

        });


        html += `
                        </tbody>

                    </table>

                </div>
            </div>
        `;


        container.innerHTML = html;



        // SELL FUNCTIONALITY WITH GAIN/LOSS PREVIEW

        document.querySelectorAll(".sell-btn")
            .forEach(button => {

                button.addEventListener("click", async (e) => {

                    const id = e.target.dataset.id;
                    const ticker = e.target.dataset.ticker;
                    const type = e.target.dataset.type;
                    const quantity = parseFloat(e.target.dataset.quantity) || 0;
                    const purchasePrice = parseFloat(e.target.dataset.price) || 0;
                    const row = e.target.closest("tr");

                    e.target.disabled = true;
                    e.target.textContent = "Checking price...";

                    let confirmMsg = `Are you sure you want to sell ${quantity} share(s) of ${ticker}?`;

                    // If it's a stock/ETF, fetch live market price to compute gain/loss
                    if (type !== "Cash") {
                        try {
                            const market = await getStockPrice(ticker);
                            const currentPrice = market.price;
                            const totalCost = purchasePrice * quantity;
                            const currentValue = currentPrice * quantity;
                            const profitLoss = currentValue - totalCost;

                            const profitLossFormatted = formatCurrency(Math.abs(profitLoss));
                            const sign = profitLoss >= 0 ? "+" : "-";
                            const status = profitLoss >= 0 ? "GAIN" : "LOSS";

                            confirmMsg = `Selling ${quantity} share(s) of ${ticker}:\n` +
                                `- Purchase Price: ${formatCurrency(purchasePrice)}\n` +
                                `- Current Market Price: ${formatCurrency(currentPrice)}\n` +
                                `- Estimated Realized ${status}: ${sign}${profitLossFormatted}\n\n` +
                                `Are you sure you want to proceed?`;
                        } catch (err) {
                            // Fallback if price API fails or ticker is missing
                            confirmMsg = `Are you sure you want to sell ${quantity} share(s) of ${ticker}?`;
                        }
                    }

                    e.target.textContent = "Sell";
                    e.target.disabled = false;

                    if (!confirm(confirmMsg)) {
                        return;
                    }

                    e.target.disabled = true;
                    e.target.textContent = "Selling...";

                    try {

                        await deleteHolding(id);

                        row.remove();

                        showToast(
                            `Sold ${ticker} successfully!`,
                            "success"
                        );

                        refreshBalance();

                        const remaining =
                            document.querySelectorAll(
                                "#holdings-container tbody tr"
                            );

                        if (remaining.length === 0) {
                            container.innerHTML = `
                                <div class="empty-state card p-4 text-center">
                                    <h3>No holdings found</h3>
                                    <p class="text-muted mb-0">
                                        Click "Buy" to start building your portfolio.
                                    </p>
                                </div>
                            `;
                        }

                    } catch(error) {

                        showToast(
                            error.message || "Failed to sell holding",
                            "error"
                        );

                        e.target.disabled = false;
                        e.target.textContent = "Sell";

                    }

                });

            });



        // SEARCH FUNCTIONALITY

        const searchInput =
            document.querySelector(".topbar-search");


        if (searchInput) {

            searchInput.addEventListener("input", () => {

                const query =
                    searchInput.value
                    .trim()
                    .toLowerCase();

                document
                    .querySelectorAll(
                        "#holdings-container tbody tr"
                    )
                    .forEach(row => {

                        const ticker =
                            row.dataset.ticker;

                        row.style.display =
                            ticker.includes(query)
                            ? ""
                            : "none";

                    });

            });

        }

    } catch(error) {

        console.error(error);

        container.innerHTML = `
            <div class="alert alert-danger">
                <h5>
                    Unable to Load Portfolio
                </h5>
                <p>
                    ${error.message}
                </p>
            </div>
        `;

    }

});