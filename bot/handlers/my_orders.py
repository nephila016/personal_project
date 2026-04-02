import logging
import math

from telegram import Update
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes

from app.database import get_session
from app.services import order_service
from bot.keyboards.customer_kb import pagination_keyboard
from bot.middlewares.auth import require_customer
from bot.utils.i18n import format_order_short_i18n, get_lang, t

logger = logging.getLogger(__name__)

ORDERS_PER_PAGE = 5


@require_customer
async def myorders_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show the first page of the customer's orders."""
    lang = get_lang(context)
    customer_id = context.user_data["customer_id"]
    await _send_orders_page(update.message, customer_id, page=1, lang=lang)


async def myorders_page_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle pagination callback queries for myorders."""
    lang = get_lang(context)
    query = update.callback_query
    await query.answer()

    customer_id = context.user_data.get("customer_id")
    if not customer_id:
        await query.edit_message_text(t("register_first", lang))
        return

    # Extract page number from callback data: "myorders_page_N"
    try:
        page = int(query.data.split("_")[-1])
    except (IndexError, ValueError):
        page = 1

    await _send_orders_page(query, customer_id, page=page, edit=True, lang=lang)


async def _send_orders_page(
    target, customer_id: int, page: int = 1, edit: bool = False, lang: str = "ru"
) -> None:
    """Fetch and display a page of orders."""
    offset = (page - 1) * ORDERS_PER_PAGE

    with get_session() as session:
        orders, total = order_service.get_customer_orders(
            session, customer_id, limit=ORDERS_PER_PAGE, offset=offset
        )
        # Extract all needed data inside the session to avoid DetachedInstanceError
        order_dicts = []
        for o in orders:
            order_dicts.append({
                "id": o.id,
                "bottle_count": o.bottle_count,
                "status": o.status,
                "created_at": o.created_at,
            })

    if not order_dicts and page == 1:
        text = t("no_orders_yet", lang)
        if edit:
            await target.edit_message_text(text)
        else:
            await target.reply_text(text)
        return

    total_pages = max(1, math.ceil(total / ORDERS_PER_PAGE))

    lines = [t("your_orders_page", lang, page=page, total=total_pages) + "\n"]
    for od in order_dicts:
        lines.append(format_order_short_i18n(od, lang))
    text = "\n".join(lines)

    keyboard = pagination_keyboard("myorders", page, total_pages, lang)

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
