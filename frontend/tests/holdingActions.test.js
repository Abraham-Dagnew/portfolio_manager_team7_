import test from 'node:test';
import assert from 'node:assert/strict';

import { addHolding, deleteHolding } from '../static/js/api.js';

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

test('deleteHolding calls DELETE on the holding id', async () => {
  let calledUrl;
  let requestOptions;
  mockFetch((url, options) => {
    calledUrl = url;
    requestOptions = options;
    return mockResponse({ jsonData: { message: 'Holding deleted' } });
  });

  const result = await deleteHolding(8);

  assert.equal(calledUrl, 'http://127.0.0.1:8000/portfolio/8');
  assert.equal(requestOptions.method, 'DELETE');
  assert.deepEqual(result, { message: 'Holding deleted' });
});
