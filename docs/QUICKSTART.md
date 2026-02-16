# 🚀 Quick Reference Guide

## What We Built

### ✅ Phase 1: Model Training Infrastructure
- **Training pipeline** with MLflow experiment tracking
- **Data collection & labeling** workflow
- **Model fine-tuning** scripts for custom models
- **Evaluation framework** with comprehensive metrics
- **Active learning** pipeline for iterative improvement

**Location**: `training/`
**Documentation**: `training/README.md`

### ✅ Phase 2: FastAPI Backend
- **Production-ready REST API** with async PostgreSQL
- **Authentication** with JWT tokens
- **Rate limiting** and request logging middleware
- **Classification endpoints** for real-time bias detection
- **Celery task queue** for background jobs
- **Docker Compose** setup for full stack

**Location**: `backend/`
**API Docs**: http://localhost:8000/api/docs (when running)

### ✅ Phase 3: Browser Extension
- **Chrome/Firefox extension** for real-time analysis
- **Content script** that detects and analyzes articles
- **Visual bias indicators** with floating badges
- **Popup interface** for manual analysis
- **Settings page** for configuration

**Location**: `browser-extension/`
**Documentation**: `browser-extension/README.md`

---

## 🎯 Getting Started (Choose One Path)

### Path 1: Quick Start with Docker (Recommended)
```bash
# 1. Run setup script
./setup.sh

# 2. Choose option 1 (Docker Compose)

# 3. Access services:
# - Frontend: http://localhost:8501
# - Backend API: http://localhost:8000/api/docs
# - Flower (Celery): http://localhost:5555
```

### Path 2: Model Training First
```bash
# 1. Run setup script
./setup.sh

# 2. Choose option 2 (Model training)

# 3. Collect and label data
python training/data_collection.py

# 4. Train model (after labeling)
python training/train_model.py

# 5. View experiments
mlflow ui
```

### Path 3: Backend Development
```bash
# 1. Run setup script
./setup.sh

# 2. Choose option 3 (Backend API)

# 3. Start backend
uvicorn backend.main:app --reload

# 4. Test API
curl http://localhost:8000/health
```

### Path 4: Extension Development
```bash
# 1. Ensure backend is running
docker-compose up -d

# 2. Load extension in Chrome
# - Open chrome://extensions/
# - Enable Developer mode
# - Load unpacked → select browser-extension/

# 3. Test on news article
# Navigate to CNN.com article → Click extension icon
```

---

## 📂 Project Structure

```
Political Bias Detector/
├── 🎓 training/              # ML model training
│   ├── config.yaml           # Training config
│   ├── data_collection.py    # Data pipeline
│   ├── train_model.py        # Model training
│   ├── evaluate_model.py     # Evaluation
│   └── mlflow_setup.py       # Experiment tracking
│
├── 🔌 backend/               # FastAPI backend
│   ├── main.py               # API entry point
│   ├── config.py             # Settings
│   ├── database.py           # DB models
│   ├── auth.py               # Authentication
│   ├── api/v1/               # API routes
│   │   └── endpoints/
│   │       ├── classify.py   # Classification API
│   │       ├── articles.py   # Article management
│   │       ├── sources.py    # Source management
│   │       └── auth.py       # Auth endpoints
│   ├── middleware/           # Rate limit, logging
│   └── services/             # Business logic
│
├── 🧩 browser-extension/     # Chrome/Firefox extension
│   ├── manifest.json         # Extension config
│   ├── content.js            # Page analysis
│   ├── popup.html            # Extension UI
│   └── background.js         # Background worker
│
├── 📊 src/                   # Original Streamlit app
│   ├── backend/              # Existing classifier
│   └── frontend/             # Streamlit UI
│
├── 📋 docker-compose.yml     # Full stack setup
├── 🔧 .env.example           # Environment template
├── 🚀 setup.sh               # Quick setup script
└── 📖 README-*.md            # Documentation
```

---

## 🛠️ Common Commands

### Development
```bash
# Start full stack
docker-compose up -d

# View logs
docker-compose logs -f backend

# Stop services
docker-compose down

# Rebuild containers
docker-compose up -d --build
```

### Model Training
```bash
# Start MLflow UI
mlflow ui

# Train model
cd training && python train_model.py

# Evaluate model
python evaluate_model.py
```

### Backend API
```bash
# Run backend locally
uvicorn backend.main:app --reload

# Run tests
pytest backend/tests/ -v

# Database migration
alembic upgrade head

# Start Celery worker
celery -A backend.celery_app worker -l info
```

### Browser Extension
```bash
# Package extension for distribution
cd browser-extension
zip -r bias-detector-v1.0.zip . -x "*.git*"
```

---

## 📊 Key Metrics & Targets

### Model Performance
- **Accuracy**: >85% on test set
- **F1 Score**: >0.85 (macro average)
- **Calibration Error**: <0.1
- **Inference Time**: <200ms per article

### API Performance
- **Response Time**: <200ms (p95)
- **Throughput**: >100 req/sec
- **Uptime**: >99.9%
- **Error Rate**: <1%

### Extension
- **Analysis Time**: <2 seconds
- **Compatibility**: Chrome/Firefox/Edge
- **Resource Usage**: <50MB RAM

---

## 🔥 Quick Wins (Implement These First)

### Week 1: Foundation
1. ✅ Setup development environment
2. ✅ Run existing Streamlit app
3. ✅ Start collecting training data
4. ✅ Test browser extension locally

### Week 2: Model Training
1. Label 500+ articles (use Label Studio)
2. Train first custom model
3. Evaluate and log to MLflow
4. Compare with baseline

### Week 3: Backend Integration
1. Deploy backend with Docker Compose
2. Test classification API
3. Integrate with browser extension
4. Add caching for predictions

### Week 4: Polish & Launch
1. Add comprehensive tests
2. Setup monitoring
3. Create user documentation
4. Beta launch with 10 users

---

## 🐛 Troubleshooting

### "Docker is not running"
```bash
# macOS
open -a Docker

# Linux
sudo systemctl start docker
```

### "Port already in use"
```bash
# Check what's using port 8000
lsof -i :8000

# Kill process
kill -9 <PID>
```

### "Module not found"
```bash
# Activate virtual environment
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### "Database connection failed"
```bash
# Check PostgreSQL is running
docker ps | grep postgres

# Restart database
docker-compose restart postgres
```

### "Extension not loading"
```bash
# Check manifest.json is valid
# Open chrome://extensions/ and check errors
# Reload extension after changes
```

---

## 📚 Next Steps

### Immediate Actions (Today)
1. [ ] Run `./setup.sh` to initialize project
2. [ ] Review `.env` and update configuration
3. [ ] Choose your starting path (training, backend, or extension)
4. [ ] Read relevant documentation

### This Week
1. [ ] Setup development environment completely
2. [ ] Start collecting training data
3. [ ] Test all three components locally
4. [ ] Create GitHub repository (optional)

### This Month
1. [ ] Label 1000+ articles
2. [ ] Train and evaluate first model
3. [ ] Deploy backend to staging
4. [ ] Test browser extension on major news sites

### Next 3 Months
1. [ ] Achieve target model performance (>85% F1)
2. [ ] Launch backend API to production
3. [ ] Publish browser extension (beta)
4. [ ] Collect user feedback

---

## 🎓 Learning Resources

### ML & NLP
- [Hugging Face Course](https://huggingface.co/course)
- [Fine-tuning Transformers](https://huggingface.co/docs/transformers/training)
- [MLflow Quickstart](https://mlflow.org/docs/latest/quickstart.html)

### Backend Development
- [FastAPI Tutorial](https://fastapi.tiangolo.com/tutorial/)
- [PostgreSQL Tutorial](https://www.postgresqltutorial.com/)
- [Celery Guide](https://docs.celeryq.dev/en/stable/getting-started/introduction.html)

### Browser Extensions
- [Chrome Extension Docs](https://developer.chrome.com/docs/extensions)
- [Web Extensions API](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions)

---

## 💬 Support

- **Implementation Guide**: `README-IMPLEMENTATION.md`
- **Model Training**: `training/README.md`
- **Browser Extension**: `browser-extension/README.md`
- **Issues**: Create GitHub issue
- **Questions**: Check documentation first

---


🚀 **Ready to start? Run `./setup.sh` now!**
