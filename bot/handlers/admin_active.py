"""Admin handler: manage in-progress (active) orders."""

import logging
import re

from telegram import Update
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from app.database import get_session
from app.models.order import CanceledBy
from app.services import bottle_service, order_service
from bot.keyboards.admin_kb import active_order_keyboard
from bot.middlewares.auth import require_admin
from bot.utils.formatters import format_order_for_admin
from bot.utils.notifications import notify_customer

logger = logging.getLogger(__name__)

# Conversation state for the cancel-reason flow
CANCEL_REASON = 0


# ---------------------------------------------------------------------------
# /myactive command
# ---------------------------------------------------------------------------

@require_admin
async def myactive_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/myactive - list the admin's own in-progress orders."""
    admin_id = context.user_data["admin_id"]

    with get_session() as session:
        orders = order_service.get_admin_active_orders(session, admin_id)
        if not orders:
            await update.effective_message.reply_text(
                "You have no active (in-progress) orders."
            )
            return

        for order in orders:
            text = format_order_for_admin(order)
            keyboard = active_order_keyboard(order)
            await update.effective_message.reply_text(
                text=text, reply_markup=keyboard
            )


# ---------------------------------------------------------------------------
# Deliver callback
# ---------------------------------------------------------------------------

@require_admin
async def deliver_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle deliver_{order_id}_{version} callback."""
    query = update.callback_query
    await query.answer()

    match = re.match(r"^deliver_(\d+)_(\d+)$", query.data)
    if not match:
        return

    order_id = int(match.group(1))
    expected_version = int(match.group(2))
    admin_id = context.user_data["admin_id"]

    with get_session() as session:
        try:
            order = order_service.mark_delivered(
                session, order_id, admin_id, expected_version
            )
        except ValueError as exc:
            # Insufficient stock
            await query.edit_message_text(text=f"Cannot deliver: {exc}")
            return

        if order is None:
            await query.edit_message_text(
                text=f"Order #{order_id} could not be delivered "
                     "(already delivered, canceled, or version conflict)."
            )
            return

        # Grab remaining stock while the session is open.
        stock = bottle_service.get_admin_stock(session, admin_id)
        customer_id = order.customer_id
        bottle_count = order.bottle_count

    await query.edit_message_text(
        text=(
            f"Order #{order_id} marked as delivered.\n"
            f"Remaining stock: {stock} bottles."
        )
    )

    await notify_customer(
        context.bot,
        customer_id,
        f"Your order #{order_id} ({bottle_count} bottles) has been delivered. Enjoy!",
    )


# ---------------------------------------------------------------------------
# Cancel flow  (ConversationHandler)
# ---------------------------------------------------------------------------

@require_admin
async def admincancel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start cancel flow: ask the admin for a reason."""
    query = update.callback_query
    await query.answer()

    match = re.match(r"^admincancel_(\d+)_(\d+)$", query.data)
    if not match:
        return ConversationHandler.END

    order_id = int(match.group(1))
    expected_version = int(match.group(2))

    # Store in user_data for next step.
    context.user_data["cancel_order_id"] = order_id
    context.user_data["cancel_version"] = expected_version

    await query.edit_message_text(
        text=(
            f"Canceling order #{order_id}.\n"
            "Please type the reason for cancellation (or /cancel to abort):"
        )
    )
    return CANCEL_REASON


@require_admin
async def cancel_reason_entered(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive the cancellation reason and execute the cancel."""
    reason = update.message.text.strip()
    order_id = context.user_data.get("cancel_order_id")
    expected_version = context.user_data.get("cancel_version")
    admin_id = context.user_data["admin_id"]

    if not order_id:
        await update.message.reply_text("No order selected. Use /myactive to start.")
        return ConversationHandler.END

    with get_session() as session:
        order = order_service.cancel_order(
            session,
            order_id=order_id,
            expected_version=expected_version,
            canceled_by=CanceledBy.ADMIN.value,
            reason=reason,
            admin_id=admin_id,
        )

        if order is None:
            await update.message.reply_text(
                f"Order #{order_id} could not be canceled "
                "(already delivered, canceled, or version conflict)."
            )
            _clear_cancel_data(context)
            return ConversationHandler.END

        customer_id = order.customer_id

    await update.message.reply_text(f"Order #{order_id} has been canceled.")

    await notify_customer(
        context.bot,
        customer_id,
        f"Your order #{order_id} was canceled by the driver.\nReason: {reason}",
    )

    _clear_cancel_data(context)
    return ConversationHandler.END


async def cancel_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/cancel fallback inside the cancel-reason conversation."""
    _clear_cancel_data(context)
    await update.message.reply_text("Cancellation aborted.")
    return ConversationHandler.END


def _clear_cancel_data(context: ContextTypes.DEFAULT_TYPE):
    context.user_data.pop("cancel_order_id", None)
    context.user_data.pop("cancel_version", None)


# ---------------------------------------------------------------------------
# Handler registration
# ---------------------------------------------------------------------------

def get_handlers():
    """Return the list of handlers to register on the Application."""
    cancel_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(
                admincancel_callback, pattern=r"^admincancel_\d+_\d+$"
            ),
        ],
        states={
            CANCEL_REASON: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND, cancel_reason_entered
                ),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_conversation),
        ],
        conversation_timeout=600,
        per_message=False,
    )

    return [
        CommandHandler("myactive", myactive_command),
        CallbackQueryHandler(deliver_callback, pattern=r"^deliver_\d+_\d+$"),
        cancel_conv,
    ]
