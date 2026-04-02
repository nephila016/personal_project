"""Admin handler: manage in-progress (active) orders."""

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
from app.models.order import CanceledBy
from app.services import bottle_service, order_service
from bot.keyboards.admin_kb import active_order_keyboard
from bot.middlewares.auth import require_admin
from bot.utils.i18n import get_lang, t
from bot.utils.notifications import notify_customer

logger = logging.getLogger(__name__)

# Conversation state for the cancel-reason flow
CANCEL_REASON = 0


def _extract_order_for_list(order) -> dict:
    """Extract plain dict from ORM Order while session is open."""
    customer = order.customer
    return {
        "id": order.id,
        "version": order.version,
        "bottle_count": order.bottle_count,
        "delivery_address": order.delivery_address,
        "delivery_notes": order.delivery_notes,
        "customer_name": customer.full_name if customer else "?",
    }


def _format_order_line(d: dict, lang: str) -> str:
    """Format a single order dict for the list view."""
    lines = [
        t("order_line", lang, id=d["id"], name=d["customer_name"],
          bottles=d["bottle_count"], address=d["delivery_address"]),
    ]
    if d.get("delivery_notes"):
        lines.append(t("order_line_notes", lang, notes=d["delivery_notes"]))
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# /myactive command
# ---------------------------------------------------------------------------

@require_admin
async def myactive_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/myactive - list the admin's own in-progress orders."""
    lang = get_lang(context)
    admin_id = context.user_data["admin_id"]

    with get_session() as session:
        orders = order_service.get_admin_active_orders(session, admin_id)
        if not orders:
            await update.effective_message.reply_text(
                t("no_active_orders", lang)
            )
            return

        order_dicts = [_extract_order_for_list(o) for o in orders]

    for d in order_dicts:
        text = _format_order_line(d, lang)
        keyboard = active_order_keyboard(d, lang=lang)
        await update.effective_message.reply_text(
            text=text, reply_markup=keyboard
        )


# ---------------------------------------------------------------------------
# Deliver callback
# ---------------------------------------------------------------------------

@require_admin
async def deliver_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle deliver_{order_id}_{version} callback."""
    query = update.callback_query
    await query.answer()

    lang = get_lang(context)

    match = re.match(r"^deliver_(\d+)_(\d+)$", query.data)
    if not match:
        return

    order_id = int(match.group(1))
    expected_version = int(match.group(2))
    admin_id = context.user_data["admin_id"]

    with get_session() as session:
        try:
            order = order_service.mark_delivered(
                session, order_id, admin_id, expected_version
            )
        except ValueError:
            await query.edit_message_text(
                text=t("insufficient_stock_deliver", lang, id=order_id)
            )
            return

        if order is None:
            await query.edit_message_text(
                text=t("order_cannot_deliver", lang, id=order_id)
            )
            return

        stock = bottle_service.get_admin_stock(session, admin_id)
        customer_id = order.customer_id
        bottle_count = order.bottle_count

    await query.edit_message_text(
        text=t("order_delivered_stock", lang, id=order_id, stock=stock)
    )

    # Notify customer in default lang ("ru") since we don't store lang in DB
    customer_lang = "ru"
    await notify_customer(
        context.bot,
        customer_id,
        t("notif_order_delivered_customer", customer_lang,
          id=order_id, bottles=bottle_count),
    )


# ---------------------------------------------------------------------------
# Cancel flow  (ConversationHandler)
# ---------------------------------------------------------------------------

@require_admin
async def admincancel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start cancel flow: ask the admin for a reason."""
    query = update.callback_query
    await query.answer()

    lang = get_lang(context)

    match = re.match(r"^admincancel_(\d+)_(\d+)$", query.data)
    if not match:
        return ConversationHandler.END

    order_id = int(match.group(1))
    expected_version = int(match.group(2))

    context.user_data["cancel_order_id"] = order_id
    context.user_data["cancel_version"] = expected_version

    await query.edit_message_text(
        text=t("cancel_order_prompt", lang, id=order_id)
    )
    return CANCEL_REASON


@require_admin
async def cancel_reason_entered(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive the cancellation reason and execute the cancel."""
    lang = get_lang(context)
    reason = update.message.text.strip()
    order_id = context.user_data.get("cancel_order_id")
    expected_version = context.user_data.get("cancel_version")
    admin_id = context.user_data["admin_id"]

    if not order_id:
        await update.message.reply_text(
            t("order_not_selected", lang)
        )
        return ConversationHandler.END

    with get_session() as session:
        order = order_service.cancel_order(
            session,
            order_id=order_id,
            expected_version=expected_version,
            canceled_by=CanceledBy.ADMIN.value,
            reason=reason,
            admin_id=admin_id,
        )

        if order is None:
            await update.message.reply_text(
                t("order_cannot_cancel", lang, id=order_id)
            )
            _clear_cancel_data(context)
            return ConversationHandler.END

        customer_id = order.customer_id

    await update.message.reply_text(
        t("admin_order_cancelled", lang, id=order_id)
    )

    # Notify customer in default lang ("ru") since we don't store lang in DB
    customer_lang = "ru"
    await notify_customer(
        context.bot,
        customer_id,
        t("notif_order_cancelled_driver", customer_lang,
          id=order_id, reason=reason),
    )

    _clear_cancel_data(context)
    return ConversationHandler.END


async def cancel_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/cancel fallback inside the cancel-reason conversation."""
    lang = get_lang(context)
    _clear_cancel_data(context)
    await update.message.reply_text(t("cancel_aborted_admin", lang))
    return ConversationHandler.END


def _clear_cancel_data(context: ContextTypes.DEFAULT_TYPE):
    context.user_data.pop("cancel_order_id", None)
    context.user_data.pop("cancel_version", None)


# ---------------------------------------------------------------------------
# Handler registration
# ---------------------------------------------------------------------------

def get_handlers():
    """Return the list of handlers to register on the Application."""
    cancel_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(
                admincancel_callback, pattern=r"^admincancel_\d+_\d+$"
            ),
        ],
        states={
            CANCEL_REASON: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND, cancel_reason_entered
                ),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_conversation),
        ],
        conversation_timeout=600,
        per_message=False,
    allow_reentry=True,
    )

    return [
        CommandHandler("myactive", myactive_command),
        CallbackQueryHandler(deliver_callback, pattern=r"^deliver_\d+_\d+$"),
        cancel_conv,
    ]
