import logging

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
from app.services import order_service
from bot.keyboards.customer_kb import confirm_reorder_keyboard
from bot.middlewares.auth import require_customer
from bot.utils.notifications import notify_admins_new_order
from bot.utils.validators import validate_bottle_count
from config import Config

logger = logging.getLogger(__name__)

# Conversation states
CONFIRM_REORDER, CHANGE_AMOUNT = range(2)


@require_customer
async def reorder_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Entry point for /reorder. Fetch last delivered order and offer to repeat it."""
    customer_id = context.user_data["customer_id"]

    with get_session() as session:
        last_order = order_service.get_customer_last_delivered(session, customer_id)

        if not last_order:
            await update.message.reply_text(
                "You don't have any previous delivered orders to reorder.\n"
                "Use /order to place a new order."
            )
            return ConversationHandler.END

        context.user_data["reorder_bottles"] = last_order.bottle_count
        context.user_data["reorder_address"] = last_order.delivery_address

    bottles = context.user_data["reorder_bottles"]
    address = context.user_data["reorder_address"]

    await update.message.reply_text(
        "Reorder from your last delivery:\n\n"
        f"Bottles: {bottles}\n"
        f"Address: {address}\n\n"
        "Would you like to confirm or change the amount?",
        reply_markup=confirm_reorder_keyboard(),
    )
    return CONFIRM_REORDER


async def confirm_reorder(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle reorder confirmation."""
    query = update.callback_query
    await query.answer()

    customer_id = context.user_data["customer_id"]
    bottles = context.user_data["reorder_bottles"]
    address = context.user_data["reorder_address"]

    try:
        with get_session() as session:
            ok, msg = order_service.can_create_order(session, customer_id, bottles)
            if not ok:
                await query.edit_message_text(msg)
                _cleanup_reorder_data(context)
                return ConversationHandler.END

            order = order_service.create_order(
                session=session,
                customer_id=customer_id,
                bottle_count=bottles,
                delivery_address=address,
            )
            order_id = order.id

            # Re-fetch with relationships for notification
            from app.models.order import Order
            order = session.get(Order, order_id)

            await query.edit_message_text(
                f"Order #{order_id} placed successfully!\n"
                f"{bottles} bottle(s) to {address}\n\n"
                "You will be notified when an admin picks up your order."
            )

            await notify_admins_new_order(context.bot, order)

    except ValueError as e:
        await query.edit_message_text(f"Could not create order: {e}")

    _cleanup_reorder_data(context)
    return ConversationHandler.END


async def change_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle Change Amount button -- prompt for new bottle count."""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        f"Enter the number of bottles (1-{Config.MAX_BOTTLES_PER_ORDER}):"
    )
    return CHANGE_AMOUNT


async def change_amount_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive new bottle count for reorder."""
    count = validate_bottle_count(update.message.text, Config.MAX_BOTTLES_PER_ORDER)

    if count is None:
        await update.message.reply_text(
            f"Invalid number. Please enter a number between 1 and {Config.MAX_BOTTLES_PER_ORDER}:"
        )
        return CHANGE_AMOUNT

    context.user_data["reorder_bottles"] = count
    address = context.user_data["reorder_address"]

    await update.message.reply_text(
        "Updated reorder:\n\n"
        f"Bottles: {count}\n"
        f"Address: {address}\n\n"
        "Confirm or change again?",
        reply_markup=confirm_reorder_keyboard(),
    )
    return CONFIRM_REORDER


async def cancel_reorder_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the Cancel button on the reorder keyboard."""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Reorder cancelled.")
    _cleanup_reorder_data(context)
    return ConversationHandler.END


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle /cancel during reorder conversation."""
    _cleanup_reorder_data(context)
    await update.message.reply_text("Reorder cancelled.")
    return ConversationHandler.END


def _cleanup_reorder_data(context: ContextTypes.DEFAULT_TYPE):
    """Remove reorder-related keys from user_data."""
    for key in ("reorder_bottles", "reorder_address"):
        context.user_data.pop(key, None)


reorder_conversation = ConversationHandler(
    entry_points=[CommandHandler("reorder", reorder_command)],
    states={
        CONFIRM_REORDER: [
            CallbackQueryHandler(confirm_reorder, pattern=r"^reorder_confirm$"),
            CallbackQueryHandler(change_amount, pattern=r"^reorder_change$"),
            CallbackQueryHandler(cancel_reorder_callback, pattern=r"^reorder_cancel$"),
        ],
        CHANGE_AMOUNT: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, change_amount_input),
        ],
    },
    fallbacks=[CommandHandler("cancel", cancel_command)],
    per_message=False,
    conversation_timeout=600,
)


def get_handlers():
    return [reorder_conversation]
