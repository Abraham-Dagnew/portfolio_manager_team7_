import { getPortfolio, getHoldings, getStockPrice, sellHolding } from './api.js';
import { showToast } from './toast.js';
import { refreshBalance } from './balance.js';
import { formatCurrency, formatNumber } from './format.js';

document.addEventListener("DOMContentLoaded", async () => {
    const holdingsContainer = document.getElementById("holdings-container");
    const transactionsContainer = document.getElementById("transactions-container");
    const holdingsPanel = document.getElementById("holdings-panel");
    const transactionsPanel = document.getElementById("transactions-panel");
    const searchInput = document.querySelector(".topbar-search");
    const tabButtons = Array.from(document.querySelectorAll(".tab-button"));
    let sellModal = null;
    let sellModalInput = null;
    let sellModalMessage = null;
    let sellModalConfirmButton = null;
    let sellModalTicker = null;
    let sellModalMaxQuantity = 0;
    let sellModalLivePrice = null;
    let sellModalAveragePrice = null;

    if (!holdingsContainer || !transactionsContainer || !holdingsPanel || !transactionsPanel) {
        return;
    }

    let holdings = [];
    let transactions = [];
    let activeTab = "holdings";

    function setActiveTab(tabName) {
        activeTab = tabName;

        tabButtons.forEach((button) => {
            const isActive = button.dataset.tab === tabName;
            button.classList.toggle("active", isActive);
            button.setAttribute("aria-selected", isActive ? "true" : "false");
        });

        holdingsPanel.classList.toggle("hidden", tabName !== "holdings");
        transactionsPanel.classList.toggle("hidden", tabName !== "transactions");

        if (searchInput) {
            searchInput.style.display = "";
        }
    }

    function renderEmptyState(container, title, message) {
        container.innerHTML = `
            <div class="empty-state">
                <h3>${title}</h3>
                <p>${message}</p>
            </div>
        `;
    }

    function ensureSellModal() {
        if (sellModal) {
            return;
        }

        sellModal = document.createElement("div");
        sellModal.className = "sell-modal hidden";
        sellModal.innerHTML = `
            <div class="sell-modal__backdrop" data-action="close"></div>
            <div class="sell-modal__dialog" role="dialog" aria-modal="true" aria-labelledby="sell-modal-title">
                <h3 id="sell-modal-title">Sell shares</h3>
                <p class="sell-modal__message"></p>
                <label class="sell-modal__label" for="sellModalQuantity">Quantity to sell</label>
                <input id="sellModalQuantity" type="number" min="0.0001" step="0.01">
                <div class="sell-modal__actions">
                    <button type="button" class="sell-modal__button sell-modal__button--secondary" data-action="cancel">Cancel</button>
                    <button type="button" class="sell-modal__button sell-modal__button--primary" data-action="confirm">Sell</button>
                </div>
            </div>
        `;

        document.body.appendChild(sellModal);
        sellModalInput = sellModal.querySelector("#sellModalQuantity");
        sellModalMessage = sellModal.querySelector(".sell-modal__message");
        sellModalConfirmButton = sellModal.querySelector('[data-action="confirm"]');

        sellModal.addEventListener("click", (event) => {
            const action = event.target?.dataset?.action;
            if (action === "close" || action === "cancel") {
                closeSellModal();
            }
            if (action === "confirm") {
                confirmSellModal();
            }
        });

        sellModalInput.addEventListener("keydown", (event) => {
            if (event.key === "Enter") {
                event.preventDefault();
                confirmSellModal();
            }
        });

        sellModalInput.addEventListener("input", renderSellModalDetails);
    }

    function renderSellModalDetails() {
        if (!sellModalMessage || !sellModalInput || sellModalLivePrice === null || sellModalAveragePrice === null) {
            return;
        }

        const quantityToSell = Number(String(sellModalInput.value).replace(/,/g, "").trim()) || 0;
        const estimatedProceeds = quantityToSell * sellModalLivePrice;
        const estimatedGainLoss = (sellModalLivePrice - sellModalAveragePrice) * quantityToSell;
        const gainLossLabel = estimatedGainLoss >= 0 ? "Estimated gain" : "Estimated loss";

        sellModalMessage.innerHTML = `
            Live sell price: <strong>${formatCurrency(sellModalLivePrice)}</strong><br>
            Average buy price: <strong>${formatCurrency(sellModalAveragePrice)}</strong><br>
            Estimated proceeds: <strong>${formatCurrency(estimatedProceeds)}</strong><br>
            ${gainLossLabel}: <strong>${formatCurrency(Math.abs(estimatedGainLoss))}</strong><br>
            Maximum available: <strong>${formatNumber(sellModalMaxQuantity)} shares</strong>
        `;
    }

    async function openSellModal(ticker, quantity, averagePrice) {
        ensureSellModal();
        sellModalTicker = ticker;
        sellModalMaxQuantity = Number(quantity);
        sellModalAveragePrice = Number(averagePrice);
        sellModalLivePrice = null;
        sellModalInput.value = String(quantity);
        sellModalInput.max = String(quantity);
        sellModalInput.disabled = true;
        if (sellModalConfirmButton) {
            sellModalConfirmButton.disabled = true;
        }
        sellModalMessage.innerHTML = `Loading live price for ${ticker}...`;
        sellModal.classList.remove("hidden");
        window.setTimeout(() => sellModalInput.focus(), 0);

        try {
            const market = await getStockPrice(ticker);
            sellModalLivePrice = Number(market.price);
            renderSellModalDetails();
        } catch (error) {
            sellModalLivePrice = 0;
            sellModalMessage.textContent = error.message || `Could not load a live price for ${ticker}.`;
            showToast(error.message || `Could not load a live price for ${ticker}.`, "error");
        } finally {
            sellModalInput.disabled = false;
            if (sellModalConfirmButton) {
                sellModalConfirmButton.disabled = false;
            }
            sellModalInput.focus();
        }
    }

    function closeSellModal() {
        if (!sellModal) {
            return;
        }

        sellModal.classList.add("hidden");
        sellModalTicker = null;
        sellModalMaxQuantity = 0;
        sellModalLivePrice = null;
        sellModalAveragePrice = null;
    }

    async function confirmSellModal() {
        if (!sellModalTicker) {
            return;
        }

        const quantityToSell = Number(String(sellModalInput.value).replace(/,/g, "").trim());

        if (!Number.isFinite(quantityToSell) || quantityToSell <= 0) {
            showToast("Enter a valid quantity greater than zero.", "error");
            return;
        }

        if (quantityToSell > sellModalMaxQuantity) {
            showToast(
                `You only own ${formatNumber(sellModalMaxQuantity)} shares of ${sellModalTicker}.`,
                "error"
            );
            return;
        }

        const ticker = sellModalTicker;
        closeSellModal();
        await submitSellOrder(ticker, quantityToSell);
    }

    function applyPortfolioFilter() {
        if (!searchInput) {
            return;
        }

        const query = searchInput.value.trim().toLowerCase();

        holdingsContainer.querySelectorAll("tbody tr").forEach((row) => {
            row.style.display = row.dataset.ticker.includes(query) ? "" : "none";
        });

        transactionsContainer.querySelectorAll("tbody tr").forEach((row) => {
            row.style.display = row.dataset.ticker.includes(query) ? "" : "none";
        });
    }

    function renderHoldingsTable() {
        if (!holdings.length) {
            renderEmptyState(
                holdingsContainer,
                "No holdings yet",
                'Buy an asset to see your current positions here.'
            );
            return;
        }

        holdingsContainer.innerHTML = `
            <div class="table-responsive">
                <table>
                    <thead>
                        <tr>
                            <th>Ticker</th>
                            <th>Average Price</th>
                            <th>Current Price</th>
                            <th>Quantity</th>
                            <th>Sell</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${holdings
                            .map(
                                (holding) => `
                                    <tr data-ticker="${holding.ticker.toLowerCase()}">
                                        <td><strong>${holding.ticker}</strong></td>
                                        <td>${formatCurrency(holding.averagePrice)}</td>
                                        <td>${formatCurrency(holding.currentPrice)}</td>
                                        <td>${formatNumber(holding.quantity)}</td>
                                        <td>
                                            <button
                                                type="button"
                                                class="sell-btn"
                                                data-ticker="${holding.ticker}"
                                                data-quantity="${holding.quantity}"
                                            >
                                                Sell
                                            </button>
                                        </td>
                                    </tr>
                                `
                            )
                            .join("")}
                    </tbody>
                </table>
            </div>
        `;

        holdingsContainer.querySelectorAll(".sell-btn").forEach((button) => {
            button.addEventListener("click", handleSellClick);
        });

        applyPortfolioFilter();
    }

    function renderTransactionsTable() {
        if (!transactions.length) {
            renderEmptyState(
                transactionsContainer,
                "No transactions yet",
                'Every buy and sell will appear here once you start trading.'
            );
            return;
        }

        transactionsContainer.innerHTML = `
            <div class="table-responsive">
                <table>
                    <thead>
                        <tr>
                            <th>Date</th>
                            <th>Ticker</th>
                            <th>Side</th>
                            <th>Price</th>
                            <th>Quantity</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${transactions
                            .map(
                                (transaction) => `
                                    <tr data-ticker="${transaction.ticker.toLowerCase()}">
                                        <td>${transaction.purchaseDate}</td>
                                        <td><strong>${transaction.ticker}</strong></td>
                                        <td>${String(transaction.side || "buy").toUpperCase()}</td>
                                        <td>${formatCurrency(transaction.purchasePrice)}</td>
                                        <td>${formatNumber(transaction.quantity)}</td>
                                    </tr>
                                `
                            )
                            .join("")}
                    </tbody>
                </table>
            </div>
        `;
    }

    async function loadPortfolioData() {
        const [holdingsData, transactionsData] = await Promise.all([
            getHoldings(),
            getPortfolio(),
        ]);

        holdings = Array.isArray(holdingsData) ? holdingsData : [];
        transactions = Array.isArray(transactionsData) ? transactionsData : [];

        renderHoldingsTable();
        renderTransactionsTable();
    }

    async function refreshAllViews() {
        await loadPortfolioData();
        await refreshBalance();
    }

    async function submitSellOrder(ticker, quantityToSell) {
        const button = holdingsContainer.querySelector(`.sell-btn[data-ticker="${ticker}"]`);
        const currentHolding = holdings.find((holding) => holding.ticker === ticker);

        if (!currentHolding) {
            showToast(`Could not find ${ticker} in your holdings.`, "error");
            return;
        }

        if (quantityToSell > Number(currentHolding.quantity)) {
            showToast(`You only own ${formatNumber(currentHolding.quantity)} shares of ${ticker}.`, "error");
            return;
        }

        if (button) {
            button.disabled = true;
            button.textContent = "Selling...";
        }

        try {
            const result = await sellHolding({ ticker, quantity: quantityToSell });
            showToast(result.message || `Sold ${ticker} successfully.`, "success");
            if (searchInput) {
                searchInput.value = "";
            }
            await refreshAllViews();
        } catch (error) {
            showToast(error.message || "Failed to sell holding.", "error");
        } finally {
            if (button) {
                button.disabled = false;
                button.textContent = "Sell";
            }
        }
    }

    async function handleSellClick(event) {
        const button = event.currentTarget;
        const ticker = button.dataset.ticker;
        const currentHolding = holdings.find((holding) => holding.ticker === ticker);

        if (!currentHolding) {
            showToast(`Could not find ${ticker} in your holdings.`, "error");
            return;
        }

        openSellModal(ticker, currentHolding.quantity, currentHolding.averagePrice);
    }

    tabButtons.forEach((button) => {
        button.addEventListener("click", () => {
            setActiveTab(button.dataset.tab);
        });
    });

    if (searchInput) {
        searchInput.addEventListener("input", applyPortfolioFilter);
    }

    try {
        await refreshAllViews();
        setActiveTab("holdings");
    } catch (error) {
        console.error(error);

        const message = error.message || "Unable to load portfolio data.";
        holdingsContainer.innerHTML = `
            <div class="empty-state">
                <h3>Unable to load holdings</h3>
                <p>${message}</p>
            </div>
        `;
        transactionsContainer.innerHTML = `
            <div class="empty-state">
                <h3>Unable to load transactions</h3>
                <p>${message}</p>
            </div>
        `;
    }
});