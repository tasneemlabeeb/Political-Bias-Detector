#!/bin/bash
set -e

echo "🎓 Setting Up Model Training Environment"
echo "========================================"
echo ""

# Check if Python 3.9+ is installed
echo "🐍 Checking Python version..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.9 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "✅ Found Python $PYTHON_VERSION"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo ""
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment exists"
fi

# Activate virtual environment
echo ""
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo ""
echo "⬆️  Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1

# Install training dependencies
echo ""
echo "📚 Installing training dependencies..."
echo "   This may take a few minutes..."

# Create requirements for training if not exists
if [ ! -f "training/requirements.txt" ]; then
    cat > training/requirements.txt << 'EOF'
# Core ML
torch>=2.1.0
transformers>=4.36.0
datasets>=2.16.0
accelerate>=0.25.0

# Experiment Tracking
mlflow>=2.10.0

# Data Processing
pandas>=2.1.0
numpy>=1.24.0
scikit-learn>=1.3.0

# Visualization
matplotlib>=3.8.0
seaborn>=0.13.0

# Active Learning
modAL-python>=0.4.1

# Utilities
tqdm>=4.66.0
pyyaml>=6.0
python-dotenv>=1.0.0

# Optional: Data Labeling
# label-studio>=1.10.0
# prodigy>=1.12.0
EOF
fi

pip install -r training/requirements.txt

echo ""
echo "✅ Training environment is ready!"
echo ""
echo "========================================"
echo "🎯 Next Steps for Model Training:"
echo "========================================"
echo ""
echo "1. Activate the environment:"
echo "   source venv/bin/activate"
echo ""
echo "2. Start data collection:"
echo "   python training/data_collection.py"
echo ""
echo "3. Label your data (use Label Studio or manual labeling)"
echo ""
echo "4. Train your first model:"
echo "   python training/train_model.py"
echo ""
echo "5. View experiments in MLflow:"
echo "   mlflow ui"
echo "   Then open: http://localhost:5000"
echo ""
echo "6. Evaluate model:"
echo "   python training/evaluate_model.py"
echo ""
echo "📖 For detailed instructions, see: training/README.md"
echo ""
