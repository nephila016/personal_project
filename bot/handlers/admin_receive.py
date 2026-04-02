"""Admin handler: record bottle receipts from supplier."""

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
from app.services import bottle_service
from bot.keyboards.admin_kb import confirm_receipt_keyboard, skip_keyboard
from bot.middlewares.auth import require_admin
from bot.utils.i18n import get_lang, t
from bot.utils.validators import validate_receipt_quantity
from config import Config

logger = logging.getLogger(__name__)

# Conversation states
ENTER_QTY, ENTER_NOTES, CONFIRM = range(3)


# ---------------------------------------------------------------------------
# /receive entry point
# ---------------------------------------------------------------------------

@require_admin
async def receive_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/receive - start the bottle-receipt flow."""
    lang = get_lang(context)
    await update.message.reply_text(
        t("how_many_received_full", lang, max=Config.MAX_RECEIPT_QUANTITY)
    )
    return ENTER_QTY


# ---------------------------------------------------------------------------
# Step 1: enter quantity
# ---------------------------------------------------------------------------

@require_admin
async def enter_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Validate and store the receipt quantity."""
    lang = get_lang(context)
    qty = validate_receipt_quantity(
        update.message.text, max_qty=Config.MAX_RECEIPT_QUANTITY
    )
    if qty is None:
        await update.message.reply_text(
            t("enter_valid_quantity", lang, max=Config.MAX_RECEIPT_QUANTITY)
        )
        return ENTER_QTY

    context.user_data["receipt_qty"] = qty
    await update.message.reply_text(
        t("add_receipt_note_prompt", lang),
        reply_markup=skip_keyboard(callback_data="receipt_skip_notes", lang=lang),
    )
    return ENTER_NOTES


# ---------------------------------------------------------------------------
# Step 2: enter notes (or skip)
# ---------------------------------------------------------------------------

@require_admin
async def enter_notes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Store notes from text input."""
    context.user_data["receipt_notes"] = update.message.text.strip()
    return await _show_confirmation(update, context)


@require_admin
async def skip_notes_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Skip button pressed - no notes."""
    query = update.callback_query
    await query.answer()
    context.user_data["receipt_notes"] = None
    return await _show_confirmation(update, context, edit=True)


async def _show_confirmation(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    *,
    edit: bool = False,
):
    lang = get_lang(context)
    qty = context.user_data.get("receipt_qty")
    notes = context.user_data.get("receipt_notes")

    text = t("confirm_receipt_text", lang, qty=qty)
    if notes:
        text += "\n" + t("confirm_receipt_notes_line", lang, notes=notes)

    keyboard = confirm_receipt_keyboard(lang=lang)

    if edit and update.callback_query:
        await update.callback_query.edit_message_text(
            text=text, reply_markup=keyboard
        )
    else:
        await update.effective_message.reply_text(
            text=text, reply_markup=keyboard
        )
    return CONFIRM


# ---------------------------------------------------------------------------
# Step 3: confirm or cancel receipt
# ---------------------------------------------------------------------------

@require_admin
async def confirm_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Record the receipt in the database."""
    query = update.callback_query
    await query.answer()

    lang = get_lang(context)
    qty = context.user_data.get("receipt_qty")
    notes = context.user_data.get("receipt_notes")
    admin_id = context.user_data["admin_id"]

    if not qty:
        await query.edit_message_text(
            t("receipt_error", lang)
        )
        _clear_receipt_data(context)
        return ConversationHandler.END

    with get_session() as session:
        receipt = bottle_service.record_receipt(
            session, admin_id=admin_id, quantity=qty, notes=notes
        )
        receipt_id = receipt.id
        stock = bottle_service.get_admin_stock(session, admin_id)

    await query.edit_message_text(
        t("receipt_recorded_full", lang, id=receipt_id, qty=qty, stock=stock)
    )

    _clear_receipt_data(context)
    return ConversationHandler.END


@require_admin
async def cancel_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel button on confirmation step."""
    query = update.callback_query
    await query.answer()
    lang = get_lang(context)
    await query.edit_message_text(t("receipt_cancelled_admin", lang))
    _clear_receipt_data(context)
    return ConversationHandler.END


# ---------------------------------------------------------------------------
# Fallback: /cancel at any point
# ---------------------------------------------------------------------------

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/cancel fallback."""
    lang = get_lang(context)
    _clear_receipt_data(context)
    await update.message.reply_text(t("receipt_cancelled_admin", lang))
    return ConversationHandler.END


def _clear_receipt_data(context: ContextTypes.DEFAULT_TYPE):
    context.user_data.pop("receipt_qty", None)
    context.user_data.pop("receipt_notes", None)


# ---------------------------------------------------------------------------
# Handler registration
# ---------------------------------------------------------------------------

def get_handlers():
    """Return the list of handlers to register on the Application."""
    conv = ConversationHandler(
        entry_points=[
            CommandHandler("receive", receive_command),
        ],
        states={
            ENTER_QTY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, enter_quantity),
            ],
            ENTER_NOTES: [
                CallbackQueryHandler(
                    skip_notes_callback, pattern=r"^receipt_skip_notes$"
                ),
                MessageHandler(filters.TEXT & ~filters.COMMAND, enter_notes),
            ],
            CONFIRM: [
                CallbackQueryHandler(confirm_receipt, pattern=r"^receipt_confirm$"),
                CallbackQueryHandler(cancel_receipt, pattern=r"^receipt_cancel$"),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_command),
        ],
        conversation_timeout=600,
        per_message=False,
    allow_reentry=True,
    )
    return [conv]
