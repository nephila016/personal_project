#!/usr/bin/env python3
"""Entry point for the Telegram bot."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.env_check import check_env
from app.logging_config import setup_bot_logging

check_env(for_bot=True)
setup_bot_logging()

from bot.main import run

if __name__ == "__main__":
    run()
