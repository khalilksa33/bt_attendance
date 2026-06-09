#!/bin/bash
# Docker deployment script for bt_attendance on Host A
# Pulls latest image from Docker Hub and starts containers

set -e

PROJECT_DIR="$HOME/bt_attendance"
LOG_FILE="$PROJECT_DIR/deploy.log"

echo "=== BT Attendance Docker Deployment ===" | tee -a "$LOG_FILE"
echo "Deployment started at $(date)" >> "$LOG_FILE"

# 1. Navigate to project directory
echo "[1/7] Navigating to project directory..." | tee -a "$LOG_FILE"
cd "$PROJECT_DIR"

# 2. Pull latest code from GitHub
echo "[2/7] Pulling latest code from GitHub..." | tee -a "$LOG_FILE"
git fetch origin main 2>&1 | tee -a "$LOG_FILE"
git reset --hard origin/main 2>&1 | tee -a "$LOG_FILE"

# 3. Check if .env exists
echo "[3/7] Checking configuration..." | tee -a "$LOG_FILE"
if [ ! -f ".env" ]; then
    echo "⚠️  .env not found, creating from template..." | tee -a "$LOG_FILE"
    cp .env.example .env
    echo "⚠️  IMPORTANT: Edit .env with your configuration before starting!" | tee -a "$LOG_FILE"
    exit 1
fi

# 4. Login to Docker Hub
echo "[4/7] Logging in to Docker Hub..." | tee -a "$LOG_FILE"
# Assumes DOCKERHUB_USERNAME and DOCKERHUB_TOKEN environment variables are set
if [ -z "$DOCKERHUB_USERNAME" ] || [ -z "$DOCKERHUB_TOKEN" ]; then
    echo "❌ DOCKERHUB_USERNAME or DOCKERHUB_TOKEN not set" | tee -a "$LOG_FILE"
    exit 1
fi

echo "$DOCKERHUB_TOKEN" | docker login -u "$DOCKERHUB_USERNAME" --password-stdin 2>&1 | tee -a "$LOG_FILE"

# 5. Pull latest Docker image
echo "[5/7] Pulling latest Docker image..." | tee -a "$LOG_FILE"
docker pull "$DOCKERHUB_USERNAME/bt_attendance:latest" 2>&1 | tee -a "$LOG_FILE"

# 6. Stop and remove old containers
echo "[6/7] Stopping old containers..." | tee -a "$LOG_FILE"
docker-compose down 2>/dev/null || true

# 7. Start new containers
echo "[7/7] Starting containers..." | tee -a "$LOG_FILE"
docker-compose up -d 2>&1 | tee -a "$LOG_FILE"

# Wait for services to be ready
sleep 3

echo "" | tee -a "$LOG_FILE"
echo "=== Deployment Summary ===" | tee -a "$LOG_FILE"
echo "✅ Code updated from GitHub" | tee -a "$LOG_FILE"
echo "✅ Docker image pulled from Docker Hub" | tee -a "$LOG_FILE"
echo "✅ Containers started" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"
echo "Container Status:" | tee -a "$LOG_FILE"
docker-compose ps 2>&1 | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"
echo "Portal: http://192.168.8.250:5001" | tee -a "$LOG_FILE"
echo "Admin: http://192.168.8.250:5002" | tee -a "$LOG_FILE"
echo "Deployment completed at $(date)" >> "$LOG_FILE"
