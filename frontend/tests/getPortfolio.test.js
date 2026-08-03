import test from 'node:test';
import assert from 'node:assert/strict';

import { getPortfolio, getHoldings } from '../static/js/api.js';

const originalFetch = global.fetch;

function mockFetch(responseFactory) {
  global.fetch = async (...args) => responseFactory(...args);
}

function mockResponse({ ok = true, jsonData = {}, status = 200 } = {}) {
  return {
    ok,
    status,
    json: async () => jsonData,
  };
}

test.afterEach(() => {
  global.fetch = originalFetch;
});

test('getPortfolio calls the portfolio endpoint', async () => {
  let calledUrl;
  mockFetch((url) => {
    calledUrl = url;
    return mockResponse({ jsonData: [{ id: 1, ticker: 'AAPL', side: 'buy' }] });
  });

  const result = await getPortfolio();

  assert.equal(calledUrl, 'http://127.0.0.1:8000/portfolio');
  assert.deepEqual(result, [{ id: 1, ticker: 'AAPL', side: 'buy' }]);
});

test('getHoldings calls the holdings endpoint', async () => {
  let calledUrl;
  mockFetch((url) => {
    calledUrl = url;
    return mockResponse({ jsonData: [{ ticker: 'AAPL', averagePrice: 100, currentPrice: 120, quantity: 2 }] });
  });

  const result = await getHoldings();

  assert.equal(calledUrl, 'http://127.0.0.1:8000/portfolio/holdings');
  assert.deepEqual(result, [{ ticker: 'AAPL', averagePrice: 100, currentPrice: 120, quantity: 2 }]);
});

test('getPortfolio throws a friendly error when the API fails', async () => {
  mockFetch(() => mockResponse({ ok: false, status: 500 }));

  await assert.rejects(getPortfolio(), /Failed to fetch portfolio/);
});
