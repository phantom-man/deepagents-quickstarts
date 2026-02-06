#!/bin/bash

# Environmental Monitoring System - Deployment Script
# This script helps set up and deploy the environmental monitoring system

set -e

echo "🌱 Environmental Monitoring System - Deployment Script"
echo "======================================================"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo "📋 Checking prerequisites..."

if ! command_exists python3; then
    echo "❌ Python 3 is required but not installed. Please install Python 3.9+ first."
    exit 1
fi

if ! command_exists pip; then
    echo "❌ pip is required but not installed. Please install pip first."
    exit 1
fi

echo "✅ Prerequisites check passed"

# Create virtual environment
echo "🐍 Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "🔧 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your actual configuration values"
fi

# Initialize database
echo "🗄️  Initializing database..."
python3 -c "from app.services.database import init_database; import asyncio; asyncio.run(init_database())"

# Run tests
echo "🧪 Running tests..."
python3 -m pytest tests/ -v

# Create logs directory
mkdir -p logs

echo ""
echo "🎉 Deployment completed successfully!"
echo ""
echo "🚀 To start the application:"
echo "   source venv/bin/activate"
echo "   python main.py"
echo ""
echo "📖 API documentation will be available at: http://localhost:8000/docs"
echo "🏥 Health check endpoint: http://localhost:8000/health"
echo ""
echo "📝 Don't forget to:"
echo "   - Configure your .env file with actual API keys"
echo "   - Set up external services (email, SMS, Slack) if needed"
echo "   - Configure sensor data sources"
echo ""
echo "Happy monitoring! 🌍"