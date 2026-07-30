import { getPortfolio, deleteHolding } from './api.js';

document.addEventListener("DOMContentLoaded", async () => {
    const container = document.getElementById("holdings-container");

    try {
        const holdings = await getPortfolio();

        if (!holdings || holdings.length === 0) {
            container.innerHTML = `
                <div class="empty-state card p-4 text-center">
                    <h3>No holdings found</h3>
                    <p class="text-muted mb-0">Click "+ Add Holding" to start building your portfolio.</p>
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
                <tr>
                    <td><strong>${item.ticker}</strong></td>
                    <td><span class="badge bg-light text-dark text-capitalize">${item.type}</span></td>
                    <td>${item.quantity}</td>
                    <td>$${Number(item.purchasePrice).toFixed(2)}</td>
                    <td>${item.purchaseDate}</td>
                    <td>
                        <button class="delete-btn btn btn-sm btn-outline-danger" data-id="${item.id}">Delete</button>
                    </td>
                </tr>
            `;
        });

        html += `</tbody></table></div></div>`;
        container.innerHTML = html;

        document.querySelectorAll(".delete-btn").forEach(button => {
            button.addEventListener("click", async (e) => {
                const id = e.target.getAttribute("data-id");
                if (confirm(`Are you sure you want to delete holding #${id}?`)) {
                    try {
                        await deleteHolding(id);
                        window.location.reload();
                    } catch (err) {
                        alert("Failed to delete holding.");
                    }
                }
            });
        });

    } catch (error) {
        console.error("Error loading portfolio:", error);
        
        container.innerHTML = `
            <div class="alert alert-danger shadow-sm border-0 p-4" role="alert">
                <h5 class="alert-heading mb-2">Unable to Load Portfolio</h5>
                <p class="mb-0">Could not retrieve holdings from backend (${error.message || 'Network error'}). Please make sure the FastAPI backend is running at <code>http://127.0.0.1:8000</code> and try refreshing.</p>
            </div>
        `;
    }
});