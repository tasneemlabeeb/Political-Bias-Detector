# Quick Deploy to 10.122.0.3

## Step-by-Step Deployment

### 1. SSH into Server
```bash
ssh user@10.122.0.3
```

### 2. Install Docker (if not already installed)
```bash
# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install Docker
sudo apt-get install -y docker.io docker-compose

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Verify
docker --version
docker-compose --version
```

### 3. Clone/Upload Project
```bash
# Option A: Upload via git
git clone <repository-url> /opt/political-bias-detector
cd /opt/political-bias-detector

# Option B: Upload files via SCP
scp -r ./Political\ Bias\ Detector user@10.122.0.3:/opt/
cd /opt/Political\ Bias\ Detector
```

### 4. Configure Environment
```bash
# Copy template
cp .env.production.example .env.production

# Edit configuration (add your API keys)
nano .env.production
```

**Required API Keys to add:**
- `GEMINI_API_KEY=AIzaSyAwFjWSAIr7t3K2SAZNEGKr2B_mqLXX8KU`
- `NEWS_API_KEY=07e8e55d4bf34310ada5a3fd903508c7`
- `SERPER_API_KEY=b2931e4e23ee011070c3e39b5c61c67df0e59b99`

### 5. Make Deploy Script Executable
```bash
chmod +x scripts/deploy.sh
```

### 6. Deploy!
```bash
# Quick deploy
./scripts/deploy.sh up

# Or full manual:
docker-compose -f docker-compose.production.yml build
docker-compose -f docker-compose.production.yml up -d
```

### 7. Verify Deployment
```bash
# Check services
./scripts/deploy.sh status

# Run health check
./scripts/deploy.sh health

# View logs
./scripts/deploy.sh logs
```

## Access Application

- **Frontend**: http://10.122.0.3
- **API Docs**: http://10.122.0.3/api/docs
- **Health**: http://10.122.0.3/health

## Useful Commands

```bash
# View all logs
docker-compose -f docker-compose.production.yml logs -f

# View backend logs only
docker-compose -f docker-compose.production.yml logs -f backend

# Stop all services
docker-compose -f docker-compose.production.yml down

# Restart
docker-compose -f docker-compose.production.yml restart

# Database backup
docker-compose -f docker-compose.production.yml exec postgres pg_dump \
  -U pbd_user political_bias_detector > backup.sql
```

## Troubleshooting

### Services won't start
```bash
# Check logs
docker-compose -f docker-compose.production.yml logs
docker-compose -f docker-compose.production.yml logs backend
```

### API returns 502 Bad Gateway
```bash
# Check if backend is running
docker-compose -f docker-compose.production.yml ps
docker-compose -f docker-compose.production.yml logs backend
```

### Database connection issues
```bash
# Verify database is running
docker-compose -f docker-compose.production.yml exec postgres psql -U pbd_user -c "SELECT 1"
```

### Port already in use
```bash
# Find process using port 80
sudo lsof -i :80
# Kill it
sudo kill -9 <PID>
```

## Production Checklist

- [ ] Updated all API keys in .env.production
- [ ] Changed default DATABASE password
- [ ] Set DEBUG=false
- [ ] Generated new SECRET_KEY
- [ ] Configured SSL/TLS (optional but recommended)
- [ ] Set up automatic backups
- [ ] Verified all services are running
- [ ] Tested API endpoints
- [ ] Verified frontend loads
- [ ] Tested search functionality
- [ ] Monitored resource usage

---

**Deployed on**: 10.122.0.3  
**Status**: Ready for production  
**Last Updated**: February 17, 2026
