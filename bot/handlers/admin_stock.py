"""Admin handler: view current bottle inventory / stock status."""

import logging

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from app.database import get_session
from app.services import bottle_service
from bot.middlewares.auth import require_admin
from bot.utils.i18n import get_lang, t
from config import Config

logger = logging.getLogger(__name__)


def _format_inventory(inv: dict, lang: str) -> str:
    """Format the inventory dict in the admin's language."""
    sep = t("stock_separator", lang)
    lines = [
        t("stock_header", lang),
        sep,
        t("stock_received", lang, n=inv["total_received"]),
        t("stock_delivered", lang, n=inv["total_delivered"]),
        t("stock_current", lang, n=inv["current_stock"]),
        sep,
        t("stock_empties", lang, n=inv["empties_collected"]),
        sep,
        t("stock_pending", lang, bottles=inv["pending_bottles"],
          orders=inv["pending_orders"]),
    ]
    return "\n".join(lines)


@require_admin
async def stock_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/stock - display admin's bottle inventory with low-stock warnings."""
    lang = get_lang(context)
    admin_id = context.user_data["admin_id"]

    with get_session() as session:
        inv = bottle_service.get_admin_inventory(session, admin_id)

    text = _format_inventory(inv, lang)

    # Low-stock warnings
    warnings: list[str] = []
    current = inv["current_stock"]
    pending = inv["pending_bottles"]

    if current < Config.LOW_STOCK_WARNING_THRESHOLD:
        warnings.append(
            t("stock_low_warning_full", lang,
              current=current, threshold=Config.LOW_STOCK_WARNING_THRESHOLD)
        )

    if current < pending:
        warnings.append(
            t("stock_insufficient_for_pending", lang,
              current=current, pending=pending, orders=inv["pending_orders"])
        )

    if warnings:
        text += "\n\n" + "\n".join(warnings)

    await update.message.reply_text(text)


# ---------------------------------------------------------------------------
# Handler registration
# ---------------------------------------------------------------------------

def get_handlers():
    """Return the list of handlers to register on the Application."""
    return [
        CommandHandler("stock", stock_command),
    ]
