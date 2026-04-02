import logging
import os
import sys

from telegram import BotCommand
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    PicklePersistence,
)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config

logger = logging.getLogger(__name__)


async def post_init(application: Application):
    """Set bot commands after startup."""
    customer_commands = [
        BotCommand("start", "Register or see welcome message"),
        BotCommand("order", "Order water bottles"),
        BotCommand("reorder", "Repeat your last order"),
        BotCommand("myorders", "View your order history"),
        BotCommand("cancel", "Cancel a pending order"),
        BotCommand("profile", "View or edit your profile"),
        BotCommand("help", "Show available commands"),
    ]
    await application.bot.set_my_commands(customer_commands)
    logger.info("Bot commands registered.")


def create_application() -> Application:
    persistence = PicklePersistence(filepath="bot_persistence/bot_data")

    app = (
        Application.builder()
        .token(Config.TELEGRAM_BOT_TOKEN)
        .persistence(persistence)
        .post_init(post_init)
        .build()
    )

    from bot.handlers.start import get_handlers as start_handlers
    from bot.handlers.order import get_handlers as order_handlers
    from bot.handlers.reorder import get_handlers as reorder_handlers
    from bot.handlers.my_orders import get_handlers as my_orders_handlers
    from bot.handlers.cancel import get_handlers as cancel_handlers
    from bot.handlers.profile import get_handlers as profile_handlers
    from bot.handlers.help import get_handlers as help_handlers
    from bot.handlers.error import error_handler

    from bot.handlers.admin_pending import get_handlers as admin_pending_handlers
    from bot.handlers.admin_active import get_handlers as admin_active_handlers
    from bot.handlers.admin_receive import get_handlers as admin_receive_handlers
    from bot.handlers.admin_returns import get_handlers as admin_returns_handlers
    from bot.handlers.admin_customer import get_handlers as admin_customer_handlers
    from bot.handlers.admin_stock import get_handlers as admin_stock_handlers

    handler_modules = [
        start_handlers,
        order_handlers,
        reorder_handlers,
        my_orders_handlers,
        cancel_handlers,
        profile_handlers,
        help_handlers,
        admin_pending_handlers,
        admin_active_handlers,
        admin_receive_handlers,
        admin_returns_handlers,
        admin_customer_handlers,
        admin_stock_handlers,
    ]

    for get_handlers in handler_modules:
        for handler in get_handlers():
            app.add_handler(handler)

    # Global callback for claim buttons from notifications
    app.add_handler(
        CallbackQueryHandler(
            _handle_notification_claim, pattern=r"^claim_\d+_\d+$"
        )
    )

    app.add_error_handler(error_handler)

    return app


async def _handle_notification_claim(update, context):
    """Handle claim buttons pressed from admin group notifications."""
    from bot.handlers.admin_pending import claim_callback

    await claim_callback(update, context)


def run():
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO,
    )

    os.makedirs("bot_persistence", exist_ok=True)

    app = create_application()
    logger.info("Starting bot in polling mode...")
    app.run_polling(drop_pending_updates=True)
