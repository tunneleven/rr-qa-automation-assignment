"""Structured logging helpers for business actions performed during a test."""

from __future__ import annotations

import logging
from typing import Any


def log_action(logger: logging.Logger, action: str, **context: Any) -> None:
    """Log one business action as `action=<name> <key>=<value>` pairs.

    A single key/value shape keeps console output, the HTML report log section,
    and any later log parsing consistent across page objects and fixtures.
    """
    if not context:
        logger.info("action=%s", action)
        return

    details = " ".join(f"{key}={value}" for key, value in context.items())
    logger.info("action=%s %s", action, details)
