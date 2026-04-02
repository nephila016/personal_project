from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def bottle_count_keyboard() -> InlineKeyboardMarkup:
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
                InlineKeyboardButton("Custom", callback_data="bottles_custom"),
            ],
        ]
    )


def confirm_order_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Confirm", callback_data="order_confirm")],
            [
                InlineKeyboardButton(
                    "Change Address", callback_data="order_change_address"
                ),
                InlineKeyboardButton(
                    "Change Notes", callback_data="order_change_notes"
                ),
            ],
            [InlineKeyboardButton("Cancel", callback_data="order_cancel")],
        ]
    )


def confirm_reorder_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Confirm", callback_data="reorder_confirm")],
            [
                InlineKeyboardButton(
                    "Change Amount", callback_data="reorder_change"
                )
            ],
            [InlineKeyboardButton("Cancel", callback_data="reorder_cancel")],
        ]
    )


def yes_no_keyboard(prefix: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Yes, Cancel", callback_data=f"{prefix}_yes"),
                InlineKeyboardButton("No, Keep It", callback_data=f"{prefix}_no"),
            ]
        ]
    )


def edit_profile_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Edit Name", callback_data="edit_name"),
                InlineKeyboardButton("Edit Address", callback_data="edit_address"),
                InlineKeyboardButton("Edit Phone", callback_data="edit_phone"),
            ]
        ]
    )


def confirm_edit_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Confirm", callback_data="reg_confirm")],
            [
                InlineKeyboardButton("Edit Name", callback_data="reg_edit_name"),
                InlineKeyboardButton("Edit Address", callback_data="reg_edit_address"),
                InlineKeyboardButton("Edit Phone", callback_data="reg_edit_phone"),
            ],
        ]
    )


def pagination_keyboard(prefix: str, page: int, total_pages: int) -> InlineKeyboardMarkup:
    buttons = []
    if page > 1:
        buttons.append(
            InlineKeyboardButton("< Prev", callback_data=f"{prefix}_page_{page - 1}")
        )
    if page < total_pages:
        buttons.append(
            InlineKeyboardButton("Next >", callback_data=f"{prefix}_page_{page + 1}")
        )
    if buttons:
        return InlineKeyboardMarkup([buttons])
    return None
