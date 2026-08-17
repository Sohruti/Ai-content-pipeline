"""Structured logging for the 2OS Content Operating System."""

import logging
import sys
from rich.logging import RichHandler


def get_logger(name: str) -> logging.Logger:
    """Get a configured logger with rich formatting."""
    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = RichHandler(
            rich_tracebacks=True,
            show_path=False,
            markup=True,
        )
        handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

    return logger
