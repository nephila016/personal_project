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

        try:
            await bot.send_message(chat_id=customer.telegram_id, text=text)
            if customer.notification_blocked:
                customer.notification_blocked = False
                session.commit()
        except Forbidden:
            logger.warning(
                f"Customer {customer_id} has blocked the bot."
            )
            customer.notification_blocked = True
            session.commit()
        except TelegramError as e:
            logger.error(f"Failed to notify customer {customer_id}: {e}")


async def notify_admins_new_order(bot: Bot, order):
    """Notify admin group or individual admins about a new order."""
    text = (
        f"New Order #{order.id}\n"
        f"Customer: {order.customer.full_name}\n"
        f"Bottles: {order.bottle_count}\n"
        f"Address: {order.delivery_address}"
    )
    if order.delivery_notes:
        text += f"\nNotes: {order.delivery_notes}"
    text += f"\nPhone: {order.customer.phone}"

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    f"Claim #{order.id}",
                    callback_data=f"claim_{order.id}_{order.version}",
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
            admins = (
                session.query(Admin).filter(Admin.is_active == True).all()
            )
            for admin in admins:
                try:
                    await bot.send_message(
                        chat_id=admin.telegram_id,
                        text=text,
                        reply_markup=keyboard,
                    )
                except TelegramError as e:
                    logger.error(
                        f"Failed to notify admin {admin.id}: {e}"
                    )


async def notify_admin_group(bot: Bot, text: str):
    """Send a text message to the admin group."""
    if Config.ADMIN_GROUP_CHAT_ID:
        try:
            await bot.send_message(
                chat_id=Config.ADMIN_GROUP_CHAT_ID, text=text
            )
        except TelegramError as e:
            logger.error(f"Failed to notify admin group: {e}")
