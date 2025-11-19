#!/bin/bash

#############################################################################
# M3 Machine - Start Services Script
# Starts vLLM server and optionally other services
#############################################################################

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}M3 Machine - Service Starter${NC}"
echo -e "${BLUE}========================================${NC}\n"

# Source environment if it exists
if [ -f "$PROJECT_ROOT/.env" ]; then
    export $(grep -v '^#' "$PROJECT_ROOT/.env" | xargs)
    echo -e "${GREEN}✅${NC} Loaded environment from .env"
fi

# Activate virtual environment
if [ -f "$PROJECT_ROOT/.venv/bin/activate" ]; then
    source "$PROJECT_ROOT/.venv/bin/activate"
    echo -e "${GREEN}✅${NC} Activated virtual environment"
else
    echo -e "${RED}❌${NC} Virtual environment not found at $PROJECT_ROOT/.venv"
    echo "Run install_m3.sh first"
    exit 1
fi

# Default values
MODEL_NAME="${LLM_MODEL_NAME:-meta-llama/Meta-Llama-3.1-70B-Instruct}"
GPU_MEM="${GPU_MEMORY_UTILIZATION:-0.9}"
MAX_LEN="${MAX_MODEL_LEN:-8192}"
TENSOR_PARALLEL="${TENSOR_PARALLEL_SIZE:-1}"

echo ""
echo "Configuration:"
echo "  Model: $MODEL_NAME"
echo "  GPU Memory Utilization: $GPU_MEM"
echo "  Max Model Length: $MAX_LEN"
echo "  Tensor Parallel Size: $TENSOR_PARALLEL"
echo ""

# Check if vLLM is already running
if curl -s http://localhost:11434/v1/models &> /dev/null; then
    echo -e "${YELLOW}⚠️${NC}  vLLM server is already running on port 11434"
    read -p "Stop and restart? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        pkill -f "vllm.entrypoints.openai.api_server"
        sleep 3
    else
        exit 0
    fi
fi

# Start vLLM server
echo -e "\n${GREEN}==>${NC} Starting vLLM server..."

# Create logs directory
mkdir -p "$PROJECT_ROOT/data/logs"

# Start vLLM in background with logging
nohup python -m vllm.entrypoints.openai.api_server \
    --model "$MODEL_NAME" \
    --host 0.0.0.0 \
    --port 11434 \
    --dtype auto \
    --gpu-memory-utilization "$GPU_MEM" \
    --max-model-len "$MAX_LEN" \
    --tensor-parallel-size "$TENSOR_PARALLEL" \
    > "$PROJECT_ROOT/data/logs/vllm.log" 2>&1 &

VLLM_PID=$!

echo "vLLM server starting with PID: $VLLM_PID"
echo "Waiting for server to be ready..."

# Wait for server to be ready
MAX_WAIT=120
WAIT_COUNT=0
while [ $WAIT_COUNT -lt $MAX_WAIT ]; do
    if curl -s http://localhost:11434/v1/models &> /dev/null; then
        echo -e "${GREEN}✅${NC} vLLM server is ready!"
        echo ""
        echo "Server information:"
        curl -s http://localhost:11434/v1/models | python3 -m json.tool 2>/dev/null || echo "Server responding"
        break
    fi
    sleep 2
    WAIT_COUNT=$((WAIT_COUNT + 2))
    echo -n "."
done

if [ $WAIT_COUNT -ge $MAX_WAIT ]; then
    echo -e "\n${RED}❌${NC} Server failed to start within ${MAX_WAIT} seconds"
    echo "Check logs: tail -f $PROJECT_ROOT/data/logs/vllm.log"
    exit 1
fi

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}Services Started Successfully!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "vLLM Server:"
echo "  PID: $VLLM_PID"
echo "  URL: http://localhost:11434/v1"
echo "  Log: $PROJECT_ROOT/data/logs/vllm.log"
echo ""
echo "Monitoring:"
echo "  GPU: watch nvidia-smi"
echo "  Logs: tail -f $PROJECT_ROOT/data/logs/vllm.log"
echo ""
echo "Stop services:"
echo "  pkill -f 'vllm.entrypoints.openai.api_server'"
echo ""
echo "Test API:"
echo "  curl http://localhost:11434/v1/models"
echo ""

