"""Centralized logging configuration for bot and web processes.

Log files:
    logs/bot.log         — All bot activity (INFO+)
    logs/web.log         — All web activity (INFO+)
    logs/error.log       — Errors only from both processes (ERROR+)
    logs/orders.log      — Order lifecycle events (creation, claim, delivery, cancel)
    logs/bottles.log     — Bottle inventory events (receipts, returns, stock changes)

All logs rotate at 5 MB, keeping 5 backups.
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)-30s | %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
MAX_BYTES = 5 * 1024 * 1024  # 5 MB
BACKUP_COUNT = 5


def _make_handler(filename: str, level: int = logging.INFO) -> RotatingFileHandler:
    os.makedirs(LOG_DIR, exist_ok=True)
    handler = RotatingFileHandler(
        os.path.join(LOG_DIR, filename),
        maxBytes=MAX_BYTES,
        backupCount=BACKUP_COUNT,
        encoding="utf-8",
    )
    handler.setLevel(level)
    handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT))
    return handler


def setup_bot_logging():
    """Configure logging for the bot process."""
    root = logging.getLogger()
    root.setLevel(logging.INFO)

    # Console
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    console.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT))
    root.addHandler(console)

    # Main bot log
    root.addHandler(_make_handler("bot.log", logging.INFO))

    # Error-only log
    root.addHandler(_make_handler("error.log", logging.ERROR))

    # Order lifecycle log
    order_logger = logging.getLogger("orders")
    order_logger.addHandler(_make_handler("orders.log", logging.INFO))

    # Bottle inventory log
    bottle_logger = logging.getLogger("bottles")
    bottle_logger.addHandler(_make_handler("bottles.log", logging.INFO))

    # Quiet noisy libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("apscheduler").setLevel(logging.WARNING)
    logging.getLogger("telegram.ext._updater").setLevel(logging.WARNING)


def setup_web_logging():
    """Configure logging for the web process."""
    root = logging.getLogger()
    root.setLevel(logging.INFO)

    # Console
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    console.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT))
    root.addHandler(console)

    # Main web log
    root.addHandler(_make_handler("web.log", logging.INFO))

    # Error-only log (shared file with bot)
    root.addHandler(_make_handler("error.log", logging.ERROR))

    # Quiet noisy libraries
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
