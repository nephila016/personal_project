#!/usr/bin/env bash
# ==============================================
# Water Distribution Bot — Install Script
# Supports: Ubuntu/Debian, CentOS/RHEL, macOS
# ==============================================
set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

APP_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$APP_DIR"

# ---- Detect OS ----
detect_os() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
    elif [ -f /etc/debian_version ]; then
        OS="debian"
    elif [ -f /etc/redhat-release ]; then
        OS="rhel"
    else
        OS="unknown"
    fi
    info "Detected OS: $OS"
}

# ---- Install system dependencies ----
install_system_deps() {
    info "Installing system dependencies..."
    case "$OS" in
        debian)
            sudo apt-get update -qq
            sudo apt-get install -y -qq python3 python3-venv python3-pip postgresql postgresql-contrib libpq-dev >/dev/null
            ;;
        rhel)
            sudo yum install -y python3 python3-pip postgresql-server postgresql-contrib libpq-devel >/dev/null
            sudo postgresql-setup --initdb 2>/dev/null || true
            ;;
        macos)
            if ! command -v brew &>/dev/null; then
                error "Homebrew is required. Install from https://brew.sh"
            fi
            brew install python3 postgresql >/dev/null 2>&1 || true
            ;;
        *)
            warn "Unknown OS. Make sure Python 3.11+ and PostgreSQL are installed."
            ;;
    esac
}

# ---- Start PostgreSQL ----
start_postgres() {
    info "Starting PostgreSQL..."
    case "$OS" in
        debian)
            sudo systemctl start postgresql 2>/dev/null || sudo service postgresql start
            sudo systemctl enable postgresql 2>/dev/null || true
            ;;
        rhel)
            sudo systemctl start postgresql
            sudo systemctl enable postgresql
            ;;
        macos)
            brew services start postgresql 2>/dev/null || pg_ctl -D /usr/local/var/postgres start
            ;;
    esac
    sleep 2
}

# ---- Setup database ----
setup_database() {
    info "Setting up database..."
    local DB_NAME="water_dis"
    local DB_USER="water_user"
    local DB_PASS

    DB_PASS=$(python3 -c "import secrets; print(secrets.token_hex(16))")

    # Create user and database
    sudo -u postgres psql -tc "SELECT 1 FROM pg_roles WHERE rolname='$DB_USER'" | grep -q 1 || \
        sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASS';"

    sudo -u postgres psql -tc "SELECT 1 FROM pg_database WHERE datname='$DB_NAME'" | grep -q 1 || \
        sudo -u postgres psql -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;"

    sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"

    echo "postgresql://$DB_USER:$DB_PASS@localhost:5432/$DB_NAME"
}

# ---- Create .env ----
create_env() {
    local DB_URL="$1"

    if [ -f .env ]; then
        warn ".env already exists. Skipping creation."
        return
    fi

    local FLASK_KEY
    FLASK_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")

    echo ""
    echo "======================================"
    echo "  Configuration"
    echo "======================================"

    read -rp "Telegram Bot Token (from @BotFather): " BOT_TOKEN
    [ -z "$BOT_TOKEN" ] && error "Bot token is required."

    read -rp "Admin Telegram IDs (comma-separated): " ADMIN_IDS
    [ -z "$ADMIN_IDS" ] && error "At least one admin ID is required."

    read -rp "Admin Group Chat ID (leave empty if none): " GROUP_ID

    cat > .env << ENVEOF
# Database
DATABASE_URL=$DB_URL

# Telegram Bot
TELEGRAM_BOT_TOKEN=$BOT_TOKEN
ADMIN_TELEGRAM_IDS=$ADMIN_IDS
ADMIN_GROUP_CHAT_ID=$GROUP_ID
BOT_MODE=polling

# Flask
FLASK_SECRET_KEY=$FLASK_KEY
FLASK_ENV=production

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
ENVEOF

    info ".env created."
}

# ---- Setup Python venv ----
setup_venv() {
    info "Creating Python virtual environment..."
    python3 -m venv .venv
    source .venv/bin/activate

    info "Installing Python dependencies..."
    pip install --quiet --upgrade pip
    pip install --quiet -r requirements.txt
    pip install --quiet "python-telegram-bot[job-queue]"

    info "Dependencies installed."
}

# ---- Seed database ----
seed_db() {
    info "Seeding database..."
    source .venv/bin/activate
    python seed.py
}

# ---- Create systemd services ----
create_systemd_services() {
    if [[ "$OS" != "debian" && "$OS" != "rhel" ]]; then
        warn "Systemd not available on $OS. Use 'install.sh start' to run manually."
        return
    fi

    local USER
    USER=$(whoami)

    info "Creating systemd services..."

    sudo tee /etc/systemd/system/water-bot.service >/dev/null << SVCEOF
[Unit]
Description=Water Distribution Telegram Bot
After=network.target postgresql.service
Requires=postgresql.service

[Service]
Type=simple
User=$USER
WorkingDirectory=$APP_DIR
ExecStart=$APP_DIR/.venv/bin/python $APP_DIR/run_bot.py
Restart=always
RestartSec=10
Environment=PATH=$APP_DIR/.venv/bin:/usr/bin
EnvironmentFile=$APP_DIR/.env

[Install]
WantedBy=multi-user.target
SVCEOF

    sudo tee /etc/systemd/system/water-web.service >/dev/null << SVCEOF
[Unit]
Description=Water Distribution Web Dashboard
After=network.target postgresql.service
Requires=postgresql.service

[Service]
Type=simple
User=$USER
WorkingDirectory=$APP_DIR
ExecStart=$APP_DIR/.venv/bin/gunicorn -c $APP_DIR/gunicorn.conf.py run_web:app
Restart=always
RestartSec=10
Environment=PATH=$APP_DIR/.venv/bin:/usr/bin
EnvironmentFile=$APP_DIR/.env

[Install]
WantedBy=multi-user.target
SVCEOF

    sudo systemctl daemon-reload
    info "Systemd services created: water-bot, water-web"
}

# ---- Start/Stop/Status ----
start_services() {
    if command -v systemctl &>/dev/null && [ -f /etc/systemd/system/water-bot.service ]; then
        sudo systemctl start water-bot water-web
        sudo systemctl enable water-bot water-web
        info "Services started via systemd."
        sudo systemctl status water-bot water-web --no-pager
    else
        info "Starting services in background..."
        source .venv/bin/activate
        mkdir -p logs bot_persistence
        nohup python run_bot.py >> logs/bot_stdout.log 2>&1 &
        echo $! > .bot.pid
        nohup gunicorn -c gunicorn.conf.py run_web:app >> logs/web_stdout.log 2>&1 &
        echo $! > .web.pid
        info "Bot PID: $(cat .bot.pid) | Web PID: $(cat .web.pid)"
        info "Dashboard: http://$(hostname -I | awk '{print $1}'):5000"
    fi
}

stop_services() {
    if command -v systemctl &>/dev/null && [ -f /etc/systemd/system/water-bot.service ]; then
        sudo systemctl stop water-bot water-web
        info "Services stopped."
    else
        [ -f .bot.pid ] && kill "$(cat .bot.pid)" 2>/dev/null && rm .bot.pid && info "Bot stopped."
        [ -f .web.pid ] && kill "$(cat .web.pid)" 2>/dev/null && rm .web.pid && info "Web stopped."
    fi
}

show_status() {
    if command -v systemctl &>/dev/null && [ -f /etc/systemd/system/water-bot.service ]; then
        sudo systemctl status water-bot water-web --no-pager
    else
        echo "Bot: $([ -f .bot.pid ] && (kill -0 "$(cat .bot.pid)" 2>/dev/null && echo "running (PID $(cat .bot.pid))" || echo "dead") || echo "not running")"
        echo "Web: $([ -f .web.pid ] && (kill -0 "$(cat .web.pid)" 2>/dev/null && echo "running (PID $(cat .web.pid))" || echo "dead") || echo "not running")"
    fi
    echo ""
    echo "Logs:"
    ls -lh logs/ 2>/dev/null || echo "  No logs yet."
}

show_logs() {
    tail -f logs/bot.log logs/web.log logs/error.log 2>/dev/null
}

# ---- Main ----
case "${1:-install}" in
    install)
        echo "======================================"
        echo "  Water Distribution Bot — Installer"
        echo "======================================"
        echo ""
        detect_os
        install_system_deps
        start_postgres
        DB_URL=$(setup_database)
        create_env "$DB_URL"
        setup_venv
        seed_db
        create_systemd_services
        echo ""
        echo "======================================"
        echo "  Installation Complete!"
        echo "======================================"
        echo ""
        echo "Start:   ./install.sh start"
        echo "Stop:    ./install.sh stop"
        echo "Status:  ./install.sh status"
        echo "Logs:    ./install.sh logs"
        echo ""
        echo "Dashboard: http://localhost:5000"
        echo ""
        ;;
    start)
        start_services
        ;;
    stop)
        stop_services
        ;;
    restart)
        stop_services
        sleep 2
        start_services
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    seed)
        source .venv/bin/activate
        python seed.py
        ;;
    *)
        echo "Usage: $0 {install|start|stop|restart|status|logs|seed}"
        exit 1
        ;;
esac
