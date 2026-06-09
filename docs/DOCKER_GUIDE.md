# BT Attendance - Docker Deployment Guide

This guide covers Docker-based deployment for the BT Attendance system.

## Overview

Docker containerization provides:
- ✅ Consistent environment across development and production
- ✅ Easy scaling and service management
- ✅ Automatic container restarts on failure
- ✅ Simplified dependency management
- ✅ Fast deployments via Docker Hub
- ✅ Improved security with non-root user execution

## Architecture

```
GitHub Repository
    ↓ (git push to main)
GitHub Actions
    ├─ Build Docker image
    ├─ Push to Docker Hub (khalilksa33/bt_attendance)
    ├─ Run syntax checks
    └─ Deploy to Host A
        ↓
Host A Docker Environment
├─ Portal Container (5001)
├─ Admin Portal Container (5002)
└─ Attendance Bot Container (scheduled)
```

## Quick Start - Docker Deployment on Host A

### Prerequisites
- Docker installed on Host A
- docker-compose installed
- Git access to repository
- Docker Hub credentials (optional for pulling public images)

### 1. Setup Host A with Docker

```bash
# SSH into Host A
ssh user@192.168.8.250

# Clone repository
cd ~
git clone https://github.com/khalilksa33/bt_attendance.git
cd bt_attendance

# Copy environment template
cp .env.example .env

# Edit configuration
nano .env
# Fill in: ERP_URL, EMAIL settings, BIOMETRIC_IP, etc.
```

### 2. Start Services with Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Check container status
docker-compose ps

# Stop services
docker-compose down
```

### 3. Verify Services

```bash
# Portal
curl http://localhost:5001

# Admin Portal
curl http://localhost:5002
```

## GitHub Actions CI/CD with Docker

### Setup GitHub Secrets

Go to: **GitHub → Repository → Settings → Secrets and variables → Actions**

Add these secrets:

```
# Docker Hub credentials
DOCKERHUB_USERNAME = khalilksa33
DOCKERHUB_TOKEN = your-docker-hub-token

# Host A credentials (SSH deployment)
HOST_A_IP = 192.168.8.250
HOST_A_USER = your-username
HOST_A_SSH_KEY = your-private-ssh-key
```

**Note:** Get Docker Hub token from https://hub.docker.com/settings/security

### How CI/CD Works

1. **Push to main branch**
   ```bash
   git push origin main
   ```

2. **GitHub Actions automatically:**
   - Builds Docker image
   - Pushes to Docker Hub (khalilksa33/bt_attendance:latest)
   - Runs syntax checks
   - Deploys to Host A via SSH
   - Starts docker-compose containers

3. **Verify Deployment**
   - Check GitHub Actions tab
   - View container logs: `docker-compose logs`
   - Test: `curl http://192.168.8.250:5001`

## Building Docker Image Locally

### Build Image

```bash
# Build image with tag
docker build -t khalilksa33/bt_attendance:latest .

# Build specific version
docker build -t khalilksa33/bt_attendance:v1.0.0 .

# Build with build args
docker build --build-arg PYTHON_VERSION=3.9 -t khalilksa33/bt_attendance:latest .
```

### Push to Docker Hub

```bash
# Login to Docker Hub
docker login

# Push image
docker push khalilksa33/bt_attendance:latest

# Push specific version
docker push khalilksa33/bt_attendance:v1.0.0
```

### Run Individual Containers

```bash
# Portal service
docker run -d \
  -p 5001:5001 \
  --name bt-portal \
  --env-file .env \
  -v $(pwd)/logs:/app/logs \
  khalilksa33/bt_attendance:latest \
  python portal.py

# Admin Portal
docker run -d \
  -p 5002:5002 \
  --name bt-admin \
  --env-file .env \
  -v $(pwd)/logs:/app/logs \
  khalilksa33/bt_attendance:latest \
  python admin_portal.py

# View logs
docker logs -f bt-portal
docker logs -f bt-admin

# Stop containers
docker stop bt-portal bt-admin
docker rm bt-portal bt-admin
```

## Docker Compose Reference

### File: docker-compose.yml

Defines three services:
- **portal** - Remote check-in (port 5001)
- **admin-portal** - Admin dashboard (port 5002)
- **attendance-bot** - Report generator (on-demand)

### Common Commands

```bash
# Start all services
docker-compose up -d

# Start specific service
docker-compose up -d portal admin-portal

# View running containers
docker-compose ps

# View logs
docker-compose logs              # All logs
docker-compose logs portal       # Specific service
docker-compose logs -f           # Follow/tail logs

# Execute command in container
docker-compose exec portal sh
docker-compose exec admin-portal sh

# Stop services
docker-compose stop

# Stop and remove containers
docker-compose down

# Remove volumes (includes logs)
docker-compose down -v

# Rebuild images
docker-compose build

# Rebuild and restart
docker-compose up -d --build

# Check service health
docker-compose ps
docker stats
```

## Environment Variables

Create `.env` file in project root:

```bash
# Portal Configuration
PORT=5001
PORTAL_ACCESS_CODE=optional-code

# Admin Portal Configuration
ADMIN_PORTAL_PORT=5002
ADMIN_PORTAL_USERNAME=admin
ADMIN_PORTAL_PASSWORD=SecurePassword123!

# ERP Configuration
ERP_URL=https://your-erp-server.com
ERP_API_KEY=your-api-key
ERP_API_SECRET=your-secret

# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_USER=your@company.com
EMAIL_PASS=your-app-password
RECIPIENT_EMAIL=manager@company.com

# Biometric Device
BIOMETRIC_IP=192.168.8.4
BIOMETRIC_PORT=4370

# Other Settings
OUTPUT_DIR=reports
LOGO_PATH=reports/images/iicc_final_logo.jpeg
```

## Docker Image Versions

Available on Docker Hub: https://hub.docker.com/r/khalilksa33/bt_attendance

### Tags

- `latest` - Most recent build
- `{commit-hash}` - Specific commit version
- `{timestamp}` - Build timestamp version
- `stable` - Stable release (if tagged)
- `v1.0.0` - Semantic versioning (when available)

### Pull Image

```bash
# Latest
docker pull khalilksa33/bt_attendance:latest

# Specific version
docker pull khalilksa33/bt_attendance:v1.0.0

# Specific commit
docker pull khalilksa33/bt_attendance:abc1234
```

## Managing Containers

### View Container Logs

```bash
# Docker Compose
docker-compose logs -f portal

# Direct Docker
docker logs -f container-id

# Last N lines
docker logs --tail 50 container-id

# Follow and timestamps
docker logs -f --timestamps container-id
```

### Container Health Check

```bash
# Check container health
docker-compose ps

# Manual health test
docker-compose exec portal curl http://localhost:5001

# Check Docker stats
docker stats
```

### Restart Containers

```bash
# Restart specific service
docker-compose restart portal

# Restart all services
docker-compose restart

# Hard stop and restart
docker-compose down
docker-compose up -d
```

## Database & Logs in Docker

### Access Logs Directory

```bash
# Inside container
docker-compose exec portal ls /app/logs

# From host (with volumes mounted)
ls logs/

# View log file
docker-compose exec portal tail -f /app/logs/portal.log
```

### Backup Database & Logs

```bash
# Backup volumes
docker-compose exec portal tar -czf /tmp/backup.tar.gz /app/logs

# Copy from container to host
docker cp container-id:/app/logs/attendance_logs.db ./backup/

# Or with compose
docker-compose exec portal sh -c 'tar -czf - /app/logs' > logs_backup.tar.gz
```

## Troubleshooting

### Containers Won't Start

```bash
# View error logs
docker-compose logs

# Check image exists
docker images | grep bt_attendance

# Try rebuilding
docker-compose build --no-cache
docker-compose up -d

# Check .env file
ls -la .env
cat .env
```

### Port Already in Use

```bash
# Find what's using port 5001
lsof -i :5001
netstat -tlnp | grep 5001

# Kill process
kill -9 $(lsof -t -i :5001)

# Or use different port in .env
PORT=5011
```

### Docker Hub Authentication Failed

```bash
# Login to Docker Hub
docker login

# Or use Docker access token
cat ~/token.txt | docker login -u khalilksa33 --password-stdin
```

### Out of Disk Space

```bash
# Check disk usage
docker system df

# Clean up unused images/containers
docker system prune

# Remove all unused data (careful!)
docker system prune -a
```

### Container Keeps Restarting

```bash
# View restart count
docker-compose ps

# Check logs for errors
docker-compose logs portal

# Inspect container
docker inspect container-id | grep -A 20 "State"
```

## Performance Optimization

### Resource Limits

Edit `docker-compose.yml`:

```yaml
services:
  portal:
    # ... other config ...
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 256M
```

### Volume Performance

```yaml
services:
  portal:
    volumes:
      - ./logs:/app/logs:cached        # Better performance
      - ./reports:/app/reports:cached
```

## Advanced: Custom Entrypoint

Create `docker-entrypoint.sh`:

```bash
#!/bin/bash
set -e

echo "Starting BT Attendance..."

# Wait for dependencies
sleep 2

# Execute command
exec "$@"
```

Update Dockerfile:

```dockerfile
COPY docker-entrypoint.sh /app/
RUN chmod +x /app/docker-entrypoint.sh
ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["python", "portal.py"]
```

## Security Best Practices

1. **Use specific image versions** (not just `latest`)
   ```yaml
   image: khalilksa33/bt_attendance:v1.0.0
   ```

2. **Non-root user** (already configured in Dockerfile)
   ```dockerfile
   USER appuser
   ```

3. **Secrets management**
   - Use Docker Secrets for production
   - Never commit `.env` to git
   - Use separate `.env.production`

4. **Network isolation**
   - Use custom networks
   - Don't expose unnecessary ports

5. **Regular image updates**
   ```bash
   docker pull khalilksa33/bt_attendance:latest
   docker-compose up -d
   ```

## Monitoring

### Container Monitoring

```bash
# Real-time stats
docker stats

# With compose
docker-compose stats

# Check health
docker-compose ps
```

### Log Aggregation

```bash
# Centralized logging
docker-compose logs --follow > all_logs.txt

# Per-service
docker-compose logs portal > portal_logs.txt
```

## Integration with Kubernetes (Optional)

For production at scale, consider Kubernetes deployment. Generate K8s manifests:

```bash
# Convert docker-compose to K8s
kompose convert -f docker-compose.yml
```

## Support & Resources

- Docker Docs: https://docs.docker.com
- Docker Hub Repository: https://hub.docker.com/r/khalilksa33/bt_attendance
- docker-compose Reference: https://docs.docker.com/compose/compose-file/
- GitHub Actions: https://docs.github.com/en/actions

## Next Steps

1. **Install Docker on Host A**: `curl https://get.docker.com | sh`
2. **Clone repository** and configure `.env`
3. **Start with docker-compose**: `docker-compose up -d`
4. **Test services**: Visit `http://192.168.8.250:5001`
5. **Setup internet access**: Use Cloudflare Tunnel or ngrok (see DEPLOYMENT.md)
6. **Enable CI/CD**: Add GitHub Secrets for automated deployments

---

**Version**: 1.0  
**Last Updated**: 2026-06-09  
**Docker Hub**: https://hub.docker.com/r/khalilksa33/bt_attendance  
**Repository**: https://github.com/khalilksa33/bt_attendance
