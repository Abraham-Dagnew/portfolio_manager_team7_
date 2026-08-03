"""
Domain-level errors for the portfolio manager.

These represent business-rule violations (insufficient funds, unknown
ticker, etc.) as distinct from framework/validation errors. The web
layer (main.py) catches DomainError once, globally, and converts it
into an HTTP response - services and persistence code never need to
know about HTTP status codes.
"""


class DomainError(Exception):
    """Base class for business-rule violations that should be shown to the user."""

    status_code = 400

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class InvalidTickerError(DomainError):
    """Raised when a ticker doesn't resolve to a real, tradeable asset."""

    status_code = 400


class TickerNotFoundError(DomainError):
    """Raised when a price lookup for a ticker comes back empty."""

    status_code = 404


class InsufficientFundsError(DomainError):
    """Raised when a purchase or withdrawal would exceed the cash balance."""

    status_code = 400


class InsufficientSharesError(DomainError):
    """Raised when a sell order exceeds the shares actually owned."""

    status_code = 400


class NoTransactionsFoundError(DomainError):
    """Raised when there's no buy history for a ticker being sold."""

    status_code = 404


class BalanceNotInitializedError(DomainError):
    """Raised when the balance table hasn't been seeded (db_conn.py wasn't run)."""

    status_code = 500
