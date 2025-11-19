#!/bin/bash
# Startup script for AI Research Processor Web Application on M3

set -e

echo "🚀 Starting AI Research Processor Web Application"
echo "================================================"

# Check if running on M3 (optional - adapt to your setup)
echo "✓ Deployment Target: M3 Machine"

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p data temp_sessions logs nginx/ssl

# Check if .env.production exists
if [ ! -f .env.production ]; then
    echo "⚠️  .env.production not found. Copying from example..."
    cp .env.production.example .env.production
    echo "⚠️  Please edit .env.production with actual values before running!"
    exit 1
fi

# Check ChromaDB connectivity (Mystery machine)
echo "🔍 Checking ChromaDB connection..."
source .env.production
if curl -s "http://${CHROMA_HOST}:${CHROMA_PORT}/api/v1/heartbeat" > /dev/null; then
    echo "✓ ChromaDB is accessible at ${CHROMA_HOST}:${CHROMA_PORT}"
else
    echo "❌ Cannot connect to ChromaDB at ${CHROMA_HOST}:${CHROMA_PORT}"
    echo "   Make sure ChromaDB is running on Mystery machine"
    exit 1
fi

# Check vLLM service (M3 local)
echo "🔍 Checking vLLM service..."
if curl -s "http://localhost:11434/v1/models" > /dev/null 2>&1; then
    echo "✓ vLLM service is running on M3"
else
    echo "⚠️  vLLM service not detected on port 11434"
    echo "   Make sure vLLM/Ollama is running if using local LLM"
fi

# Build and start services
echo "🏗️  Building Docker images..."
docker-compose -f docker-compose.prod.yml build

echo "🚀 Starting services..."
docker-compose -f docker-compose.prod.yml up -d

echo ""
echo "✅ Application started successfully!"
echo ""
echo "📊 Service Status:"
docker-compose -f docker-compose.prod.yml ps

echo ""
echo "🌐 Access the application:"
echo "   Frontend: http://localhost (or your configured domain)"
echo "   Backend API: http://localhost/api/"
echo "   API Docs: http://localhost/api/docs"
echo ""
echo "📝 View logs:"
echo "   docker-compose -f docker-compose.prod.yml logs -f"
echo ""
echo "🛑 Stop services:"
echo "   docker-compose -f docker-compose.prod.yml down"

