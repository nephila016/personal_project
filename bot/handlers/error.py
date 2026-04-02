import logging
import traceback

from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Global error handler. Logs the exception and sends a generic message to the user."""
    logger.error("Exception while handling an update:", exc_info=context.error)

    # Log the full traceback for debugging
    tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    tb_string = "".join(tb_list)
    logger.error(f"Traceback:\n{tb_string}")

    # Attempt to notify the user
    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "Something went wrong. Please try again later.\n"
                "If the problem persists, contact support."
            )
        except Exception:
            # If we can't even send the error message, just log it
            logger.error("Failed to send error message to user.")

    elif isinstance(update, Update) and update.callback_query:
        try:
            await update.callback_query.answer(
                "Something went wrong. Please try again.", show_alert=True
            )
        except Exception:
            logger.error("Failed to send error callback answer to user.")
