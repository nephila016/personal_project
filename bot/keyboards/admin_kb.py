from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from app.models.order import Order


def pending_orders_keyboard(
    orders: list[Order], page: int = 1, total_pages: int = 1
) -> InlineKeyboardMarkup:
    buttons = []
    for order in orders:
        buttons.append(
            [
                InlineKeyboardButton(
                    f"Claim #{order.id}",
                    callback_data=f"claim_{order.id}_{order.version}",
                )
            ]
        )
    nav = []
    if page > 1:
        nav.append(
            InlineKeyboardButton(
                "< Prev", callback_data=f"pending_page_{page - 1}"
            )
        )
    if page < total_pages:
        nav.append(
            InlineKeyboardButton(
                "Next >", callback_data=f"pending_page_{page + 1}"
            )
        )
    if nav:
        buttons.append(nav)
    return InlineKeyboardMarkup(buttons)


def active_order_keyboard(order: Order) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    f"Delivered #{order.id}",
                    callback_data=f"deliver_{order.id}_{order.version}",
                ),
                InlineKeyboardButton(
                    f"Cancel #{order.id}",
                    callback_data=f"admincancel_{order.id}_{order.version}",
                ),
            ]
        ]
    )


def confirm_receipt_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Confirm", callback_data="receipt_confirm"),
                InlineKeyboardButton("Cancel", callback_data="receipt_cancel"),
            ]
        ]
    )


def confirm_return_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Confirm", callback_data="return_confirm"),
                InlineKeyboardButton("Cancel", callback_data="return_cancel"),
            ]
        ]
    )


def skip_keyboard(callback_data: str = "skip") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("Skip", callback_data=callback_data)]]
    )


def recent_customers_keyboard(customers: list) -> InlineKeyboardMarkup:
    buttons = []
    for c in customers:
        buttons.append(
            [
                InlineKeyboardButton(
                    f"{c['name']} - {c['in_hand']} in hand",
                    callback_data=f"retcust_{c['id']}",
                )
            ]
        )
    return InlineKeyboardMarkup(buttons) if buttons else None
