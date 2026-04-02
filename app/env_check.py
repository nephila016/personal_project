"""Validate required environment variables before startup."""

import os
import sys

from dotenv import load_dotenv

load_dotenv()

REQUIRED_VARS = {
    "DATABASE_URL": "PostgreSQL connection string",
    "TELEGRAM_BOT_TOKEN": "Bot token from @BotFather",
    "FLASK_SECRET_KEY": "Random secret for Flask sessions",
}

REQUIRED_FOR_BOT = {
    "ADMIN_TELEGRAM_IDS": "Comma-separated Telegram IDs for admins",
}


def check_env(for_bot: bool = False):
    """Check that all required env vars are set. Exits on failure."""
    missing = []
    checks = {**REQUIRED_VARS}
    if for_bot:
        checks.update(REQUIRED_FOR_BOT)

    for var, description in checks.items():
        val = os.environ.get(var, "").strip()
        if not val:
            missing.append(f"  {var} — {description}")

    if missing:
        print("FATAL: Missing required environment variables:\n")
        for m in missing:
            print(m)
        print("\nCopy .env.example to .env and fill in the values.")
        sys.exit(1)

    # Validate DATABASE_URL format
    db_url = os.environ.get("DATABASE_URL", "")
    if not db_url.startswith("postgresql"):
        print(f"WARNING: DATABASE_URL doesn't look like PostgreSQL: {db_url[:30]}...")

    # Validate bot token format
    if for_bot:
        token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
        if ":" not in token:
            print("FATAL: TELEGRAM_BOT_TOKEN looks invalid (missing ':').")
            sys.exit(1)

        admin_ids = os.environ.get("ADMIN_TELEGRAM_IDS", "")
        for part in admin_ids.split(","):
            part = part.strip()
            if part and not part.isdigit():
                print(f"FATAL: ADMIN_TELEGRAM_IDS contains non-numeric value: '{part}'")
                sys.exit(1)
