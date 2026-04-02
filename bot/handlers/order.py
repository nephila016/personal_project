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
from app.services import customer_service, order_service
from bot.keyboards.customer_kb import bottle_count_keyboard, confirm_order_keyboard
from bot.middlewares.auth import require_customer
from bot.utils.notifications import notify_admins_new_order
from bot.utils.validators import validate_address, validate_bottle_count
from config import Config

logger = logging.getLogger(__name__)

# Conversation states
SELECT_BOTTLES, CUSTOM_AMOUNT, DELIVERY_NOTES, CONFIRM_ORDER, CHANGE_ADDRESS, CHANGE_NOTES = range(6)


@require_customer
async def order_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Entry point for /order. Show bottle count selection."""
    customer_id = context.user_data["customer_id"]

    # Load customer address for later use
    with get_session() as session:
        customer = customer_service.get_by_id(session, customer_id)
        if not customer:
            await update.message.reply_text("Customer not found. Please /start to register.")
            return ConversationHandler.END
        context.user_data["order_address"] = customer.address

    await update.message.reply_text(
        "How many bottles would you like to order?",
        reply_markup=bottle_count_keyboard(),
    )
    return SELECT_BOTTLES


async def select_bottles(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle bottle count selection from inline keyboard."""
    query = update.callback_query
    await query.answer()

    data = query.data  # e.g. "bottles_5" or "bottles_custom"

    if data == "bottles_custom":
        await query.edit_message_text(
            f"Enter the number of bottles (1-{Config.MAX_BOTTLES_PER_ORDER}):"
        )
        return CUSTOM_AMOUNT

    try:
        count = int(data.split("_")[1])
    except (IndexError, ValueError):
        await query.edit_message_text(
            "Invalid selection. Please try again.",
            reply_markup=bottle_count_keyboard(),
        )
        return SELECT_BOTTLES

    if count < 1 or count > Config.MAX_BOTTLES_PER_ORDER:
        await query.edit_message_text(
            f"Please choose between 1 and {Config.MAX_BOTTLES_PER_ORDER} bottles.",
            reply_markup=bottle_count_keyboard(),
        )
        return SELECT_BOTTLES

    context.user_data["order_bottles"] = count

    await query.edit_message_text(
        "Add delivery notes (special instructions, landmarks, etc.)?\n\n"
        "Type your notes or press Skip.",
        reply_markup=_skip_keyboard(),
    )
    return DELIVERY_NOTES


async def custom_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle custom bottle count text input."""
    count = validate_bottle_count(update.message.text, Config.MAX_BOTTLES_PER_ORDER)

    if count is None:
        await update.message.reply_text(
            f"Invalid number. Please enter a number between 1 and {Config.MAX_BOTTLES_PER_ORDER}:"
        )
        return CUSTOM_AMOUNT

    context.user_data["order_bottles"] = count

    await update.message.reply_text(
        "Add delivery notes (special instructions, landmarks, etc.)?\n\n"
        "Type your notes or press Skip.",
        reply_markup=_skip_keyboard(),
    )
    return DELIVERY_NOTES


async def delivery_notes_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle delivery notes text input."""
    notes = update.message.text.strip()
    if len(notes) > 500:
        await update.message.reply_text(
            "Notes are too long (max 500 characters). Please shorten them:"
        )
        return DELIVERY_NOTES

    context.user_data["order_notes"] = notes
    return await _show_order_summary(update, context)


async def delivery_notes_skip(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the Skip button for delivery notes."""
    query = update.callback_query
    await query.answer()

    context.user_data["order_notes"] = None
    return await _show_order_summary(update, context, edit_message=query)


async def _show_order_summary(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    edit_message=None,
) -> int:
    """Display the order summary for confirmation."""
    bottles = context.user_data["order_bottles"]
    address = context.user_data["order_address"]
    notes = context.user_data.get("order_notes")

    summary = (
        "Please confirm your order:\n\n"
        f"Bottles: {bottles}\n"
        f"Address: {address}\n"
    )
    if notes:
        summary += f"Notes: {notes}\n"

    if edit_message:
        await edit_message.edit_message_text(summary, reply_markup=confirm_order_keyboard())
    else:
        await update.message.reply_text(summary, reply_markup=confirm_order_keyboard())
    return CONFIRM_ORDER


async def confirm_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle order confirmation."""
    query = update.callback_query
    await query.answer()

    customer_id = context.user_data["customer_id"]
    bottles = context.user_data["order_bottles"]
    address = context.user_data["order_address"]
    notes = context.user_data.get("order_notes")

    try:
        with get_session() as session:
            # Check duplicate / pending limit
            ok, msg = order_service.can_create_order(session, customer_id, bottles)
            if not ok:
                await query.edit_message_text(msg)
                _cleanup_order_data(context)
                return ConversationHandler.END

            order = order_service.create_order(
                session=session,
                customer_id=customer_id,
                bottle_count=bottles,
                delivery_address=address,
                delivery_notes=notes,
            )
            order_id = order.id

            # Re-fetch with relationships for notification
            order = session.get(order_service.Order, order_id)

            await query.edit_message_text(
                f"Order #{order_id} placed successfully!\n"
                f"{bottles} bottle(s) to {address}\n\n"
                "You will be notified when an admin picks up your order."
            )

            # Notify admins
            await notify_admins_new_order(context.bot, order)

    except ValueError as e:
        await query.edit_message_text(f"Could not create order: {e}")

    _cleanup_order_data(context)
    return ConversationHandler.END


async def cancel_order_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle cancel callback during order conversation."""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Order cancelled.")
    _cleanup_order_data(context)
    return ConversationHandler.END


async def change_address(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle Change Address button."""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "Please enter the new delivery address:"
    )
    return CHANGE_ADDRESS


async def change_address_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive new delivery address."""
    address = update.message.text.strip()

    if not validate_address(address):
        await update.message.reply_text(
            "Address must be between 1 and 500 characters. Please try again:"
        )
        return CHANGE_ADDRESS

    context.user_data["order_address"] = address
    return await _show_order_summary(update, context)


async def change_notes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle Change Notes button."""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "Please enter the new delivery notes (or type 'none' to clear):"
    )
    return CHANGE_NOTES


async def change_notes_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive new delivery notes."""
    text = update.message.text.strip()

    if text.lower() == "none":
        context.user_data["order_notes"] = None
    elif len(text) > 500:
        await update.message.reply_text(
            "Notes are too long (max 500 characters). Please shorten them:"
        )
        return CHANGE_NOTES
    else:
        context.user_data["order_notes"] = text

    return await _show_order_summary(update, context)


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle /cancel during order conversation."""
    _cleanup_order_data(context)
    await update.message.reply_text("Order cancelled.")
    return ConversationHandler.END


def _cleanup_order_data(context: ContextTypes.DEFAULT_TYPE):
    """Remove order-related keys from user_data."""
    for key in ("order_bottles", "order_address", "order_notes"):
        context.user_data.pop(key, None)


def _skip_keyboard():
    """Inline keyboard with a Skip button."""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup

    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("Skip", callback_data="order_skip_notes")]]
    )


order_conversation = ConversationHandler(
    entry_points=[CommandHandler("order", order_command)],
    states={
        SELECT_BOTTLES: [
            CallbackQueryHandler(select_bottles, pattern=r"^bottles_"),
        ],
        CUSTOM_AMOUNT: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, custom_amount),
        ],
        DELIVERY_NOTES: [
            CallbackQueryHandler(delivery_notes_skip, pattern=r"^order_skip_notes$"),
            MessageHandler(filters.TEXT & ~filters.COMMAND, delivery_notes_text),
        ],
        CONFIRM_ORDER: [
            CallbackQueryHandler(confirm_order, pattern=r"^order_confirm$"),
            CallbackQueryHandler(cancel_order_conversation, pattern=r"^order_cancel$"),
            CallbackQueryHandler(change_address, pattern=r"^order_change_address$"),
            CallbackQueryHandler(change_notes, pattern=r"^order_change_notes$"),
        ],
        CHANGE_ADDRESS: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, change_address_input),
        ],
        CHANGE_NOTES: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, change_notes_input),
        ],
    },
    fallbacks=[CommandHandler("cancel", cancel_command)],
    per_message=False,
    conversation_timeout=600,
)


def get_handlers():
    return [order_conversation]
