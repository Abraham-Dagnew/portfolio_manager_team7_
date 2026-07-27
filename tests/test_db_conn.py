"""
Tests for the MySQL connection helper and table setup.
"""

import os
import sys
import unittest
from unittest.mock import patch

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import db_conn


class DbConnTests(unittest.TestCase):
    @patch("db_conn.mysql.connector.connect")
    def test_get_connection_uses_environment_values(self, mock_connect):
        """
        Verifies the connection helper passes environment values to MySQL.
        """

        with patch.dict("os.environ", {
            "DB_HOST": "127.0.0.1",
            "DB_PORT": "3306",
            "DB_USER": "pm_user",
            "DB_PASS": "secret",
            "DB_NAME": "portfolio_db",
        }, clear=False):
            db_conn.get_connection()

        mock_connect.assert_called_once_with(
            host="127.0.0.1",
            port=3306,
            user="pm_user",
            password="secret",
            database="portfolio_db",
        )

    @patch("db_conn.mysql.connector.connect")
    def test_create_table_runs_expected_sql(self, mock_connect):
        """
        Verifies the table creation helper executes the expected SQL.
        """

        fake_conn = mock_connect.return_value
        fake_cursor = fake_conn.cursor.return_value

        db_conn.create_table()

        fake_cursor.execute.assert_called_once()
        sql = fake_cursor.execute.call_args[0][0]
        self.assertIn("CREATE TABLE IF NOT EXISTS portfolio", sql)
        self.assertIn("ticker VARCHAR(10)", sql)
        fake_conn.commit.assert_called_once()


if __name__ == "__main__":
    unittest.main()
