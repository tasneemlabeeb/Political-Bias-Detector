# Deployment Guide

Complete guide for deploying the Political Bias Detector application.

## Quick Start (Production)

### Using Ploi (Recommended)

```bash
# 1. Connect your GitHub repo to Ploi
# 2. Set environment variables in Ploi dashboard:
SECRET_KEY=<generate with: openssl rand -hex 32>
DB_PASSWORD=<secure-password-16+ chars>
GEMINI_API_KEY=<your-api-key>
NEWS_API_KEY=<your-api-key>
SERPER_API_KEY=<your-api-key>

# 3. Push to main branch - Ploi auto-deploys
git push origin main
```

See [PLOI_SETUP.md](#ploi-setup) for detailed instructions.

---

## Local Development Deployment

### Prerequisites
```bash
docker --version  # Docker 20+
docker compose version  # or docker-compose
python --version  # Python 3.11+
```

### Deploy Locally

```bash
# Build and start all services
docker-compose -f docker-compose.yml up -d

# Check status
docker-compose -f docker-compose.yml ps

# View logs
docker-compose -f docker-compose.yml logs -f
```

Services available:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

---

## Production Deployment

### Server Requirements
- **OS**: Ubuntu 20.04+ or similar Linux
- **CPU**: 2+ cores
- **RAM**: 4GB+ (8GB recommended)
- **Disk**: 20GB+ free
- **Ports**: 80, 443 available

### Manual Deploy (Non-Ploi)

#### 1. Setup Server

```bash
# SSH into server
ssh user@your-server

# Install Docker
sudo apt-get update
sudo apt-get install -y docker.io docker-compose
sudo usermod -aG docker $USER
newgrp docker

# Verify installation
docker --version
docker-compose --version
```

#### 2. Clone Project

```bash
git clone https://github.com/tasneemlabeeb/Political-Bias-Detector.git /opt/political-bias-detector
cd /opt/political-bias-detector

# Or upload via SCP:
# scp -r ./Political-Bias-Detector user@server:/opt/
```

#### 3. Configure Environment

```bash
cp .env.production .env.production.local

# Edit with your credentials
nano .env.production.local

# Required variables:
# DATABASE_URL=postgresql://pbd_user:PASSWORD@postgres:5432/political_bias_detector
# GEMINI_API_KEY=your-key
# NEWS_API_KEY=your-key
# SERPER_API_KEY=your-key
# SECRET_KEY=generated-secret
```

#### 4. Deploy

```bash
# Build images
docker-compose -f docker-compose.production.yml build --pull

# Start services
docker-compose -f docker-compose.production.yml up -d

# Verify
docker-compose -f docker-compose.production.yml ps

# Check health
curl http://localhost/health
```

#### 5. Post-Deploy Verification

```bash
# Check all services running
docker-compose -f docker-compose.production.yml ps

# View logs
docker-compose -f docker-compose.production.yml logs --tail 50

# Test endpoints
curl http://localhost/
curl http://localhost/api/health
curl http://localhost/api/docs
```

---

## Ploi Setup

### 1. Create Ploi Account & Site

1. Go to https://ploi.io
2. Create account or login
3. Add new site
4. Connect GitHub repository

### 2. Configure Environment Variables

In Ploi Dashboard → **Environment Variables**, set:

```
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=openssl rand -hex 32
DATABASE_URL=postgresql://pbd_user:${DB_PASSWORD}@postgres:5432/political_bias_detector
DB_USER=pbd_user
DB_PASSWORD=your-secure-password
DB_NAME=political_bias_detector
GEMINI_API_KEY=your-api-key
NEWS_API_KEY=your-api-key
SERPER_API_KEY=your-api-key
CORS_ORIGINS=http://your-domain,http://localhost
```

### 3. Deploy

Ploi will auto-deploy when you push to `main` branch:

```bash
git push origin main
```

Monitor deployment progress in Ploi Dashboard → **Deployments**.

### 4. Troubleshooting

**Docker Compose not found?**
- The wrapper script handles both `docker compose` and `docker-compose`
- Check Ploi logs: Dashboard → Deployments → View Logs

**Services failing?**
- SSH to server: `ssh your-server`
- Check logs: `docker-compose -f docker-compose.production.yml logs`
- See [Troubleshooting](#troubleshooting) section

---

## Docker Compose Commands

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# Restart all services
docker-compose restart

# View logs (all services)
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f nginx

# Rebuild images
docker-compose build --no-cache

# Execute command in container
docker-compose exec backend sh
docker-compose exec postgres psql -U pbd_user

# Database operations
docker-compose exec postgres pg_dump -U pbd_user political_bias_detector > backup.sql
docker-compose exec postgres psql -U pbd_user < backup.sql

# Clean up everything
docker-compose down -v  # Includes volumes
```

---

## Troubleshooting

### Services won't start

```bash
# Check logs
docker-compose logs

# Check docker daemon
docker ps

# Debug specific service
docker-compose logs backend
docker-compose logs postgres
```

**Solutions:**
- Port in use: `sudo lsof -i :80` → Kill process or change port
- Disk full: `df -h` → Clean up with `docker system prune`
- Out of memory: Increase Docker memory limits

### Database connection failed

```bash
# Check PostgreSQL container
docker-compose ps postgres

# Access psql shell
docker-compose exec postgres psql -U pbd_user

# Check database exists
\l

# Check tables
\dt
```

### Backend returns errors

```bash
# Check backend logs for specific errors
docker-compose logs -f backend --tail 100

# Common issues:
# - Missing API keys: Check .env.production
# - Model not found: mkdir -p models/custom_bias_detector
# - Port conflict: Check docker-compose.production.yml port mappings
```

### API returns 502 Bad Gateway

```bash
# Check if backend is running
docker-compose ps backend

# Check nginx logs
docker-compose logs nginx

# Test backend directly
curl http://backend:8000/health
```

### Frontend not loading

```bash
# Check frontend logs
docker-compose logs -f frontend

# Common issues:
# - npm build failed: Check npm errors in logs
# - API endpoint misconfigured: Check NEXT_PUBLIC_API_URL in docker-compose
# - Port conflict: Check port 3000
```

---

## SSL/TLS Configuration

### Using Let's Encrypt (Recommended)

```bash
# Install Certbot
sudo apt-get install -y certbot python3-certbot-nginx

# Get certificate
sudo certbot certonly --standalone -d your-domain.com

# Copy certificates
sudo mkdir -p nginx/ssl
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem nginx/ssl/cert.pem
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem nginx/ssl/key.pem

# Update nginx/conf.d/default.conf - uncomment HTTPS server block

# Restart nginx
docker-compose restart nginx
```

### Self-Signed Certificate (Testing)

```bash
mkdir -p nginx/ssl
openssl req -x509 -newkey rsa:4096 -nodes \
  -out nginx/ssl/cert.pem -keyout nginx/ssl/key.pem -days 365

# Update nginx config to enable HTTPS
```

---

## Maintenance

### Daily Checks

```bash
# Check service health
docker-compose -f docker-compose.production.yml ps

# Check logs for errors
docker-compose -f docker-compose.production.yml logs --since 1h

# Check disk usage
df -h
docker system df
```

### Backups

```bash
# Database backup
docker-compose -f docker-compose.production.yml exec postgres \
  pg_dump -U pbd_user political_bias_detector > backup-$(date +%Y%m%d).sql

# Backup volumes
tar -czf backup-volumes-$(date +%Y%m%d).tar.gz \
  /var/lib/docker/volumes/postgres_data
```

### Updates

```bash
# Pull latest code
git pull origin main

# Rebuild images
docker-compose -f docker-compose.production.yml build --pull

# Restart services
docker-compose -f docker-compose.production.yml restart
```

### Cleanup

```bash
# Remove unused images
docker image prune -a

# Remove unused volumes
docker volume prune

# Remove all unused data
docker system prune -a --volumes
```

---

## Monitoring & Logging

### Available Logs

```bash
# All services
docker-compose logs

# Follow live logs
docker-compose logs -f

# Last N lines
docker-compose logs --tail 50

# Since specific time
docker-compose logs --since 2h
```

### Health Checks

```bash
# Backend health
curl http://localhost:8000/health

# Frontend
curl http://localhost:3000

# Through nginx
curl http://localhost/health
```

### Performance Monitoring

```bash
# CPU and memory usage
docker stats

# Check resource limits
docker inspect CONTAINER_ID | grep -A 20 HostConfig
```

---

## Production Checklist

- [ ] All environment variables set securely
- [ ] Database password changed from default
- [ ] SECRET_KEY generated with secure random value
- [ ] DEBUG=false in production
- [ ] SSL/TLS certificate configured
- [ ] Firewall rules configured (ports 80, 443)
- [ ] Regular backups scheduled
- [ ] Monitoring/alerting configured
- [ ] All API keys valid and not rate-limited
- [ ] CORS_ORIGINS configured correctly
- [ ] Database backup location secured
- [ ] Log rotation configured
- [ ] Auto-restart policies active

---

## Architecture

```
┌─────────────────────────────────────────────┐
│             Client Browser                  │
└────────────────┬────────────────────────────┘
                 │ HTTP/HTTPS Port 80/443
         ┌───────▼────────┐
         │  Nginx Proxy   │ (Reverse proxy, static files, TLS)
         └────┬───────┬───┘
              │       │
        ┌─────▼─┐   ┌─▼──────────┐
        │Backend│   │  Frontend  │
        │(8000) │   │ (3000)     │
        └────┬──┘   └────────────┘
             │
        ┌────▼──────────┐
        │  PostgreSQL   │
        │  (5432)       │
        └───────────────┘
```

---

## Support & Resources

- **Ploi Docs**: https://docs.ploi.io/
- **Docker Docs**: https://docs.docker.com/
- **Docker Compose**: https://docs.docker.com/compose/
- **GitHub Issues**: https://github.com/tasneemlabeeb/Political-Bias-Detector/issues

---

**Last Updated**: February 17, 2026
