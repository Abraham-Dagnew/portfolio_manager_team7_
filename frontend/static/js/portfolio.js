import { getPortfolio, deleteHolding } from './api.js';

document.addEventListener("DOMContentLoaded", async () => {
    const container = document.getElementById("holdings-container");

    try {
        const holdings = await getPortfolio();

        if (!holdings || holdings.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <h3>No holdings found</h3>
                    <p>Click "+ Add Holding" above to start building your portfolio.</p>
                </div>
            `;
            return;
        }

        // Build the table layout
        let html = `
            <table>
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
                    <td>${item.type}</td>
                    <td>${item.quantity}</td>
                    <td>$${Number(item.purchasePrice).toFixed(2)}</td>
                    <td>${item.purchaseDate}</td>
                    <td>
                        <button class="delete-btn" data-id="${item.id}" style="color:red; cursor:pointer;">Delete</button>
                    </td>
                </tr>
            `;
        });

        html += `</tbody></table>`;
        container.innerHTML = html;

        // Attach event listeners to the delete buttons (Person C integration)
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
        container.innerHTML = `<p style="color: red;">Error loading portfolio: ${error.message}</p>`;
    }
});