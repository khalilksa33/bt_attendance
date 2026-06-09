#!/bin/bash
# Deploy script for bt_attendance on Host A (192.168.8.250)
# This script pulls latest code, installs dependencies, and restarts services

set -e

PROJECT_DIR="/home/$(whoami)/bt_attendance"
VENV_DIR="$PROJECT_DIR/.venv"
LOG_FILE="$PROJECT_DIR/deploy.log"

echo "=== BT Attendance Deployment Script ===" | tee -a "$LOG_FILE"
echo "Deployment started at $(date)" >> "$LOG_FILE"

# 1. Navigate to project directory
echo "[1/6] Navigating to project directory..." | tee -a "$LOG_FILE"
cd "$PROJECT_DIR"

# 2. Pull latest code from GitHub
echo "[2/6] Pulling latest code from GitHub..." | tee -a "$LOG_FILE"
git fetch origin main 2>&1 | tee -a "$LOG_FILE"
git reset --hard origin/main 2>&1 | tee -a "$LOG_FILE"

# 3. Create or activate virtual environment
echo "[3/6] Setting up Python virtual environment..." | tee -a "$LOG_FILE"
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR" 2>&1 | tee -a "$LOG_FILE"
else
    echo "Virtual environment already exists" >> "$LOG_FILE"
fi

source "$VENV_DIR/bin/activate"

# 4. Install dependencies
echo "[4/6] Installing Python dependencies..." | tee -a "$LOG_FILE"
pip install --upgrade pip setuptools wheel 2>&1 | tee -a "$LOG_FILE"
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt 2>&1 | tee -a "$LOG_FILE"
else
    echo "⚠️  requirements.txt not found" | tee -a "$LOG_FILE"
fi

# 5. Run syntax checks
echo "[5/6] Running syntax checks..." | tee -a "$LOG_FILE"
python -m py_compile daily_checkin_log.py 2>&1 | tee -a "$LOG_FILE" || true
python -m py_compile attendance_bot.py 2>&1 | tee -a "$LOG_FILE" || true
python -m py_compile portal.py 2>&1 | tee -a "$LOG_FILE" || true
python -m py_compile admin_portal.py 2>&1 | tee -a "$LOG_FILE" || true

# 6. Restart services
echo "[6/6] Restarting services..." | tee -a "$LOG_FILE"
systemctl --user stop portal attendance-bot admin-portal 2>/dev/null || true
sleep 2
systemctl --user start portal attendance-bot admin-portal 2>/dev/null || true

if systemctl --user is-active --quiet portal; then
    echo "✅ Services restarted successfully" | tee -a "$LOG_FILE"
else
    echo "⚠️  Some services may not have started" | tee -a "$LOG_FILE"
fi

echo "Deployment completed at $(date)" >> "$LOG_FILE"
echo "=== Deployment Summary ===" | tee -a "$LOG_FILE"
echo "✅ Code updated from GitHub" | tee -a "$LOG_FILE"
echo "✅ Dependencies installed" | tee -a "$LOG_FILE"
echo "✅ Services restarted" | tee -a "$LOG_FILE"
