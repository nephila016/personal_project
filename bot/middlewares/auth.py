import functools
import logging

from telegram import Update
from telegram.ext import ContextTypes

from app.database import get_session
from app.models.admin import Admin
from app.models.customer import Customer

logger = logging.getLogger(__name__)


def require_customer(func):
    """Decorator: requires the user to be a registered, active customer."""

    @functools.wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        if not user:
            return

        with get_session() as session:
            customer = (
                session.query(Customer)
                .filter(Customer.telegram_id == user.id)
                .first()
            )

        if not customer:
            await update.effective_message.reply_text(
                "Please register first with /start"
            )
            return

        if not customer.is_active:
            await update.effective_message.reply_text(
                "Your account has been deactivated. Contact support."
            )
            return

        context.user_data["customer_id"] = customer.id
        return await func(update, context)

    return wrapper


def require_admin(func):
    """Decorator: requires the user to be a registered, active admin."""

    @functools.wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        if not user:
            return

        with get_session() as session:
            admin = (
                session.query(Admin)
                .filter(Admin.telegram_id == user.id, Admin.is_active == True)
                .first()
            )

        if not admin:
            return  # Silent ignore for non-admins

        context.user_data["admin_id"] = admin.id
        return await func(update, context)

    return wrapper
