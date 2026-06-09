#!/bin/bash
# Health check script for BT Attendance services on Host A
# Shows the status of all services and connectivity

echo "=========================================="
echo "BT Attendance - Health Check"
echo "=========================================="
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check service status
check_service() {
    local service=$1
    local port=$2
    
    if systemctl --user is-active --quiet "$service"; then
        echo -e "${GREEN}✅${NC} $service is running"
        
        # Check if port is listening
        if netstat -tlnp 2>/dev/null | grep -q ":$port"; then
            echo "   └─ Listening on port $port"
        fi
    else
        echo -e "${RED}❌${NC} $service is NOT running"
        return 1
    fi
}

echo "Service Status:"
echo "==============="
check_service "portal.service" "5001" || true
check_service "admin-portal.service" "5002" || true

echo ""
echo "Timer Status:"
echo "============="
if systemctl --user is-active --quiet attendance-bot.timer; then
    echo -e "${GREEN}✅${NC} attendance-bot.timer is active"
    
    # Show next run time
    next_run=$(systemctl --user list-timers --all | grep "attendance-bot" | awk '{print $1, $2}')
    if [ ! -z "$next_run" ]; then
        echo "   └─ Next run: $next_run"
    fi
else
    echo -e "${RED}❌${NC} attendance-bot.timer is NOT active"
fi

echo ""
echo "Network Connectivity:"
echo "===================="

# Check localhost connectivity
echo -n "Portal (localhost:5001): "
if curl -s http://localhost:5001 >/dev/null 2>&1; then
    echo -e "${GREEN}✅${NC}"
else
    echo -e "${RED}❌${NC}"
fi

echo -n "Admin Portal (localhost:5002): "
if curl -s http://localhost:5002 >/dev/null 2>&1; then
    echo -e "${GREEN}✅${NC}"
else
    echo -e "${RED}❌${NC}"
fi

echo ""
echo "Disk Usage:"
echo "=========="
project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
disk_usage=$(du -sh "$project_dir" 2>/dev/null | cut -f1)
echo "Project directory: $disk_usage"

logs_size=$(du -sh "$project_dir/logs" 2>/dev/null | cut -f1)
echo "Logs directory: $logs_size"

echo ""
echo "Recent Errors (last 20 lines):"
echo "=============================="
if [ -f "$project_dir/logs/portal.log" ]; then
    echo "Portal errors:"
    grep -i "error\|exception\|traceback" "$project_dir/logs/portal.log" | tail -5
    echo ""
fi

echo ""
echo "Last Activity:"
echo "=============="
if [ -f "$project_dir/logs/portal.log" ]; then
    echo "Portal (last update):"
    ls -l "$project_dir/logs/portal.log" | awk '{print $6, $7, $8}'
fi

if [ -f "$project_dir/logs/admin_portal.log" ]; then
    echo "Admin Portal (last update):"
    ls -l "$project_dir/logs/admin_portal.log" | awk '{print $6, $7, $8}'
fi

echo ""
echo "=========================================="
echo "Health Check Complete"
echo "=========================================="
echo ""
echo "For detailed logs, use:"
echo "  journalctl --user-unit=portal.service -n 50"
echo "  journalctl --user-unit=admin-portal.service -n 50"
echo "  journalctl --user-unit=attendance-bot.timer -n 50"
