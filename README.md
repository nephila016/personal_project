# Water Distribution Management System

Telegram bot + web dashboard for managing water bottle delivery. Tracks every bottle: how many each customer has, how many each driver carries, and how many empties have been returned.

**Languages:** Russian / Uzbek

## Quick Install (One Command)

```bash
git clone https://github.com/nephila016/personal_project.git
cd personal_project
chmod +x install.sh
./install.sh
```

The script auto-detects Docker. If Docker is installed, it uses Docker (recommended). Otherwise, it installs bare-metal with systemd.

## What You Need Before Installing

| Item | How to get it |
|------|---------------|
| **Telegram Bot Token** | Message [@BotFather](https://t.me/BotFather) on Telegram, create a bot, copy the token |
| **Driver Telegram IDs** | Each driver messages [@userinfobot](https://t.me/userinfobot) to get their numeric ID |
| **Group Chat ID** (optional) | Add the bot to your drivers group, then get the chat ID from a message link (`https://t.me/c/XXXXXXX/1` → chat ID is `-100XXXXXXX`) |

## Installation Options

### Option 1: Docker (Recommended)

```bash
./install.sh docker
```

Installs Docker if needed, builds containers, starts everything. **Minimum 1 GB RAM, 10 GB disk.**

### Option 2: Bare-metal (Ubuntu/Debian/CentOS)

```bash
sudo ./install.sh bare
```

Installs PostgreSQL, Python venv, creates systemd services.

### Option 3: Manual

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && pip install "python-telegram-bot[job-queue]"
cp .env.example .env && nano .env    # fill in values
python seed.py                        # creates admin (prints password)
python run_bot.py &                   # start bot
gunicorn -c gunicorn.conf.py run_web:app  # start web
```

## Management Commands

```bash
./install.sh start       # Start all services
./install.sh stop        # Stop all services
./install.sh restart     # Restart all services
./install.sh status      # Check service status
./install.sh logs        # Follow live logs
./install.sh backup      # Backup database to backups/
./install.sh update      # Pull latest code & rebuild
./install.sh seed        # Re-run database seed
```

## Recommended Server

| Users | Server | Storage | Cost |
|-------|--------|---------|------|
| 1-50 customers | 1 vCPU, 1 GB RAM | 20 GB SSD | ~$5/mo (DigitalOcean, Hetzner) |
| 50-500 customers | 2 vCPU, 2 GB RAM | 40 GB SSD | ~$10/mo |
| 500+ customers | 4 vCPU, 4 GB RAM | 80 GB SSD | ~$20/mo |

**Storage breakdown:**
- System + app: ~2 GB
- PostgreSQL data: ~100 MB per 10,000 orders
- Logs: ~500 MB (auto-rotated)
- Docker images: ~500 MB
- Backups: ~50 MB per backup (30 kept)

**Recommended providers:** Hetzner Cloud (cheapest EU), DigitalOcean, Linode, any VPS with Ubuntu 22.04+.

## How It Works

### Bottle Tracking (Core Feature)

The system tracks every bottle across the supply chain:

```
Supplier → Driver (full bottles) → Customer → Driver (empty bottles) → Supplier
```

| Metric | Where to see it |
|--------|-----------------|
| **Bottles at each customer** | Web dashboard, bot `/customer` lookup |
| **Bottles at each driver** | Web dashboard, bot `/stock` |
| **Last delivery date per customer** | Web dashboard, bot `/profile` |
| **Total bottles in circulation** | Web dashboard (Bottle Accountability) |
| **Empties returned** | Web dashboard, bot `/stock` |

### Order Flow

1. **Customer** orders via Telegram bot
2. **Notification** goes to drivers group with "Claim" button
3. **Driver** claims the order (sees customer's bottle count)
4. **Driver** delivers, marks "Delivered"
5. **Bot asks** how many empty bottles collected
6. **Everything tracked** per driver, per customer

### Web Dashboard

Login at `http://your-server:5000` with credentials printed during install.

- Overview with bottle accountability
- Orders management (cancel, reassign)
- Customer list with bottles in hand
- Driver list with stock levels
- Inventory (receipts, returns)
- CSV exports

### Bot Commands

**Customers:**

| Command | Description |
|---------|-------------|
| `/start` | Register / show menu |
| `/order` | Place new order |
| `/reorder` | Repeat last order |
| `/myorders` | Order history |
| `/cancel` | Cancel pending order |
| `/profile` | View profile + bottle stats |
| `/lang` | Switch language |
| `/help` | Show all commands |

**Drivers (Admins):**

| Command | Description |
|---------|-------------|
| `/pending` | View pending orders to claim |
| `/myactive` | View your active deliveries |
| `/receive` | Load full bottles (stock receipt) |
| `/returns` | Record empty bottle collection |
| `/stock` | View your stock (full + empties) |
| `/customer` | Look up customer info |
| `/help` | Show all commands |

## Configuration (.env)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `TELEGRAM_BOT_TOKEN` | Yes | — | Bot token from @BotFather |
| `ADMIN_TELEGRAM_IDS` | Yes | — | Driver Telegram IDs (comma-separated) |
| `ADMIN_GROUP_CHAT_ID` | No | — | Group chat for order notifications |
| `FLASK_SECRET_KEY` | Yes | — | Random string (auto-generated by installer) |
| `DATABASE_URL` | Yes | — | PostgreSQL URL (auto-generated by installer) |
| `MAX_BOTTLES_PER_ORDER` | No | 50 | Max bottles in one order |
| `MAX_PENDING_ORDERS_PER_CUSTOMER` | No | 3 | Max concurrent pending orders |
| `LOW_STOCK_WARNING_THRESHOLD` | No | 10 | Warn driver when stock is below this |
| `LOGIN_MAX_ATTEMPTS` | No | 10 | Web login attempts before lockout |
| `WEB_PORT` | No | 5000 | Web dashboard port |

## Backups

```bash
# Manual backup
./install.sh backup

# Auto-backup via cron (daily at 2 AM)
echo "0 2 * * * cd $(pwd) && ./install.sh backup" | crontab -
```

Backups are saved to `backups/` as gzipped SQL dumps. Last 30 are kept.

## Logs

| File | Content |
|------|---------|
| `logs/bot.log` | Bot activity |
| `logs/web.log` | Web dashboard |
| `logs/error.log` | Errors |
| `logs/orders.log` | Order events |
| `logs/bottles.log` | Bottle receipts & returns |

## Adding Drivers After Install

**Option A: Web Dashboard** — Go to Admins → Add New Admin → enter their Telegram ID. No restart needed.

**Option B: .env** — Add their ID to `ADMIN_TELEGRAM_IDS` and restart (`./install.sh restart`).
