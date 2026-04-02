# 07 — Project Structure

## 1. Directory Tree

```
water_dis/
├── specs/                              # Specification documents (this directory)
│   ├── 01-system-overview.md
│   ├── 02-database-schema.md
│   ├── 03-order-state-machine.md
│   ├── 04-bottle-inventory.md
│   ├── 05-telegram-bot-flows.md
│   ├── 06-web-api-endpoints.md
│   ├── 07-project-structure.md
│   └── 08-implementation-sequence.md
│
├── app/                                # Shared application package
│   ├── __init__.py                     # Package init
│   ├── database.py                     # Engine, session factory, Flask-SQLAlchemy setup
│   │
│   ├── models/                         # SQLAlchemy models (shared by bot + web)
│   │   ├── __init__.py                 # Imports all models, exports Base
│   │   ├── customer.py                 # Customer model
│   │   ├── admin.py                    # Admin model
│   │   ├── global_admin.py             # GlobalAdmin model (web login)
│   │   ├── order.py                    # Order model + OrderStatus enum
│   │   ├── order_status_log.py         # OrderStatusLog model
│   │   ├── bottle_receipt.py           # BottleReceipt model
│   │   └── bottle_return.py            # BottleReturn model
│   │
│   └── services/                       # Business logic layer (shared by bot + web)
│       ├── __init__.py
│       ├── customer_service.py         # Register, lookup, update, deactivate
│       ├── order_service.py            # Create, change status (state machine + locking)
│       ├── bottle_service.py           # Stock calc, record receipt, record return
│       └── stats_service.py            # Aggregate stats for dashboard
│
├── bot/                                # Telegram bot package
│   ├── __init__.py
│   ├── main.py                         # Bot Application setup, handler registration
│   │
│   ├── handlers/                       # ConversationHandlers for each flow
│   │   ├── __init__.py
│   │   ├── start.py                    # /start — welcome + registration flow
│   │   ├── order.py                    # /order — place order flow
│   │   ├── reorder.py                  # /reorder — repeat last delivered order
│   │   ├── my_orders.py                # /myorders — view order history (paginated)
│   │   ├── cancel.py                   # /cancel — cancel pending order
│   │   ├── profile.py                  # /profile — view/edit profile
│   │   ├── switch_mode.py              # /switchmode — switch customer/admin mode
│   │   ├── admin_pending.py            # /pending — view + claim pending orders (paginated)
│   │   ├── admin_active.py             # /myactive — manage in-progress orders
│   │   ├── admin_receive.py            # /receive — record supplier receipt
│   │   ├── admin_returns.py            # /returns — record customer bottle returns
│   │   ├── admin_customer.py           # /customer — lookup customer stats
│   │   ├── admin_stock.py              # /stock — view own inventory
│   │   ├── help.py                     # /help — show available commands
│   │   └── error.py                    # Global error handler
│   │
│   ├── middlewares/
│   │   ├── __init__.py
│   │   └── auth.py                     # @require_customer, @require_admin decorators
│   │
│   ├── keyboards/
│   │   ├── __init__.py
│   │   ├── customer_kb.py              # Inline keyboards for customer flows
│   │   └── admin_kb.py                 # Inline keyboards for admin flows
│   │
│   └── utils/
│       ├── __init__.py
│       ├── notifications.py            # Send messages to admin group / customer DMs
│       ├── formatters.py               # Format order details, stats for Telegram
│       └── validators.py               # Phone, name, bottle count validation
│
├── web/                                # Flask web application
│   ├── __init__.py                     # Flask app factory: create_app()
│   │
│   ├── auth/                           # Auth blueprint
│   │   ├── __init__.py
│   │   ├── routes.py                   # GET/POST /login, GET /logout
│   │   └── forms.py                    # WTForms LoginForm
│   │
│   ├── dashboard/                      # Dashboard blueprint (HTML pages)
│   │   ├── __init__.py
│   │   └── routes.py                   # /dashboard, /dashboard/orders, etc.
│   │
│   ├── api/                            # API blueprint (JSON endpoints)
│   │   ├── __init__.py
│   │   ├── orders.py                   # /api/v1/orders/*
│   │   ├── customers.py                # /api/v1/customers/*
│   │   ├── admins.py                   # /api/v1/admins/*
│   │   ├── inventory.py                # /api/v1/inventory/*
│   │   └── stats.py                    # /api/v1/stats
│   │
│   ├── templates/                      # Jinja2 templates
│   │   ├── base.html                   # Base layout (sidebar, nav, footer)
│   │   ├── login.html                  # Login form
│   │   ├── dashboard.html              # Overview with stats + charts
│   │   ├── orders.html                 # Orders table with filters
│   │   ├── order_detail.html           # Single order view + status history
│   │   ├── customers.html              # Customer list
│   │   ├── customer_detail.html        # Customer profile + bottles
│   │   ├── admins.html                 # Admin list + performance
│   │   ├── admin_detail.html           # Admin profile + stock
│   │   ├── admin_form.html             # Add/edit admin form
│   │   └── inventory.html              # Global bottle tracking
│   │
│   └── static/                         # Static assets
│       ├── css/
│       │   └── style.css               # Dashboard styles
│       ├── js/
│       │   └── app.js                  # Client-side interactions (filters, search, charts)
│       └── img/
│
├── migrations/                         # Alembic migrations (via Flask-Migrate)
│   ├── alembic.ini
│   ├── env.py
│   └── versions/                       # Auto-generated migration files
│
├── tests/                              # Test suite
│   ├── __init__.py
│   ├── conftest.py                     # Fixtures: test DB, sessions, mock bot, test client
│   ├── test_models.py                  # Model creation, constraints, relationships
│   ├── test_order_service.py           # State machine transitions, locking, edge cases
│   ├── test_bottle_service.py          # Stock calculations, receipt, return validation
│   ├── test_customer_service.py        # Registration, lookup, update
│   ├── test_api_orders.py              # Orders API endpoints
│   ├── test_api_customers.py           # Customers API endpoints
│   ├── test_api_admins.py              # Admins API endpoints
│   ├── test_bot_registration.py        # Bot registration conversation flow
│   └── test_bot_order_flow.py          # Bot order placement + admin claim flow
│
├── config.py                           # Configuration classes (Dev, Prod, Test)
├── run_bot.py                          # Entry point: start Telegram bot
├── run_web.py                          # Entry point: start Flask web app
├── seed.py                             # Create initial global admin (random password printed to console)
├── requirements.txt                    # Python dependencies
├── .env.example                        # Environment variable template
├── .gitignore                          # Git ignore rules
├── bot_persistence/                    # ConversationHandler persistence files (gitignored)
└── README.md                           # Setup and usage instructions
```

## 2. File Responsibilities

### 2.1 Entry Points

| File | Purpose | Command |
|------|---------|---------|
| `run_bot.py` | Starts the Telegram bot process | `python run_bot.py` |
| `run_web.py` | Starts the Flask web server | `python run_web.py` |
| `seed.py` | Creates initial data (global admin, optional test data) | `python seed.py` |

### 2.2 Shared Layer (`app/`)

The `app/` package is imported by both `bot/` and `web/`. It contains:

- **Models**: SQLAlchemy ORM classes — single source of truth for database schema
- **Services**: Business logic functions that encapsulate database operations. All data access goes through services, never directly from handlers/routes.
- **Database**: Connection setup that works for both the async bot (plain `sessionmaker`) and sync Flask (`Flask-SQLAlchemy`)

```mermaid
graph TD
    BOT[bot/handlers/*] --> SVC[app/services/*]
    WEB_R[web/dashboard/routes.py] --> SVC
    WEB_A[web/api/*] --> SVC
    SVC --> MOD[app/models/*]
    MOD --> DB[app/database.py]
    DB --> PG[(PostgreSQL)]
```

### 2.3 Database Setup (`app/database.py`)

This file must handle two different usage patterns:

1. **Bot process**: Uses plain SQLAlchemy `sessionmaker` (no Flask context)
2. **Web process**: Uses Flask-SQLAlchemy (request-scoped sessions)

```python
# Simplified pattern:
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

class Base(DeclarativeBase):
    pass

# For bot: plain session factory
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

# For web: Flask-SQLAlchemy extension
# Initialized in web/__init__.py with db.init_app(app)
```

### 2.4 Service Layer Pattern

Each service module provides stateless functions that accept a database session:

```python
# app/services/order_service.py
def create_order(session, customer_id: int, bottle_count: int) -> Order:
    ...

def claim_order(session, order_id: int, admin_id: int, version: int) -> bool:
    ...

def mark_delivered(session, order_id: int, admin_id: int, version: int) -> bool:
    ...
```

Services handle:
- Data validation (business rules)
- State machine enforcement
- Optimistic locking
- Audit logging (status log entries)
- Stock calculations

Services do NOT handle:
- HTTP request/response formatting (that's the web layer)
- Telegram message formatting (that's the bot layer)
- Authentication (that's middleware)

### 2.5 Bot Handlers

Each handler file corresponds to one bot command or flow. Handlers use `ConversationHandler` for multi-step flows.

Pattern:
```python
# bot/handlers/order.py
from app.services import order_service

async def start_order(update, context):
    # Entry point for /order command
    ...

async def select_bottles(update, context):
    # Handle bottle count selection
    ...

async def confirm_order(update, context):
    # Create order via service layer
    order = order_service.create_order(session, customer_id, bottles)
    ...

# ConversationHandler exported for registration in main.py
order_handler = ConversationHandler(
    entry_points=[CommandHandler('order', start_order)],
    states={...},
    fallbacks=[...],
)
```

### 2.6 Web Blueprints

Flask routes are organized into blueprints:

- `web/auth/` — Login/logout (renders HTML)
- `web/dashboard/` — Dashboard pages (renders HTML via templates)
- `web/api/` — JSON API endpoints (consumed by dashboard JS)

## 3. Configuration (`config.py`)

```python
class Config:
    DATABASE_URL = os.environ['DATABASE_URL']
    SECRET_KEY = os.environ['FLASK_SECRET_KEY']
    TELEGRAM_BOT_TOKEN = os.environ['TELEGRAM_BOT_TOKEN']
    ADMIN_GROUP_CHAT_ID = os.environ.get('ADMIN_GROUP_CHAT_ID')
    MAX_BOTTLES_PER_ORDER = int(os.environ.get('MAX_BOTTLES_PER_ORDER', 50))
    MAX_RECEIPT_QUANTITY = int(os.environ.get('MAX_RECEIPT_QUANTITY', 1000))
    STALE_ORDER_HOURS = int(os.environ.get('STALE_ORDER_HOURS', 24))

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

class TestConfig(Config):
    TESTING = True
    DATABASE_URL = 'postgresql://..._test'
```

## 4. Environment Variables (`.env.example`)

```
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/water_dis

# Telegram Bot
TELEGRAM_BOT_TOKEN=your-bot-token-from-botfather
ADMIN_GROUP_CHAT_ID=-1001234567890
BOT_MODE=polling                          # 'polling' for dev, 'webhook' for production
WEBHOOK_URL=https://yourdomain.com/webhook # only needed if BOT_MODE=webhook
WEBHOOK_PORT=8443                          # only needed if BOT_MODE=webhook

# Flask
FLASK_SECRET_KEY=change-this-to-a-random-string
FLASK_ENV=development

# Order Limits
MAX_BOTTLES_PER_ORDER=50
MAX_PENDING_ORDERS_PER_CUSTOMER=3
DUPLICATE_ORDER_COOLDOWN_SECONDS=60
MAX_RECEIPT_QUANTITY=1000

# Monitoring
STALE_ORDER_HOURS=24
LOW_STOCK_WARNING_THRESHOLD=10

# Security
LOGIN_MAX_ATTEMPTS=10
LOGIN_LOCKOUT_MINUTES=30
API_RATE_LIMIT_PER_MINUTE=60
```

## 5. Dependencies (`requirements.txt`)

```
# Core
python-telegram-bot[persistence]>=20.0
flask>=3.0
sqlalchemy>=2.0
psycopg2-binary>=2.9
python-dotenv>=1.0

# Flask extensions
flask-login>=0.6
flask-wtf>=1.2
flask-migrate>=4.0
flask-limiter>=3.0
flask-cors>=4.0

# Utilities
werkzeug>=3.0

# Testing
pytest>=7.0
pytest-asyncio>=0.21
```

Note: `python-telegram-bot[persistence]` includes the `PicklePersistence` module for surviving bot restarts.
