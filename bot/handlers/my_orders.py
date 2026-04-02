import logging
import math

from telegram import Update
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes

from app.database import get_session
from app.services import order_service
from bot.keyboards.customer_kb import pagination_keyboard
from bot.middlewares.auth import require_customer
from bot.utils.formatters import format_order_short

logger = logging.getLogger(__name__)

ORDERS_PER_PAGE = 5


@require_customer
async def myorders_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show the first page of the customer's orders."""
    customer_id = context.user_data["customer_id"]
    await _send_orders_page(update.message, customer_id, page=1)


async def myorders_page_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle pagination callback queries for myorders."""
    query = update.callback_query
    await query.answer()

    customer_id = context.user_data.get("customer_id")
    if not customer_id:
        await query.edit_message_text("Please register first with /start.")
        return

    # Extract page number from callback data: "myorders_page_N"
    try:
        page = int(query.data.split("_")[-1])
    except (IndexError, ValueError):
        page = 1

    await _send_orders_page(query, customer_id, page=page, edit=True)


async def _send_orders_page(target, customer_id: int, page: int = 1, edit: bool = False) -> None:
    """Fetch and display a page of orders."""
    offset = (page - 1) * ORDERS_PER_PAGE

    with get_session() as session:
        orders, total = order_service.get_customer_orders(
            session, customer_id, limit=ORDERS_PER_PAGE, offset=offset
        )

    if not orders and page == 1:
        text = "You don't have any orders yet.\nUse /order to place your first order!"
        if edit:
            await target.edit_message_text(text)
        else:
            await target.reply_text(text)
        return

    total_pages = max(1, math.ceil(total / ORDERS_PER_PAGE))

    lines = [f"Your Orders (Page {page}/{total_pages}):\n"]
    for order in orders:
        lines.append(format_order_short(order))
    text = "\n".join(lines)

    keyboard = pagination_keyboard("myorders", page, total_pages)

    if edit:
        await target.edit_message_text(text, reply_markup=keyboard)
    else:
        await target.reply_text(text, reply_markup=keyboard)


myorders_handler = CommandHandler("myorders", myorders_command)
myorders_page_handler = CallbackQueryHandler(
    myorders_page_callback, pattern=r"^myorders_page_\d+$"
)


def get_handlers():
    return [myorders_handler, myorders_page_handler]
