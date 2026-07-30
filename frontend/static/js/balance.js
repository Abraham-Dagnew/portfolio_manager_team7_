import { getBalance, depositFunds, withdrawFunds } from "./api.js";
import { showToast } from "./toast.js";

const amountEl = document.getElementById("balance-amount");
const errorEl = document.getElementById("balance-error");
const depositForm = document.getElementById("depositForm");
const fundsAmountInput = document.getElementById("fundsAmount");
const depositSubmitBtn = document.getElementById("depositSubmit");
const withdrawSubmitBtn = document.getElementById("withdrawSubmit");

function formatCurrency(value) {
    return `$${Number(value).toFixed(2)}`;
}

function readAmount() {
    const raw = fundsAmountInput.value;
    const amount = Number(raw);

    if (!raw || !Number.isFinite(amount) || amount <= 0) {
        errorEl.textContent = "Enter an amount greater than $0.";
        return null;
    }

    errorEl.textContent = "";
    return amount;
}

function setButtonsDisabled(disabled) {
    depositSubmitBtn.disabled = disabled;
    withdrawSubmitBtn.disabled = disabled;
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

        const amount = readAmount();
        if (amount === null) {
            return;
        }

        setButtonsDisabled(true);
        depositSubmitBtn.textContent = "...";

        try {
            const response = await depositFunds(amount);
            amountEl.textContent = formatCurrency(response.cash);
            fundsAmountInput.value = "";
            showToast(response.message || "Funds added.", "success");
        } catch (error) {
            errorEl.textContent = error.message || "Failed to add funds. Please try again.";
            showToast(error.message || "Failed to add funds.", "error");
        } finally {
            setButtonsDisabled(false);
            depositSubmitBtn.textContent = "+";
        }
    });
}

if (withdrawSubmitBtn) {
    withdrawSubmitBtn.addEventListener("click", async () => {
        const amount = readAmount();
        if (amount === null) {
            return;
        }

        setButtonsDisabled(true);
        withdrawSubmitBtn.textContent = "...";

        try {
            const response = await withdrawFunds(amount);
            amountEl.textContent = formatCurrency(response.cash);
            fundsAmountInput.value = "";
            showToast(response.message || "Funds withdrawn.", "success");
        } catch (error) {
            errorEl.textContent = error.message || "Failed to withdraw funds. Please try again.";
            showToast(error.message || "Failed to withdraw funds.", "error");
        } finally {
            setButtonsDisabled(false);
            withdrawSubmitBtn.textContent = "−";
        }
    });
}

document.addEventListener("DOMContentLoaded", refreshBalance);
