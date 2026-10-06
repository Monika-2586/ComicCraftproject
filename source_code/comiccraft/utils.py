"""Small shared helpers."""

from __future__ import annotations

import time
from typing import Callable, TypeVar

T = TypeVar("T")


def with_retries(
    func: Callable[[], T],
    attempts: int = 3,
    base_delay: float = 2.0,
) -> T:
    """Call ``func`` and retry with exponential backoff if it raises.

    Gemini calls can fail temporarily (rate limits, overload), so a short
    backoff makes the app far more reliable for demos.
    """
    last_error: Exception | None = None
    for attempt in range(attempts):
        try:
            return func()
        except Exception as exc:  # noqa: BLE001 - we re-raise after the last attempt
            last_error = exc
            if attempt < attempts - 1:
                time.sleep(base_delay * (2**attempt))
    assert last_error is not None
    raise last_error
