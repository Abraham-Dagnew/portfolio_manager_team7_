"""
Tests for the persistence layer's SQL-building functions.

These use a lightweight fake cursor and assert on the SQL text and
parameters passed to execute() - no real database involved.
"""

import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import persistence


class FakeCursor:
    def __init__(self, fetchone_result=None, fetchall_result=None, lastrowid=None):
        self.fetchone_result = fetchone_result
        self.fetchall_result = fetchall_result or []
        self.lastrowid = lastrowid
        self.executed = []

    def execute(self, query, params=None):
        self.executed.append((query, params))

    def fetchone(self):
        return self.fetchone_result

    def fetchall(self):
        return self.fetchall_result


class PersistenceTests(unittest.TestCase):
    def test_fetch_all_transactions_orders_by_date_then_id(self):
        cursor = FakeCursor(fetchall_result=[{"id": 1}])

        result = persistence.fetch_all_transactions(cursor)

        sql = cursor.executed[0][0]
        self.assertIn("ORDER BY purchaseDate ASC, id ASC", sql)
        self.assertEqual(result, [{"id": 1}])

    def test_fetch_ticker_history_orders_by_date_then_id(self):
        cursor = FakeCursor(fetchall_result=[{"side": "buy", "quantity": 10, "purchasePrice": 100.0}])

        result = persistence.fetch_ticker_history(cursor, "AAPL")

        sql, params = cursor.executed[0]
        self.assertIn("ORDER BY purchaseDate ASC, id ASC", sql)
        self.assertEqual(params, ("AAPL",))
        self.assertEqual(result, [{"side": "buy", "quantity": 10, "purchasePrice": 100.0}])

    def test_fetch_latest_buy_type_returns_none_when_missing(self):
        cursor = FakeCursor(fetchone_result=None)

        result = persistence.fetch_latest_buy_type(cursor, "AAPL")

        self.assertIsNone(result)

    def test_fetch_balance_returns_none_when_missing(self):
        cursor = FakeCursor(fetchone_result=None)

        self.assertIsNone(persistence.fetch_balance(cursor))

    def test_insert_buy_returns_new_id(self):
        cursor = FakeCursor(lastrowid=42)

        new_id = persistence.insert_buy(cursor, "AAPL", "stock", 10, 150.25, "2026-01-15")

        self.assertEqual(new_id, 42)
        sql, params = cursor.executed[0]
        self.assertIn("'buy'", sql)
        self.assertEqual(params, ("AAPL", "stock", 10, 150.25, "2026-01-15"))

    def test_insert_sell_returns_new_id(self):
        cursor = FakeCursor(lastrowid=43)

        new_id = persistence.insert_sell(cursor, "AAPL", "stock", 5, 200.0, "2026-02-01", 500.0)

        self.assertEqual(new_id, 43)
        sql, params = cursor.executed[0]
        self.assertIn("'sell'", sql)
        self.assertEqual(params, ("AAPL", "stock", 5, 200.0, "2026-02-01", 500.0))

    def test_fetch_idempotent_response_returns_none_when_missing(self):
        cursor = FakeCursor(fetchone_result=None)

        self.assertIsNone(persistence.fetch_idempotent_response(cursor, "key-1", "POST /portfolio"))

    def test_fetch_idempotent_response_parses_stored_json(self):
        cursor = FakeCursor(fetchone_result={"status_code": 200, "response_body": '{"id": 7}'})

        result = persistence.fetch_idempotent_response(cursor, "key-1", "POST /portfolio")

        self.assertEqual(result, {"status_code": 200, "body": {"id": 7}})

    def test_store_idempotent_response_uses_insert_ignore(self):
        cursor = FakeCursor()

        persistence.store_idempotent_response(cursor, "key-1", "POST /portfolio", 200, {"id": 7})

        sql, params = cursor.executed[0]
        self.assertIn("INSERT IGNORE INTO idempotency_keys", sql)
        self.assertEqual(params, ("key-1", "POST /portfolio", 200, '{"id": 7}'))


if __name__ == "__main__":
    unittest.main()
