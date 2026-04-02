import logging

from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import Forbidden, TelegramError

from app.database import get_session
from app.models.customer import Customer
from config import Config

logger = logging.getLogger(__name__)


async def notify_customer(bot: Bot, customer_id: int, text: str):
    """Send a notification to a customer. Handle blocked gracefully."""
    with get_session() as session:
        customer = session.get(Customer, customer_id)
        if not customer:
            return
        telegram_id = customer.telegram_id
        was_blocked = customer.notification_blocked

    try:
        await bot.send_message(chat_id=telegram_id, text=text)
        if was_blocked:
            with get_session() as session:
                c = session.get(Customer, customer_id)
                if c:
                    c.notification_blocked = False
    except Forbidden:
        logger.warning(f"Customer {customer_id} has blocked the bot.")
        with get_session() as session:
            c = session.get(Customer, customer_id)
            if c:
                c.notification_blocked = True
    except TelegramError as e:
        logger.error(f"Failed to notify customer {customer_id}: {e}")


async def notify_admins_new_order(bot: Bot, order_data: dict):
    """Notify admin group or individual admins about a new order.

    order_data should be a plain dict with keys:
        id, customer_name, customer_phone, bottle_count,
        delivery_address, delivery_notes, version
    """
    text = (
        f"Новый заказ #{order_data['id']}\n"
        f"Клиент: {order_data['customer_name']}\n"
        f"Бутылки: {order_data['bottle_count']}\n"
        f"Адрес: {order_data['delivery_address']}"
    )
    if order_data.get("delivery_notes"):
        text += f"\nПримечание: {order_data['delivery_notes']}"
    text += f"\nТелефон: {order_data['customer_phone']}"

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    f"Взять #{order_data['id']}",
                    callback_data=f"claim_{order_data['id']}_{order_data['version']}",
                )
            ]
        ]
    )

    if Config.ADMIN_GROUP_CHAT_ID:
        try:
            await bot.send_message(
                chat_id=Config.ADMIN_GROUP_CHAT_ID,
                text=text,
                reply_markup=keyboard,
            )
        except TelegramError as e:
            logger.error(f"Failed to notify admin group: {e}")
    else:
        from app.models.admin import Admin

        with get_session() as session:
            admins = session.query(Admin).filter(Admin.is_active == True).all()
            admin_ids = [(a.id, a.telegram_id) for a in admins]

        for admin_id, telegram_id in admin_ids:
            try:
                await bot.send_message(
                    chat_id=telegram_id,
                    text=text,
                    reply_markup=keyboard,
                )
            except TelegramError as e:
                logger.error(f"Failed to notify admin {admin_id}: {e}")


async def notify_admin_group(bot: Bot, text: str):
    """Send a text message to the admin group."""
    if Config.ADMIN_GROUP_CHAT_ID:
        try:
            await bot.send_message(
                chat_id=Config.ADMIN_GROUP_CHAT_ID, text=text
            )
        except TelegramError as e:
            logger.error(f"Failed to notify admin group: {e}")
