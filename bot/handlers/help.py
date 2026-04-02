import logging

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from app.database import get_session
from app.models.admin import Admin
from app.models.customer import Customer

logger = logging.getLogger(__name__)

CUSTOMER_COMMANDS = (
    "Customer Commands\n"
    "-----------------------------\n"
    "/start - Register or welcome\n"
    "/order - Place a new order\n"
    "/reorder - Repeat your last order\n"
    "/myorders - View your order history\n"
    "/cancel - Cancel a pending order\n"
    "/profile - View/edit your profile\n"
    "/help - Show this help message\n"
)

ADMIN_COMMANDS = (
    "Admin Commands\n"
    "-----------------------------\n"
    "/pending - View pending orders\n"
    "/active - View your active orders\n"
    "/receive - Record bottle receipt\n"
    "/returns - Record bottle returns\n"
    "/inventory - View your inventory\n"
    "/help - Show this help message\n"
)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show available commands based on the user's role."""
    user = update.effective_user
    if not user:
        return

    is_customer = False
    is_admin = False

    with get_session() as session:
        customer = (
            session.query(Customer)
            .filter(Customer.telegram_id == user.id, Customer.is_active == True)
            .first()
        )
        admin = (
            session.query(Admin)
            .filter(Admin.telegram_id == user.id, Admin.is_active == True)
            .first()
        )
        is_customer = customer is not None
        is_admin = admin is not None

    if is_customer and is_admin:
        text = f"{CUSTOMER_COMMANDS}\n{ADMIN_COMMANDS}"
    elif is_admin:
        text = ADMIN_COMMANDS
    elif is_customer:
        text = CUSTOMER_COMMANDS
    else:
        text = (
            "You are not registered yet.\n"
            "Use /start to register as a customer."
        )

    await update.message.reply_text(text)


help_handler = CommandHandler("help", help_command)


def get_handlers():
    return [help_handler]
