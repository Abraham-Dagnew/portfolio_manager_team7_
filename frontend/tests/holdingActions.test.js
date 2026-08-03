import test from 'node:test';
import assert from 'node:assert/strict';

import { addHolding, sellHolding } from '../static/js/api.js';

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

test('addHolding posts holding data as JSON', async () => {
  let requestOptions;
  mockFetch((url, options) => {
    assert.equal(url, 'http://127.0.0.1:8000/portfolio');
    requestOptions = options;
    return mockResponse({ jsonData: { message: 'Holding added', id: 7 } });
  });

  const payload = {
    ticker: 'AAPL',
    type: 'stock',
    quantity: 2,
    purchasePrice: 100.5,
    purchaseDate: '2026-07-27',
  };

  const result = await addHolding(payload);

  assert.equal(requestOptions.method, 'POST');
  assert.equal(requestOptions.headers['Content-Type'], 'application/json');
  assert.deepEqual(JSON.parse(requestOptions.body), payload);
  assert.deepEqual(result, { message: 'Holding added', id: 7 });
});

test('sellHolding posts sale data to the sell endpoint', async () => {
  let calledUrl;
  let requestOptions;
  mockFetch((url, options) => {
    calledUrl = url;
    requestOptions = options;
    return mockResponse({ jsonData: { message: 'Sold AAPL' } });
  });

  const payload = { ticker: 'AAPL', quantity: 5 };
  const result = await sellHolding(payload);

  assert.equal(calledUrl, 'http://127.0.0.1:8000/portfolio/sell');
  assert.equal(requestOptions.method, 'POST');
  assert.equal(requestOptions.headers['Content-Type'], 'application/json');
  assert.deepEqual(JSON.parse(requestOptions.body), payload);
  assert.deepEqual(result, { message: 'Sold AAPL' });
});
