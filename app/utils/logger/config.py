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
