import logging

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from app.database import get_session
from app.models.admin import Admin
from app.models.customer import Customer
from bot.utils.i18n import get_lang, t

logger = logging.getLogger(__name__)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show available commands based on the user's role."""
    user = update.effective_user
    if not user:
        return

    lang = get_lang(context)

    with get_session() as session:
        customer = (
            session.query(Customer)
            .filter(Customer.telegram_id == user.id, Customer.is_active == True)
            .first()
        )
        admin = (
            session.query(Admin)
            .filter(Admin.telegram_id == user.id, Admin.is_active == True)
            .first()
        )
        is_customer = customer is not None
        is_admin = admin is not None

    if is_customer and is_admin:
        text = t("help_customer", lang) + "\n\n" + t("help_admin", lang)
    elif is_admin:
        text = t("help_admin", lang)
    elif is_customer:
        text = t("help_customer", lang)
    else:
        text = t("help_not_registered", lang)

    await update.message.reply_text(text)


help_handler = CommandHandler("help", help_command)


def get_handlers():
    return [help_handler]
