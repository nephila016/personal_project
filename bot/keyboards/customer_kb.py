from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from bot.utils.i18n import t


def bottle_count_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("1", callback_data="bottles_1"),
                InlineKeyboardButton("2", callback_data="bottles_2"),
                InlineKeyboardButton("3", callback_data="bottles_3"),
            ],
            [
                InlineKeyboardButton("5", callback_data="bottles_5"),
                InlineKeyboardButton("10", callback_data="bottles_10"),
                InlineKeyboardButton(t("btn_other", lang), callback_data="bottles_custom"),
            ],
        ]
    )


def confirm_order_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(t("btn_confirm", lang), callback_data="order_confirm")],
            [
                InlineKeyboardButton(
                    t("btn_change_address", lang), callback_data="order_change_address"
                ),
                InlineKeyboardButton(
                    t("btn_change_notes", lang), callback_data="order_change_notes"
                ),
            ],
            [InlineKeyboardButton(t("btn_cancel", lang), callback_data="order_cancel")],
        ]
    )


def confirm_reorder_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(t("btn_confirm", lang), callback_data="reorder_confirm")],
            [
                InlineKeyboardButton(
                    t("btn_change_amount", lang), callback_data="reorder_change"
                )
            ],
            [InlineKeyboardButton(t("btn_cancel", lang), callback_data="reorder_cancel")],
        ]
    )


def yes_no_keyboard(prefix: str, lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(t("btn_yes_cancel", lang), callback_data=f"{prefix}_yes"),
                InlineKeyboardButton(t("btn_no_keep", lang), callback_data=f"{prefix}_no"),
            ]
        ]
    )


def edit_profile_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(t("btn_edit_name", lang), callback_data="edit_name"),
                InlineKeyboardButton(t("btn_edit_address", lang), callback_data="edit_address"),
                InlineKeyboardButton(t("btn_edit_phone", lang), callback_data="edit_phone"),
            ]
        ]
    )


def confirm_edit_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(t("btn_confirm", lang), callback_data="reg_confirm")],
            [
                InlineKeyboardButton(t("btn_edit_name", lang), callback_data="reg_edit_name"),
                InlineKeyboardButton(t("btn_edit_address", lang), callback_data="reg_edit_address"),
                InlineKeyboardButton(t("btn_edit_phone", lang), callback_data="reg_edit_phone"),
            ],
        ]
    )


def pagination_keyboard(prefix: str, page: int, total_pages: int, lang: str = "ru") -> InlineKeyboardMarkup:
    buttons = []
    if page > 1:
        buttons.append(
            InlineKeyboardButton(t("btn_prev", lang), callback_data=f"{prefix}_page_{page - 1}")
        )
    if page < total_pages:
        buttons.append(
            InlineKeyboardButton(t("btn_next", lang), callback_data=f"{prefix}_page_{page + 1}")
        )
    if buttons:
        return InlineKeyboardMarkup([buttons])
    return None
