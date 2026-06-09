# BT Attendance - Quick Reference Guide

## Service Management

### Start Services
```bash
systemctl --user start portal.service
systemctl --user start admin-portal.service
systemctl --user start attendance-bot.timer
```

### Stop Services
```bash
systemctl --user stop portal.service
systemctl --user stop admin-portal.service
systemctl --user stop attendance-bot.timer
```

### Restart Services
```bash
systemctl --user restart portal.service
systemctl --user restart admin-portal.service
```

### Check Status
```bash
systemctl --user status portal.service
systemctl --user status admin-portal.service
systemctl --user status attendance-bot.timer

# All services at once
systemctl --user status
```

### View Logs
```bash
# Real-time portal logs
journalctl --user-unit=portal.service -f

# Real-time admin portal logs
journalctl --user-unit=admin-portal.service -f

# Real-time attendance bot logs
journalctl --user-unit=attendance-bot.timer -f

# Last 50 lines of portal logs
journalctl --user-unit=portal.service -n 50

# Logs from today
journalctl --user-unit=portal.service --since today

# All user service logs
journalctl --user -f
```

### Enable Auto-start
```bash
systemctl --user enable portal.service
systemctl --user enable admin-portal.service
systemctl --user enable attendance-bot.timer

# Disable auto-start
systemctl --user disable portal.service
```

## Deployment & Updates

### Manual Deployment
```bash
# Navigate to project
cd ~/bt_attendance

# Pull latest code
git pull origin main

# Update dependencies
source .venv/bin/activate
pip install -r requirements.txt

# Restart services
systemctl --user restart portal.service admin-portal.service
```

### Run Deploy Script
```bash
bash scripts/deploy.sh
```

## Testing & Debugging

### Test Portal Locally
```bash
curl http://localhost:5001/
curl http://localhost:5001/login.html
```

### Test Admin Portal Locally
```bash
curl http://localhost:5002/
curl http://localhost:5002/admin/login.html
```

### Run Report Manually
```bash
source .venv/bin/activate

# Today's report
python daily_checkin_log.py

# Specific date
python daily_checkin_log.py --date 2026-06-09

# Date range
python daily_checkin_log.py --start 2026-06-01 --end 2026-06-09
```

### Test Email Configuration
```bash
python -c "
from attendance_bot import send_email
import os
from dotenv import load_dotenv

load_dotenv()
try:
    send_email('test.txt', 'Test Report')
    print('✅ Email sent successfully')
except Exception as e:
    print(f'❌ Email failed: {e}')
"
```

### Run Syntax Check
```bash
python -m py_compile daily_checkin_log.py
python -m py_compile attendance_bot.py
python -m py_compile portal.py
python -m py_compile admin_portal.py
```

## Health Monitoring

### Quick Health Check
```bash
bash scripts/health-check.sh
```

### Check Ports
```bash
# Show listening ports
netstat -tlnp | grep python

# Or using ss
ss -tlnp | grep python
```

### Check Disk Space
```bash
# Project directory
du -sh ~/bt_attendance

# Logs directory
du -sh ~/bt_attendance/logs

# System disk usage
df -h
```

## Configuration

### View Environment Variables
```bash
cat .env
```

### Edit Configuration
```bash
nano .env
# Make changes and save (Ctrl+O, Ctrl+X)
```

### Reload Configuration
```bash
# Services read .env at startup, so restart them
systemctl --user restart portal.service admin-portal.service
```

## Database & Logs

### View Logs Directory
```bash
ls -la logs/

# File sizes
du -h logs/*
```

### Clear Old Logs (if needed)
```bash
# Archive and compress
tar -czf logs_backup_$(date +%Y%m%d).tar.gz logs/

# Or delete old logs
find logs/ -name "*.log" -mtime +30 -delete
```

### Database Operations
```bash
# View database
ls -la logs/attendance_logs.db

# Database size
du -h logs/attendance_logs.db

# Query database (sqlite3 must be installed)
sqlite3 logs/attendance_logs.db ".tables"
```

## Troubleshooting

### Service Won't Start
```bash
# Check error
journalctl --user -xe

# Check Python syntax
python -m py_compile portal.py

# Check if port is already in use
netstat -tlnp | grep 5001
netstat -tlnp | grep 5002

# Kill process on port (if needed)
fuser -k 5001/tcp
fuser -k 5002/tcp
```

### High Memory/CPU Usage
```bash
# Check which process uses most resources
ps aux --sort=-%cpu,-%mem | grep python

# View detailed process info
ps -ef | grep portal
```

### GitHub Actions Deployment Fails
```bash
# Check SSH connectivity
ssh -v user@192.168.8.250

# Verify SSH key permissions
ls -la ~/.ssh/github_deploy
# Should be 600

# Check if key is in authorized_keys
grep "github_deploy" ~/.ssh/authorized_keys

# View recent deploys in GitHub
# Go to repository → Actions → Deploy to Host A
```

### Cloudflare Tunnel Issues
```bash
# Check tunnel status
cloudflared tunnel info bt-attendance

# View tunnel logs
journalctl -u cloudflared -f

# Test local service
curl http://localhost:5001
curl http://localhost:5002
```

### ngrok Issues
```bash
# Check active tunnels
ngrok api tunnels list

# View ngrok logs
tail -f ~/.ngrok2/ngrok.log

# Restart ngrok
# Kill and restart the ngrok process
pkill ngrok
ngrok start --all
```

## Useful One-Liners

```bash
# Restart all services
systemctl --user restart portal.service admin-portal.service

# Show service uptime
systemctl --user show -p ActiveEnterTimestamp portal.service

# Monitor CPU/Memory in real-time
watch -n 1 'ps aux | grep "[p]ython"'

# Count HTTP requests in portal logs
grep -c "GET\|POST" logs/portal.log

# Find errors in all logs
grep -r "ERROR\|EXCEPTION" logs/

# Backup entire project
tar -czf bt_attendance_backup_$(date +%Y%m%d_%H%M%S).tar.gz ~/bt_attendance

# Show last deployment time
stat deploy.log | grep Modify

# List all systemd timers
systemctl --user list-timers --all
```

## Performance Tips

1. **Monitor Logs Regularly**
   ```bash
   journalctl --user -f
   ```

2. **Archive Old Logs**
   ```bash
   find logs/ -name "*.log" -mtime +7 -exec gzip {} \;
   ```

3. **Reload Services After Config Changes**
   ```bash
   systemctl --user daemon-reload
   systemctl --user restart portal.service admin-portal.service
   ```

4. **Check Resource Usage**
   ```bash
   free -h  # Memory
   df -h    # Disk
   top      # CPU & Memory
   ```

## Emergency Commands

### Force Kill Process
```bash
pkill -9 -f "portal.py"
pkill -9 -f "admin_portal.py"
```

### Reset Services
```bash
systemctl --user reset-failed
systemctl --user daemon-reload
```

### Clear Temporary Files
```bash
rm -rf __pycache__
find . -type d -name ".pytest_cache" -exec rm -r {} +
```

## Support

For issues or detailed documentation, see:
- Main guide: `docs/DEPLOYMENT.md`
- GitHub: https://github.com/khalilksa33/bt_attendance
- Issues: https://github.com/khalilksa33/bt_attendance/issues
