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
    // This object matches the FastAPI HoldingCreate model
    const holding = {
        ticker: document.getElementById("ticker").value.trim().toUpperCase(),
        type: document.getElementById("type").value,
        quantity: Number(document.getElementById("quantity").value),
        purchasePrice: Number(document.getElementById("purchasePrice").value),
        purchaseDate: document.getElementById("purchaseDate").value
    };

    // Client-side validation:
    // Checks that required fields are filled and numeric values are valid
    // before sending data to the backend
    if (
        !holding.ticker ||
        !holding.type ||
        holding.quantity <= 0 ||
        holding.purchasePrice <= 0 ||
        !holding.purchaseDate
    ) {
        message.style.color = "red";
        message.textContent = "Please fill in all fields correctly.";
        return;
    }

    try {
        // Send the holding data to FastAPI using POST /portfolio
        const response = await addHolding(holding);

        // Display success message returned from the backend
        message.style.color = "green";
        message.textContent = response.message;

        // Clear the form after a successful submission
        form.reset();

    } catch (error) {
        // Handles API/network errors such as:
        // - FastAPI server not running
        // - Database failure
        // - Backend returning an error response
        message.style.color = "red";
        message.textContent = "Error adding holding: " + error.message;
    }
});