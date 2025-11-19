#!/bin/bash
# Stop script for AI Research Processor Web Application

set -e

echo "🛑 Stopping AI Research Processor Web Application"
echo "================================================"

docker-compose -f docker-compose.prod.yml down

echo "✅ Services stopped successfully"

