# Neueda-Portfolio-Project

## Market Data Integration (Person 2 - Annie)

Integrates live stock market pricing into the application using `yfinance`.

- `yahoo_service.py` — Modules to connect with the Yahoo Finance API and fetch live market quotes.
- `get_stock_price(ticker)` — Fetches the real-time market price for a given stock symbol.
- `get_multiple_prices(tickers)` — Efficiently retrieves current market prices for a batch of portfolio tickers simultaneously.

## Performance Calculations (Person 3)

Combines stored holdings with live Yahoo Finance prices to report portfolio performance.

- `math_logic.py` — pure functions to calculate total value, total cost, total gain/loss, and % change for a single holding or an entire portfolio. No DB or network dependencies.
- `GET /portfolio/performance` (in `main.py`) — fetches holdings from the DB, gets live prices via `yahoo_service.py`, and returns each holding enriched with performance figures plus an aggregate summary.

### Testing

Run the unit tests:

```powershell
python -m unittest tests.test_math_logic -v
python -m unittest tests.test_main -v
```

Manually verify against live data:

1. Create the database and table (first time only):
   ```powershell
   python db_conn.py
   ```
2. Start the API:
   ```powershell
   python -m uvicorn main:app --host 127.0.0.1 --port 8000
   ```
3. In a second terminal, add a holding:
   ```powershell
   Invoke-RestMethod -Uri http://127.0.0.1:8000/portfolio -Method Post -ContentType "application/json" -Body '{"ticker":"AAPL","type":"stock","quantity":10,"purchasePrice":150.25,"purchaseDate":"2026-01-15"}'
   ```
4. Fetch performance data (uses a live price from Yahoo Finance):
   ```powershell
   Invoke-RestMethod -Uri http://127.0.0.1:8000/portfolio/performance | ConvertTo-Json -Depth 5
   ```
   Expect each holding to include `currentPrice`, `totalValue`, `totalCost`, `totalGain`, and `gainPercent`, plus a `summary` block aggregating the whole portfolio.
5. Clean up the test holding (use the `id` returned in step 3):
   ```powershell
   Invoke-RestMethod -Uri http://127.0.0.1:8000/portfolio/<id> -Method Delete
   ```

You can also try it from the interactive Swagger docs at `http://127.0.0.1:8000/docs`.
