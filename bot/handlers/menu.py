"""Handler for persistent reply keyboard button presses."""
import logging

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

# Map button labels (all languages) to command functions
_BUTTON_COMMANDS = {}


def _build_button_map():
    """Build a mapping of button label text -> command string."""
    global _BUTTON_COMMANDS
    for lang in ("ru", "uz"):
        _BUTTON_COMMANDS[t("kb_new_order", lang)] = "/order"
        _BUTTON_COMMANDS[t("kb_my_orders", lang)] = "/myorders"
        _BUTTON_COMMANDS[t("kb_reorder", lang)] = "/reorder"
        _BUTTON_COMMANDS[t("kb_profile", lang)] = "/profile"
        _BUTTON_COMMANDS[t("kb_help", lang)] = "/help"
        _BUTTON_COMMANDS[t("kb_lang", lang)] = "/lang"
        _BUTTON_COMMANDS[t("kb_pending", lang)] = "/pending"
        _BUTTON_COMMANDS[t("kb_active", lang)] = "/myactive"
        _BUTTON_COMMANDS[t("kb_receive", lang)] = "/receive"
        _BUTTON_COMMANDS[t("kb_returns", lang)] = "/returns"
        _BUTTON_COMMANDS[t("kb_stock", lang)] = "/stock"
        _BUTTON_COMMANDS[t("kb_customer_lookup", lang)] = "/customer"


_build_button_map()


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


async def menu_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Route reply keyboard button presses to their corresponding commands."""
    text = update.message.text.strip()
    command = _BUTTON_COMMANDS.get(text)

    if not command:
        return  # Not a menu button, let other handlers deal with it

    # Fake a command message by setting the text and re-processing
    update.message.text = command
    # Process the command through the application's handlers
    await context.application.process_update(update)


def get_handlers():
    # Use a low group number so this handler is checked after ConversationHandlers
    # and only catches messages that look like our menu button labels
    button_labels = list(_BUTTON_COMMANDS.keys())
    menu_filter = filters.TEXT & filters.Regex(
        "^(" + "|".join(map(lambda x: x.replace("(", "\\(").replace(")", "\\)"), button_labels)) + ")$"
    )
    return [MessageHandler(menu_filter, menu_button_handler)]
