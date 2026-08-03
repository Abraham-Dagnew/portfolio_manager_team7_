import mysql.connector
from dotenv import load_dotenv
import os

load_dotenv()


def get_connection():
    """
    Opens a new connection to the MySQL database using credentials
    from the .env file.
    """

    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT")),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
        database=os.getenv("DB_NAME")
    )


def create_table():
    """
    Creates the `portfolio` table if it doesn't already exist.

    Table columns:
        id (INT): Auto-incrementing primary key.
        ticker (VARCHAR(10)): Asset symbol, e.g. "AAPL", "SOXL".
        type (ENUM): One of 'stock', 'etf', 'bond', 'cash'.
        quantity (DECIMAL): Number of units held.
        purchasePrice (DECIMAL): Price per unit at purchase.
        purchaseDate (DATE): Date asset was acquired.
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS portfolio (
            id INT AUTO_INCREMENT PRIMARY KEY,
            ticker VARCHAR(10) NOT NULL,
            type ENUM('stock', 'etf', 'bond', 'cash') NOT NULL,
            quantity DECIMAL(10,4) NOT NULL,
            purchasePrice DECIMAL(10,2) NOT NULL,
            purchaseDate DATE NOT NULL
        )
    """)

    conn.commit()

    cursor.close()
    conn.close()

    print("Portfolio table created successfully!")


def update_existing_table():
    """
    Updates an existing portfolio table to support ETF holdings.
    Run this once if the table already exists.
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        ALTER TABLE portfolio
        MODIFY type ENUM('stock', 'etf', 'bond', 'cash') NOT NULL
    """)

    conn.commit()

    cursor.close()
    conn.close()

    print("Portfolio table updated successfully!")


STARTING_BALANCE = 10000.00


def create_balance_table():
    """
    Creates the single-row `balance` table if it doesn't already exist,
    and seeds it with a starting cash balance. This app has no user
    accounts, so there is exactly one balance row (id=1) for the whole
    portfolio.
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS balance (
            id INT PRIMARY KEY,
            cash DECIMAL(12,2) NOT NULL
        )
    """)

    cursor.execute(
        "INSERT IGNORE INTO balance (id, cash) VALUES (1, %s)",
        (STARTING_BALANCE,),
    )

    conn.commit()

    cursor.close()
    conn.close()

    print("Balance table ready.")


if __name__ == "__main__":

    create_table()
    update_existing_table()
    create_balance_table()

