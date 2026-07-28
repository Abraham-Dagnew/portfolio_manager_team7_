import test from 'node:test';
import assert from 'node:assert/strict';

import { getPerformanceData } from '../static/js/api.js';

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

test('getPerformanceData calls the performance endpoint', async () => {
  let calledUrl;
  mockFetch((url) => {
    calledUrl = url;
    return mockResponse({ jsonData: { totalValue: 1000 } });
  });

  const result = await getPerformanceData();

  assert.equal(calledUrl, 'http://127.0.0.1:8000/portfolio/performance');
  assert.deepEqual(result, { totalValue: 1000 });
});
