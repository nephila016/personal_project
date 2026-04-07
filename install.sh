#!/usr/bin/env bash
# ==============================================================================
# Water Distribution Management System — Install & Manage
#
# Usage:
#   ./install.sh                  # Interactive install (auto-detects Docker)
#   ./install.sh docker           # Force Docker install
#   ./install.sh bare             # Force bare-metal install
#   ./install.sh start|stop|restart|status|logs|backup|update
# ==============================================================================
set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

info()  { echo -e "${GREEN}[✓]${NC} $1"; }
warn()  { echo -e "${YELLOW}[!]${NC} $1"; }
error() { echo -e "${RED}[✗]${NC} $1"; exit 1; }
step()  { echo -e "\n${CYAN}${BOLD}→ $1${NC}"; }

APP_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$APP_DIR"

# ==============================================================================
# Helpers
# ==============================================================================

has_docker() { command -v docker &>/dev/null && docker compose version &>/dev/null; }
has_systemctl() { command -v systemctl &>/dev/null; }
gen_secret() { python3 -c "import secrets; print(secrets.token_hex(32))"; }
gen_password() { python3 -c "import secrets,string; print(''.join(secrets.choice(string.ascii_letters+string.digits) for _ in range(20)))"; }

detect_os() {
    if [[ "$OSTYPE" == "darwin"* ]]; then echo "macos"
    elif [ -f /etc/debian_version ]; then echo "debian"
    elif [ -f /etc/redhat-release ]; then echo "rhel"
    else echo "unknown"; fi
}

# ==============================================================================
# Interactive .env setup
# ==============================================================================

setup_env() {
    if [ -f .env ]; then
        warn ".env already exists."
        read -rp "Overwrite? [y/N]: " overwrite
        [[ "$overwrite" != "y" && "$overwrite" != "Y" ]] && return
    fi

    echo ""
    echo -e "${BOLD}╔══════════════════════════════════════╗${NC}"
    echo -e "${BOLD}║     Configuration Setup              ║${NC}"
    echo -e "${BOLD}╚══════════════════════════════════════╝${NC}"
    echo ""

    # Bot token
    read -rp "Telegram Bot Token (from @BotFather): " BOT_TOKEN
    [ -z "$BOT_TOKEN" ] && error "Bot token is required."

    # Admin IDs
    echo ""
    echo "Enter Telegram IDs for drivers/admins."
    echo "Each driver should message @userinfobot to get their ID."
    read -rp "Admin Telegram IDs (comma-separated): " ADMIN_IDS
    [ -z "$ADMIN_IDS" ] && error "At least one admin ID is required."

    # Group chat
    echo ""
    echo "Optional: Group chat ID for order notifications to drivers."
    echo "Add the bot to your group, then get the chat ID."
    read -rp "Admin Group Chat ID (leave empty to skip): " GROUP_ID

    # Database URL (only for bare-metal, Docker uses internal)
    local DB_URL=""
    if [ "${1:-}" = "bare" ]; then
        local DB_PASS
        DB_PASS=$(gen_password)
        DB_URL="postgresql://water_user:${DB_PASS}@localhost:5432/water_dis"
    fi

    local FLASK_KEY
    FLASK_KEY=$(gen_secret)
    local DB_COMPOSE_PASS
    DB_COMPOSE_PASS=$(gen_password)

    cat > .env << ENVEOF
# ==============================================
# Water Distribution Management System
# Generated: $(date -Iseconds)
# ==============================================

# Database
DATABASE_URL=${DB_URL:-postgresql://water_user:${DB_COMPOSE_PASS}@localhost:5432/water_dis}
DB_PASSWORD=${DB_COMPOSE_PASS}

# Telegram Bot
TELEGRAM_BOT_TOKEN=${BOT_TOKEN}
ADMIN_TELEGRAM_IDS=${ADMIN_IDS}
ADMIN_GROUP_CHAT_ID=${GROUP_ID}
BOT_MODE=polling

# Flask
FLASK_SECRET_KEY=${FLASK_KEY}
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

# Production
WEB_PORT=5000
# WEB_WORKERS=2
ENVEOF

    chmod 600 .env
    info ".env created (permissions: owner-only)."
}

# ==============================================================================
# Docker Install
# ==============================================================================

install_docker_deps() {
    local OS=$(detect_os)
    if has_docker; then
        info "Docker already installed."
        return
    fi

    step "Installing Docker..."
    case "$OS" in
        debian)
            sudo apt-get update -qq
            sudo apt-get install -y -qq ca-certificates curl gnupg lsb-release >/dev/null
            sudo install -m 0755 -d /etc/apt/keyrings
            curl -fsSL https://download.docker.com/linux/$(. /etc/os-release && echo "$ID")/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg 2>/dev/null
            echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/$(. /etc/os-release && echo "$ID") $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list >/dev/null
            sudo apt-get update -qq
            sudo apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-compose-plugin >/dev/null
            sudo usermod -aG docker "$USER" 2>/dev/null || true
            ;;
        rhel)
            sudo yum install -y yum-utils >/dev/null
            sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
            sudo yum install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin >/dev/null
            sudo systemctl start docker && sudo systemctl enable docker
            sudo usermod -aG docker "$USER" 2>/dev/null || true
            ;;
        macos)
            error "Install Docker Desktop from https://docker.com/products/docker-desktop"
            ;;
        *)
            error "Install Docker manually: https://docs.docker.com/engine/install/"
            ;;
    esac
    info "Docker installed."
}

docker_install() {
    echo ""
    echo -e "${BOLD}╔══════════════════════════════════════╗${NC}"
    echo -e "${BOLD}║  Docker Installation                 ║${NC}"
    echo -e "${BOLD}╚══════════════════════════════════════╝${NC}"

    install_docker_deps
    setup_env "docker"

    step "Building and starting containers..."
    docker compose up -d --build

    echo ""
    step "Retrieving admin credentials..."
    sleep 5
    docker compose logs seed 2>&1 | grep -A5 "Global admin"

    local IP
    IP=$(hostname -I 2>/dev/null | awk '{print $1}' || echo "localhost")

    echo ""
    echo -e "${BOLD}╔══════════════════════════════════════╗${NC}"
    echo -e "${BOLD}║  Installation Complete!              ║${NC}"
    echo -e "${BOLD}╚══════════════════════════════════════╝${NC}"
    echo ""
    echo -e "  Dashboard:  ${CYAN}http://${IP}:5000${NC}"
    echo -e "  Bot:        Running (Telegram)"
    echo ""
    echo -e "  ${BOLD}Management commands:${NC}"
    echo "    ./install.sh status    — check services"
    echo "    ./install.sh logs      — view logs"
    echo "    ./install.sh stop      — stop all"
    echo "    ./install.sh start     — start all"
    echo "    ./install.sh restart   — restart all"
    echo "    ./install.sh backup    — backup database"
    echo "    ./install.sh update    — pull & rebuild"
    echo ""
}

# ==============================================================================
# Bare-metal Install
# ==============================================================================

bare_install() {
    local OS=$(detect_os)

    echo ""
    echo -e "${BOLD}╔══════════════════════════════════════╗${NC}"
    echo -e "${BOLD}║  Bare-metal Installation             ║${NC}"
    echo -e "${BOLD}╚══════════════════════════════════════╝${NC}"

    step "Installing system packages..."
    case "$OS" in
        debian)
            sudo apt-get update -qq
            sudo apt-get install -y -qq python3 python3-venv python3-pip \
                postgresql postgresql-contrib libpq-dev >/dev/null
            ;;
        rhel)
            sudo yum install -y python3 python3-pip postgresql-server \
                postgresql-contrib libpq-devel >/dev/null
            sudo postgresql-setup --initdb 2>/dev/null || true
            ;;
        macos)
            command -v brew &>/dev/null || error "Install Homebrew first: https://brew.sh"
            brew install python3 postgresql@17 >/dev/null 2>&1 || true
            ;;
        *) warn "Unknown OS. Ensure Python 3.11+ and PostgreSQL 15+ are installed." ;;
    esac

    step "Starting PostgreSQL..."
    case "$OS" in
        debian) sudo systemctl start postgresql; sudo systemctl enable postgresql ;;
        rhel) sudo systemctl start postgresql; sudo systemctl enable postgresql ;;
        macos) brew services start postgresql@17 2>/dev/null || true ;;
    esac
    sleep 2

    setup_env "bare"

    step "Creating database..."
    source .env
    local DB_PASS
    DB_PASS=$(echo "$DATABASE_URL" | sed -n 's|.*://[^:]*:\([^@]*\)@.*|\1|p')
    sudo -u postgres psql -tc "SELECT 1 FROM pg_roles WHERE rolname='water_user'" | grep -q 1 || \
        sudo -u postgres psql -c "CREATE USER water_user WITH PASSWORD '$DB_PASS';"
    sudo -u postgres psql -tc "SELECT 1 FROM pg_database WHERE datname='water_dis'" | grep -q 1 || \
        sudo -u postgres psql -c "CREATE DATABASE water_dis OWNER water_user;"
    sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE water_dis TO water_user;" 2>/dev/null || true

    step "Setting up Python environment..."
    python3 -m venv .venv
    source .venv/bin/activate
    pip install --quiet --upgrade pip
    pip install --quiet -r requirements.txt
    pip install --quiet "python-telegram-bot[job-queue]"

    step "Seeding database..."
    python seed.py

    step "Creating systemd services..."
    if has_systemctl; then
        local USER=$(whoami)
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
EnvironmentFile=$APP_DIR/.env

[Install]
WantedBy=multi-user.target
SVCEOF

        sudo systemctl daemon-reload
        info "Systemd services created."
    else
        warn "No systemd. Use ./install.sh start to run manually."
    fi

    local IP
    IP=$(hostname -I 2>/dev/null | awk '{print $1}' || echo "localhost")

    echo ""
    echo -e "${BOLD}╔══════════════════════════════════════╗${NC}"
    echo -e "${BOLD}║  Installation Complete!              ║${NC}"
    echo -e "${BOLD}╚══════════════════════════════════════╝${NC}"
    echo ""
    echo -e "  Start:      ${CYAN}./install.sh start${NC}"
    echo -e "  Dashboard:  ${CYAN}http://${IP}:5000${NC}"
    echo ""
}

# ==============================================================================
# Management Commands
# ==============================================================================

cmd_start() {
    if has_docker && [ -f docker-compose.yml ]; then
        docker compose up -d
        info "Docker services started."
        docker compose ps
    elif has_systemctl && [ -f /etc/systemd/system/water-bot.service ]; then
        sudo systemctl start water-bot water-web
        sudo systemctl enable water-bot water-web 2>/dev/null
        info "Systemd services started."
    else
        source .venv/bin/activate 2>/dev/null || error "No venv found. Run ./install.sh first."
        mkdir -p logs bot_persistence
        nohup python run_bot.py >> logs/bot_stdout.log 2>&1 &
        echo $! > .bot.pid
        nohup gunicorn -c gunicorn.conf.py run_web:app >> logs/web_stdout.log 2>&1 &
        echo $! > .web.pid
        info "Started — Bot PID: $(cat .bot.pid) | Web PID: $(cat .web.pid)"
    fi
}

cmd_stop() {
    if has_docker && [ -f docker-compose.yml ]; then
        docker compose stop
        info "Docker services stopped."
    elif has_systemctl && [ -f /etc/systemd/system/water-bot.service ]; then
        sudo systemctl stop water-bot water-web
        info "Systemd services stopped."
    else
        [ -f .bot.pid ] && kill "$(cat .bot.pid)" 2>/dev/null && rm -f .bot.pid
        [ -f .web.pid ] && kill "$(cat .web.pid)" 2>/dev/null && rm -f .web.pid
        info "Services stopped."
    fi
}

cmd_restart() {
    cmd_stop
    sleep 2
    cmd_start
}

cmd_status() {
    echo ""
    if has_docker && [ -f docker-compose.yml ]; then
        docker compose ps
    elif has_systemctl && [ -f /etc/systemd/system/water-bot.service ]; then
        systemctl status water-bot water-web --no-pager 2>/dev/null || true
    else
        echo "Bot: $([ -f .bot.pid ] && (kill -0 "$(cat .bot.pid)" 2>/dev/null && echo "running (PID $(cat .bot.pid))" || echo "dead") || echo "not running")"
        echo "Web: $([ -f .web.pid ] && (kill -0 "$(cat .web.pid)" 2>/dev/null && echo "running (PID $(cat .web.pid))" || echo "dead") || echo "not running")"
    fi
    echo ""
}

cmd_logs() {
    if has_docker && [ -f docker-compose.yml ]; then
        docker compose logs -f --tail=50
    else
        tail -f logs/bot.log logs/web.log logs/error.log 2>/dev/null || \
            warn "No log files found."
    fi
}

cmd_backup() {
    local BACKUP_DIR="$APP_DIR/backups"
    mkdir -p "$BACKUP_DIR"
    local TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    local FILE="$BACKUP_DIR/water_dis_${TIMESTAMP}.sql.gz"

    step "Backing up database..."
    if has_docker && [ -f docker-compose.yml ]; then
        source .env 2>/dev/null || true
        docker compose exec -T db pg_dump -U water_user water_dis | gzip > "$FILE"
    else
        sudo -u postgres pg_dump water_dis | gzip > "$FILE"
    fi
    info "Backup saved: $FILE ($(du -h "$FILE" | cut -f1))"

    # Keep only last 30 backups
    ls -t "$BACKUP_DIR"/*.sql.gz 2>/dev/null | tail -n +31 | xargs rm -f 2>/dev/null || true
    info "Backups in $BACKUP_DIR: $(ls "$BACKUP_DIR"/*.sql.gz 2>/dev/null | wc -l) files"
}

cmd_update() {
    step "Pulling latest code..."
    git pull origin main

    if has_docker && [ -f docker-compose.yml ]; then
        step "Rebuilding containers..."
        docker compose up -d --build
        info "Updated and restarted."
    else
        step "Updating dependencies..."
        source .venv/bin/activate
        pip install --quiet -r requirements.txt
        cmd_restart
        info "Updated and restarted."
    fi
}

# ==============================================================================
# Main
# ==============================================================================

case "${1:-}" in
    docker)   docker_install ;;
    bare)     bare_install ;;
    start)    cmd_start ;;
    stop)     cmd_stop ;;
    restart)  cmd_restart ;;
    status)   cmd_status ;;
    logs)     cmd_logs ;;
    backup)   cmd_backup ;;
    update)   cmd_update ;;
    seed)
        if has_docker && [ -f docker-compose.yml ]; then
            docker compose run --rm seed
        else
            source .venv/bin/activate && python seed.py
        fi
        ;;
    ""|install)
        echo ""
        echo -e "${BOLD}╔══════════════════════════════════════════╗${NC}"
        echo -e "${BOLD}║  Water Distribution — Installer          ║${NC}"
        echo -e "${BOLD}╚══════════════════════════════════════════╝${NC}"
        echo ""
        if has_docker; then
            echo -e "  Docker detected. Using ${CYAN}Docker installation${NC}."
            echo ""
            docker_install
        else
            echo -e "  No Docker found. Using ${CYAN}bare-metal installation${NC}."
            echo -e "  (Install Docker first for the recommended setup)"
            echo ""
            bare_install
        fi
        ;;
    *)
        echo ""
        echo "Usage: $0 [command]"
        echo ""
        echo "  Install:"
        echo "    install     Auto-detect and install (default)"
        echo "    docker      Force Docker installation"
        echo "    bare        Force bare-metal installation"
        echo ""
        echo "  Manage:"
        echo "    start       Start all services"
        echo "    stop        Stop all services"
        echo "    restart     Restart all services"
        echo "    status      Show service status"
        echo "    logs        Follow live logs"
        echo ""
        echo "  Maintain:"
        echo "    backup      Backup database to backups/"
        echo "    update      Pull latest code & rebuild"
        echo "    seed        Re-run database seed"
        echo ""
        exit 1
        ;;
esac
