const currencyFormatter = new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
});

const numberFormatter = new Intl.NumberFormat("en-US");

export function formatCurrency(value) {
    return currencyFormatter.format(Number(value));
}

export function formatNumber(value) {
    return numberFormatter.format(Number(value));
}
