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
        ticker (VARCHAR(10)): Stock/bond symbol, e.g. "AAPL".
        type (ENUM): One of 'stock', 'bond', 'cash'.
        quantity (DECIMAL(10,4)): Number of units held.
        purchasePrice (DECIMAL(10,2)): Price per unit at time of purchase.
        purchaseDate (DATE): Date the asset was acquired.

    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS portfolio (
            id INT AUTO_INCREMENT PRIMARY KEY,
            ticker VARCHAR(10) NOT NULL,
            type ENUM('stock', 'bond', 'cash') NOT NULL,
            quantity DECIMAL(10,4) NOT NULL,
            purchasePrice DECIMAL(10,2) NOT NULL,
            purchaseDate DATE NOT NULL
        )
    """)
    conn.commit()
    cursor.close()
    conn.close()
    print("Table created successfully!")


if __name__ == "__main__":
    create_table()