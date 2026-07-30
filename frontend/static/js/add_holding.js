// Import the shared API function used to send POST requests to FastAPI
import { addHolding } from "./api.js";

// Get references to the form and message display area from the HTML page
const form = document.getElementById("addHoldingForm");
const message = document.getElementById("message");

// Listen for when the user submits the add holding form
form.addEventListener("submit", async (event) => {
    // Prevent the browser from refreshing the page
    event.preventDefault();

    // Collect form values and create the holding object
    const holding = {
        ticker: document.getElementById("ticker").value.trim().toUpperCase(),
        type: document.getElementById("type").value,
        quantity: Number(document.getElementById("quantity").value),
        purchasePrice: Number(document.getElementById("purchasePrice").value),
        purchaseDate: document.getElementById("purchaseDate").value
    };

    // Specific validation checks for Quantity and Price
    const errors = [];
    if (isNaN(holding.quantity) || holding.quantity <= 0) {
        errors.push("Quantity must be a number greater than 0.");
    }
    if (isNaN(holding.purchasePrice) || holding.purchasePrice <= 0) {
        errors.push("Purchase price must be a number greater than 0.");
    }

    // Display field-specific errors if quantity or price are invalid
    if (errors.length > 0) {
        message.style.color = "red";
        message.innerHTML = errors.map(err => `• ${err}`).join("<br>");
        return;
    }

    try {
        // Send the holding data to FastAPI using POST /portfolio
        const response = await addHolding(holding);

        // Display success message returned from the backend
        message.style.color = "green";
        message.textContent = response.message || "Holding added successfully!";

        // Clear the form after a successful submission
        form.reset();

    } catch (error) {
        message.style.color = "red";
        message.textContent = "Error adding holding: " + error.message;
    }
});