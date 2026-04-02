import logging
import traceback

from telegram import Update
from telegram.ext import ContextTypes

from bot.utils.i18n import get_lang, t

logger = logging.getLogger(__name__)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Global error handler. Logs the exception and sends a generic message to the user."""
    logger.error("Exception while handling an update:", exc_info=context.error)

    # Log the full traceback for debugging
    tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    tb_string = "".join(tb_list)
    logger.error(f"Traceback:\n{tb_string}")

    # Attempt to notify the user
    if isinstance(update, Update):
        lang = get_lang(context)

        if update.effective_message:
            try:
                await update.effective_message.reply_text(t("error_generic", lang))
            except Exception:
                # If we can't even send the error message, just log it
                logger.error("Failed to send error message to user.")

        elif update.callback_query:
            try:
                await update.callback_query.answer(
                    t("error_generic", lang), show_alert=True
                )
            except Exception:
                logger.error("Failed to send error callback answer to user.")
