"""Handler for persistent reply keyboard button presses.

Simple commands (help, lang, myorders, pending, stock) are called directly.
Conversation-based commands are handled by adding MessageHandler entry points
to the ConversationHandlers (see each handler module).
"""
import logging
import re

from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters

from app.database import get_session
from app.models.admin import Admin
from app.models.customer import Customer
from bot.keyboards.customer_kb import (
    admin_reply_keyboard,
    customer_reply_keyboard,
    dual_role_reply_keyboard,
)
from bot.utils.i18n import get_lang, t

logger = logging.getLogger(__name__)


def get_reply_keyboard(user_id: int, lang: str):
    """Determine the correct reply keyboard for a user based on their roles."""
    with get_session() as session:
        is_customer = (
            session.query(Customer)
            .filter(Customer.telegram_id == user_id, Customer.is_active == True)
            .first()
        ) is not None
        is_admin = (
            session.query(Admin)
            .filter(Admin.telegram_id == user_id, Admin.is_active == True)
            .first()
        ) is not None

    if is_customer and is_admin:
        return dual_role_reply_keyboard(lang)
    elif is_admin:
        return admin_reply_keyboard(lang)
    elif is_customer:
        return customer_reply_keyboard(lang)
    return customer_reply_keyboard(lang)


def _regex_for(*i18n_keys: str) -> str:
    """Build a regex pattern matching button labels across all languages."""
    labels = []
    for key in i18n_keys:
        for lang in ("ru", "uz"):
            label = t(key, lang)
            labels.append(re.escape(label))
    return "^(" + "|".join(labels) + ")$"


# Filters for each button — used by ConversationHandler entry_points
# and by the simple-command handler below.
FILTER_ORDER = filters.Regex(_regex_for("kb_new_order"))
FILTER_MY_ORDERS = filters.Regex(_regex_for("kb_my_orders"))
FILTER_REORDER = filters.Regex(_regex_for("kb_reorder"))
FILTER_PROFILE = filters.Regex(_regex_for("kb_profile"))
FILTER_HELP = filters.Regex(_regex_for("kb_help"))
FILTER_LANG = filters.Regex(_regex_for("kb_lang"))
FILTER_PENDING = filters.Regex(_regex_for("kb_pending"))
FILTER_ACTIVE = filters.Regex(_regex_for("kb_active"))
FILTER_RECEIVE = filters.Regex(_regex_for("kb_receive"))
FILTER_RETURNS = filters.Regex(_regex_for("kb_returns"))
FILTER_STOCK = filters.Regex(_regex_for("kb_stock"))
FILTER_CUSTOMER = filters.Regex(_regex_for("kb_customer_lookup"))


async def _handle_simple_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle non-conversation buttons by calling the command function directly."""
    text = update.message.text.strip()

    try:
        for lang in ("ru", "uz"):
            if text == t("kb_my_orders", lang):
                from bot.handlers.my_orders import myorders_command
                return await myorders_command(update, context)
            if text == t("kb_help", lang):
                from bot.handlers.help import help_command
                return await help_command(update, context)
            if text == t("kb_lang", lang):
                from bot.handlers.lang import lang_command
                return await lang_command(update, context)
            if text == t("kb_pending", lang):
                from bot.handlers.admin_pending import pending_command
                return await pending_command(update, context)
            if text == t("kb_active", lang):
                from bot.handlers.admin_active import myactive_command
                return await myactive_command(update, context)
            if text == t("kb_stock", lang):
                from bot.handlers.admin_stock import stock_command
                return await stock_command(update, context)
    except Exception:
        logger.exception("Error handling menu button '%s'", text)
        lang = get_lang(context)
        await update.message.reply_text(t("error_generic", lang))


# Simple (non-conversation) button filter
SIMPLE_FILTER = (
    FILTER_MY_ORDERS | FILTER_HELP | FILTER_LANG |
    FILTER_PENDING | FILTER_ACTIVE | FILTER_STOCK
)


def get_handlers():
    return [MessageHandler(SIMPLE_FILTER, _handle_simple_button)]
