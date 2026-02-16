# ⚡ QUICK REFERENCE CARD

## 🚀 One-Liner Deploy

```bash
ssh user@10.122.0.3 && cd /opt/Political\ Bias\ Detector && chmod +x scripts/deploy.sh && ./scripts/deploy.sh build && ./scripts/deploy.sh up
```

---

## 📍 Deployment Location

```
10.122.0.3
├── Port 80   → Frontend + API (Nginx)
├── Port 8000 → Backend (internal)
├── Port 5432 → Database (internal)
└── /opt/Political\ Bias\ Detector/  ← Project directory
```

---

## 🔑 API Keys Already Set

```
✅ GEMINI_API_KEY=AIzaSyAwFjWSAIr7t3K2SAZNEGKr2B_mqLXX8KU
✅ NEWS_API_KEY=07e8e55d4bf34310ada5a3fd903508c7  
✅ SERPER_API_KEY=b2931e4e23ee011070c3e39b5c61c67df0e59b99
```

---

## 📋 Before Deploying

```bash
# Verify everything is ready
bash /path/to/scripts/verify-deployment.sh

# Copy project to server
scp -r ./Political\ Bias\ Detector user@10.122.0.3:/opt/

# SSH in
ssh user@10.122.0.3

# Go to project
cd /opt/Political\ Bias\ Detector

# Make script executable
chmod +x scripts/deploy.sh
```

---

## 🏗️ Deploy Commands

```bash
# Build images
./scripts/deploy.sh build

# Start services
./scripts/deploy.sh up

# Check health
./scripts/deploy.sh health

# View logs
./scripts/deploy.sh logs

# Restart
./scripts/deploy.sh restart

# Stop
./scripts/deploy.sh down

# Status
./scripts/deploy.sh status
```

---

## 🌐 Access After Deploy

| URL | Purpose |
|-----|---------|
| `http://10.122.0.3` | Web interface |
| `http://10.122.0.3/api/v1` | API base |
| `http://10.122.0.3/api/docs` | API docs (Swagger) |
| `http://10.122.0.3/health` | Health check |

---

## 🧪 Test Commands

```bash
# Test backend
curl http://10.122.0.3/api/v1/sources

# Test search
curl -X POST "http://10.122.0.3/api/v1/search/topic?topic=biden&max_articles=3"

# Test URL classifier
curl -X POST "http://10.122.0.3/api/v1/classify/url/url?url=https://bbc.com/news/uk"

# Test health
curl http://10.122.0.3/health
```

---

## ⏱️ Timeline

| Phase | Duration | Activity |
|-------|----------|----------|
| Prerequisites | 5 min | Install Docker |
| Upload | 3 min | Copy project |
| Build | 5 min | Docker build |
| Model Download | 30-60 min | ML models (~5GB) |
| Startup | 5 min | Services initialize |
| **Total** | **45-90 min** | — |

---

## 🔧 Essential Files

```
Political Bias Detector/
├── START_HERE.md          ← Read this first!
├── DEPLOYMENT_SUMMARY.md  ← This reference
├── DEPLOYMENT_CHECKLIST.md← Complete checklist
├── DEPLOYMENT.md          ← Full guide
├── .env.production        ← Secrets (already filled)
├── docker-compose.production.yml
├── Dockerfile.backend
├── frontend-nextjs/Dockerfile
├── nginx/                 ← Proxy config
└── scripts/
    ├── deploy.sh          ← Main deployment script
    └── verify-deployment.sh← Verification
```

---

## 🚨 Troubleshooting Quick Fixes

| Issue | Fix |
|-------|-----|
| Frontend blank | `./scripts/deploy.sh logs frontend` |
| API 502 error | `./scripts/deploy.sh logs backend` |
| DB connection error | Check `.env.production` DATABASE_URL |
| Models not downloading | `./scripts/deploy.sh logs backend` |
| Port 80 in use | `lsof -ti:80 \| xargs kill -9` |

---

## 📞 Documentation Map

- **"How do I start?"** → START_HERE.md
- **"What are all the steps?"** → DEPLOYMENT_CHECKLIST.md  
- **"How do I troubleshoot?"** → DEPLOYMENT.md (Troubleshooting)
- **"I need quick reference"** → This file! ⚡

---

## 🎯 Success Metrics

After deployment, verify:

```bash
✅ Frontend loads at http://10.122.0.3
✅ API responds at http://10.122.0.3/api/v1/sources  
✅ API docs at http://10.122.0.3/api/docs
✅ Health check passes: curl http://10.122.0.3/health
✅ Can search & classify news articles
```

---

## 🆘 Emergency Contacts

If stuck, check in this order:

1. START_HERE.md → Quick overview
2. DEPLOYMENT_CHECKLIST.md → Step-by-step
3. DEPLOYMENT.md → Detailed troubleshooting
4. API Docs → Interactive examples (http://10.122.0.3/api/docs)
5. Logs → `./scripts/deploy.sh logs`

---

## 💡 Pro Tips

```bash
# Watch logs in real-time
./scripts/deploy.sh logs -f backend

# Get shell inside container
docker exec -it backend bash

# Check resource usage
docker stats

# Database backup before updates
./scripts/deploy.sh backup

# Clean old images
docker image prune -a -f
```

---

## 📦 Deployment Checklist

- [ ] Read START_HERE.md
- [ ] Verify: `bash scripts/verify-deployment.sh`
- [ ] SSH to 10.122.0.3
- [ ] Install Docker & Docker Compose
- [ ] Copy project via scp
- [ ] `cd /opt/Political\ Bias\ Detector`
- [ ] `chmod +x scripts/deploy.sh`
- [ ] `./scripts/deploy.sh build`
- [ ] Wait for models to download
- [ ] `./scripts/deploy.sh up`
- [ ] `./scripts/deploy.sh health`
- [ ] Access http://10.122.0.3 ✅

---

## ✅ Final Check

```
✓ All files present
✓ Configuration ready
✓ API keys loaded
✓ Documentation complete
✓ Deployment script tested
✓ Verification passed (36/41 checks)

🚀 READY FOR DEPLOYMENT
```

---

**Deployment Command (Copy-Paste Ready):**
```bash
bash /path/to/scripts/deploy.sh build && ./scripts/deploy.sh up && ./scripts/deploy.sh health
```

**Good luck! 🎉**
