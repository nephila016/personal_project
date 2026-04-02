"""Admin-facing inline keyboards.

All functions accept plain dicts / scalars -- never ORM objects -- so they
can safely be called outside a database session.
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from bot.utils.i18n import t


def pending_orders_keyboard(
    orders: list[dict], page: int = 1, total_pages: int = 1, lang: str = "ru"
) -> InlineKeyboardMarkup:
    """Keyboard for the pending-orders list.

    Each item in *orders* must have keys ``id`` and ``version``.
    """
    buttons = []
    for o in orders:
        buttons.append(
            [
                InlineKeyboardButton(
                    t("btn_claim_order", lang, id=o["id"]),
                    callback_data=f"claim_{o['id']}_{o['version']}",
                )
            ]
        )
    nav = []
    if page > 1:
        nav.append(
            InlineKeyboardButton(
                t("btn_prev", lang), callback_data=f"pending_page_{page - 1}"
            )
        )
    if page < total_pages:
        nav.append(
            InlineKeyboardButton(
                t("btn_next", lang), callback_data=f"pending_page_{page + 1}"
            )
        )
    if nav:
        buttons.append(nav)
    return InlineKeyboardMarkup(buttons)


def active_order_keyboard(order: dict, lang: str = "ru") -> InlineKeyboardMarkup:
    """Keyboard for a single active order.

    *order* must have keys ``id`` and ``version``.
    """
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    t("btn_delivered_order", lang, id=order["id"]),
                    callback_data=f"deliver_{order['id']}_{order['version']}",
                ),
                InlineKeyboardButton(
                    t("btn_cancel_order", lang, id=order["id"]),
                    callback_data=f"admincancel_{order['id']}_{order['version']}",
                ),
            ]
        ]
    )


def confirm_receipt_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    t("btn_confirm", lang), callback_data="receipt_confirm"
                ),
                InlineKeyboardButton(
                    t("btn_cancel", lang), callback_data="receipt_cancel"
                ),
            ]
        ]
    )


def confirm_return_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    t("btn_confirm", lang), callback_data="return_confirm"
                ),
                InlineKeyboardButton(
                    t("btn_cancel", lang), callback_data="return_cancel"
                ),
            ]
        ]
    )


def skip_keyboard(
    callback_data: str = "skip", lang: str = "ru"
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton(t("btn_skip", lang), callback_data=callback_data)]]
    )


def recent_customers_keyboard(
    customers: list, lang: str = "ru"
) -> InlineKeyboardMarkup | None:
    """Keyboard built from a list of plain dicts with keys id, name, in_hand."""
    buttons = []
    for c in customers:
        buttons.append(
            [
                InlineKeyboardButton(
                    t("btn_on_hand_display", lang, name=c["name"], in_hand=c["in_hand"]),
                    callback_data=f"retcust_{c['id']}",
                )
            ]
        )
    return InlineKeyboardMarkup(buttons) if buttons else None
