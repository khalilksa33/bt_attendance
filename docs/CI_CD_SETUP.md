# BT Attendance CI/CD Setup

Complete automated deployment pipeline for BT Attendance on Host A (192.168.8.250).

## 📋 Overview

This CI/CD setup provides:

✅ **Automated Deployment** - Deploy on every git push to main  
✅ **LAN Access** - Direct HTTP access from local network (192.168.8.250:5001, 5002)  
✅ **Internet Access** - HTTPS via Cloudflare Tunnel or ngrok  
✅ **Service Management** - Systemd services for automatic startup & restart  
✅ **Scheduled Reports** - Attendance bot runs daily at 9:30 AM via systemd timer  
✅ **Monitoring** - Health checks and real-time logs  

## 🏗️ Architecture

```
GitHub Repository
    ↓ (git push to main)
GitHub Actions
    ├─ Run syntax checks
    ├─ SSH into Host A (192.168.8.250)
    ├─ Pull latest code
    ├─ Install dependencies
    └─ Restart services
        ↓
Host A Services
├─ Portal (Port 5001) - Remote check-in
├─ Admin Portal (Port 5002) - Admin dashboard
└─ Attendance Bot - Daily report generation (9:30 AM)
    ↓
Internet Access
├─ Cloudflare Tunnel (Recommended)
└─ ngrok (Alternative)
```

## 🚀 Quick Start (5 Minutes)

### On Host A (192.168.8.250):

```bash
# 1. Download and run setup script
cd ~
git clone https://github.com/khalilksa33/bt_attendance.git
cd bt_attendance
bash scripts/setup-host-a.sh

# 2. Configure your environment
nano .env
# Fill in: ERP_URL, EMAIL settings, BIOMETRIC_IP, etc.

# 3. Start services
systemctl --user start portal.service
systemctl --user start admin-portal.service
systemctl --user start attendance-bot.timer

# 4. Verify services are running
bash scripts/health-check.sh
```

### On GitHub:

```bash
# 1. Add SSH secrets (Settings → Secrets and variables → Actions)
HOST_A_IP = 192.168.8.250
HOST_A_USER = your-username
HOST_A_SSH_KEY = (paste your private SSH key)

# 2. Push to main and watch deployment
git push origin main
# Check GitHub Actions tab for deployment status
```

## 📖 Full Setup Guide

For detailed step-by-step instructions, see [DEPLOYMENT.md](DEPLOYMENT.md)

### Key Sections:
- **Step 1**: SSH Key Setup for GitHub
- **Step 2**: Configure GitHub Secrets
- **Step 3**: Setup Host A (Python, venv, services)
- **Step 4**: Cloudflare Tunnel for HTTPS (LAN + Internet)
- **Step 5**: ngrok Alternative (Simple HTTPS tunnel)
- **Step 6**: Verify Deployment
- **Step 7**: Automated CI/CD Workflow
- **Step 8**: Configure Daily Reports

## 📦 What's Included

```
.github/workflows/
├─ deploy.yml                    # GitHub Actions CI/CD workflow

scripts/
├─ setup-host-a.sh              # One-command setup for Host A
├─ deploy.sh                     # Manual deployment script
└─ health-check.sh              # Service status monitoring

systemd/
├─ portal.service               # Remote check-in service
├─ admin-portal.service         # Admin dashboard service
├─ attendance-bot.service       # Report generator
└─ attendance-bot.timer         # Daily scheduling (9:30 AM)

docs/
├─ DEPLOYMENT.md                # Full deployment guide
├─ QUICK_REFERENCE.md           # Common commands & troubleshooting
└─ CI_CD_SETUP.md               # This file

.env.example                     # Configuration template
requirements.txt                 # Python dependencies
```

## 🔌 Services Overview

### Portal (Port 5001)
- **Purpose**: Remote field check-in
- **URL (LAN)**: http://192.168.8.250:5001
- **URL (Internet)**: https://portal.yourdomain.com (via Cloudflare/ngrok)
- **File**: `portal.py`
- **Features**: ERP authentication, secure check-in submission

### Admin Portal (Port 5002)
- **Purpose**: Admin dashboard & reports
- **URL (LAN)**: http://192.168.8.250:5002
- **URL (Internet)**: https://admin.yourdomain.com (via Cloudflare/ngrok)
- **File**: `admin_portal.py`
- **Features**: Settings, upload logs, view statistics

### Attendance Bot (Daily)
- **Purpose**: Generate daily attendance reports
- **Schedule**: 9:30 AM every day (systemd timer)
- **File**: `daily_checkin_log.py`
- **Output**: Email with attendance log & PDF report
- **Features**: ERP, biometric, and remote check-in data consolidation

## ⚙️ Configuration

### Environment Variables (.env)

```bash
# Portal
PORT=5001
PORTAL_ACCESS_CODE=optional-code

# Admin Portal
ADMIN_PORTAL_PORT=5002
ADMIN_PORTAL_USERNAME=admin
ADMIN_PORTAL_PASSWORD=SecurePassword123!

# ERP Connection
ERP_URL=https://your-erp.com
ERP_API_KEY=your-key
ERP_API_SECRET=your-secret

# Email (for reports)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_USER=your@company.com
EMAIL_PASS=your-app-password
RECIPIENT_EMAIL=manager@company.com

# Biometric Device
BIOMETRIC_IP=192.168.8.4
BIOMETRIC_PORT=4370
```

Copy from template: `cp .env.example .env`

## 🌐 Internet Access Options

### Option 1: Cloudflare Tunnel (Recommended)
- ✅ Professional, reliable, fast
- ✅ Custom domain support (portal.yourdomain.com)
- ✅ DDoS protection
- Requires Cloudflare account
- Steps: See [DEPLOYMENT.md Section 4](DEPLOYMENT.md#step-4-set-up-internet-access-with-cloudflare-tunnel)

### Option 2: ngrok
- ✅ Simple, quick setup (2 minutes)
- ✅ Works without custom domain
- Auto-generated URLs (https://abc123.ngrok.io)
- Steps: See [DEPLOYMENT.md Section 5](DEPLOYMENT.md#step-5-alternative---set-up-internet-access-with-ngrok)

## 📊 Monitoring & Logs

### Health Check
```bash
bash scripts/health-check.sh
```

Shows:
- Service status (running/stopped)
- Port listening status
- Disk usage
- Recent errors
- Last activity timestamps

### View Logs
```bash
# Portal logs (real-time)
journalctl --user-unit=portal.service -f

# Admin portal logs (real-time)
journalctl --user-unit=admin-portal.service -f

# Last 50 lines of portal logs
journalctl --user-unit=portal.service -n 50

# Logs from today
journalctl --user-unit=portal.service --since today
```

### Service Status
```bash
# Check all services
systemctl --user status

# Specific service
systemctl --user status portal.service

# Timer status
systemctl --user status attendance-bot.timer

# Next scheduled run
systemctl --user list-timers --all
```

## 🔄 Automated Deployment Workflow

### Trigger Deployment
```bash
# Make changes and push to main
git add .
git commit -m "Update feature"
git push origin main
```

### What Happens Automatically:
1. GitHub Actions checks out code
2. Runs Python syntax checks
3. Connects to Host A via SSH
4. Pulls latest code
5. Installs/updates dependencies
6. Restarts services
7. Notifies on success/failure

### Monitor Deployment:
- Open GitHub → Repository → Actions tab
- Click "Deploy to Host A" workflow
- Watch real-time deployment progress
- Check logs if deployment fails

## 🆘 Troubleshooting

### Services Won't Start
```bash
# Check for errors
journalctl --user -xe

# Verify syntax
python -m py_compile portal.py

# Check if port is in use
netstat -tlnp | grep 5001
```

### SSH Deployment Fails
```bash
# Test SSH connection
ssh -i ~/.ssh/github_deploy user@192.168.8.250

# Verify secrets in GitHub
Settings → Secrets and variables → Actions
# Check HOST_A_IP, HOST_A_USER, HOST_A_SSH_KEY
```

### Internet Access Not Working
```bash
# Test local services first
curl http://localhost:5001
curl http://localhost:5002

# Check Cloudflare Tunnel / ngrok
cloudflared tunnel info bt-attendance
# or
ngrok api tunnels list
```

For more help, see [QUICK_REFERENCE.md](QUICK_REFERENCE.md#troubleshooting)

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| [DEPLOYMENT.md](DEPLOYMENT.md) | Complete step-by-step setup guide |
| [QUICK_REFERENCE.md](QUICK_REFERENCE.md) | Common commands & troubleshooting |
| [This File](CI_CD_SETUP.md) | CI/CD overview & quick start |

## 🔐 Security Best Practices

1. **SSH Keys**
   - Store private keys securely
   - Rotate keys periodically
   - Never commit keys to git

2. **Environment Variables**
   - Never commit `.env` to git
   - Use `.env.example` for template
   - Store secrets in GitHub Secrets

3. **Firewall Rules**
   ```bash
   sudo ufw allow 5001   # Portal
   sudo ufw allow 5002   # Admin portal
   sudo ufw allow 22     # SSH (restrict if possible)
   ```

4. **HTTPS Only**
   - Always use Cloudflare Tunnel or ngrok for internet
   - Never expose raw HTTP to internet

5. **Access Control**
   - Restrict GitHub Actions IP if possible
   - Use strong admin portal passwords
   - Enable portal access code

## 🎯 Common Tasks

### Restart Services After Config Change
```bash
# Edit .env
nano .env

# Restart services to apply changes
systemctl --user restart portal.service admin-portal.service
```

### View Real-Time Logs
```bash
# All services
journalctl --user -f

# Specific service
journalctl --user-unit=portal.service -f
```

### Manual Deployment
```bash
bash scripts/deploy.sh
```

### Generate Report Manually
```bash
source .venv/bin/activate
python daily_checkin_log.py --date 2026-06-09
```

### Check Deployment Status
```bash
# On Host A
cat deploy.log

# In GitHub Actions
# Open repository → Actions → Deploy to Host A
```

## 📞 Support & Resources

- **GitHub Issues**: https://github.com/khalilksa33/bt_attendance/issues
- **Deployment Docs**: [DEPLOYMENT.md](DEPLOYMENT.md)
- **Quick Commands**: [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
- **Python Help**: `python -h` or `python daily_checkin_log.py --help`

## ✅ Verification Checklist

After setup, verify:

- [ ] Host A can be accessed via SSH
- [ ] Portal loads at http://192.168.8.250:5001 (LAN)
- [ ] Admin portal loads at http://192.168.8.250:5002 (LAN)
- [ ] GitHub Actions deployment succeeds
- [ ] Services restart automatically after reboot
- [ ] Daily report email arrives at 9:30 AM
- [ ] Internet access works (Cloudflare/ngrok)

## 📈 Next Steps

1. **Complete full setup**: Follow [DEPLOYMENT.md](DEPLOYMENT.md)
2. **Configure services**: Edit `.env` with your details
3. **Set up internet access**: Choose Cloudflare or ngrok
4. **Monitor deployment**: Watch GitHub Actions and logs
5. **Test manually**: Visit http://192.168.8.250:5001 and 5002

---

**Version**: 1.0  
**Last Updated**: 2026-06-09  
**Repository**: https://github.com/khalilksa33/bt_attendance
