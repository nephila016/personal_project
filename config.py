import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://localhost/water_dis")
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.environ.get("FLASK_SECRET_KEY", "dev-secret-change-me")

    TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    ADMIN_TELEGRAM_IDS = [
        int(x.strip())
        for x in os.environ.get("ADMIN_TELEGRAM_IDS", "").split(",")
        if x.strip()
    ]
    ADMIN_GROUP_CHAT_ID = os.environ.get("ADMIN_GROUP_CHAT_ID", "")
    BOT_MODE = os.environ.get("BOT_MODE", "polling")

    MAX_BOTTLES_PER_ORDER = int(os.environ.get("MAX_BOTTLES_PER_ORDER", 50))
    MAX_PENDING_ORDERS_PER_CUSTOMER = int(
        os.environ.get("MAX_PENDING_ORDERS_PER_CUSTOMER", 3)
    )
    DUPLICATE_ORDER_COOLDOWN_SECONDS = int(
        os.environ.get("DUPLICATE_ORDER_COOLDOWN_SECONDS", 60)
    )
    MAX_RECEIPT_QUANTITY = int(os.environ.get("MAX_RECEIPT_QUANTITY", 1000))

    STALE_ORDER_HOURS = int(os.environ.get("STALE_ORDER_HOURS", 24))
    LOW_STOCK_WARNING_THRESHOLD = int(
        os.environ.get("LOW_STOCK_WARNING_THRESHOLD", 10)
    )

    LOGIN_MAX_ATTEMPTS = int(os.environ.get("LOGIN_MAX_ATTEMPTS", 10))
    LOGIN_LOCKOUT_MINUTES = int(os.environ.get("LOGIN_LOCKOUT_MINUTES", 30))


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "postgresql://localhost/water_dis_test"


config_map = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestConfig,
}
