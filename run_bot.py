#!/usr/bin/env python3
"""Entry point for the Telegram bot."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot.main import run

if __name__ == "__main__":
    run()
