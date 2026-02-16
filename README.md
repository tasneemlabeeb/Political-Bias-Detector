# Political Bias Detector

A comprehensive AI-powered platform for detecting political bias in news articles, social media content, videos, and citation networks. Built with Next.js, FastAPI, and state-of-the-art machine learning models.

## Overview

This project provides multiple tools for bias detection and analysis:

- **News Article Analysis**: Analyze bias in news articles using fine-tuned transformer models
- **Social Media Integration**: Analyze bias in Reddit posts and Twitter/X threads
- **Video/Audio Analysis**: Transcribe and analyze bias in YouTube videos and podcasts
- **Citation Network**: Visualize citation patterns and detect echo chambers
- **Browser Extension**: Real-time bias detection while browsing
- **Custom Model Training**: Train your own bias detection models

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker (optional, for containerized deployment)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd "Political Bias Detector"
   ```

2. **Set up backend**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Set up frontend**
   ```bash
   cd frontend-nextjs
   npm install
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

### Running the Application

**Option 1: Full Stack (Recommended)**
```bash
./scripts/start-full-stack.sh
```

**Option 2: Individual Components**

Backend:
```bash
cd backend
uvicorn main:app --reload --port 8000
```

Frontend:
```bash
cd frontend-nextjs
npm run dev
```

Access the application at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/api/docs

## Features

### 🎯 Core Features

- **Real-time Bias Detection**: Analyze news articles and social media content
- **Multi-source Analysis**: Support for RSS feeds, web scraping, and APIs
- **ML-powered Classification**: Fine-tuned BERT models for accurate bias detection
- **Interactive Visualizations**: Charts and graphs for bias distribution
- **Source Management**: Manage and categorize news sources

### 🚀 Advanced Features

- **Social Media Analysis**: Analyze Reddit posts and Twitter threads
- **Video/Audio Transcription**: Extract and analyze content from YouTube and podcasts
- **Citation Network**: Visualize citation patterns and detect echo chambers
- **Community Detection**: Identify information silos and filter bubbles
- **Temporal Analysis**: Track bias changes over time

### 🔧 Tools

- **Browser Extension**: Real-time bias detection while browsing
- **Model Training**: Custom model training with your own datasets
- **API Integration**: RESTful API for third-party integrations

## Project Structure

```
├── backend/              # FastAPI backend
│   ├── api/             # API endpoints
│   ├── middleware/      # Rate limiting, logging
│   └── services/        # Business logic
├── frontend-nextjs/     # Next.js frontend
│   ├── app/            # App router pages
│   └── components/     # React components
├── browser-extension/   # Chrome/Firefox extension
├── src/                # Core Python modules
│   └── backend/        # Bias classifier, scrapers, analyzers
├── training/           # Model training scripts
├── models/             # Trained models
├── data/               # Training and test data
├── scripts/            # Setup and deployment scripts
└── docs/               # Documentation

```

## Documentation

Comprehensive documentation is available in the [docs/](docs/) folder:

- **[QUICKSTART.md](docs/QUICKSTART.md)** - Get started quickly
- **[FEATURES_DOCUMENTATION.md](docs/FEATURES_DOCUMENTATION.md)** - Detailed feature documentation
- **[QUICKSTART_NEW_FEATURES.md](docs/QUICKSTART_NEW_FEATURES.md)** - New features guide
- **[TRAINING.md](docs/TRAINING.md)** - Model training guide
- **[CLOUD_TRAINING_OPTIONS.md](docs/CLOUD_TRAINING_OPTIONS.md)** - Cloud training setup
- **[FRONTEND_NEXTJS.md](docs/FRONTEND_NEXTJS.md)** - Frontend development guide
- **[BROWSER_EXTENSION.md](docs/BROWSER_EXTENSION.md)** - Browser extension guide
- **[README-IMPLEMENTATION.md](docs/README-IMPLEMENTATION.md)** - Implementation details
- **[POST_TRAINING_WORKFLOW.md](docs/POST_TRAINING_WORKFLOW.md)** - Post-training workflow

## API Endpoints

### News Analysis
- `POST /api/v1/classify` - Classify news article bias

### Social Media
- `POST /api/v1/social-media/reddit` - Analyze Reddit post
- `POST /api/v1/social-media/twitter` - Analyze Twitter thread

### Media Analysis
- `POST /api/v1/media/youtube` - Transcribe and analyze YouTube video
- `POST /api/v1/media/whisper` - Transcribe audio file

### Citation Network
- `POST /api/v1/citations/analyze` - Analyze citation network
- `POST /api/v1/citations/echo-chambers` - Detect echo chambers

## Technology Stack

### Frontend
- **Next.js 14** - React framework with App Router
- **TypeScript** - Type safety
- **Tailwind CSS** - Utility-first styling
- **Framer Motion** - Smooth animations

### Backend
- **FastAPI** - High-performance Python web framework
- **SQLAlchemy** - Database ORM
- **Transformers** - HuggingFace transformer models
- **PyTorch** - Deep learning framework

### Data Processing
- **Pandas** - Data manipulation
- **NetworkX** - Graph analysis
- **BeautifulSoup** - Web scraping

### APIs
- **OpenAI** - Whisper API for transcription
- **Reddit API** - Social media analysis
- **Twitter API** - Social media analysis

## Environment Variables

Create a `.env` file in the root directory:

```env
# API Keys
OPENAI_API_KEY=your_openai_api_key
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
TWITTER_BEARER_TOKEN=your_twitter_bearer_token

# Database
DATABASE_URL=sqlite:///./news_sources.db

# Model
MODEL_PATH=./models/custom_bias_detector
```

## Training Custom Models

Train your own bias detection model:

```bash
cd training
python train_model.py --config config.yaml
```

For cloud training (Google Colab, RunPod):
```bash
# See docs/CLOUD_TRAINING_OPTIONS.md
```

## Browser Extension

Install the browser extension for real-time bias detection:

1. Open Chrome/Firefox
2. Navigate to Extensions
3. Enable Developer Mode
4. Load `browser-extension/` folder

See [docs/BROWSER_EXTENSION.md](docs/BROWSER_EXTENSION.md) for details.

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License.

## Credits

**Developed by Tasneem Zaman Laeeb**

## Support

For issues and questions:
- GitHub Issues: [Create an issue](https://github.com/your-repo/issues)
- Documentation: [docs/](docs/)
# Political-Bias-Detector
