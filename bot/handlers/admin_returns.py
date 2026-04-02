"""Admin handler: record empty-bottle returns from customers."""

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
from app.models.order import Order, OrderStatus
from app.services import bottle_service, customer_service
from bot.keyboards.admin_kb import confirm_return_keyboard, recent_customers_keyboard, skip_keyboard
from bot.middlewares.auth import require_admin
from bot.utils.i18n import get_lang, t
from bot.utils.validators import validate_bottle_count, validate_phone

logger = logging.getLogger(__name__)

# Conversation states
SELECT_CUSTOMER, ENTER_QTY, ENTER_NOTES, CONFIRM = range(4)


# ---------------------------------------------------------------------------
# /returns entry point
# ---------------------------------------------------------------------------

@require_admin
async def returns_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/returns - start the bottle-return recording flow."""
    lang = get_lang(context)
    admin_id = context.user_data["admin_id"]

    with get_session() as session:
        recent_orders = (
            session.query(Order)
            .filter(
                Order.admin_id == admin_id,
                Order.status == OrderStatus.DELIVERED.value,
            )
            .order_by(Order.updated_at.desc())
            .limit(10)
            .all()
        )

        # Deduplicate by customer, keeping the most recent delivery.
        seen_ids: set[int] = set()
        customer_list: list[dict] = []
        for order in recent_orders:
            cid = order.customer_id
            if cid not in seen_ids:
                seen_ids.add(cid)
                stats = bottle_service.get_customer_bottles(session, cid)
                customer_list.append(
                    {
                        "id": cid,
                        "name": order.customer.full_name,
                        "in_hand": stats["bottles_in_hand"],
                    }
                )

    keyboard = recent_customers_keyboard(customer_list, lang=lang)
    if keyboard:
        await update.message.reply_text(
            text=t("select_customer_or_phone", lang), reply_markup=keyboard
        )
    else:
        await update.message.reply_text(
            t("no_recent_deliveries", lang)
        )
    return SELECT_CUSTOMER


# ---------------------------------------------------------------------------
# Step 1: select customer (inline button or phone search)
# ---------------------------------------------------------------------------

@require_admin
async def select_customer_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Customer chosen via inline button: retcust_{customer_id}."""
    query = update.callback_query
    await query.answer()

    match = re.match(r"^retcust_(\d+)$", query.data)
    if not match:
        return SELECT_CUSTOMER

    customer_id = int(match.group(1))
    return await _load_customer_and_ask_qty(update, context, customer_id, edit=True)


@require_admin
async def select_customer_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Customer identified by phone number typed by admin."""
    lang = get_lang(context)
    phone = update.message.text.strip()

    if not validate_phone(phone):
        await update.message.reply_text(
            t("invalid_phone_format", lang)
        )
        return SELECT_CUSTOMER

    with get_session() as session:
        customer = customer_service.get_by_phone(session, phone)
        if not customer:
            await update.message.reply_text(
                t("customer_not_found_try_again", lang)
            )
            return SELECT_CUSTOMER
        customer_id = customer.id

    return await _load_customer_and_ask_qty(update, context, customer_id)


async def _load_customer_and_ask_qty(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    customer_id: int,
    *,
    edit: bool = False,
):
    """Load the customer's bottle stats and prompt for return quantity."""
    lang = get_lang(context)

    with get_session() as session:
        customer = customer_service.get_by_id(session, customer_id)
        if not customer:
            text = t("customer_not_found_short", lang)
            if edit and update.callback_query:
                await update.callback_query.edit_message_text(text)
            else:
                await update.effective_message.reply_text(text)
            return ConversationHandler.END

        stats = bottle_service.get_customer_bottles(session, customer_id)
        cust_name = customer.full_name
        in_hand = stats["bottles_in_hand"]

    context.user_data["return_customer_id"] = customer_id
    context.user_data["return_customer_name"] = cust_name
    context.user_data["return_in_hand"] = in_hand

    text = t("return_customer_info", lang, name=cust_name, in_hand=in_hand)
    if edit and update.callback_query:
        await update.callback_query.edit_message_text(text)
    else:
        await update.effective_message.reply_text(text)
    return ENTER_QTY


# ---------------------------------------------------------------------------
# Step 2: enter return quantity
# ---------------------------------------------------------------------------

@require_admin
async def enter_return_qty(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Validate return quantity against bottles_in_hand."""
    lang = get_lang(context)
    in_hand = context.user_data.get("return_in_hand", 0)
    qty = validate_bottle_count(update.message.text, max_count=max(in_hand, 1))
    if qty is None:
        await update.message.reply_text(
            t("enter_qty_range", lang, max=in_hand)
        )
        return ENTER_QTY

    if qty > in_hand:
        await update.message.reply_text(
            t("customer_only_has", lang, in_hand=in_hand)
        )
        return ENTER_QTY

    context.user_data["return_qty"] = qty
    await update.message.reply_text(
        t("add_note_or_skip", lang),
        reply_markup=skip_keyboard(callback_data="return_skip_notes", lang=lang),
    )
    return ENTER_NOTES


# ---------------------------------------------------------------------------
# Step 3: notes (or skip)
# ---------------------------------------------------------------------------

@require_admin
async def enter_return_notes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Store notes from text."""
    context.user_data["return_notes"] = update.message.text.strip()
    return await _show_return_confirmation(update, context)


@require_admin
async def skip_return_notes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Skip notes via inline button."""
    query = update.callback_query
    await query.answer()
    context.user_data["return_notes"] = None
    return await _show_return_confirmation(update, context, edit=True)


async def _show_return_confirmation(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    *,
    edit: bool = False,
):
    lang = get_lang(context)
    cust_name = context.user_data.get("return_customer_name", "?")
    qty = context.user_data.get("return_qty")
    notes = context.user_data.get("return_notes")

    text = t("confirm_return_text", lang, name=cust_name, qty=qty)
    if notes:
        text += "\n" + t("confirm_return_notes_line", lang, notes=notes)

    keyboard = confirm_return_keyboard(lang=lang)

    if edit and update.callback_query:
        await update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
    else:
        await update.effective_message.reply_text(text=text, reply_markup=keyboard)
    return CONFIRM


# ---------------------------------------------------------------------------
# Step 4: confirm / cancel
# ---------------------------------------------------------------------------

@require_admin
async def confirm_return(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Record the return."""
    query = update.callback_query
    await query.answer()

    lang = get_lang(context)
    customer_id = context.user_data.get("return_customer_id")
    qty = context.user_data.get("return_qty")
    notes = context.user_data.get("return_notes")
    admin_id = context.user_data["admin_id"]

    if not customer_id or not qty:
        await query.edit_message_text(
            t("return_error_retry", lang)
        )
        _clear_return_data(context)
        return ConversationHandler.END

    try:
        with get_session() as session:
            ret = bottle_service.record_return(
                session,
                customer_id=customer_id,
                admin_id=admin_id,
                quantity=qty,
                notes=notes,
            )
            ret_id = ret.id
            new_stats = bottle_service.get_customer_bottles(session, customer_id)
            new_in_hand = new_stats["bottles_in_hand"]
    except ValueError as exc:
        await query.edit_message_text(t("return_error_full", lang, error=exc))
        _clear_return_data(context)
        return ConversationHandler.END

    cust_name = context.user_data.get("return_customer_name", "?")
    await query.edit_message_text(
        t("return_recorded_full", lang, id=ret_id, qty=qty,
          name=cust_name, remaining=new_in_hand)
    )

    _clear_return_data(context)
    return ConversationHandler.END


@require_admin
async def cancel_return_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel button on confirmation step."""
    query = update.callback_query
    await query.answer()
    lang = get_lang(context)
    await query.edit_message_text(t("return_cancelled_admin", lang))
    _clear_return_data(context)
    return ConversationHandler.END


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/cancel fallback."""
    lang = get_lang(context)
    _clear_return_data(context)
    await update.message.reply_text(t("return_cancelled_admin", lang))
    return ConversationHandler.END


def _clear_return_data(context: ContextTypes.DEFAULT_TYPE):
    for key in (
        "return_customer_id",
        "return_customer_name",
        "return_in_hand",
        "return_qty",
        "return_notes",
    ):
        context.user_data.pop(key, None)


# ---------------------------------------------------------------------------
# Handler registration
# ---------------------------------------------------------------------------

def get_handlers():
    """Return the list of handlers to register on the Application."""
    conv = ConversationHandler(
        entry_points=[
            CommandHandler("returns", returns_command),
        ],
        states={
            SELECT_CUSTOMER: [
                CallbackQueryHandler(
                    select_customer_callback, pattern=r"^retcust_\d+$"
                ),
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND, select_customer_phone
                ),
            ],
            ENTER_QTY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, enter_return_qty),
            ],
            ENTER_NOTES: [
                CallbackQueryHandler(
                    skip_return_notes, pattern=r"^return_skip_notes$"
                ),
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND, enter_return_notes
                ),
            ],
            CONFIRM: [
                CallbackQueryHandler(confirm_return, pattern=r"^return_confirm$"),
                CallbackQueryHandler(
                    cancel_return_callback, pattern=r"^return_cancel$"
                ),
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
