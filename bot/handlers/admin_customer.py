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
from bot.utils.formatters import format_bottle_stats, format_date, format_order_short

logger = logging.getLogger(__name__)

# Conversation states
ENTER_SEARCH, SELECT_CUSTOMER = range(2)


# ---------------------------------------------------------------------------
# /customer entry point
# ---------------------------------------------------------------------------

@require_admin
async def customer_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/customer - start a customer-lookup flow."""
    await update.message.reply_text(
        "Enter a customer name or phone number to search:"
    )
    return ENTER_SEARCH


# ---------------------------------------------------------------------------
# Step 1: search
# ---------------------------------------------------------------------------

@require_admin
async def enter_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Search customers by the text the admin entered."""
    query_text = update.message.text.strip()
    if not query_text:
        await update.message.reply_text("Please enter a name or phone number.")
        return ENTER_SEARCH

    with get_session() as session:
        results = customer_service.search_customers(session, query_text, limit=10)

    if not results:
        await update.message.reply_text(
            "No customers found. Try a different search or /cancel."
        )
        return ENTER_SEARCH

    if len(results) == 1:
        # Only one match -- show detail directly.
        return await _show_customer_detail(update, context, results[0].id)

    # Multiple matches -- show selection keyboard.
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
    keyboard = InlineKeyboardMarkup(buttons)
    await update.message.reply_text(
        f"Found {len(results)} customers. Select one:",
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
    with get_session() as session:
        customer = customer_service.get_by_id(session, customer_id)
        if not customer:
            text = "Customer not found."
            if edit and update.callback_query:
                await update.callback_query.edit_message_text(text)
            else:
                await update.effective_message.reply_text(text)
            return ConversationHandler.END

        stats = bottle_service.get_customer_bottles(session, customer_id)
        orders, total_orders = order_service.get_customer_orders(
            session, customer_id, limit=5
        )

        # Build text.
        lines = [
            "Customer Profile",
            "-----------------------------",
            f"Name:     {customer.full_name}",
            f"Phone:    {customer.phone}",
            f"Address:  {customer.address}",
            f"Active:   {'Yes' if customer.is_active else 'No'}",
            f"Joined:   {format_date(customer.created_at)}",
            "",
            "Bottle Statistics",
            "-----------------------------",
            format_bottle_stats(stats),
            "",
            f"Recent Orders ({total_orders} total)",
            "-----------------------------",
        ]

        if orders:
            for order in orders:
                lines.append(format_order_short(order))
        else:
            lines.append("No orders yet.")

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
    await update.message.reply_text("Customer search canceled.")
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
    )
    return [conv]
