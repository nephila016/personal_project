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
from app.services import bottle_service, customer_service
from bot.keyboards.customer_kb import edit_profile_keyboard
from bot.middlewares.auth import require_customer
from bot.utils.formatters import format_bottle_stats
from bot.utils.validators import normalize_phone, validate_address, validate_name, validate_phone

logger = logging.getLogger(__name__)

# Conversation states
SHOW_PROFILE, EDIT_NAME, EDIT_ADDRESS, EDIT_PHONE = range(4)


@require_customer
async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show the customer's profile and bottle statistics."""
    customer_id = context.user_data["customer_id"]

    with get_session() as session:
        customer = customer_service.get_by_id(session, customer_id)
        if not customer:
            await update.message.reply_text("Profile not found. Please /start to register.")
            return ConversationHandler.END

        stats = bottle_service.get_customer_bottles(session, customer_id)

        text = (
            "Your Profile\n"
            "-----------------------------\n"
            f"Name: {customer.full_name}\n"
            f"Address: {customer.address}\n"
            f"Phone: {customer.phone}\n"
            "-----------------------------\n"
            "Bottle Statistics\n"
            "-----------------------------\n"
            f"{format_bottle_stats(stats)}"
        )

    await update.message.reply_text(
        text, reply_markup=edit_profile_keyboard()
    )
    return SHOW_PROFILE


async def edit_name_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle Edit Name button."""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Enter your new name:")
    return EDIT_NAME


async def edit_name_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive and save the new name."""
    name = update.message.text.strip()

    if not validate_name(name):
        await update.message.reply_text(
            "Name must be between 2 and 100 characters. Please try again:"
        )
        return EDIT_NAME

    customer_id = context.user_data["customer_id"]

    with get_session() as session:
        customer_service.update_customer(session, customer_id, full_name=name)

    await update.message.reply_text(
        f"Name updated to: {name}\n\nUse /profile to view your updated profile."
    )
    return ConversationHandler.END


async def edit_address_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle Edit Address button."""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Enter your new delivery address:")
    return EDIT_ADDRESS


async def edit_address_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive and save the new address."""
    address = update.message.text.strip()

    if not validate_address(address):
        await update.message.reply_text(
            "Address must be between 1 and 500 characters. Please try again:"
        )
        return EDIT_ADDRESS

    customer_id = context.user_data["customer_id"]

    with get_session() as session:
        customer_service.update_customer(session, customer_id, address=address)

    await update.message.reply_text(
        f"Address updated to: {address}\n\nUse /profile to view your updated profile."
    )
    return ConversationHandler.END


async def edit_phone_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle Edit Phone button."""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Enter your new phone number:")
    return EDIT_PHONE


async def edit_phone_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive and save the new phone number."""
    raw_phone = update.message.text.strip()

    if not validate_phone(raw_phone):
        await update.message.reply_text(
            "Invalid phone number. Please enter a valid phone number "
            "(7-15 digits, optionally starting with +):"
        )
        return EDIT_PHONE

    phone = normalize_phone(raw_phone)
    customer_id = context.user_data["customer_id"]

    # Check if phone is already taken by another customer
    with get_session() as session:
        existing = customer_service.get_by_phone(session, phone)
        if existing and existing.id != customer_id:
            await update.message.reply_text(
                "This phone number is already registered to another account. "
                "Please enter a different number:"
            )
            return EDIT_PHONE

        customer_service.update_customer(session, customer_id, phone=phone)

    await update.message.reply_text(
        f"Phone updated to: {phone}\n\nUse /profile to view your updated profile."
    )
    return ConversationHandler.END


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle /cancel during profile editing."""
    await update.message.reply_text("Profile editing cancelled.")
    return ConversationHandler.END


profile_conversation = ConversationHandler(
    entry_points=[CommandHandler("profile", profile_command)],
    states={
        SHOW_PROFILE: [
            CallbackQueryHandler(edit_name_start, pattern=r"^edit_name$"),
            CallbackQueryHandler(edit_address_start, pattern=r"^edit_address$"),
            CallbackQueryHandler(edit_phone_start, pattern=r"^edit_phone$"),
        ],
        EDIT_NAME: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, edit_name_input),
        ],
        EDIT_ADDRESS: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, edit_address_input),
        ],
        EDIT_PHONE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, edit_phone_input),
        ],
    },
    fallbacks=[CommandHandler("cancel", cancel_command)],
    per_message=False,
    conversation_timeout=600,
)


def get_handlers():
    return [profile_conversation]
