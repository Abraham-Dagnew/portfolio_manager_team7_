import { getPortfolio, deleteHolding } from './api.js';
import { showToast } from './toast.js';
import { refreshBalance } from './balance.js';

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
                        Click "+ Add Holding" to start building your portfolio.
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

                    <td>${item.quantity}</td>

                    <td>
                        $${Number(item.purchasePrice).toFixed(2)}
                    </td>

                    <td>
                        ${item.purchaseDate}
                    </td>

                    <td>

                        <button
                            class="delete-btn btn btn-sm btn-outline-danger"
                            data-id="${item.id}">
                            Delete
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



        // DELETE FUNCTIONALITY

        document.querySelectorAll(".delete-btn")
            .forEach(button => {


                button.addEventListener("click", async (e) => {


                    const id = e.target.dataset.id;
                    const row = e.target.closest("tr");


                    if (!confirm("Are you sure you want to delete this holding?")) {
                        return;
                    }


                    e.target.disabled = true;
                    e.target.textContent = "Deleting...";


                    try {

                        await deleteHolding(id);


                        row.remove();


                        showToast(
                            "Holding deleted successfully",
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
                                        Click "+ Add Holding" to start building your portfolio.
                                    </p>

                                </div>
                            `;
                        }


                    } catch(error) {


                        showToast(
                            error.message || "Failed to delete holding",
                            "error"
                        );


                        e.target.disabled = false;
                        e.target.textContent = "Delete";

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