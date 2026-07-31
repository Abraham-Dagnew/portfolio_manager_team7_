import { addHolding, searchStocks, getStockPrice, getTrendingTickers } from "./api.js";
import { showToast } from "./toast.js";
import { refreshBalance } from "./balance.js";
import { formatCurrency } from "./format.js";


const form = document.getElementById("addHoldingForm");
const submitBtn = document.getElementById("submitBtn");

const tickerInput = document.getElementById("ticker");
const typeInput = document.getElementById("type");
const quantityInput = document.getElementById("quantity");
const purchasePriceInput = document.getElementById("purchasePrice");
const purchaseDateInput = document.getElementById("purchaseDate");
const stockSuggestions = document.getElementById("stockSuggestions");
const purchasePriceHint = document.getElementById("purchasePriceHint");


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

    Object.values(fieldErrorEls).forEach(el => {

        if (el) {
            el.textContent = "";
        }

    });

}



function setFieldError(field, message) {

    if (fieldErrorEls[field]) {
        fieldErrorEls[field].textContent = message;
    }

}



// Display date as M/D/YYYY
function setPurchaseDateToday() {

    const today = new Date();

    purchaseDateInput.value =
        `${today.getMonth() + 1}/${today.getDate()}/${today.getFullYear()}`;

}



// Convert display date back to backend format
function getBackendDateFormat(displayDate) {

    if (!displayDate) {
        return "";
    }


    const parts = displayDate.split("/");


    if (parts.length !== 3) {
        return "";
    }


    const month = parts[0].padStart(2, "0");
    const day = parts[1].padStart(2, "0");
    const year = parts[2];


    return `${year}-${month}-${day}`;

}




purchasePriceInput.addEventListener("input", () => {

    purchasePriceTouchedByUser = true;

});




function validate(holding) {

    const errors = {};


    if (!holding.ticker || !TICKER_REGEX.test(holding.ticker)) {

        errors.ticker =
            "Ticker must be 1-5 uppercase letters.";

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
            "Purchase price must be positive.";

    }



    if (!holding.purchaseDate) {

        errors.purchaseDate =
            "Please select a purchase date.";

    }
    else {

        const selectedDate =
            new Date(holding.purchaseDate + "T00:00:00");


        const currentDate =
            new Date();


        selectedDate.setHours(0,0,0,0);
        currentDate.setHours(0,0,0,0);



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


    const ticker =
        rawTicker.trim().toUpperCase();



    if (!TICKER_REGEX.test(ticker) || isCashType()) {
        return;
    }



    if (ticker === lastVerifiedTicker) {
        return;
    }



    try {


        const result =
            await getStockPrice(ticker);



        lastVerifiedTicker = ticker;


        setFieldError("ticker", "");



        if (!purchasePriceTouchedByUser) {


            purchasePriceInput.value =
                result.price.toFixed(2);



            purchasePriceHint.textContent =
                    `Auto-filled from ${ticker}'s live market price (${formatCurrency(result.price)}).`;

        }



    }
    catch(error) {


        lastVerifiedTicker = null;


        setFieldError(
            "ticker",
            error.message || "Invalid ticker."
        );

    }

}





tickerInput.addEventListener("blur", () => {

    verifyTickerAndPrefillPrice(
        tickerInput.value
    );

});





typeInput.addEventListener("change", () => {


    verifyTickerAndPrefillPrice(
        tickerInput.value
    );


});







form.addEventListener("submit", async(event)=>{


    event.preventDefault();


    clearFieldErrors();



    const holding = {


        ticker:
            tickerInput.value.trim().toUpperCase(),


        type:
            typeInput.value,


        quantity:
            Number(quantityInput.value),


        purchasePrice:
            Number(purchasePriceInput.value),


        purchaseDate:
            getBackendDateFormat(
                purchaseDateInput.value
            ),

    };



    const errors =
        validate(holding);



    if(Object.keys(errors).length > 0){


        Object.entries(errors).forEach(([field,message])=>{

            setFieldError(field,message);

        });


        showToast(
            "Please fix the highlighted fields.",
            "error"
        );


        return;

    }





    submitBtn.disabled = true;
    submitBtn.textContent = "Buying...";



    try{


        const response =
            await addHolding(holding);



        showToast(
            response.message || "Holding purchased successfully!",
            "success"
        );


        refreshBalance();



        form.reset();



        purchaseDateInput.value = "";


        purchasePriceTouchedByUser = false;


        lastVerifiedTicker = null;


        stockSuggestions.innerHTML = "";



    }
    catch(error){


        showToast(
            error.message || "Purchase failed.",
            "error"
        );


    }
    finally{


        submitBtn.disabled = false;

        submitBtn.textContent = "Buy";


    }


});







tickerInput.addEventListener("input",()=>{


    clearTimeout(searchTimer);


    lastVerifiedTicker = null;


    const query =
        tickerInput.value.trim();



    if(query.length < 2){

        stockSuggestions.innerHTML="";
        return;

    }



    searchTimer=setTimeout(async()=>{


        try{


            const results =
                await searchStocks(query);



            stockSuggestions.innerHTML="";



            results.forEach(stock=>{


                const option =
                    document.createElement("div");


                option.className="stock-option";



                option.innerHTML=`

                    <strong>${stock.ticker}</strong>

                    <span>${stock.name}</span>

                    <em>${stock.type}</em>

                `;



                option.addEventListener("click",async()=>{


                    tickerInput.value =
                        stock.ticker;



                    stockSuggestions.innerHTML="";



                    const mappedType =
                        TYPE_MAP[stock.type];



                    if(mappedType){

                        typeInput.value =
                            mappedType;

                    }



                    // Populate date after stock selection
                    setPurchaseDateToday();



                    await verifyTickerAndPrefillPrice(
                        stock.ticker
                    );


                });



                stockSuggestions.appendChild(option);



            });


        }
        catch(error){

            console.error(error);

        }


    },300);



});





document.addEventListener("click",(event)=>{


    if(
        !tickerInput.contains(event.target) &&
        !stockSuggestions.contains(event.target)
    ){

        stockSuggestions.innerHTML="";

    }


});



// Popular tickers widget

const trendingListEl = document.getElementById("trendingList");

async function loadTrendingTickers() {

    if (!trendingListEl) {
        return;
    }

    try {

        const movers = await getTrendingTickers();

        if (!movers || movers.length === 0) {
            trendingListEl.innerHTML = "<p>No trending data available right now.</p>";
            return;
        }

        trendingListEl.innerHTML = "";

        movers.forEach((mover) => {

            const item = document.createElement("div");
            item.className = "trending-item";

            const changeClass = mover.changePercent >= 0 ? "gain-positive" : "gain-negative";
            const changeSign = mover.changePercent >= 0 ? "+" : "";

            item.innerHTML = `
                <span>
                    <span class="trending-ticker">${mover.ticker}</span>
                    <span class="trending-name">${mover.name}</span>
                </span>
                <span class="trending-price">
                    ${formatCurrency(mover.price)}
                    <span class="trending-change ${changeClass}">${changeSign}${mover.changePercent.toFixed(2)}%</span>
                </span>
            `;

            item.addEventListener("click", async () => {

                tickerInput.value = mover.ticker;
                stockSuggestions.innerHTML = "";

                typeInput.value = TYPE_MAP.stock;

                setPurchaseDateToday();

                await verifyTickerAndPrefillPrice(mover.ticker);

            });

            trendingListEl.appendChild(item);

        });

    } catch (error) {

        trendingListEl.innerHTML = "<p>Could not load trending tickers.</p>";
        console.error(error);

    }

}

loadTrendingTickers();