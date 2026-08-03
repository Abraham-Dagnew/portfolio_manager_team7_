"""
Idempotency support for mutating endpoints (buy, sell, deposit, withdraw).

If a client doesn't receive a response for a request - a timeout, a
dropped connection - it can't tell whether the operation actually
happened server-side. Retrying a plain POST /portfolio in that
situation risks buying the same shares twice.

The fix: the caller sends the same Idempotency-Key header on every
attempt of the same logical request. The first attempt runs normally
and its result (success or domain error) is cached against that key.
Any later request with the same key replays the cached result instead
of executing the operation again.
"""

from typing import Callable

import persistence
from errors import DomainError, ReplayedError


def run_idempotent(key: str | None, endpoint: str, operation: Callable[[], dict]) -> dict:
    """
    Runs `operation()` exactly once per (key, endpoint) pair.

    If `key` is None, idempotency is skipped entirely and the
    operation just runs normally - the header is optional, not
    required, so existing clients aren't broken.
    """

    if not key:
        return operation()

    with persistence.transaction() as cursor:
        cached = persistence.fetch_idempotent_response(cursor, key, endpoint)

    if cached is not None:
        if cached["status_code"] >= 400:
            raise ReplayedError(cached["body"].get("detail", "Request failed."), cached["status_code"])
        return cached["body"]

    try:
        result = operation()
    except DomainError as exc:
        with persistence.transaction() as cursor:
            persistence.store_idempotent_response(cursor, key, endpoint, exc.status_code, {"detail": exc.message})
        raise

    with persistence.transaction() as cursor:
        persistence.store_idempotent_response(cursor, key, endpoint, 200, result)

    return result
