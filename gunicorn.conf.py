"""Gunicorn configuration for production deployment."""

import os

bind = os.environ.get("WEB_BIND", "0.0.0.0:5000")
workers = int(os.environ.get("WEB_WORKERS", 2))
timeout = 120
accesslog = "logs/web_access.log"
errorlog = "logs/web_error.log"
loglevel = "info"
capture_output = True
