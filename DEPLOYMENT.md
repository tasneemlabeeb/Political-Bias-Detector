# Political Bias Detector - Deployment Guide

## Deployment Environment
- **Server IP**: 10.122.0.3
- **Frontend Port**: 80 (via Nginx)
- **Backend Port**: 8000 (internal)
- **Database Port**: 5432 (internal)

## Architecture
```
┌─────────────────────────────────────────────────┐
│  Client Browser (10.122.0.3)                    │
└────────────────┬────────────────────────────────┘
                 │ HTTP:80 / HTTPS:443
         ┌───────▼────────┐
         │  Nginx Proxy   │
         │  (Reverse)     │
         └───┬────────┬───┘
             │        │
      ┌──────▼─┐   ┌──▼────────┐
      │Backend │   │ Frontend   │
      │(8000)  │   │ (3000)     │
      └──┬─────┘   └────────────┘
         │
      ┌──▼──────────┐
      │  PostgreSQL  │
      │  (5432)      │
      └──────────────┘
```

## Prerequisites

### On Server (10.122.0.3)
```bash
# 1. Install Docker
sudo apt-get update
sudo apt-get install -y docker.io docker-compose

# 2. Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# 3. Enable Docker service
sudo systemctl enable docker
sudo systemctl start docker

# 4. Verify installation
docker --version
docker-compose --version
```

## Deployment Steps

### Step 1: Clone or Upload Project

```bash
# Option A: Clone from git (if available)
git clone <your-repo> /opt/political-bias-detector
cd /opt/political-bias-detector

# Option B: Upload via SCP/SFTP
scp -r ./Political\ Bias\ Detector user@10.122.0.3:/opt/
```

### Step 2: Configure Environment

```bash
cd /opt/political-bias-detector

# Copy production environment template
cp .env.production.example .env.production

# Edit with your API keys
nano .env.production
```

**Required environment variables to configure:**
```
GEMINI_API_KEY=your-key
NEWS_API_KEY=your-key
SERPER_API_KEY=your-key
DB_PASSWORD=secure-password
SECRET_KEY=secure-random-string
```

### Step 3: Prepare Models

The ML models need to be available in the `models/` directory:

```bash
# Create models directory
mkdir -p models/production/direction
mkdir -p models/production/intensity

# Models will be automatically downloaded on first run
# (or copy pre-trained models if you have them)
```

### Step 4: Build and Start Services

```bash
# Build Docker images
docker-compose -f docker-compose.production.yml build

# Start all services
docker-compose -f docker-compose.production.yml up -d

# Verify services are running
docker-compose -f docker-compose.production.yml ps
```

### Step 5: Verify Deployment

```bash
# Check backend health
curl http://10.122.0.3/health

# Check API endpoints
curl http://10.122.0.3/api/docs

# Check frontend
curl http://10.122.0.3/
```

## Post-Deployment Configuration

### Access the Application

- **Frontend**: http://10.122.0.3
- **API Docs**: http://10.122.0.3/api/docs
- **Health Check**: http://10.122.0.3/health

### View Logs

```bash
# All services
docker-compose -f docker-compose.production.yml logs -f

# Specific service
docker-compose -f docker-compose.production.yml logs -f backend
docker-compose -f docker-compose.production.yml logs -f frontend
docker-compose -f docker-compose.production.yml logs -f nginx
```

### Database Access

```bash
# Connect directly to PostgreSQL
docker-compose -f docker-compose.production.yml exec postgres psql -U pbd_user -d political_bias_detector

# Backup database
docker-compose -f docker-compose.production.yml exec postgres pg_dump -U pbd_user political_bias_detector > backup.sql
```

## SSL/TLS Configuration (Recommended)

### Option 1: Using Let's Encrypt with Certbot

```bash
# Install Certbot
sudo apt-get install -y certbot python3-certbot-nginx

# Get certificate (requires domain name, not IP)
sudo certbot certonly --standalone -d your-domain.com

# Copy certificates to nginx directory
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem ./nginx/ssl/cert.pem
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem ./nginx/ssl/key.pem

# Update nginx/conf.d/default.conf to enable HTTPS
# Uncomment the HTTPS server block
```

### Option 2: Self-Signed Certificate (For Testing)

```bash
# Generate self-signed certificate
mkdir -p nginx/ssl
openssl req -x509 -newkey rsa:4096 -nodes \
  -out nginx/ssl/cert.pem -keyout nginx/ssl/key.pem -days 365

# Update nginx config to use HTTPS
# Uncomment the HTTPS server block in nginx/conf.d/default.conf
```

## Maintenance

### Stop Services
```bash
docker-compose -f docker-compose.production.yml down
```

### Restart Services
```bash
docker-compose -f docker-compose.production.yml restart
```

### Update Application
```bash
# Pull latest code
git pull origin main

# Rebuild images
docker-compose -f docker-compose.production.yml build

# Restart with new images
docker-compose -f docker-compose.production.yml up -d
```

### Clean Up
```bash
# Remove stopped containers
docker-compose -f docker-compose.production.yml down -v

# Remove unused images
docker image prune
```

## Troubleshooting

### Backend not connecting to database
```bash
# Check database logs
docker-compose -f docker-compose.production.yml logs postgres

# Verify connection string in .env.production
# Format: postgresql://user:password@postgres:5432/dbname
```

### Frontend can't reach API
```bash
# Check NEXT_PUBLIC_API_URL in docker-compose.production.yml
# Should be: http://10.122.0.3:8080/api (or http://10.122.0.3/api after nginx setup)

# Verify nginx is routing correctly
docker-compose -f docker-compose.production.yml logs nginx
```

### ML models not downloading
```bash
# Check backend logs for model download errors
docker-compose -f docker-compose.production.yml logs backend

# Models require internet connection and disk space (~5-10GB)
# Verify disk space: df -h
```

### High memory usage
```bash
# Check resource usage
docker stats

# Limit resource in docker-compose.production.yml:
# services:
#   backend:
#     deploy:
#       resources:
#         limits:
#           memory: 4G
#         reserves:
#           memory: 2G
```

## Performance Optimization

### Increase Worker Processes
Edit `docker-compose.production.yml` backend service:
```bash
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

### Enable Caching
Configure Redis in `docker-compose.production.yml`:
```yaml
redis:
  image: redis:7-alpine
  container_name: pbd-redis
```

### Database Optimization
```bash
# Connect to database
docker-compose -f docker-compose.production.yml exec postgres psql -U pbd_user -d political_bias_detector

# Create indexes
CREATE INDEX idx_articles_source ON articles(source_id);
CREATE INDEX idx_articles_published ON articles(published_date);
```

## Security Checklist

- [ ] Change all default passwords
- [ ] Configure firewall rules
- [ ] Enable HTTPS/SSL
- [ ] Set DEBUG=false in production
- [ ] Use strong SECRET_KEY
- [ ] Regular database backups
- [ ] Monitor API rate limits
- [ ] Keep Docker images updated
- [ ] Document API credentials securely
- [ ] Enable logging and monitoring

## Monitoring

### Health Checks
```bash
# Continuous health monitoring
watch -n 5 'curl -s http://10.122.0.3/health'
```

### Prometheus Metrics
Access metrics at: http://10.122.0.3/metrics

### System Resources
```bash
# Monitor all containers
watch -n 2 'docker stats'
```

## Support & Troubleshooting

For issues, check:
1. Container logs: `docker-compose logs -f <service>`
2. Network connectivity: `docker network inspect pbd-network`
3. Port availability: `netstat -tlnp | grep LISTEN`
4. Disk space: `df -h`
5. Memory usage: `free -h`

## Rollback

```bash
# Stop current version
docker-compose -f docker-compose.production.yml down

# Restore from backup (if using version control)
git reset --hard HEAD~1

# Rebuild and restart
docker-compose -f docker-compose.production.yml build
docker-compose -f docker-compose.production.yml up -d
```

---

**Deployment Date**: [Add date]  
**Last Updated**: February 17, 2026  
**Status**: ✅ Production Ready
