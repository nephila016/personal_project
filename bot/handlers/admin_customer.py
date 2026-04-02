"""Admin handler: search and view customer details."""

import logging
import re

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
from app.services import bottle_service, customer_service, order_service
from bot.middlewares.auth import require_admin
from bot.utils.i18n import (
    format_bottle_stats_i18n,
    format_order_short_i18n,
    get_lang,
    get_status_label,
    t,
)

logger = logging.getLogger(__name__)

# Conversation states
ENTER_SEARCH, SELECT_CUSTOMER = range(2)


def _format_date(dt, lang: str) -> str:
    if not dt:
        return t("na", lang)
    return dt.strftime("%d.%m.%Y %H:%M")


# ---------------------------------------------------------------------------
# /customer entry point
# ---------------------------------------------------------------------------

@require_admin
async def customer_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/customer - start a customer-lookup flow."""
    lang = get_lang(context)
    await update.message.reply_text(
        t("enter_name_or_phone", lang)
    )
    return ENTER_SEARCH


# ---------------------------------------------------------------------------
# Step 1: search
# ---------------------------------------------------------------------------

@require_admin
async def enter_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Search customers by the text the admin entered."""
    lang = get_lang(context)
    query_text = update.message.text.strip()
    if not query_text:
        await update.message.reply_text(t("enter_name_or_phone_short", lang))
        return ENTER_SEARCH

    with get_session() as session:
        results = customer_service.search_customers(session, query_text, limit=10)

        if not results:
            await update.message.reply_text(
                t("customers_not_found", lang)
            )
            return ENTER_SEARCH

        if len(results) == 1:
            customer_id = results[0].id
            # fall through to show detail within this session scope
        else:
            # Multiple matches -- build keyboard from extracted data.
            buttons = []
            for cust in results:
                buttons.append(
                    [
                        InlineKeyboardButton(
                            f"{cust.full_name} ({cust.phone})",
                            callback_data=f"custview_{cust.id}",
                        )
                    ]
                )

    if len(results) == 1:
        return await _show_customer_detail(update, context, customer_id)

    keyboard = InlineKeyboardMarkup(buttons)
    await update.message.reply_text(
        t("found_n_customers", lang, count=len(results)),
        reply_markup=keyboard,
    )
    return SELECT_CUSTOMER


# ---------------------------------------------------------------------------
# Step 2: select from results
# ---------------------------------------------------------------------------

@require_admin
async def select_customer_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle custview_{customer_id} inline button."""
    query = update.callback_query
    await query.answer()

    match = re.match(r"^custview_(\d+)$", query.data)
    if not match:
        return ConversationHandler.END

    customer_id = int(match.group(1))
    await _show_customer_detail(update, context, customer_id, edit=True)
    return ConversationHandler.END


# ---------------------------------------------------------------------------
# Detail view
# ---------------------------------------------------------------------------

async def _show_customer_detail(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    customer_id: int,
    *,
    edit: bool = False,
):
    """Fetch and display full customer profile."""
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
        orders, total_orders = order_service.get_customer_orders(
            session, customer_id, limit=5
        )

        # Extract all needed values inside the session.
        cust_name = customer.full_name
        cust_phone = customer.phone
        cust_address = customer.address
        cust_active = customer.is_active
        cust_created = customer.created_at

        order_data_list = []
        for o in orders:
            order_data_list.append({
                "id": o.id,
                "bottle_count": o.bottle_count,
                "status": o.status,
                "created_at": o.created_at,
            })

    # Build text outside session -- only plain values used.
    active_label = t("yes", lang) if cust_active else t("no", lang)
    separator = t("stock_separator", lang)

    lines = [
        t("customer_profile_header", lang),
        separator,
        t("customer_detail_name", lang, name=cust_name),
        t("customer_detail_phone", lang, phone=cust_phone),
        t("customer_detail_address", lang, address=cust_address),
        t("customer_detail_active", lang, value=active_label),
        t("customer_detail_registered", lang, date=_format_date(cust_created, lang)),
        "",
        t("bottle_stats_header", lang),
        separator,
        format_bottle_stats_i18n(stats, lang),
        "",
        t("recent_orders_header", lang, total=total_orders),
        separator,
    ]

    if order_data_list:
        for od in order_data_list:
            lines.append(format_order_short_i18n(od, lang))
    else:
        lines.append(t("no_orders_yet_short", lang))

    text = "\n".join(lines)

    if edit and update.callback_query:
        await update.callback_query.edit_message_text(text)
    else:
        await update.effective_message.reply_text(text)

    return ConversationHandler.END


# ---------------------------------------------------------------------------
# Fallback
# ---------------------------------------------------------------------------

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/cancel fallback."""
    lang = get_lang(context)
    await update.message.reply_text(t("customer_search_cancelled", lang))
    return ConversationHandler.END


# ---------------------------------------------------------------------------
# Handler registration
# ---------------------------------------------------------------------------

def get_handlers():
    """Return the list of handlers to register on the Application."""
    conv = ConversationHandler(
        entry_points=[
            CommandHandler("customer", customer_command),
        ],
        states={
            ENTER_SEARCH: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, enter_search),
            ],
            SELECT_CUSTOMER: [
                CallbackQueryHandler(
                    select_customer_callback, pattern=r"^custview_\d+$"
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
