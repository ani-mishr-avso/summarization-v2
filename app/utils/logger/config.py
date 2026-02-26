"""
Central logging configuration. Level from LOG_LEVEL env (default INFO).
"""

import logging
import os


def configure_logging() -> None:
    """Configure root logger: StreamHandler on stderr, timestamp/level/name/message format, level from env."""
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    if not isinstance(level, int):
        level = logging.INFO

    fmt = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    formatter = logging.Formatter(fmt)

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(level)
    if not root.handlers:
        root.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    """Return a logger for the given name. Use after configure_logging() for consistent config."""
    return logging.getLogger(name)
