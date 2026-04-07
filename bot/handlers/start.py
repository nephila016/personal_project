import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
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
from bot.utils.i18n import get_lang, t
from bot.handlers.menu import get_reply_keyboard
from bot.utils.validators import normalize_phone, validate_address, validate_name, validate_phone

logger = logging.getLogger(__name__)

# Conversation states
CHOOSE_LANG, ENTER_NAME, ENTER_ADDRESS, ENTER_PHONE, CONFIRM_REGISTRATION = range(5)


def _lang_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("\U0001f1f7\U0001f1fa Русский", callback_data="set_lang_ru"),
                InlineKeyboardButton("\U0001f1fa\U0001f1ff O'zbekcha", callback_data="set_lang_uz"),
            ]
        ]
    )


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle /start. If already registered, welcome back. Otherwise begin registration."""
    user = update.effective_user
    if not user:
        return ConversationHandler.END

    with get_session() as session:
        customer = customer_service.get_by_telegram_id(session, user.id)
        customer_name = customer.full_name if customer else None

    if customer_name:
        lang = get_lang(context)
        keyboard = get_reply_keyboard(user.id, lang)
        await update.message.reply_text(
            t("welcome_back", lang, name=customer_name),
            reply_markup=keyboard,
        )
        return ConversationHandler.END

    # New user -- check if they already have a language set (e.g. from /lang)
    if context.user_data.get("lang"):
        lang = get_lang(context)
        await update.message.reply_text(t("welcome_new", lang))
        return ENTER_NAME

    # Ask for language first
    await update.message.reply_text(
        t("choose_language", "ru"),
        reply_markup=_lang_keyboard(),
    )
    return CHOOSE_LANG


async def choose_lang(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle language selection during registration."""
    query = update.callback_query
    await query.answer()

    lang_code = query.data.split("_")[-1]  # "ru" or "uz"
    context.user_data["lang"] = lang_code
    lang = lang_code

    await query.edit_message_text(t("welcome_new", lang))
    return ENTER_NAME


async def enter_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive and validate the customer's name."""
    lang = get_lang(context)
    name = update.message.text.strip()

    if not validate_name(name):
        await update.message.reply_text(t("invalid_name", lang))
        return ENTER_NAME

    context.user_data["reg_name"] = name
    await update.message.reply_text(t("enter_address", lang))
    return ENTER_ADDRESS


async def enter_address(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive and validate the customer's address."""
    lang = get_lang(context)
    address = update.message.text.strip()

    if not validate_address(address):
        await update.message.reply_text(t("invalid_address", lang))
        return ENTER_ADDRESS

    context.user_data["reg_address"] = address
    await update.message.reply_text(t("enter_phone", lang))
    return ENTER_PHONE


async def enter_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive and validate the customer's phone number."""
    lang = get_lang(context)
    raw_phone = update.message.text.strip()

    if not validate_phone(raw_phone):
        await update.message.reply_text(t("invalid_phone", lang))
        return ENTER_PHONE

    phone = normalize_phone(raw_phone)

    # Check if phone already registered
    with get_session() as session:
        existing = customer_service.get_by_phone(session, phone)
        phone_taken = existing is not None

    if phone_taken:
        await update.message.reply_text(t("phone_taken", lang))
        return ENTER_PHONE

    context.user_data["reg_phone"] = phone

    # Show confirmation
    name = context.user_data["reg_name"]
    address = context.user_data["reg_address"]

    await update.message.reply_text(
        t("confirm_registration", lang, name=name, address=address, phone=phone),
        reply_markup=confirm_edit_keyboard(lang),
    )
    return CONFIRM_REGISTRATION


async def confirm_registration(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the confirm button press to finalize registration."""
    lang = get_lang(context)
    query = update.callback_query
    await query.answer()

    user = update.effective_user
    name = context.user_data.get("reg_name")
    address = context.user_data.get("reg_address")
    phone = context.user_data.get("reg_phone")

    if not all([name, address, phone]):
        await query.edit_message_text(t("registration_missing", lang))
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

        await query.edit_message_text(t("registration_complete", lang))

        # Send the persistent reply keyboard
        keyboard = get_reply_keyboard(user.id, lang)
        await query.message.reply_text("👇", reply_markup=keyboard)
    except ValueError as e:
        await query.edit_message_text(t("registration_error", lang, error=str(e)))

    return ConversationHandler.END


async def edit_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the Edit Name button during registration."""
    lang = get_lang(context)
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(t("enter_name", lang))
    return ENTER_NAME


async def edit_address(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the Edit Address button during registration."""
    lang = get_lang(context)
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(t("enter_address", lang))
    return ENTER_ADDRESS


async def edit_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the Edit Phone button during registration."""
    lang = get_lang(context)
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(t("enter_phone", lang))
    return ENTER_PHONE


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the registration conversation."""
    lang = get_lang(context)
    for key in ("reg_name", "reg_address", "reg_phone"):
        context.user_data.pop(key, None)

    await update.message.reply_text(t("registration_cancelled", lang))
    return ConversationHandler.END


start_conversation = ConversationHandler(
    entry_points=[CommandHandler("start", start_command)],
    states={
        CHOOSE_LANG: [
            CallbackQueryHandler(choose_lang, pattern=r"^set_lang_(ru|uz)$"),
        ],
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
    allow_reentry=True,
    conversation_timeout=600,
)


def get_handlers():
    return [start_conversation]
