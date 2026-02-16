#!/bin/bash
set -e

echo "🚀 Starting Political Bias Detector - Full Stack"
echo "================================================="
echo ""

# Check if Docker is running
echo "📦 Checking Docker..."
if ! docker info > /dev/null 2>&1; then
    echo "⚠️  Docker is not running. Starting Docker Desktop..."
    open -a Docker
    echo "⏳ Waiting for Docker to start (this may take 30-60 seconds)..."
    
    # Wait for Docker to be ready
    counter=0
    until docker info > /dev/null 2>&1; do
        sleep 2
        counter=$((counter + 1))
        if [ $counter -gt 30 ]; then
            echo "❌ Docker failed to start. Please start Docker Desktop manually."
            exit 1
        fi
    done
    echo "✅ Docker is ready!"
else
    echo "✅ Docker is running"
fi

echo ""
echo "🐳 Starting Docker Compose services..."
docker-compose up -d

echo ""
echo "⏳ Waiting for services to be healthy..."
sleep 10

echo ""
echo "📊 Service Status:"
docker-compose ps

echo ""
echo "================================================="
echo "✅ Full Stack is Running!"
echo "================================================="
echo ""
echo "🌐 Access your services:"
echo "   • Frontend (Streamlit):  http://localhost:8501"
echo "   • Backend API:           http://localhost:8000/api/docs"
echo "   • Celery Flower:         http://localhost:5555"
echo "   • MLflow:                http://localhost:5000"
echo ""
echo "📋 Useful commands:"
echo "   • View logs:             docker-compose logs -f"
echo "   • Stop services:         docker-compose down"
echo "   • Restart services:      docker-compose restart"
echo ""
echo "🔍 Check service health:"
echo "   curl http://localhost:8000/health"
echo ""
