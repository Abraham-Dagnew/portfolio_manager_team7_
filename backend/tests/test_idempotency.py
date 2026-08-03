"""
Unit tests for the idempotency wrapper.

Persistence is faked out with a simple cursor double and a fake
`transaction()` context manager, mirroring the pattern used in
test_services.py.
"""

import os
import sys
import unittest
from contextlib import contextmanager
from unittest.mock import patch

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from errors import InsufficientFundsError, ReplayedError
from idempotency import run_idempotent


class FakeCursor:
    def __init__(self, fetchone_results=None):
        self.fetchone_results = list(fetchone_results) if fetchone_results else []
        self.executed = []

    def execute(self, query, params=None):
        self.executed.append((query, params))

    def fetchone(self):
        if self.fetchone_results:
            return self.fetchone_results.pop(0)
        return None


def fake_transaction(cursor):
    @contextmanager
    def _transaction():
        yield cursor

    return _transaction


class RunIdempotentTests(unittest.TestCase):
    def test_runs_operation_directly_when_no_key_given(self):
        calls = []

        def operation():
            calls.append(1)
            return {"message": "done"}

        result = run_idempotent(None, "POST /portfolio", operation)

        self.assertEqual(result, {"message": "done"})
        self.assertEqual(len(calls), 1)

    def test_runs_and_caches_operation_on_first_call(self):
        cursor = FakeCursor(fetchone_results=[None])
        calls = []

        def operation():
            calls.append(1)
            return {"message": "Holding added", "id": 7}

        with patch("idempotency.persistence.transaction", fake_transaction(cursor)):
            result = run_idempotent("key-123", "POST /portfolio", operation)

        self.assertEqual(result, {"message": "Holding added", "id": 7})
        self.assertEqual(len(calls), 1)

        # Second execute() call should be the INSERT IGNORE storing the response.
        store_sql = cursor.executed[1][0]
        self.assertIn("INSERT IGNORE INTO idempotency_keys", store_sql)

    def test_replays_cached_success_without_rerunning_operation(self):
        cursor = FakeCursor(fetchone_results=[{"status_code": 200, "response_body": '{"message": "Holding added", "id": 7}'}])
        calls = []

        def operation():
            calls.append(1)
            return {"message": "should not run"}

        with patch("idempotency.persistence.transaction", fake_transaction(cursor)):
            result = run_idempotent("key-123", "POST /portfolio", operation)

        self.assertEqual(result, {"message": "Holding added", "id": 7})
        self.assertEqual(len(calls), 0)

    def test_replays_cached_error_without_rerunning_operation(self):
        cursor = FakeCursor(
            fetchone_results=[{"status_code": 400, "response_body": '{"detail": "Insufficient funds: ..."}'}]
        )
        calls = []

        def operation():
            calls.append(1)
            return {"message": "should not run"}

        with patch("idempotency.persistence.transaction", fake_transaction(cursor)):
            with self.assertRaises(ReplayedError) as ctx:
                run_idempotent("key-123", "POST /portfolio", operation)

        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("Insufficient funds", ctx.exception.message)
        self.assertEqual(len(calls), 0)

    def test_caches_a_domain_error_raised_by_the_operation(self):
        cursor = FakeCursor(fetchone_results=[None])

        def operation():
            raise InsufficientFundsError("Insufficient funds: this purchase costs $100 but you only have $10 available.")

        with patch("idempotency.persistence.transaction", fake_transaction(cursor)):
            with self.assertRaises(InsufficientFundsError):
                run_idempotent("key-123", "POST /portfolio", operation)

        store_sql, store_params = cursor.executed[1]
        self.assertIn("INSERT IGNORE INTO idempotency_keys", store_sql)
        self.assertEqual(store_params[2], 400)


if __name__ == "__main__":
    unittest.main()
