#!/bin/bash

#############################################################################
# Mystery Machine - Start Services Script
# Starts ChromaDB server
#############################################################################

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
VENV_PATH="${HOME}/chromadb_venv"
CHROMADB_DATA_DIR="${HOME}/chromadb_data"
CHROMADB_LOGS_DIR="${HOME}/chromadb_logs"
CHROMADB_PORT="${CHROMA_PORT:-8000}"  # Default to 8000, can be overridden by env var

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Mystery Machine - Service Starter${NC}"
echo -e "${BLUE}========================================${NC}\n"

# Check if virtual environment exists
if [ ! -d "$VENV_PATH" ]; then
    echo -e "${RED}❌${NC} Virtual environment not found at $VENV_PATH"
    echo "Run install_mystery.sh first"
    exit 1
fi

# Activate virtual environment
source "$VENV_PATH/bin/activate"
echo -e "${GREEN}✅${NC} Activated virtual environment"

# Check if ChromaDB is already running
if curl -s http://localhost:${CHROMADB_PORT}/api/v1/heartbeat &> /dev/null; then
    echo -e "${YELLOW}⚠️${NC}  ChromaDB server is already running on port ${CHROMADB_PORT}"
    read -p "Stop and restart? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        pkill -f "chroma run"
        sleep 3
    else
        exit 0
    fi
fi

# Create directories
mkdir -p "$CHROMADB_DATA_DIR"
mkdir -p "$CHROMADB_LOGS_DIR"

# Start ChromaDB server
echo -e "\n${GREEN}==>${NC} Starting ChromaDB server..."
echo "  Host: 0.0.0.0"
echo "  Port: $CHROMADB_PORT"
echo "  Data: $CHROMADB_DATA_DIR"

# Start ChromaDB in background with logging
nohup chroma run \
    --host 0.0.0.0 \
    --port "$CHROMADB_PORT" \
    --path "$CHROMADB_DATA_DIR" \
    > "$CHROMADB_LOGS_DIR/chromadb.log" 2>&1 &

CHROMA_PID=$!

echo "ChromaDB server starting with PID: $CHROMA_PID"
echo "Waiting for server to be ready..."

# Wait for server to be ready
MAX_WAIT=30
WAIT_COUNT=0
while [ $WAIT_COUNT -lt $MAX_WAIT ]; do
    if curl -s http://localhost:${CHROMADB_PORT}/api/v1/heartbeat &> /dev/null; then
        echo -e "${GREEN}✅${NC} ChromaDB server is ready!"
        echo ""
        echo "Server information:"
        curl -s http://localhost:${CHROMADB_PORT}/api/v1/heartbeat | python3 -m json.tool 2>/dev/null || echo "Heartbeat OK"
        break
    fi
    sleep 1
    WAIT_COUNT=$((WAIT_COUNT + 1))
    echo -n "."
done

if [ $WAIT_COUNT -ge $MAX_WAIT ]; then
    echo -e "\n${RED}❌${NC} Server failed to start within ${MAX_WAIT} seconds"
    echo "Check logs: tail -f $CHROMADB_LOGS_DIR/chromadb.log"
    exit 1
fi

# Get IP addresses
echo ""
echo "IP Addresses:"
hostname -I | tr ' ' '\n' | grep -v '^$'

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}ChromaDB Server Started Successfully!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "Server Information:"
echo "  PID: $CHROMA_PID"
echo "  Host: 0.0.0.0 (all interfaces)"
echo "  Port: $CHROMADB_PORT"
echo "  Data: $CHROMADB_DATA_DIR"
echo "  Log: $CHROMADB_LOGS_DIR/chromadb.log"
echo ""
echo "Monitoring:"
echo "  RAM: watch free -h"
echo "  Logs: tail -f $CHROMADB_LOGS_DIR/chromadb.log"
echo ""
echo "Stop service:"
echo "  pkill -f 'chroma run'"
echo ""
echo "Test from M3:"
echo "  curl http://MYSTERY_IP:${CHROMADB_PORT}/api/v1/heartbeat"
echo ""

