// Import the shared API functions
import { addHolding, searchStocks, getStockPrice } from "./api.js";
import { showToast } from "./toast.js";
import { refreshBalance } from "./balance.js";

// Get references to the form and message display area
const form = document.getElementById("addHoldingForm");
const message = document.getElementById("message");
const submitBtn = document.getElementById("submitBtn");

const tickerInput = document.getElementById("ticker");
const typeInput = document.getElementById("type");
const quantityInput = document.getElementById("quantity");
const purchasePriceInput = document.getElementById("purchasePrice");
const purchaseDateInput = document.getElementById("purchaseDate");
const stockSuggestions = document.getElementById("stockSuggestions");
const purchasePriceHint = document.getElementById("purchasePriceHint");

// Prevent selecting future dates from the browser date picker
const today = new Date().toISOString().split("T")[0];
purchaseDateInput.max = today;

let searchTimer;

const TICKER_REGEX = /^[A-Z]{1,5}$/;

const TYPE_MAP = {
    stock: "Stock",
    etf: "ETF",
    bond: "Bond",
    cash: "Cash",
};

let purchasePriceTouchedByUser = false;

let lastVerifiedTicker = null;


const fieldErrorEls = {
    ticker: document.getElementById("tickerError"),
    type: document.getElementById("typeError"),
    quantity: document.getElementById("quantityError"),
    purchasePrice: document.getElementById("purchasePriceError"),
    purchaseDate: document.getElementById("purchaseDateError"),
};


function clearFieldErrors() {

    Object.values(fieldErrorEls).forEach((el) => {

        if (el) {
            el.textContent = "";
        }

    });

}


function setFieldError(field, text) {

    const el = fieldErrorEls[field];

    if (el) {
        el.textContent = text;
    }

}


purchasePriceInput.addEventListener("input", () => {

    purchasePriceTouchedByUser = true;

});


function validate(holding) {

    const errors = {};


    if (!holding.ticker || !TICKER_REGEX.test(holding.ticker)) {

        errors.ticker =
            "Ticker must be 1-5 uppercase letters (example: AAPL).";

    }


    if (!holding.type) {

        errors.type =
            "Please select a holding type.";

    }


    if (!Number.isFinite(holding.quantity) || holding.quantity <= 0) {

        errors.quantity =
            "Quantity must be a positive number.";

    }


    if (!Number.isFinite(holding.purchasePrice) || holding.purchasePrice <= 0) {

        errors.purchasePrice =
            "Purchase price must be a positive number.";

    }


    if (!holding.purchaseDate) {

    errors.purchaseDate =
        "Please select a purchase date.";

} else {

    const selectedDate = new Date(holding.purchaseDate);
    const currentDate = new Date();

    // Ignore time, compare dates only
    selectedDate.setHours(0, 0, 0, 0);
    currentDate.setHours(0, 0, 0, 0);


    if (selectedDate > currentDate) {

        errors.purchaseDate =
            "Purchase date cannot be in the future.";

    }

}


    return errors;

}



function isCashType() {

    return typeInput.value === "Cash";

}



async function verifyTickerAndPrefillPrice(rawTicker) {

    const ticker = rawTicker.trim().toUpperCase();


    if (!TICKER_REGEX.test(ticker) || isCashType()) {
        return;
    }


    if (ticker === lastVerifiedTicker) {
        return;
    }


    try {

        const result = await getStockPrice(ticker);


        lastVerifiedTicker = ticker;


        setFieldError("ticker", "");


        if (!purchasePriceTouchedByUser) {

            purchasePriceInput.value =
                result.price.toFixed(2);


            purchasePriceHint.textContent =
                `Filled from ${ticker}'s live price ($${result.price.toFixed(2)}). You can change it.`;

        }


    } catch (error) {

        lastVerifiedTicker = null;


        setFieldError(
            "ticker",
            error.message || `${ticker} is not a valid ticker.`
        );

    }

}



tickerInput.addEventListener("blur", () => {

    verifyTickerAndPrefillPrice(tickerInput.value);

});



typeInput.addEventListener("change", () => {

    if (isCashType()) {

        setFieldError("ticker", "");

    } else {

        verifyTickerAndPrefillPrice(tickerInput.value);

    }

});



// Submit form

form.addEventListener("submit", async (event) => {

    event.preventDefault();


    clearFieldErrors();


    const holding = {

        ticker: tickerInput.value.trim().toUpperCase(),

        type: typeInput.value,

        quantity: Number(quantityInput.value),

        purchasePrice: Number(purchasePriceInput.value),

        purchaseDate: purchaseDateInput.value,

    };



    const errors = validate(holding);



    if (Object.keys(errors).length > 0) {


        Object.entries(errors).forEach(([field, text]) => {

            setFieldError(field, text);

        });


        showToast(
            "Please fix the highlighted fields.",
            "error"
        );


        return;

    }



    submitBtn.disabled = true;

    submitBtn.textContent = "Adding...";



    if (
        holding.type !== "Cash" &&
        holding.ticker !== lastVerifiedTicker
    ) {


        try {

            await getStockPrice(holding.ticker);

            lastVerifiedTicker = holding.ticker;


        } catch (error) {


            setFieldError(
                "ticker",
                error.message || `${holding.ticker} is not a valid ticker.`
            );


            showToast(
                "Invalid ticker.",
                "error"
            );


            submitBtn.disabled = false;

            submitBtn.textContent = "Add Holding";

            return;

        }

    }



    try {


        const response = await addHolding(holding);



        showToast(
            response.message || "Holding added successfully!",
            "success"
        );

        refreshBalance();

        form.reset();

        purchaseDateInput.max = today;


        stockSuggestions.innerHTML = "";


        purchasePriceTouchedByUser = false;


        purchasePriceHint.textContent =
            "Auto-filled from live price once a valid ticker is entered.";


        lastVerifiedTicker = null;



    } catch (error) {


        if (/ticker/i.test(error.message)) {

            setFieldError(
                "ticker",
                error.message
            );

        }


        showToast(
            error.message || "Failed to add holding.",
            "error"
        );



    } finally {


        submitBtn.disabled = false;


        submitBtn.textContent = "Add Holding";


    }

});



// Stock autocomplete

tickerInput.addEventListener("input", () => {


    clearTimeout(searchTimer);


    lastVerifiedTicker = null;


    const query = tickerInput.value.trim();



    if (query.length < 2) {

        stockSuggestions.innerHTML = "";

        return;

    }



    searchTimer = setTimeout(async () => {


        try {


            const results = await searchStocks(query);



            stockSuggestions.innerHTML = "";



            results.forEach(stock => {


                const option = document.createElement("div");


                option.className = "stock-option";



                option.innerHTML = `

                    <strong>${stock.ticker}</strong>

                    <span>${stock.name}</span>

                    <em>${stock.type}</em>

                `;



                option.addEventListener("click", async () => {


                    tickerInput.value = stock.ticker;


                    stockSuggestions.innerHTML = "";



                    const mappedType =
                        TYPE_MAP[stock.type];



                    if (mappedType) {

                        typeInput.value = mappedType;

                    }



                    await verifyTickerAndPrefillPrice(stock.ticker);


                });



                stockSuggestions.appendChild(option);


            });



        } catch (error) {

            console.error(error);

        }



    }, 300);


});



document.addEventListener("click", (event) => {


    if (
        !tickerInput.contains(event.target) &&
        !stockSuggestions.contains(event.target)
    ) {

        stockSuggestions.innerHTML = "";

    }


});