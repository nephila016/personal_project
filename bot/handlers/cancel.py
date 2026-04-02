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
from bot.utils.i18n import format_order_short_i18n, get_lang, t

logger = logging.getLogger(__name__)

# Conversation states
SELECT_ORDER, CONFIRM_CANCEL = range(2)


@require_customer
async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Entry point for /cancel. Find pending orders and prompt cancellation."""
    lang = get_lang(context)
    customer_id = context.user_data["customer_id"]

    with get_session() as session:
        pending = order_service.get_customer_pending_orders(session, customer_id)
        # Extract all needed data inside the session
        pending_data = []
        for o in pending:
            pending_data.append({
                "id": o.id,
                "bottle_count": o.bottle_count,
                "status": o.status,
                "created_at": o.created_at,
                "version": o.version,
            })

    if not pending_data:
        await update.message.reply_text(t("no_pending_to_cancel", lang))
        return ConversationHandler.END

    if len(pending_data) == 1:
        od = pending_data[0]
        context.user_data["cancel_order_id"] = od["id"]
        context.user_data["cancel_order_version"] = od["version"]
        await update.message.reply_text(
            t("cancel_this_order", lang) + "\n\n" + format_order_short_i18n(od, lang),
            reply_markup=yes_no_keyboard("cancelorder", lang),
        )
        return CONFIRM_CANCEL

    # Multiple pending orders -- let user choose
    bottles_label = t("bottles_short", lang)
    buttons = []
    for od in pending_data:
        buttons.append(
            [
                InlineKeyboardButton(
                    f"#{od['id']} - {od['bottle_count']} {bottles_label}",
                    callback_data=f"cancelselect_{od['id']}_{od['version']}",
                )
            ]
        )
    buttons.append(
        [InlineKeyboardButton(t("btn_not_needed", lang), callback_data="cancelselect_abort")]
    )

    await update.message.reply_text(
        t("which_order_cancel", lang),
        reply_markup=InlineKeyboardMarkup(buttons),
    )
    return SELECT_ORDER


async def select_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle order selection from the list."""
    lang = get_lang(context)
    query = update.callback_query
    await query.answer()

    if query.data == "cancelselect_abort":
        await query.edit_message_text(t("cancel_aborted", lang))
        return ConversationHandler.END

    # Parse: cancelselect_{order_id}_{version}
    parts = query.data.split("_")
    try:
        order_id = int(parts[1])
        version = int(parts[2])
    except (IndexError, ValueError):
        await query.edit_message_text(t("error_generic", lang))
        return ConversationHandler.END

    context.user_data["cancel_order_id"] = order_id
    context.user_data["cancel_order_version"] = version

    with get_session() as session:
        from app.models.order import Order
        order = session.get(Order, order_id)
        if not order:
            await query.edit_message_text(t("error_generic", lang))
            return ConversationHandler.END
        od = {
            "id": order.id,
            "bottle_count": order.bottle_count,
            "status": order.status,
            "created_at": order.created_at,
        }

    await query.edit_message_text(
        t("cancel_this_order", lang) + "\n\n" + format_order_short_i18n(od, lang),
        reply_markup=yes_no_keyboard("cancelorder", lang),
    )
    return CONFIRM_CANCEL


async def confirm_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle yes/no confirmation for order cancellation."""
    lang = get_lang(context)
    query = update.callback_query
    await query.answer()

    if query.data == "cancelorder_no":
        await query.edit_message_text(t("cancel_kept", lang))
        _cleanup_cancel_data(context)
        return ConversationHandler.END

    # cancelorder_yes
    order_id = context.user_data.get("cancel_order_id")
    version = context.user_data.get("cancel_order_version")
    customer_id = context.user_data.get("customer_id")

    if not order_id or version is None:
        await query.edit_message_text(t("error_generic", lang))
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
        await query.edit_message_text(t("order_cancelled_success", lang, id=order_id))
    else:
        await query.edit_message_text(t("order_cancel_failed", lang, id=order_id))

    _cleanup_cancel_data(context)
    return ConversationHandler.END


async def cancel_fallback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle /cancel typed during the cancel conversation itself."""
    lang = get_lang(context)
    _cleanup_cancel_data(context)
    await update.message.reply_text(t("cancel_flow_exited", lang))
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
    allow_reentry=True,
    conversation_timeout=600,
)


def get_handlers():
    return [cancel_conversation]
