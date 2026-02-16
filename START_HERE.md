# Political Bias Detector - START HERE 🚀

Welcome to the Political Bias Detector production deployment guide. This document provides everything you need to get the system live on **10.122.0.3**.

## Quick Summary

This is a **production-ready AI system** that:
- 🔍 Searches for news articles on any topic
- 🤖 Uses trained ML models to analyze political bias
- 📊 Provides bias classification with confidence scores
- 🌐 Serves via web interface and API

**Tech Stack:**
- Frontend: Next.js 14 (React, TypeScript, Tailwind CSS)
- Backend: FastAPI (Python 3.11)
- Database: PostgreSQL (Neon)
- ML Models: Transformers (HuggingFace)
- News Sources: NewsAPI + Serper API
- Deployment: Docker + Docker Compose + Nginx

---

## 🎯 Your Mission

Deploy this system to **10.122.0.3** and make it accessible via HTTP.

**Estimated Time:** 45-90 minutes (first deployment slower due to ML model downloads)

---

## 📋 What You're Deploying

### Services (All containerized)

1. **PostgreSQL Database**
   - Stores articles, user data, configurations
   - Port: 5432 (internal only)
   - Data persists in Docker volume

2. **Backend API (FastAPI)**
   - Search endpoint: `/api/v1/search/topic`
   - Classification endpoint: `/api/v1/classify/url/url`
   - Health check: `/health`
   - Auto-docs: `/api/docs`
   - Port: 8000 (internal), exposed via Nginx

3. **Frontend (Next.js)**
   - Web interface for users
   - Search interface, results display, analytics
   - Port: 3000 (internal), exposed via Nginx

4. **Nginx Reverse Proxy**
   - Routes traffic to backend/frontend
   - Rate limiting enabled
   - SSL/TLS ready
   - Port: 80 (HTTP), 443 (HTTPS - optional)

### ML Models (Auto-download on first run)
- **politicalBiasBERT**: Classifies bias direction (Left/Center-Left/Centrist/Center-Right/Right)
- **bias-detector**: Calculates bias intensity

---

## 🚀 Quick Deployment (5 Steps)

### Step 1: Connect to Server
```bash
ssh user@10.122.0.3
```

### Step 2: Install Docker
```bash
sudo apt-get update
sudo apt-get install -y docker.io docker-compose
sudo usermod -aG docker $USER
```

### Step 3: Deploy
```bash
# Copy project (from your local machine)
scp -r ./Political\ Bias\ Detector user@10.122.0.3:/opt/

# SSH back in and deploy
ssh user@10.122.0.3
cd /opt/Political\ Bias\ Detector

# Make deployment script executable
chmod +x scripts/deploy.sh

# Start deployment
./scripts/deploy.sh build
./scripts/deploy.sh up
```

### Step 4: Wait for Models to Download
First deployment takes 30-60 seconds while ML models download (~5GB).

### Step 5: Verify & Access
```bash
# Health check
./scripts/deploy.sh health

# Then access:
# Frontend: http://10.122.0.3
# API: http://10.122.0.3/api/v1
# API Docs: http://10.122.0.3/api/docs
```

✅ **System is now live!**

---

## 🔑 Important Files

| File | Purpose |
|------|---------|
| [`.env.production`](.env.production) | Production secrets (already filled) |
| [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) | Complete step-by-step checklist |
| [DEPLOYMENT.md](DEPLOYMENT.md) | Comprehensive deployment guide |
| [QUICK_DEPLOY.md](QUICK_DEPLOY.md) | Fast reference guide |
| [docker-compose.production.yml](docker-compose.production.yml) | Container orchestration |
| [scripts/deploy.sh](scripts/deploy.sh) | Deployment helper script |

---

## 📡 API Usage

### Search with Bias Classification
```bash
curl -X POST "http://10.122.0.3/api/v1/search/topic?topic=biden&max_articles=3"
```

**Response:**
```json
{
  "articles": [
    {
      "title": "Article Title",
      "link": "https://...",
      "ml_bias": "Center-Left",
      "ml_confidence": 0.85,
      "spectrum": {
        "left": 0.45,
        "center": 0.30,
        "right": 0.25
      }
    }
  ]
}
```

### Classify URL Directly
```bash
curl -X POST "http://10.122.0.3/api/v1/classify/url/url?url=https://example.com/article"
```

---

## 🛠️ Common Commands

```bash
# Check service status
./scripts/deploy.sh status

# View logs
./scripts/deploy.sh logs backend      # Backend logs
./scripts/deploy.sh logs frontend     # Frontend logs
./scripts/deploy.sh logs nginx        # Nginx/proxy logs

# Restart services
./scripts/deploy.sh restart

# Stop everything
./scripts/deploy.sh down

# Backup database
./scripts/deploy.sh backup

# Health check
./scripts/deploy.sh health
```

---

## ⚠️ Configuration Before Deployment

**BEFORE running `./scripts/deploy.sh up`**, edit `.env.production`:

```bash
nano .env.production
```

**Fields to review:**
- `SECRET_KEY` - Change to random string (security)
- `DB_PASSWORD` - Change to strong password
- `CORS_ORIGINS` - Add your domain if using custom domain
- API keys already filled with valid credentials ✅

**Save and exit:** `Ctrl+X`, `Y`, `Enter`

---

## 🧠 System Architecture

```
Client Browser
    ↓
Nginx (Port 80)
    ├→ /api/* → FastAPI Backend (Port 8000)
    │           ├→ Transformers Models (HuggingFace)
    │           ├→ NewsAPI + Serper Integration
    │           └→ PostgreSQL Database
    │
    └→ /* → Next.js Frontend (Port 3000)
            └→ React + Tailwind CSS
```

---

## 📊 Monitoring

### Health Endpoint
```bash
curl http://10.122.0.3/health
```

Returns:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "services": {
    "database": "connected",
    "models": "loaded"
  }
}
```

### Real-time Status
```bash
./scripts/deploy.sh status
```

Shows Docker container status and resource usage.

---

## 🔒 Security Notes

1. **Database Password:** Already set in `.env.production` - change if needed
2. **Secret Key:** Must change from default value
3. **API Keys:** Already populated (NewsAPI, Serper, Gemini)
4. **SSL/TLS:** Optional but recommended for production
5. **Rate Limiting:** Enabled by default (10req/s for API)

---

## 🐛 Troubleshooting

### Frontend Not Loading
```bash
./scripts/deploy.sh logs frontend
# Look for build errors or connection issues
```

### API Returning 502 Error
```bash
./scripts/deploy.sh logs backend
# Backend likely crashed or not responding
```

### Database Connection Error
```bash
# Check DATABASE_URL in .env.production
nano .env.production
# Verify credentials match your setup
```

### Models Not Downloading
- Check internet connectivity
- Verify disk space (need ~10GB)
- Check logs: `./scripts/deploy.sh logs backend`

**For detailed troubleshooting:** See **DEPLOYMENT.md**

---

## 📈 Performance Expectations

| Operation | Time | Notes |
|-----------|------|-------|
| First deployment | 30-60min | ML models download first time |
| Subsequent restarts | 5-10sec | Models already cached |
| News search | 2-5sec | API + classification latency |
| URL classification | 1-3sec | Direct classification |
| API response | <500ms | After classification done |

---

## 🔄 Regular Maintenance

### Weekly
- Check logs for errors: `./scripts/deploy.sh logs`
- Monitor disk usage: `df -h`
- Monitor memory: `docker stats`

### Monthly
- Backup database: `./scripts/deploy.sh backup`
- Update packages: `sudo apt-get update && sudo apt-get upgrade`
- Review API key quotas (NewsAPI, Serper)

### As Needed
- Restart services: `./scripts/deploy.sh restart`
- Update containers: `./scripts/deploy.sh build && ./scripts/deploy.sh up`

---

## 📞 Support Resources

1. **Complete Checklist:** [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)
2. **Full Documentation:** [DEPLOYMENT.md](DEPLOYMENT.md)
3. **Quick Reference:** [QUICK_DEPLOY.md](QUICK_DEPLOY.md)
4. **API Documentation:** After deployment at `http://10.122.0.3/api/docs`

---

## ✅ Post-Deployment Verification

After running `./scripts/deploy.sh up`, verify:

- [ ] Access http://10.122.0.3 in browser (frontend loads)
- [ ] API responds: `curl http://10.122.0.3/api/v1/sources`
- [ ] API docs work: `http://10.122.0.3/api/docs`
- [ ] Health check passes: `./scripts/deploy.sh health`
- [ ] Search works: Test via web interface

---

## 🎉 You're Ready!

Everything is prepared and tested. Follow the **Quick Deployment** section above to get live.

**Questions?**
- Check the relevant documentation file
- Review logs with `./scripts/deploy.sh logs`
- Run `./scripts/deploy.sh help` for all commands

**Good luck! 🚀**

---

**Deployment Prepared By:** AI Assistant  
**Date:** February 17, 2026  
**Status:** ✅ Production Ready
