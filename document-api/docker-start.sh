#!/bin/bash
# Script to start Document API with Docker Compose

echo "🚀 Starting Document API with Docker..."
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop first."
    exit 1
fi

# Load environment variables from .env.docker if it exists
if [ -f .env.docker ]; then
    export $(cat .env.docker | grep -v '^#' | xargs)
fi

# Start the services
echo "📦 Building and starting containers..."
docker-compose up -d --build

# Wait for services to be healthy
echo ""
echo "⏳ Waiting for services to be ready..."
sleep 5

# Check if containers are running
if docker-compose ps | grep -q "Up"; then
    echo ""
    echo "✅ Document API is running!"
    echo ""
    echo "📍 API URL: http://localhost:8000"
    echo "📍 API Docs: http://localhost:8000/docs"
    echo "📍 Health Check: http://localhost:8000/health"
    echo ""
    echo "💡 To view logs: docker-compose logs -f"
    echo "💡 To stop: docker-compose down"
    echo "💡 Or use: ./docker-stop.sh"
    echo ""

    # Test the health endpoint
    echo "🏥 Testing health endpoint..."
    sleep 3
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ API is responding!"
        curl -s http://localhost:8000/health | python3 -m json.tool 2>/dev/null || curl -s http://localhost:8000/health
    else
        echo "⚠️  API not responding yet. It may still be starting up."
        echo "   Check logs with: docker-compose logs -f api"
    fi
else
    echo ""
    echo "❌ Failed to start containers. Check logs with:"
    echo "   docker-compose logs"
fi

echo ""
