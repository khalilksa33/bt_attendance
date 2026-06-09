#!/bin/bash
# Quick setup script for BT Attendance on Host A
# Run this once to set up the entire system

set -e

echo "============================================"
echo "BT Attendance - Host A Setup Script"
echo "============================================"
echo ""

# Check if running on Linux
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    echo "❌ This script only works on Linux. Detected: $OSTYPE"
    exit 1
fi

# 1. Install system dependencies
echo "[1/8] Installing system dependencies..."
sudo apt-get update -qq
sudo apt-get install -y -qq \
    python3 \
    python3-venv \
    python3-pip \
    git \
    curl \
    wget \
    net-tools \
    &>/dev/null
echo "✅ System dependencies installed"

# 2. Clone repository (if not exists)
echo "[2/8] Setting up repository..."
if [ ! -d "$HOME/bt_attendance" ]; then
    git clone https://github.com/khalilksa33/bt_attendance.git "$HOME/bt_attendance"
    echo "✅ Repository cloned"
else
    echo "✅ Repository already exists"
    cd "$HOME/bt_attendance"
    git pull origin main
fi

cd "$HOME/bt_attendance"

# 3. Create virtual environment
echo "[3/8] Creating Python virtual environment..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

source .venv/bin/activate

# 4. Install Python packages
echo "[4/8] Installing Python dependencies..."
pip install --upgrade pip setuptools wheel -q
pip install -r requirements.txt -q
echo "✅ Python dependencies installed"

# 5. Create logs directory
echo "[5/8] Setting up logs directory..."
mkdir -p logs
chmod 755 logs
echo "✅ Logs directory created"

# 6. Setup environment file
echo "[6/8] Setting up environment configuration..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "✅ .env file created (edit with: nano .env)"
    echo "⚠️  IMPORTANT: Edit .env with your configuration before starting services"
else
    echo "✅ .env file already exists"
fi

# 7. Install systemd user services
echo "[7/8] Installing systemd services..."
mkdir -p "$HOME/.config/systemd/user"

for service in systemd/*.service systemd/*.timer; do
    if [ -f "$service" ]; then
        cp "$service" "$HOME/.config/systemd/user/"
        echo "  Installed: $(basename $service)"
    fi
done

systemctl --user daemon-reload
echo "✅ Systemd services installed"

# 8. Enable and start services
echo "[8/8] Configuring service startup..."
systemctl --user enable portal.service admin-portal.service attendance-bot.timer 2>/dev/null || true
echo "✅ Services configured for auto-start"

echo ""
echo "============================================"
echo "✅ Setup Complete!"
echo "============================================"
echo ""
echo "NEXT STEPS:"
echo ""
echo "1. Edit your environment file:"
echo "   nano ~/.env"
echo "   (Configure ERP, email, biometric settings)"
echo ""
echo "2. Start services:"
echo "   systemctl --user start portal.service"
echo "   systemctl --user start admin-portal.service"
echo "   systemctl --user start attendance-bot.timer"
echo ""
echo "3. Check service status:"
echo "   systemctl --user status portal.service"
echo "   systemctl --user status admin-portal.service"
echo ""
echo "4. View logs:"
echo "   tail -f logs/portal.log"
echo "   tail -f logs/admin_portal.log"
echo ""
echo "5. Set up internet access (choose one):"
echo "   - Cloudflare Tunnel: See docs/DEPLOYMENT.md (Section 4)"
echo "   - ngrok: See docs/DEPLOYMENT.md (Section 5)"
echo ""
echo "6. For CI/CD deployment setup:"
echo "   See docs/DEPLOYMENT.md (Sections 1-2)"
echo ""
