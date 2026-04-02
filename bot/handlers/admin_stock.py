"""Admin handler: view current bottle inventory / stock status."""

import logging

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from app.database import get_session
from app.services import bottle_service
from bot.middlewares.auth import require_admin
from bot.utils.formatters import format_admin_inventory
from config import Config

logger = logging.getLogger(__name__)


@require_admin
async def stock_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/stock - display admin's bottle inventory with low-stock warnings."""
    admin_id = context.user_data["admin_id"]

    with get_session() as session:
        inv = bottle_service.get_admin_inventory(session, admin_id)

    text = format_admin_inventory(inv)

    # Low-stock warnings
    warnings = []
    current = inv["current_stock"]
    pending = inv["pending_bottles"]

    if current < Config.LOW_STOCK_WARNING_THRESHOLD:
        warnings.append(
            f"Your stock ({current}) is below the warning threshold "
            f"({Config.LOW_STOCK_WARNING_THRESHOLD}). Use /receive to restock."
        )

    if current < pending:
        warnings.append(
            f"Your stock ({current}) is less than pending delivery "
            f"requirements ({pending} bottles across {inv['pending_orders']} orders). "
            "Some deliveries may fail."
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
