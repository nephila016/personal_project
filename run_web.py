#!/usr/bin/env python3
"""Entry point for the Flask web dashboard."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.env_check import check_env
from app.logging_config import setup_web_logging

check_env(for_bot=False)
setup_web_logging()

from web import create_app

app = create_app()

if __name__ == "__main__":
    debug = os.environ.get("FLASK_ENV") == "development"
    app.run(host="0.0.0.0", port=5000, debug=debug)
