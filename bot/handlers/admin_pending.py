"""Admin handler: view and claim pending orders."""

import logging
import math
import re

from telegram import Update
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes

from app.database import get_session
from app.services import bottle_service, order_service
from bot.keyboards.admin_kb import pending_orders_keyboard
from bot.middlewares.auth import require_admin
from bot.utils.i18n import get_lang, t
from bot.utils.notifications import notify_customer

logger = logging.getLogger(__name__)

PAGE_SIZE = 5


def _extract_order_list(orders) -> list[dict]:
    """Extract plain dicts from ORM Order objects while the session is open."""
    result = []
    for o in orders:
        customer = o.customer
        d = {
            "id": o.id,
            "version": o.version,
            "bottle_count": o.bottle_count,
            "delivery_address": o.delivery_address,
            "delivery_notes": o.delivery_notes,
            "customer_name": customer.full_name if customer else "?",
        }
        result.append(d)
    return result


def _extract_order_detail(order) -> dict:
    """Extract a detailed dict from an ORM Order while the session is open."""
    customer = order.customer
    return {
        "id": order.id,
        "version": order.version,
        "customer_id": order.customer_id,
        "bottle_count": order.bottle_count,
        "delivery_address": order.delivery_address,
        "delivery_notes": order.delivery_notes,
        "customer_name": customer.full_name if customer else "?",
        "customer_phone": customer.phone if customer else "?",
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


def _build_pending_text(order_dicts: list[dict], page: int, total: int, lang: str) -> str:
    """Build the text body for the pending-orders list."""
    total_pages = max(1, math.ceil(total / PAGE_SIZE))
    if not order_dicts:
        return t("no_pending_orders", lang)

    lines = [t("pending_orders_page_header", lang, page=page,
               total_pages=total_pages, total=total)]
    for d in order_dicts:
        lines.append(_format_order_line(d, lang))
        lines.append("")
    return "\n".join(lines)


async def _send_pending_page(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    page: int,
    *,
    edit: bool = False,
):
    """Fetch page *page* of pending orders and send / edit message."""
    lang = get_lang(context)
    offset = (page - 1) * PAGE_SIZE

    with get_session() as session:
        orders, total = order_service.get_pending_orders(
            session, limit=PAGE_SIZE, offset=offset
        )
        total_pages = max(1, math.ceil(total / PAGE_SIZE))
        order_dicts = _extract_order_list(orders)

    text = _build_pending_text(order_dicts, page, total, lang)
    keyboard = pending_orders_keyboard(order_dicts, page=page,
                                       total_pages=total_pages, lang=lang)

    if edit and update.callback_query:
        await update.callback_query.edit_message_text(
            text=text, reply_markup=keyboard
        )
    else:
        await update.effective_message.reply_text(text=text, reply_markup=keyboard)


@require_admin
async def pending_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/pending - list pending orders (page 1)."""
    await _send_pending_page(update, context, page=1)


@require_admin
async def pending_page_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle pagination: pending_page_{n}."""
    query = update.callback_query
    await query.answer()

    match = re.match(r"^pending_page_(\d+)$", query.data)
    if not match:
        return
    page = int(match.group(1))
    await _send_pending_page(update, context, page=page, edit=True)


@require_admin
async def claim_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle claim_{order_id}_{version} callback."""
    query = update.callback_query
    await query.answer()

    lang = get_lang(context)

    match = re.match(r"^claim_(\d+)_(\d+)$", query.data)
    if not match:
        return

    order_id = int(match.group(1))
    expected_version = int(match.group(2))
    admin_id = context.user_data["admin_id"]

    with get_session() as session:
        order = order_service.claim_order(
            session, order_id, admin_id, expected_version
        )

        if order is None:
            await query.edit_message_text(
                text=t("already_claimed", lang, id=order_id)
            )
            await _send_pending_page(update, context, page=1)
            return

        detail = _extract_order_detail(order)
        cust_bottles = bottle_service.get_customer_bottles(session, detail["customer_id"])
        detail["bottles_in_hand"] = cust_bottles["bottles_in_hand"]

    text = t("claimed_order_full", lang, id=order_id,
             name=detail["customer_name"], phone=detail["customer_phone"],
             address=detail["delivery_address"], bottles=detail["bottle_count"],
             in_hand=detail["bottles_in_hand"])
    if detail.get("delivery_notes"):
        text += t("claimed_notes", lang, notes=detail["delivery_notes"])
    await query.edit_message_text(text=text)

    # Notify customer in default lang ("ru") since we don't store lang in DB
    customer_lang = "ru"
    customer_id = detail["customer_id"]
    customer_text = t("notif_order_accepted", customer_lang, id=order_id)
    await notify_customer(context.bot, customer_id, customer_text)


# ---------------------------------------------------------------------------
# Handler registration
# ---------------------------------------------------------------------------

def get_handlers():
    """Return the list of handlers to register on the Application."""
    return [
        CommandHandler("pending", pending_command),
        CallbackQueryHandler(pending_page_callback, pattern=r"^pending_page_\d+$"),
        CallbackQueryHandler(claim_callback, pattern=r"^claim_\d+_\d+$"),
    ]
