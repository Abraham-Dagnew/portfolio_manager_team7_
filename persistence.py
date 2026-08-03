"""
Persistence layer: the only place in the codebase that writes raw SQL.

Every function here takes an already-open cursor and does exactly one
thing - no business rules, no HTTP concerns. Multi-step operations
(e.g. "check balance, insert a transaction, update balance") are
composed by the service layer inside a single `transaction()` block,
so they commit or roll back together.
"""

from contextlib import contextmanager

from db_conn import get_connection


@contextmanager
def transaction():
    """
    Opens a connection + dictionary cursor, commits on success, and
    rolls back on any exception. Yields the cursor for callers to run
    one or more persistence functions against.
    """

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        yield cursor
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def fetch_all_transactions(cursor) -> list[dict]:
    cursor.execute("SELECT * FROM portfolio ORDER BY purchaseDate ASC, id ASC")
    return cursor.fetchall()


def fetch_net_quantity(cursor, ticker: str) -> float:
    cursor.execute(
        """
        SELECT COALESCE(SUM(CASE WHEN side = 'buy' THEN quantity ELSE -quantity END), 0) AS quantity
        FROM portfolio
        WHERE ticker = %s
    """,
        (ticker,),
    )
    row = cursor.fetchone()
    return float(row["quantity"] if row and row["quantity"] is not None else 0.0)


def fetch_latest_buy_type(cursor, ticker: str) -> str | None:
    cursor.execute(
        """
        SELECT type
        FROM portfolio
        WHERE ticker = %s AND side = 'buy'
        ORDER BY purchaseDate ASC, id ASC
        LIMIT 1
    """,
        (ticker,),
    )
    row = cursor.fetchone()
    return row["type"] if row else None


def fetch_balance(cursor) -> float | None:
    cursor.execute("SELECT cash FROM balance WHERE id = 1")
    row = cursor.fetchone()
    return float(row["cash"]) if row else None


def update_balance(cursor, new_balance: float) -> None:
    cursor.execute("UPDATE balance SET cash = %s WHERE id = 1", (new_balance,))


def insert_buy(cursor, ticker: str, asset_type: str, quantity: float, purchase_price: float, purchase_date: str) -> int:
    cursor.execute(
        """
        INSERT INTO portfolio (ticker, type, side, quantity, purchasePrice, purchaseDate)
        VALUES (%s, %s, 'buy', %s, %s, %s)
    """,
        (ticker, asset_type, quantity, purchase_price, purchase_date),
    )
    return cursor.lastrowid


def insert_sell(cursor, ticker: str, asset_type: str, quantity: float, price: float, sold_date: str) -> int:
    cursor.execute(
        """
        INSERT INTO portfolio (ticker, type, side, quantity, purchasePrice, purchaseDate)
        VALUES (%s, %s, 'sell', %s, %s, %s)
    """,
        (ticker, asset_type, quantity, price, sold_date),
    )
    return cursor.lastrowid
