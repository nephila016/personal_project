import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes

from bot.utils.i18n import get_lang, t

logger = logging.getLogger(__name__)


def _lang_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("\U0001f1f7\U0001f1fa Русский", callback_data="lang_pick_ru"),
                InlineKeyboardButton("\U0001f1fa\U0001f1ff O'zbekcha", callback_data="lang_pick_uz"),
            ]
        ]
    )


async def lang_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show language picker."""
    lang = get_lang(context)
    await update.message.reply_text(
        t("choose_language", lang),
        reply_markup=_lang_keyboard(),
    )


async def lang_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle language selection callback."""
    query = update.callback_query
    await query.answer()

    lang_code = query.data.split("_")[-1]  # "ru" or "uz"
    context.user_data["lang"] = lang_code

    await query.edit_message_text(t("lang_selected", lang_code))


lang_handler = CommandHandler("lang", lang_command)
lang_callback_handler = CallbackQueryHandler(lang_callback, pattern=r"^lang_pick_(ru|uz)$")


def get_handlers():
    return [lang_handler, lang_callback_handler]
