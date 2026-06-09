# BT Attendance - CI/CD Deployment Guide

## Overview

This guide sets up automated CI/CD deployment for the BT Attendance system on Host A (192.168.8.250) with support for both local network (LAN) and internet access.

**Architecture:**
- GitHub Actions: Runs tests and triggers deployment on git push
- SSH Deployment: Securely deploys code to Host A (192.168.8.250)
- Systemd Services: Manages application lifecycle
- Cloudflare Tunnel/ngrok: Provides HTTPS access from internet

## Prerequisites

- Host A (192.168.8.250) with Linux (Ubuntu 20.04+)
- GitHub account with repository access
- Cloudflare account OR ngrok account for internet access
- SSH access to Host A

## Step 1: Set Up SSH Keys on Host A

### 1.1 Generate SSH Key Pair (if not exists)

```bash
# On Host A
ssh-keygen -t rsa -b 4096 -f ~/.ssh/github_deploy -C "github-deployment"
```

### 1.2 Display Private Key for GitHub Secrets

```bash
cat ~/.ssh/github_deploy
```

Keep this key safe - you'll paste it into GitHub Secrets.

### 1.3 Add Public Key to Authorized Keys

```bash
cat ~/.ssh/github_deploy.pub >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

## Step 2: Configure GitHub Secrets

Go to GitHub repository → Settings → Secrets and Variables → Actions

Add these secrets:

| Secret Name | Value |
|-------------|-------|
| `HOST_A_IP` | `192.168.8.250` |
| `HOST_A_USER` | Your username (e.g., `khalil`) |
| `HOST_A_SSH_KEY` | Private key from Step 1.2 |

**Example:**
```
HOST_A_IP = 192.168.8.250
HOST_A_USER = khalil
HOST_A_SSH_KEY = -----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA...
-----END RSA PRIVATE KEY-----
```

## Step 3: Setup Host A

### 3.1 Clone Repository

```bash
cd ~
git clone https://github.com/khalilksa33/bt_attendance.git
cd bt_attendance
```

### 3.2 Install Python & Dependencies

```bash
# Update system
sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-pip git

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

### 3.3 Create Logs Directory

```bash
mkdir -p logs
chmod 755 logs
```

### 3.4 Copy Environment File

```bash
# Create .env from template
cp .env.example .env
# Edit with your configuration
nano .env
```

### 3.5 Install Systemd Services (User-Level)

```bash
# Create user systemd directory
mkdir -p ~/.config/systemd/user

# Copy service files
cp systemd/*.service ~/.config/systemd/user/
cp systemd/*.timer ~/.config/systemd/user/

# Reload systemd
systemctl --user daemon-reload

# Enable and start services
systemctl --user enable portal.service
systemctl --user enable admin-portal.service
systemctl --user enable attendance-bot.timer

systemctl --user start portal.service
systemctl --user start admin-portal.service
systemctl --user start attendance-bot.timer

# Verify services are running
systemctl --user status portal.service
systemctl --user status admin-portal.service
systemctl --user status attendance-bot.timer
```

### 3.6 View Logs

```bash
# Portal logs
tail -f logs/portal.log

# Admin portal logs
tail -f logs/admin_portal.log

# Bot logs
tail -f logs/bot.log
```

## Step 4: Set Up Internet Access with Cloudflare Tunnel

### 4.1 Install Cloudflare Tunnel

```bash
# Download cloudflared
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared-linux-amd64.deb
rm cloudflared-linux-amd64.deb
```

### 4.2 Authenticate with Cloudflare

```bash
cloudflared tunnel login
# This opens a browser to authenticate with your Cloudflare account
```

### 4.3 Create Tunnel Configuration

```bash
# Create config directory
mkdir -p ~/.cloudflared

# Create tunnel config file
cat > ~/.cloudflared/config.yml << 'EOF'
tunnel: bt-attendance
credentials-file: /home/USERNAME/.cloudflared/TUNNEL_ID.json

ingress:
  - hostname: portal.yourdomain.com
    service: http://localhost:5001
  - hostname: admin.yourdomain.com
    service: http://localhost:5002
  - service: http_status:404

# Cloudflare account details
originRequest:
  http2Origin: false
EOF
```

Replace `USERNAME` and `yourdomain.com` with your values.

### 4.4 Run Cloudflare Tunnel

```bash
# Test tunnel
cloudflared tunnel run bt-attendance

# Or run as systemd service
sudo cloudflared service install
sudo systemctl start cloudflared
sudo systemctl enable cloudflared
```

### 4.5 Create DNS Records in Cloudflare

In Cloudflare Dashboard:
1. Add CNAME records pointing to your tunnel:
   - `portal.yourdomain.com` → tunnel ID
   - `admin.yourdomain.com` → tunnel ID

## Step 5: Alternative - Set Up Internet Access with ngrok

### 5.1 Install ngrok

```bash
# Download and install
wget https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.zip
unzip ngrok-v3-stable-linux-amd64.zip
sudo mv ngrok /usr/local/bin/
rm ngrok-v3-stable-linux-amd64.zip
```

### 5.2 Authenticate ngrok

```bash
# Get auth token from https://dashboard.ngrok.com/auth/your-authtoken
ngrok config add-authtoken YOUR_AUTH_TOKEN
```

### 5.3 Start ngrok Tunnel

```bash
# Expose portal (5001) and admin portal (5002)
ngrok start --all

# Or create ngrok.yml config:
cat > ~/.ngrok2/ngrok.yml << 'EOF'
version: "2"
authtoken: YOUR_AUTH_TOKEN

tunnels:
  portal:
    proto: http
    addr: localhost:5001
    domain: your-subdomain.ngrok.io
  admin:
    proto: http
    addr: localhost:5002
    domain: your-admin-subdomain.ngrok.io
EOF

# Then run:
ngrok start --all
```

## Step 6: Verify Deployment

### 6.1 Check Services Locally

```bash
# Portal
curl http://localhost:5001/

# Admin Portal
curl http://localhost:5002/

# Check logs
journalctl --user-unit=portal.service -f
journalctl --user-unit=admin-portal.service -f
```

### 6.2 Check Internet Access

```bash
# Get your Cloudflare Tunnel URL
cloudflared tunnel info bt-attendance

# Or ngrok URL
ngrok api tunnels list
```

Then visit:
- `https://portal.yourdomain.com` (Cloudflare) or ngrok URL
- `https://admin.yourdomain.com` (Cloudflare) or ngrok URL

## Step 7: Automated Deployment Workflow

### How It Works

1. **Push to main branch:**
   ```bash
   git push origin main
   ```

2. **GitHub Actions automatically:**
   - Runs syntax checks
   - Connects to Host A via SSH
   - Pulls latest code
   - Installs dependencies
   - Restarts services

3. **Monitor deployment:**
   - Check GitHub Actions tab in repository
   - View deploy logs in `/home/user/bt_attendance/deploy.log` on Host A

### Manual Deployment (if needed)

```bash
# SSH into Host A
ssh user@192.168.8.250

# Run deploy script manually
cd ~/bt_attendance
bash scripts/deploy.sh
```

## Step 8: Configure Daily Reports

The attendance bot runs automatically at 9:30 AM via systemd timer.

### Manual Test Run

```bash
# Test report generation
cd ~/bt_attendance
source .venv/bin/activate
python daily_checkin_log.py --date 2026-06-09
```

### Check Scheduled Runs

```bash
# View timer status
systemctl --user status attendance-bot.timer

# View timer logs
journalctl --user-unit=attendance-bot.timer -f

# View next scheduled run
systemctl --user list-timers --all
```

## Troubleshooting

### Services Not Starting

```bash
# Check systemd errors
systemctl --user status portal.service
journalctl --user -xe

# Verify Python path
which python
python --version
```

### SSH Deployment Fails

```bash
# Test SSH connection
ssh -i ~/.ssh/github_deploy user@192.168.8.250 "echo 'SSH works!'"

# Check GitHub secret values in Actions
# Settings → Secrets and Variables → Actions → Review values
```

### Cloudflare Tunnel Not Working

```bash
# Check tunnel status
cloudflared tunnel info bt-attendance

# Test local services
curl http://localhost:5001
curl http://localhost:5002

# Restart cloudflared
systemctl restart cloudflared
```

### ngrok Issues

```bash
# Check auth token
ngrok config check

# View active tunnels
ngrok api tunnels list

# Check ngrok logs
tail -f ~/.ngrok2/ngrok.log
```

## Monitoring

### View Real-Time Logs

```bash
# Portal service
journalctl --user-unit=portal.service -f

# Admin portal
journalctl --user-unit=admin-portal.service -f

# All logs
journalctl --user -f
```

### Service Health Check Script

```bash
#!/bin/bash
echo "=== BT Attendance Health Check ==="
echo -n "Portal: "
systemctl --user is-active portal.service && echo "✅ Running" || echo "❌ Stopped"

echo -n "Admin Portal: "
systemctl --user is-active admin-portal.service && echo "✅ Running" || echo "❌ Stopped"

echo -n "Report Bot Timer: "
systemctl --user is-active attendance-bot.timer && echo "✅ Active" || echo "❌ Inactive"

echo ""
echo "Port status:"
netstat -tlnp | grep -E ':5001|:5002' || echo "Services not listening"
```

## Security Recommendations

1. **Rotate SSH Keys Periodically**
   ```bash
   ssh-keygen -p -f ~/.ssh/github_deploy
   ```

2. **Restrict SSH Access**
   ```bash
   # Edit ~/.ssh/authorized_keys and add IP restrictions
   # from="192.168.8.0/24,YOUR.GITHUB.IP" ssh-rsa ...
   ```

3. **Use Environment Variables Securely**
   - Store sensitive data in `.env` (not in git)
   - Use `.env.example` for template only

4. **Enable Firewall Rules**
   ```bash
   sudo ufw allow 5001  # Portal
   sudo ufw allow 5002  # Admin portal
   sudo ufw allow 22    # SSH
   ```

5. **HTTPS Only**
   - Always use Cloudflare Tunnel or ngrok for internet access
   - Never expose raw HTTP to internet

## Additional Resources

- GitHub Actions: https://docs.github.com/en/actions
- Systemd User Services: https://wiki.archlinux.org/title/Systemd/User
- Cloudflare Tunnel: https://developers.cloudflare.com/cloudflare-one/connections/connect-applications/
- ngrok: https://ngrok.com/docs

## Support

For issues or questions, check:
- GitHub Issues: https://github.com/khalilksa33/bt_attendance/issues
- Service logs: `journalctl --user -f`
- Deployment log: `/home/user/bt_attendance/deploy.log`
