# Political Bias Detector - Production Implementation Guide

A production-grade political bias detection system with ML model training, REST API backend, and browser extension.

## 🎯 Project Structure

```
Political Bias Detector/
├── training/                    # ML Model Training Pipeline
│   ├── config.yaml             # Training configuration
│   ├── data_collection.py      # Data labeling & collection
│   ├── train_model.py          # Model fine-tuning
│   ├── evaluate_model.py       # Model evaluation
│   ├── mlflow_setup.py         # Experiment tracking
│   └── README.md               # Training documentation
│
├── backend/                     # FastAPI Production Backend
│   ├── main.py                 # FastAPI app entry point
│   ├── config.py               # Settings & configuration
│   ├── database.py             # Database models
│   ├── auth.py                 # Authentication
│   ├── api/v1/                 # API endpoints
│   ├── middleware/             # Rate limiting, logging
│   └── Dockerfile              # Backend container
│
├── browser-extension/           # Chrome/Firefox Extension
│   ├── manifest.json           # Extension configuration
│   ├── content.js              # Page analysis script
│   ├── popup.html              # Extension popup
│   ├── background.js           # Background worker
│   └── README.md               # Extension documentation
│
├── src/                         # Original Streamlit App
│   ├── backend/                # Existing bias classifier
│   └── frontend/               # Existing Streamlit UI
│
├── docker-compose.yml           # Full stack deployment
└── README-IMPLEMENTATION.md     # This file
```

## 🚀 Quick Start Guide

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- PostgreSQL 15+ (or use Docker)
- Redis (or use Docker)
- Node.js 18+ (for extension development)

### Option 1: Docker Compose (Recommended)

```bash
# Start full stack
docker-compose up -d

# Access services:
# - Frontend: http://localhost:8501
# - Backend API: http://localhost:8000
# - API Docs: http://localhost:8000/api/docs
# - MLflow UI: mlflow ui --port 5000
# - Celery Flower: http://localhost:5555
```

### Option 2: Manual Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt
pip install -r training/requirements-training.txt
pip install -r backend/requirements-backend.txt

# 2. Setup environment variables
cp .env.example .env
# Edit .env with your configuration

# 3. Initialize database
alembic upgrade head

# 4. Start backend
uvicorn backend.main:app --reload

# 5. (Optional) Start MLflow
mlflow ui

# 6. (Optional) Start Celery worker
celery -A backend.celery_app worker --loglevel=info
```

## 📋 Implementation Roadmap

### Phase 1: Model Training (Weeks 1-6) ✅

#### Week 1-2: Data Collection & Labeling
```bash
cd training/

# 1. Setup MLflow
python mlflow_setup.py

# 2. Export unlabeled articles
python data_collection.py

# 3. Label data using Label Studio or Prodigy
# - Install: pip install label-studio
# - Start: label-studio start
# - Import data/labeling/unlabeled_articles_*.csv
# - Label articles with bias categories
# - Export as CSV

# 4. Create training dataset
python -c "
from training.data_collection import DataCollector
collector = DataCollector()
train, val, test = collector.create_training_dataset([
    'data/labeling/labeled_batch_1.csv'
])
"
```

**Goal**: Collect 1000+ labeled articles per bias category (5000+ total)

#### Week 3-4: Model Fine-Tuning
```bash
# Train custom model
python train_model.py

# Or use the training script:
from training.train_model import BiasModelTrainer

trainer = BiasModelTrainer()
trainer.train(
    train_file="data/processed/train_*.csv",
    val_file="data/processed/val_*.csv",
    model_name="roberta-base",
    output_dir="models/custom_roberta_v1"
)
```

**Goal**: Achieve >85% F1 score on validation set

#### Week 5-6: Model Evaluation & Optimization
```bash
# Evaluate model
python evaluate_model.py

# View results in MLflow
mlflow ui

# Register best model to production
python -c "
from training.mlflow_setup import MLflowManager
manager = MLflowManager()
manager.promote_model_to_production('political_bias_classifier', version=1)
"
```

**Goal**: Production-ready model with documented performance

### Phase 2: Backend API (Weeks 7-12) ✅

#### Week 7-8: Core Infrastructure
```bash
# 1. Setup PostgreSQL
docker run -d \
  --name bias_detector_db \
  -e POSTGRES_USER=bias_user \
  -e POSTGRES_PASSWORD=your_password \
  -e POSTGRES_DB=bias_detector \
  -p 5432:5432 \
  postgres:15-alpine

# 2. Initialize database
alembic init alembic
alembic revision --autogenerate -m "Initial schema"
alembic upgrade head

# 3. Start backend
uvicorn backend.main:app --reload

# 4. Test API
curl http://localhost:8000/health
curl http://localhost:8000/api/docs
```

**Goal**: Working REST API with authentication

#### Week 9-10: ML Integration
```bash
# Integrate trained models into backend

# Create classification service
# backend/services/classification.py

# Test classification endpoint
curl -X POST http://localhost:8000/api/v1/classify/text \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Article text here...",
    "title": "Article Title"
  }'
```

**Goal**: Real-time bias classification via API

#### Week 11-12: Production Hardening
- [ ] Add comprehensive tests (pytest)
- [ ] Setup CI/CD pipeline (GitHub Actions)
- [ ] Add monitoring (Prometheus + Grafana)
- [ ] Setup error tracking (Sentry)
- [ ] Load testing and optimization
- [ ] Security audit

**Goal**: Production-ready backend with >99% uptime

### Phase 3: Browser Extension (Weeks 13-16) ✅

#### Week 13-14: Extension Development
```bash
cd browser-extension/

# Load extension in Chrome
# 1. Open chrome://extensions/
# 2. Enable Developer mode
# 3. Click "Load unpacked"
# 4. Select browser-extension/ directory

# Test on news article
# Navigate to CNN, Fox News, etc.
# Click extension icon → Analyze This Page
```

**Goal**: Working extension with bias detection

#### Week 15-16: Polish & Publishing
- [ ] Add icons and branding
- [ ] Create promotional screenshots
- [ ] Write privacy policy
- [ ] Submit to Chrome Web Store
- [ ] Submit to Firefox Add-ons
- [ ] Create marketing website

**Goal**: Public extension with 1000+ users

## 🧪 Testing Strategy

### Model Testing
```bash
cd training/
pytest tests/test_models.py
pytest tests/test_data_pipeline.py
```

### Backend Testing
```bash
cd backend/
pytest tests/test_api.py
pytest tests/test_auth.py
pytest tests/test_classification.py --cov
```

### Extension Testing
- Manual testing on major news sites
- Cross-browser compatibility (Chrome, Firefox, Edge)
- Performance testing (analysis speed)

## 📊 Monitoring & Metrics

### Key Metrics to Track

**Model Performance**
- Accuracy, F1 score per bias category
- Calibration error (confidence vs accuracy)
- Prediction latency

**API Performance**
- Request rate (req/sec)
- Response time (p50, p95, p99)
- Error rate
- Cache hit rate

**User Engagement**
- Extension installs & active users
- Articles analyzed per user
- User feedback/ratings

### Monitoring Setup

```bash
# Prometheus
docker run -d \
  --name prometheus \
  -p 9090:9090 \
  -v ./prometheus.yml:/etc/prometheus/prometheus.yml \
  prom/prometheus

# Grafana
docker run -d \
  --name grafana \
  -p 3000:3000 \
  grafana/grafana
```

## 🔒 Security Checklist

- [ ] HTTPS/TLS certificates (Let's Encrypt)
- [ ] API rate limiting (per user, per IP)
- [ ] Input validation & sanitization
- [ ] SQL injection prevention (ORM)
- [ ] XSS protection (CSP headers)
- [ ] Secrets management (environment variables)
- [ ] Database encryption at rest
- [ ] Regular security audits
- [ ] GDPR compliance (data deletion)
- [ ] API key rotation policy

## 🚢 Deployment

### Development
```bash
docker-compose up
```

### Staging
```bash
docker-compose -f docker-compose.staging.yml up -d
```

### Production (AWS Example)
```bash
# 1. Build and push images
docker build -t bias-detector-api:latest -f backend/Dockerfile .
docker tag bias-detector-api:latest YOUR_ECR_REPO/bias-detector-api:latest
docker push YOUR_ECR_REPO/bias-detector-api:latest

# 2. Deploy to ECS/EKS
aws ecs update-service \
  --cluster production \
  --service bias-detector-api \
  --force-new-deployment

# 3. Run migrations
kubectl exec -it deployment/bias-detector-api -- alembic upgrade head
```

## 📈 Scaling Strategy

### Horizontal Scaling
- API servers: Auto-scale based on CPU/memory
- Celery workers: Scale based on queue depth
- Database: Read replicas for scaling reads

### Optimization
- Model inference: Batch predictions, GPU acceleration
- Caching: Redis for predictions, source metadata
- CDN: Static assets, model files

### Cost Optimization
- Use spot instances for Celery workers
- Compress model files (ONNX quantization)
- Cache frequently accessed predictions

## 🎓 Training & Documentation

### For ML Engineers
- Read `training/README.md`
- Review MLflow experiments
- Understand model architecture & training pipeline

### For Backend Developers
- Read API documentation at `/api/docs`
- Review database schema
- Understand authentication flow

### For Extension Developers
- Read `browser-extension/README.md`
- Review Chrome extension documentation
- Test on different news sites

## 📞 Support & Contribution

### Getting Help
- GitHub Issues: Bug reports & feature requests
- Documentation: https://docs.biasdetector.com
- Email: dev@biasdetector.com

### Contributing
1. Fork repository
2. Create feature branch
3. Write tests
4. Submit pull request

## 📝 Next Steps

### Immediate (This Week)
1. ✅ Review this implementation plan
2. Choose deployment platform (AWS, GCP, Azure)
3. Setup development environment
4. Start data collection for model training

### Short Term (Month 1-2)
1. Collect & label 5000+ articles
2. Train and evaluate custom models
3. Deploy backend API to staging
4. Test browser extension locally

### Medium Term (Month 3-4)
1. Launch public beta
2. Collect user feedback
3. Iterate on model & features
4. Prepare for production launch

### Long Term (Month 5-6)
1. Public launch
2. Marketing & user acquisition
3. Monitor metrics & optimize
4. Plan v2.0 features

## 🎯 Success Criteria

### Model Training
- ✅ 5000+ labeled training examples
- ✅ >85% F1 score on test set
- ✅ <0.1 calibration error
- ✅ Models tracked in MLflow

### Backend API
- ✅ <200ms p95 response time
- ✅ >99.9% uptime
- ✅ 100+ requests/second capacity
- ✅ Comprehensive test coverage

### Browser Extension
- ✅ 1000+ active users
- ✅ Works on 10+ major news sites
- ✅ <2sec analysis time
- ✅ 4.5+ star rating

## 📚 Resources

### Technologies Used
- **ML**: Transformers, PyTorch, MLflow
- **Backend**: FastAPI, PostgreSQL, Redis, Celery
- **Frontend**: Streamlit, React (future)
- **Extension**: Vanilla JavaScript, Chrome APIs
- **DevOps**: Docker, Kubernetes, GitHub Actions

### Learning Resources
- [FastAPI Tutorial](https://fastapi.tiangolo.com/tutorial/)
- [Transformers Documentation](https://huggingface.co/docs/transformers)
- [Chrome Extension Docs](https://developer.chrome.com/docs/extensions)
- [MLflow Guide](https://mlflow.org/docs/latest/index.html)

---

**Ready to build a production-grade bias detector!** 🚀

Start with Phase 1 (Model Training) and work your way through the roadmap systematically.
