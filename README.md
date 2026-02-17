# Political Bias Detector

An advanced machine learning system for detecting and analyzing political bias in media content, social media posts, and news articles.

**Status**: Production-ready | **Updated**: February 17, 2026

---

## 🎯 Quick Start

### Local Development

```bash
# Start all services with Docker
docker-compose up -d

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000/docs
```

### Production Deployment

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for complete deployment instructions.

**Recommended**: Deploy via [Ploi](https://ploi.io)
```bash
git push origin main  # Auto-deploys to Ploi
```

---

## 📁 Project Structure

```
├── backend/                 # FastAPI backend
│   ├── main.py
│   ├── api/                 # API endpoints
│   ├── Dockerfile
│   └── requirements-backend.txt
│
├── frontend-nextjs/         # Next.js frontend
│   ├── app/
│   ├── components/
│   ├── Dockerfile
│   └── package.json
│
├── browser-extension/       # Chrome extension
│
├── nginx/                   # Reverse proxy
│
├── scripts/                 # Utility scripts
│   ├── deploy.sh
│   ├── setup.sh
│   ├── utils/               # Tools & utilities
│   └── tests/               # Test scripts
│
├── training/                # ML training code
│
├── models/                  # Model storage
│
├── data/                    # Data directories
│
└── docs/                    # Documentation
```

---

## 🚀 Features

- **Political Bias Detection**: Analyze media for left/right political bias
- **Intensity Classification**: Determine bias intensity levels
- **Multi-Source Support**: News, social media, transcribed video
- **Browser Extension**: On-demand analysis from your browser
- **REST API**: Full-featured API for integrations
- **Real-time Search**: Integration with multiple news sources

---

## 🛠️ Technology Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | FastAPI, Python 3.11, PostgreSQL |
| **Frontend** | Next.js 14, TypeScript, Tailwind CSS |
| **ML** | Transformers, PyTorch |
| **Infrastructure** | Docker, Docker Compose, Nginx |
| **Deployment** | Ploi, GitHub, any VPS |

---

## ⚙️ Environment Setup

### Create .env.production

```bash
cp .env.example .env.production
```

**Required Variables:**
```env
# Application
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=openssl rand -hex 32

# Database
DB_USER=pbd_user
DB_PASSWORD=<secure-password>
DB_NAME=political_bias_detector
DATABASE_URL=postgresql://pbd_user:PASSWORD@postgres:5432/political_bias_detector

# API Keys
GEMINI_API_KEY=<your-key>
NEWS_API_KEY=<your-key>
SERPER_API_KEY=<your-key>

# Server
CORS_ORIGINS=http://your-domain,http://localhost
```

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for complete setup.

---

## 🐳 Docker Commands

```bash
# Development
docker-compose up -d

# Production
docker-compose -f docker-compose.production.yml up -d

# View logs
docker-compose logs -f

# Restart a service
docker-compose restart backend

# Stop all services
docker-compose down
```

---

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| [DEPLOYMENT.md](docs/DEPLOYMENT.md) | Complete deployment guide |
| [QUICKSTART.md](docs/QUICKSTART.md) | Quick setup guide |
| [TRAINING.md](docs/TRAINING.md) | ML model training |
| [BROWSER_EXTENSION.md](docs/BROWSER_EXTENSION.md) | Browser extension setup |

---

## 🚀 Deploy to Production

### Via Ploi (Recommended)
```bash
git push origin main  # Auto-deploys
```

### Manual Deployment
```bash
cd /opt/political-bias-detector
docker-compose -f docker-compose.production.yml build --pull
docker-compose -f docker-compose.production.yml up -d
```

---

## 🔧 Common Commands

```bash
# Connect to database
docker-compose exec postgres psql -U pbd_user -d political_bias_detector

# Backup database
docker-compose exec postgres pg_dump -U pbd_user political_bias_detector > backup.sql

# View backend logs
docker-compose logs -f backend

# Run utility tests
python scripts/tests/test_gemini.py
python scripts/tests/test_ml_search.py
python scripts/tests/test_news_fetch.py
```

---

## 📊 API Endpoints

### Health Check
```
GET /health
GET /api/health
```

### API Documentation
```
GET /api/docs        (Swagger UI)
GET /api/redoc       (ReDoc)
```

---

## 🐛 Troubleshooting

### Services won't start
```bash
docker-compose logs
docker system prune
```

### Database connection failed
```bash
docker-compose exec postgres psql -U pbd_user -c "SELECT 1"
```

### Port already in use
```bash
sudo lsof -i :80
sudo kill -9 <PID>
```

See [docs/DEPLOYMENT.md#troubleshooting](docs/DEPLOYMENT.md#troubleshooting) for more help.

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit changes
4. Push to branch
5. Open a Pull Request

---

## 📄 License

[Your License Here]

---

## 👤 Author

Tasneem Labeeb

---

## 📞 Support

- 🐛 **Issues**: [GitHub Issues](https://github.com/tasneemlabeeb/Political-Bias-Detector/issues)
- 📚 **Docs**: [docs/](docs/) folder
- 🚀 **Deployment**: [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)

---

**Version**: 1.0.0 | **Status**: Production Ready
