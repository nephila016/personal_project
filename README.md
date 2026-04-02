# Water Distribution Management System

Telegram bot for water ordering + Flask admin dashboard. Supports Russian and Uzbek languages.

## Quick Deploy

### Option 1: Docker (Recommended)

```bash
git clone https://github.com/nephila016/personal_project.git
cd personal_project

# Create .env
cp .env.example .env
nano .env  # Fill in TELEGRAM_BOT_TOKEN, ADMIN_TELEGRAM_IDS, etc.

# Start everything
docker compose up -d

# Check logs
docker compose logs -f bot
docker compose logs seed  # Shows admin password
```

### Option 2: Install Script (Ubuntu/Debian)

```bash
git clone https://github.com/nephila016/personal_project.git
cd personal_project

# Install & configure (interactive — asks for bot token, admin IDs)
sudo ./install.sh install

# Manage
./install.sh start
./install.sh stop
./install.sh status
./install.sh logs
```

### Option 3: Manual

```bash
# Prerequisites: Python 3.11+, PostgreSQL
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pip install "python-telegram-bot[job-queue]"

# Database
createdb water_dis
cp .env.example .env && nano .env

# Seed (prints admin password)
python seed.py

# Run
python run_bot.py &          # Telegram bot
python run_web.py             # Web dashboard (dev)
gunicorn -c gunicorn.conf.py run_web:app  # Web dashboard (prod)
```

## Configuration (.env)

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `TELEGRAM_BOT_TOKEN` | Yes | From @BotFather |
| `ADMIN_TELEGRAM_IDS` | Yes | Comma-separated admin Telegram IDs |
| `FLASK_SECRET_KEY` | Yes | Random string for sessions |
| `ADMIN_GROUP_CHAT_ID` | No | Telegram group for order notifications |

## Log Files

| File | Content |
|------|---------|
| `logs/bot.log` | All bot activity |
| `logs/web.log` | Web dashboard activity |
| `logs/error.log` | Errors from both processes |
| `logs/orders.log` | Order events: created, claimed, delivered, canceled |
| `logs/bottles.log` | Bottle receipts and returns |

## Web Dashboard

Login at `http://your-server:5000` with the credentials printed by `seed.py`.

## Bot Commands

**Customers:** `/start` `/order` `/reorder` `/myorders` `/cancel` `/profile` `/lang` `/help`

**Admins:** `/pending` `/myactive` `/receive` `/returns` `/customer` `/stock` `/help`
