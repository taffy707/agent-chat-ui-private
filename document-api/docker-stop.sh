#!/bin/bash
# Script to stop Document API Docker containers

echo "🛑 Stopping Document API containers..."
echo ""

docker-compose down

echo ""
echo "✅ Containers stopped!"
echo ""
echo "💡 To remove all data (including database): docker-compose down -v"
echo "💡 To start again: ./docker-start.sh"
echo ""
