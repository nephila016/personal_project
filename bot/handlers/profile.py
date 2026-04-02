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
from bot.utils.i18n import format_bottle_stats_i18n, get_lang, t
from bot.utils.validators import normalize_phone, validate_address, validate_name, validate_phone

logger = logging.getLogger(__name__)

# Conversation states
SHOW_PROFILE, EDIT_NAME, EDIT_ADDRESS, EDIT_PHONE = range(4)


@require_customer
async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show the customer's profile and bottle statistics."""
    lang = get_lang(context)
    customer_id = context.user_data["customer_id"]

    with get_session() as session:
        customer = customer_service.get_by_id(session, customer_id)
        if not customer:
            await update.message.reply_text(t("customer_not_found", lang))
            return ConversationHandler.END

        # Extract all needed values inside the session
        full_name = customer.full_name
        address = customer.address
        phone = customer.phone

        stats = bottle_service.get_customer_bottles(session, customer_id)

    stats_text = format_bottle_stats_i18n(stats, lang)

    text = t("your_profile", lang, name=full_name, address=address, phone=phone, stats=stats_text)

    await update.message.reply_text(
        text, reply_markup=edit_profile_keyboard(lang)
    )
    return SHOW_PROFILE


async def edit_name_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle Edit Name button."""
    lang = get_lang(context)
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(t("enter_new_name", lang))
    return EDIT_NAME


async def edit_name_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive and save the new name."""
    lang = get_lang(context)
    name = update.message.text.strip()

    if not validate_name(name):
        await update.message.reply_text(t("invalid_name", lang))
        return EDIT_NAME

    customer_id = context.user_data["customer_id"]

    with get_session() as session:
        customer_service.update_customer(session, customer_id, full_name=name)

    await update.message.reply_text(t("name_updated", lang, name=name))
    return ConversationHandler.END


async def edit_address_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle Edit Address button."""
    lang = get_lang(context)
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(t("enter_new_delivery_address", lang))
    return EDIT_ADDRESS


async def edit_address_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive and save the new address."""
    lang = get_lang(context)
    address = update.message.text.strip()

    if not validate_address(address):
        await update.message.reply_text(t("invalid_address", lang))
        return EDIT_ADDRESS

    customer_id = context.user_data["customer_id"]

    with get_session() as session:
        customer_service.update_customer(session, customer_id, address=address)

    await update.message.reply_text(t("address_updated", lang, address=address))
    return ConversationHandler.END


async def edit_phone_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle Edit Phone button."""
    lang = get_lang(context)
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(t("enter_new_phone", lang))
    return EDIT_PHONE


async def edit_phone_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive and save the new phone number."""
    lang = get_lang(context)
    raw_phone = update.message.text.strip()

    if not validate_phone(raw_phone):
        await update.message.reply_text(t("invalid_phone", lang))
        return EDIT_PHONE

    phone = normalize_phone(raw_phone)
    customer_id = context.user_data["customer_id"]

    # Check if phone is already taken by another customer
    with get_session() as session:
        existing = customer_service.get_by_phone(session, phone)
        if existing and existing.id != customer_id:
            await update.message.reply_text(t("phone_taken", lang))
            return EDIT_PHONE

        customer_service.update_customer(session, customer_id, phone=phone)

    await update.message.reply_text(t("phone_updated", lang, phone=phone))
    return ConversationHandler.END


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle /cancel during profile editing."""
    lang = get_lang(context)
    await update.message.reply_text(t("profile_edit_cancelled", lang))
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
    allow_reentry=True,
    conversation_timeout=600,
)


def get_handlers():
    return [profile_conversation]
