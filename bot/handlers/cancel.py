import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
)

from app.database import get_session
from app.models.order import CanceledBy
from app.services import order_service
from bot.keyboards.customer_kb import yes_no_keyboard
from bot.middlewares.auth import require_customer
from bot.utils.formatters import format_order_short

logger = logging.getLogger(__name__)

# Conversation states
SELECT_ORDER, CONFIRM_CANCEL = range(2)


@require_customer
async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Entry point for /cancel. Find pending orders and prompt cancellation."""
    customer_id = context.user_data["customer_id"]

    with get_session() as session:
        pending = order_service.get_customer_pending_orders(session, customer_id)

    if not pending:
        await update.message.reply_text(
            "You have no pending orders to cancel."
        )
        return ConversationHandler.END

    if len(pending) == 1:
        order = pending[0]
        context.user_data["cancel_order_id"] = order.id
        context.user_data["cancel_order_version"] = order.version
        await update.message.reply_text(
            f"Cancel this order?\n\n{format_order_short(order)}",
            reply_markup=yes_no_keyboard("cancelorder"),
        )
        return CONFIRM_CANCEL

    # Multiple pending orders -- let user choose
    buttons = []
    for order in pending:
        buttons.append(
            [
                InlineKeyboardButton(
                    f"#{order.id} - {order.bottle_count} bottles",
                    callback_data=f"cancelselect_{order.id}_{order.version}",
                )
            ]
        )
    buttons.append(
        [InlineKeyboardButton("Never mind", callback_data="cancelselect_abort")]
    )

    await update.message.reply_text(
        "Which order would you like to cancel?",
        reply_markup=InlineKeyboardMarkup(buttons),
    )
    return SELECT_ORDER


async def select_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle order selection from the list."""
    query = update.callback_query
    await query.answer()

    if query.data == "cancelselect_abort":
        await query.edit_message_text("Cancellation aborted.")
        return ConversationHandler.END

    # Parse: cancelselect_{order_id}_{version}
    parts = query.data.split("_")
    try:
        order_id = int(parts[1])
        version = int(parts[2])
    except (IndexError, ValueError):
        await query.edit_message_text("Invalid selection. Please try /cancel again.")
        return ConversationHandler.END

    context.user_data["cancel_order_id"] = order_id
    context.user_data["cancel_order_version"] = version

    with get_session() as session:
        from app.models.order import Order
        order = session.get(Order, order_id)
        if not order:
            await query.edit_message_text("Order not found. It may have already been processed.")
            return ConversationHandler.END
        summary = format_order_short(order)

    await query.edit_message_text(
        f"Cancel this order?\n\n{summary}",
        reply_markup=yes_no_keyboard("cancelorder"),
    )
    return CONFIRM_CANCEL


async def confirm_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle yes/no confirmation for order cancellation."""
    query = update.callback_query
    await query.answer()

    if query.data == "cancelorder_no":
        await query.edit_message_text("Order kept. No changes made.")
        _cleanup_cancel_data(context)
        return ConversationHandler.END

    # cancelorder_yes
    order_id = context.user_data.get("cancel_order_id")
    version = context.user_data.get("cancel_order_version")
    customer_id = context.user_data.get("customer_id")

    if not order_id or version is None:
        await query.edit_message_text("Something went wrong. Please try /cancel again.")
        _cleanup_cancel_data(context)
        return ConversationHandler.END

    with get_session() as session:
        result = order_service.cancel_order(
            session=session,
            order_id=order_id,
            expected_version=version,
            canceled_by=CanceledBy.CUSTOMER.value,
            customer_id=customer_id,
        )

    if result:
        await query.edit_message_text(
            f"Order #{order_id} has been cancelled."
        )
    else:
        await query.edit_message_text(
            f"Could not cancel order #{order_id}. "
            "It may have already been picked up or cancelled."
        )

    _cleanup_cancel_data(context)
    return ConversationHandler.END


async def cancel_fallback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle /cancel typed during the cancel conversation itself."""
    _cleanup_cancel_data(context)
    await update.message.reply_text("Cancellation flow exited.")
    return ConversationHandler.END


def _cleanup_cancel_data(context: ContextTypes.DEFAULT_TYPE):
    """Remove cancel-related keys from user_data."""
    for key in ("cancel_order_id", "cancel_order_version"):
        context.user_data.pop(key, None)


cancel_conversation = ConversationHandler(
    entry_points=[CommandHandler("cancel", cancel_command)],
    states={
        SELECT_ORDER: [
            CallbackQueryHandler(select_order, pattern=r"^cancelselect_"),
        ],
        CONFIRM_CANCEL: [
            CallbackQueryHandler(confirm_cancel, pattern=r"^cancelorder_(yes|no)$"),
        ],
    },
    fallbacks=[CommandHandler("cancel", cancel_fallback)],
    per_message=False,
    conversation_timeout=600,
)


def get_handlers():
    return [cancel_conversation]
