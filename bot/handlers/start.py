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
from app.services import customer_service
from bot.keyboards.customer_kb import confirm_edit_keyboard
from bot.utils.validators import normalize_phone, validate_address, validate_name, validate_phone

logger = logging.getLogger(__name__)

# Conversation states
ENTER_NAME, ENTER_ADDRESS, ENTER_PHONE, CONFIRM_REGISTRATION = range(4)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle /start. If already registered, welcome back. Otherwise begin registration."""
    user = update.effective_user
    if not user:
        return ConversationHandler.END

    with get_session() as session:
        customer = customer_service.get_by_telegram_id(session, user.id)

    if customer:
        await update.message.reply_text(
            f"Welcome back, {customer.full_name}!\n\n"
            "Use /order to place a new order, /myorders to view your orders, "
            "or /help to see all commands."
        )
        return ConversationHandler.END

    await update.message.reply_text(
        "Welcome to the Water Delivery Bot!\n\n"
        "Let's get you registered. Please enter your full name:"
    )
    return ENTER_NAME


async def enter_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive and validate the customer's name."""
    name = update.message.text.strip()

    if not validate_name(name):
        await update.message.reply_text(
            "Name must be between 2 and 100 characters. Please try again:"
        )
        return ENTER_NAME

    context.user_data["reg_name"] = name
    await update.message.reply_text(
        "Great! Now please enter your delivery address:"
    )
    return ENTER_ADDRESS


async def enter_address(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive and validate the customer's address."""
    address = update.message.text.strip()

    if not validate_address(address):
        await update.message.reply_text(
            "Address must be between 1 and 500 characters. Please try again:"
        )
        return ENTER_ADDRESS

    context.user_data["reg_address"] = address
    await update.message.reply_text(
        "Now please enter your phone number (e.g. +251912345678):"
    )
    return ENTER_PHONE


async def enter_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive and validate the customer's phone number."""
    raw_phone = update.message.text.strip()

    if not validate_phone(raw_phone):
        await update.message.reply_text(
            "Invalid phone number. Please enter a valid phone number "
            "(7-15 digits, optionally starting with +):"
        )
        return ENTER_PHONE

    phone = normalize_phone(raw_phone)

    # Check if phone already registered
    with get_session() as session:
        existing = customer_service.get_by_phone(session, phone)

    if existing:
        await update.message.reply_text(
            "This phone number is already registered. "
            "Please enter a different phone number:"
        )
        return ENTER_PHONE

    context.user_data["reg_phone"] = phone

    # Show confirmation
    name = context.user_data["reg_name"]
    address = context.user_data["reg_address"]

    await update.message.reply_text(
        "Please confirm your registration details:\n\n"
        f"Name: {name}\n"
        f"Address: {address}\n"
        f"Phone: {phone}\n",
        reply_markup=confirm_edit_keyboard(),
    )
    return CONFIRM_REGISTRATION


async def confirm_registration(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the confirm button press to finalize registration."""
    query = update.callback_query
    await query.answer()

    user = update.effective_user
    name = context.user_data.get("reg_name")
    address = context.user_data.get("reg_address")
    phone = context.user_data.get("reg_phone")

    if not all([name, address, phone]):
        await query.edit_message_text(
            "Registration data is missing. Please start over with /start."
        )
        return ConversationHandler.END

    try:
        with get_session() as session:
            customer = customer_service.register_customer(
                session=session,
                telegram_id=user.id,
                full_name=name,
                address=address,
                phone=phone,
                telegram_username=user.username,
            )
            customer_id = customer.id

        # Clean up user_data
        for key in ("reg_name", "reg_address", "reg_phone"):
            context.user_data.pop(key, None)

        await query.edit_message_text(
            "Registration successful!\n\n"
            "You can now place orders using /order.\n"
            "Use /help to see all available commands."
        )
    except ValueError as e:
        await query.edit_message_text(
            f"Registration failed: {e}\nPlease try again with /start."
        )

    return ConversationHandler.END


async def edit_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the Edit Name button during registration."""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Please enter your full name:")
    return ENTER_NAME


async def edit_address(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the Edit Address button during registration."""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Please enter your delivery address:")
    return ENTER_ADDRESS


async def edit_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the Edit Phone button during registration."""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Please enter your phone number:")
    return ENTER_PHONE


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the registration conversation."""
    for key in ("reg_name", "reg_address", "reg_phone"):
        context.user_data.pop(key, None)

    await update.message.reply_text(
        "Registration cancelled. You can start again anytime with /start."
    )
    return ConversationHandler.END


start_conversation = ConversationHandler(
    entry_points=[CommandHandler("start", start_command)],
    states={
        ENTER_NAME: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, enter_name),
        ],
        ENTER_ADDRESS: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, enter_address),
        ],
        ENTER_PHONE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, enter_phone),
        ],
        CONFIRM_REGISTRATION: [
            CallbackQueryHandler(confirm_registration, pattern=r"^reg_confirm$"),
            CallbackQueryHandler(edit_name, pattern=r"^reg_edit_name$"),
            CallbackQueryHandler(edit_address, pattern=r"^reg_edit_address$"),
            CallbackQueryHandler(edit_phone, pattern=r"^reg_edit_phone$"),
        ],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
    per_message=False,
    conversation_timeout=600,
)


def get_handlers():
    return [start_conversation]
