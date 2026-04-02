#!/usr/bin/env python3
"""Seed script: creates initial global admin and optionally pre-registers admins from .env."""
import os
import secrets
import string
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv

load_dotenv()

from app.database import Base, get_engine, get_session
from app.models import Admin, GlobalAdmin  # noqa: F401 - needed for table creation
from config import Config


def generate_password(length: int = 16) -> str:
    chars = string.ascii_letters + string.digits + "!@#$%"
    return "".join(secrets.choice(chars) for _ in range(length))


def seed():
    engine = get_engine()
    Base.metadata.create_all(engine)

    with get_session() as session:
        # Create global admin if none exists
        existing = session.query(GlobalAdmin).filter(GlobalAdmin.username == "admin").first()
        if existing:
            print("Global admin 'admin' already exists. Skipping.")
        else:
            password = generate_password()
            admin = GlobalAdmin(
                username="admin",
                full_name="Global Admin",
                must_change_password=True,
            )
            admin.set_password(password)
            session.add(admin)
            print("=" * 50)
            print("Global admin created:")
            print(f"  Username: admin")
            print(f"  Password: {password}")
            print("  (You will be asked to change this on first login)")
            print("=" * 50)

        # Pre-register Telegram admins from .env
        if Config.ADMIN_TELEGRAM_IDS:
            for tid in Config.ADMIN_TELEGRAM_IDS:
                existing = session.query(Admin).filter(Admin.telegram_id == tid).first()
                if existing:
                    print(f"Admin with Telegram ID {tid} already exists. Skipping.")
                else:
                    admin = Admin(
                        telegram_id=tid,
                        full_name=f"Admin {tid}",
                    )
                    session.add(admin)
                    print(f"Telegram admin registered: ID {tid}")
                    print(f"  (Update their name via the web dashboard)")

        session.commit()

    print("\nSeed complete. Run the bot with: python run_bot.py")
    print("Run the web dashboard with: python run_web.py")


if __name__ == "__main__":
    seed()
