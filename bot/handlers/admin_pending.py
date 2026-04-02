"""Admin handler: view and claim pending orders."""

import logging
import math
import re

from telegram import Update
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes

from app.database import get_session
from app.services import order_service
from bot.keyboards.admin_kb import pending_orders_keyboard
from bot.middlewares.auth import require_admin
from bot.utils.formatters import format_order_for_admin, format_order_for_admin_detail
from bot.utils.notifications import notify_customer

logger = logging.getLogger(__name__)

PAGE_SIZE = 5


def _build_pending_text(orders, page: int, total: int) -> str:
    """Build the text body for the pending-orders list."""
    total_pages = max(1, math.ceil(total / PAGE_SIZE))
    if not orders:
        return "No pending orders right now."

    lines = [f"Pending Orders (page {page}/{total_pages}, {total} total)\n"]
    for order in orders:
        lines.append(format_order_for_admin(order))
        lines.append("")
    return "\n".join(lines)


async def _send_pending_page(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    page: int,
    *,
    edit: bool = False,
):
    """Fetch page *page* of pending orders and send / edit message."""
    offset = (page - 1) * PAGE_SIZE

    with get_session() as session:
        orders, total = order_service.get_pending_orders(
            session, limit=PAGE_SIZE, offset=offset
        )
        total_pages = max(1, math.ceil(total / PAGE_SIZE))
        text = _build_pending_text(orders, page, total)
        keyboard = pending_orders_keyboard(orders, page=page, total_pages=total_pages)

    if edit and update.callback_query:
        await update.callback_query.edit_message_text(
            text=text, reply_markup=keyboard
        )
    else:
        await update.effective_message.reply_text(text=text, reply_markup=keyboard)


@require_admin
async def pending_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/pending - list pending orders (page 1)."""
    await _send_pending_page(update, context, page=1)


@require_admin
async def pending_page_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle pagination: pending_page_{n}."""
    query = update.callback_query
    await query.answer()

    match = re.match(r"^pending_page_(\d+)$", query.data)
    if not match:
        return
    page = int(match.group(1))
    await _send_pending_page(update, context, page=page, edit=True)


@require_admin
async def claim_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle claim_{order_id}_{version} callback."""
    query = update.callback_query
    await query.answer()

    match = re.match(r"^claim_(\d+)_(\d+)$", query.data)
    if not match:
        return

    order_id = int(match.group(1))
    expected_version = int(match.group(2))
    admin_id = context.user_data["admin_id"]

    with get_session() as session:
        order = order_service.claim_order(
            session, order_id, admin_id, expected_version
        )

        if order is None:
            # Optimistic-lock conflict: order was already claimed or changed.
            await query.edit_message_text(
                text=f"Order #{order_id} was already claimed or is no longer pending."
            )
            # Send a refreshed list as a new message so the admin can continue.
            await _send_pending_page(update, context, page=1)
            return

        # Success -- show the admin the full order detail.
        detail = format_order_for_admin_detail(order)
        text = f"You claimed this order.\n\n{detail}"
        await query.edit_message_text(text=text)

        # Notify the customer.
        customer_id = order.customer_id
        customer_text = (
            f"Your order #{order.id} has been picked up by a driver "
            f"and is on its way!"
        )

    await notify_customer(context.bot, customer_id, customer_text)


# ---------------------------------------------------------------------------
# Handler registration
# ---------------------------------------------------------------------------

def get_handlers():
    """Return the list of handlers to register on the Application."""
    return [
        CommandHandler("pending", pending_command),
        CallbackQueryHandler(pending_page_callback, pattern=r"^pending_page_\d+$"),
        CallbackQueryHandler(claim_callback, pattern=r"^claim_\d+_\d+$"),
    ]
