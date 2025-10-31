#!/bin/bash
# Quick setup script for FastAPI Document Upload Service

set -e

echo "🚀 Setting up FastAPI Document Upload Service..."
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo ""
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo ""
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo ""
echo "📦 Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1

# Install dependencies
echo ""
echo "📦 Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "✅ Installation complete!"
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found. Creating from .env.example..."
    cp .env.example .env
    echo ""
    echo "📝 IMPORTANT: Edit .env file with your configuration:"
    echo "   - GCP_PROJECT_ID"
    echo "   - VERTEX_AI_DATA_STORE_ID"
    echo "   - GCS_BUCKET_NAME"
    echo ""
    echo "   nano .env"
    echo ""
else
    echo "✅ .env file exists"
    echo ""
fi

# Check authentication
echo "🔐 Checking Google Cloud authentication..."
if gcloud auth application-default print-access-token &> /dev/null; then
    echo "✅ Google Cloud authentication configured"
else
    echo "⚠️  Google Cloud authentication not found."
    echo ""
    echo "   Run one of these commands:"
    echo "   1. For local development:"
    echo "      gcloud auth application-default login"
    echo ""
    echo "   2. For service account:"
    echo "      export GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json"
    echo ""
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env with your configuration (if not done)"
echo "2. Activate virtual environment: source venv/bin/activate"
echo "3. Start the server: python main.py"
echo "4. Visit http://localhost:8000/docs"
echo ""
