#!/bin/bash
# Quick Start Script for Political Bias Detector Development

set -e  # Exit on error

echo "🚀 Political Bias Detector - Development Setup"
echo "=============================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check prerequisites
echo "📋 Checking prerequisites..."

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 not found. Please install Python 3.11+${NC}"
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}⚠️  Docker not found. Some features will be limited.${NC}"
    DOCKER_AVAILABLE=false
else
    DOCKER_AVAILABLE=true
fi

if ! command -v git &> /dev/null; then
    echo -e "${YELLOW}⚠️  Git not found.${NC}"
fi

echo -e "${GREEN}✅ Prerequisites check complete${NC}"
echo ""

# Setup environment
echo "🔧 Setting up environment..."

if [ ! -f .env ]; then
    echo "Creating .env file from example..."
    cp .env.example .env
    echo -e "${GREEN}✅ .env file created. Please review and update if needed.${NC}"
else
    echo -e "${YELLOW}⚠️  .env file already exists. Skipping.${NC}"
fi

# Create virtual environment
echo ""
echo "🐍 Creating Python virtual environment..."

if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
else
    echo -e "${YELLOW}⚠️  Virtual environment already exists${NC}"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo ""
echo "📦 Installing dependencies..."
echo "This may take a few minutes..."

pip install --upgrade pip
pip install -r requirements.txt

echo -e "${GREEN}✅ Core dependencies installed${NC}"

# Ask user what to setup
echo ""
echo "What would you like to setup?"
echo "1) Full stack (Docker Compose - recommended for development)"
echo "2) Model training only"
echo "3) Backend API only"
echo "4) Browser extension only"
echo "5) All of the above (manual setup)"

read -p "Enter your choice (1-5): " choice

case $choice in
    1)
        echo ""
        echo "🐳 Setting up with Docker Compose..."
        
        if [ "$DOCKER_AVAILABLE" = false ]; then
            echo -e "${RED}❌ Docker is required for this option${NC}"
            exit 1
        fi
        
        # Create necessary directories
        mkdir -p data/raw data/processed data/labeling logs models mlruns
        
        echo "Starting Docker Compose..."
        docker-compose up -d
        
        echo ""
        echo -e "${GREEN}✅ Docker Compose setup complete!${NC}"
        echo ""
        echo "Services available at:"
        echo "  - Streamlit Frontend: http://localhost:8501"
        echo "  - Backend API: http://localhost:8000"
        echo "  - API Documentation: http://localhost:8000/api/docs"
        echo "  - Celery Flower: http://localhost:5555"
        echo ""
        echo "To view logs: docker-compose logs -f"
        echo "To stop: docker-compose down"
        ;;
        
    2)
        echo ""
        echo "🎓 Setting up model training..."
        
        pip install -r training/requirements-training.txt
        
        mkdir -p data/raw data/processed data/labeling logs models mlruns evaluation_results
        
        # Initialize MLflow
        python training/mlflow_setup.py
        
        echo -e "${GREEN}✅ Model training setup complete!${NC}"
        echo ""
        echo "Next steps:"
        echo "  1. Collect and label training data"
        echo "  2. Run: python training/data_collection.py"
        echo "  3. Run: python training/train_model.py"
        echo "  4. View experiments: mlflow ui"
        echo ""
        echo "See training/README.md for detailed instructions"
        ;;
        
    3)
        echo ""
        echo "🔌 Setting up backend API..."
        
        pip install -r backend/requirements-backend.txt
        
        mkdir -p logs
        
        if [ "$DOCKER_AVAILABLE" = true ]; then
            echo "Starting PostgreSQL and Redis with Docker..."
            docker run -d --name bias_detector_db \
                -e POSTGRES_USER=bias_user \
                -e POSTGRES_PASSWORD=bias_pass_dev \
                -e POSTGRES_DB=bias_detector \
                -p 5432:5432 \
                postgres:15-alpine
            
            docker run -d --name bias_detector_redis \
                -p 6379:6379 \
                redis:7-alpine
            
            echo "Waiting for database to be ready..."
            sleep 5
        else
            echo -e "${YELLOW}⚠️  Please install PostgreSQL and Redis manually${NC}"
        fi
        
        echo -e "${GREEN}✅ Backend API setup complete!${NC}"
        echo ""
        echo "To start the backend:"
        echo "  uvicorn backend.main:app --reload"
        echo ""
        echo "API will be available at:"
        echo "  - http://localhost:8000"
        echo "  - Documentation: http://localhost:8000/api/docs"
        ;;
        
    4)
        echo ""
        echo "🧩 Setting up browser extension..."
        
        mkdir -p browser-extension/icons
        
        echo -e "${GREEN}✅ Browser extension setup complete!${NC}"
        echo ""
        echo "To install the extension:"
        echo "  Chrome:"
        echo "    1. Open chrome://extensions/"
        echo "    2. Enable 'Developer mode'"
        echo "    3. Click 'Load unpacked'"
        echo "    4. Select the 'browser-extension' folder"
        echo ""
        echo "  Firefox:"
        echo "    1. Open about:debugging#/runtime/this-firefox"
        echo "    2. Click 'Load Temporary Add-on'"
        echo "    3. Select 'browser-extension/manifest.json'"
        echo ""
        echo "See browser-extension/README.md for details"
        ;;
        
    5)
        echo ""
        echo "📦 Installing all dependencies..."
        
        pip install -r requirements.txt
        pip install -r training/requirements-training.txt
        pip install -r backend/requirements-backend.txt
        
        mkdir -p data/raw data/processed data/labeling logs models mlruns evaluation_results browser-extension/icons
        
        python training/mlflow_setup.py
        
        echo -e "${GREEN}✅ All dependencies installed!${NC}"
        echo ""
        echo "Manual setup required:"
        echo "  1. Install PostgreSQL and Redis (or use Docker)"
        echo "  2. Configure .env file with database credentials"
        echo "  3. Start services as needed"
        ;;
        
    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac

echo ""
echo "=============================================="
echo -e "${GREEN}🎉 Setup complete!${NC}"
echo ""
echo "📚 Documentation:"
echo "  - Main guide: README-IMPLEMENTATION.md"
echo "  - Model training: training/README.md"
echo "  - Browser extension: browser-extension/README.md"
echo ""
echo "💡 Tip: Review .env file and update configuration as needed"
echo ""
echo "Happy coding! 🚀"
