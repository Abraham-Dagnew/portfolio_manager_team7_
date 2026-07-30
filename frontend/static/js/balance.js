import { getBalance, depositFunds } from "./api.js";
import { showToast } from "./toast.js";

const amountEl = document.getElementById("balance-amount");
const errorEl = document.getElementById("balance-error");
const depositForm = document.getElementById("depositForm");
const depositAmountInput = document.getElementById("depositAmount");
const depositSubmitBtn = document.getElementById("depositSubmit");

function formatCurrency(value) {
    return `$${Number(value).toFixed(2)}`;
}

export async function refreshBalance() {
    if (!amountEl) {
        return;
    }

    try {
        const data = await getBalance();
        amountEl.textContent = formatCurrency(data.cash);
        errorEl.textContent = "";
    } catch (error) {
        amountEl.textContent = "--";
        errorEl.textContent = error.message || "Could not load balance.";
    }
}

if (depositForm) {
    depositForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        errorEl.textContent = "";

        const rawAmount = depositAmountInput.value;
        const amount = Number(rawAmount);

        if (!rawAmount || !Number.isFinite(amount) || amount <= 0) {
            errorEl.textContent = "Enter an amount greater than $0.";
            return;
        }

        depositSubmitBtn.disabled = true;
        depositSubmitBtn.textContent = "Adding...";

        try {
            const response = await depositFunds(amount);
            amountEl.textContent = formatCurrency(response.cash);
            depositAmountInput.value = "";
            showToast(response.message || "Funds added.", "success");
        } catch (error) {
            errorEl.textContent = error.message || "Failed to add funds. Please try again.";
            showToast(error.message || "Failed to add funds.", "error");
        } finally {
            depositSubmitBtn.disabled = false;
            depositSubmitBtn.textContent = "+ Add Funds";
        }
    });
}

document.addEventListener("DOMContentLoaded", refreshBalance);
