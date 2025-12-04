#!/bin/bash

#############################################################################
# M3 Machine Installation Script
# Main processing machine with 198GB VRAM and 1.7TB storage
# Installs: Python environment, vLLM, dependencies, directory structure
#############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REQUIRED_PYTHON_VERSION="3.8"
REQUIRED_DISK_SPACE_GB=100
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
VENV_PATH="$PROJECT_ROOT/.venv"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}M3 Machine Installation Script${NC}"
echo -e "${BLUE}========================================${NC}\n"

#############################################################################
# Helper Functions
#############################################################################

print_step() {
    echo -e "\n${GREEN}==>${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

check_command() {
    if command -v "$1" &> /dev/null; then
        return 0
    else
        return 1
    fi
}

#############################################################################
# Pre-Installation Checks
#############################################################################

print_step "Performing pre-installation checks..."

# Check if running on Ubuntu/Debian
if [ -f /etc/os-release ]; then
    . /etc/os-release
    echo "OS: $NAME $VERSION"
else
    print_error "Cannot detect OS version"
    exit 1
fi

# Check sudo access
if sudo -n true 2>/dev/null; then
    print_success "Passwordless sudo available"
    SUDO_AVAILABLE=true
else
    print_warning "This script requires sudo privileges for system package installation"
    echo "You may be prompted for your password during installation"
    
    # Test if user can sudo at all
    if sudo -v; then
        print_success "Sudo privileges confirmed"
        SUDO_AVAILABLE=true
        # Keep sudo session alive
        while true; do sudo -n true; sleep 60; kill -0 "$$" || exit; done 2>/dev/null &
    else
        print_error "Cannot obtain sudo privileges"
        echo "Options:"
        echo "  1. Run as a user with sudo privileges"
        echo "  2. Install system dependencies manually:"
        echo "     sudo apt-get install python3-pip python3-venv build-essential git curl wget htop"
        read -p "Continue without system dependencies? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
        SUDO_AVAILABLE=false
    fi
fi

# Check Python version
if check_command python3; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)
    
    if [ "$PYTHON_MAJOR" -ge 3 ] && [ "$PYTHON_MINOR" -ge 8 ]; then
        print_success "Python $PYTHON_VERSION detected"
    else
        print_error "Python 3.8+ required, found $PYTHON_VERSION"
        exit 1
    fi
else
    print_error "Python 3 not found"
    exit 1
fi

# Check CUDA/NVIDIA drivers
if check_command nvidia-smi; then
    print_success "NVIDIA drivers detected"
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
else
    print_warning "NVIDIA drivers not found. vLLM requires CUDA-capable GPU"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check disk space
AVAILABLE_SPACE=$(df "$PROJECT_ROOT" | tail -1 | awk '{print int($4/1024/1024)}')
if [ "$AVAILABLE_SPACE" -ge "$REQUIRED_DISK_SPACE_GB" ]; then
    print_success "Disk space: ${AVAILABLE_SPACE}GB available"
else
    print_warning "Only ${AVAILABLE_SPACE}GB available (recommended: ${REQUIRED_DISK_SPACE_GB}GB+)"
fi

#############################################################################
# System Dependencies
#############################################################################

if [ "$SUDO_AVAILABLE" = true ]; then
    print_step "Installing system dependencies..."

    sudo apt-get update
    sudo apt-get install -y \
        python3-pip \
        python3-venv \
        build-essential \
        git \
        curl \
        wget \
        htop \
        nvtop \
        tmux \
        rsync

    print_success "System dependencies installed"
else
    print_warning "Skipping system dependencies (no sudo access)"
    echo "Make sure these are installed: python3-pip python3-venv build-essential git curl wget htop"
fi

#############################################################################
# Python Virtual Environment
#############################################################################

print_step "Setting up Python virtual environment..."

if [ -d "$VENV_PATH" ]; then
    print_warning "Virtual environment already exists at $VENV_PATH"
    read -p "Remove and recreate? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf "$VENV_PATH"
    else
        print_success "Using existing virtual environment"
    fi
fi

if [ ! -d "$VENV_PATH" ]; then
    python3 -m venv "$VENV_PATH"
    print_success "Virtual environment created"
fi

source "$VENV_PATH/bin/activate"

# Upgrade pip
pip install --upgrade pip setuptools wheel

print_success "Python virtual environment ready"

#############################################################################
# Python Dependencies
#############################################################################

print_step "Installing Python dependencies..."

cd "$PROJECT_ROOT"

# Install base requirements
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    print_success "Base dependencies installed"
else
    print_error "requirements.txt not found"
    exit 1
fi

# Install vLLM (GPU-optimized)
print_step "Installing vLLM..."
pip install vllm

# Install additional dependencies for M3
pip install \
    python-dotenv \
    requests \
    httpx

print_success "All Python dependencies installed"

#############################################################################
# Directory Structure
#############################################################################

print_step "Creating directory structure..."

# Data directories
mkdir -p "$PROJECT_ROOT/data/embeddings/xrvix_embeddings"/{biorxiv,medrxiv,pubmed,semantic_scholar}
mkdir -p "$PROJECT_ROOT/data/scraped_data"
mkdir -p "$PROJECT_ROOT/data/logs"
mkdir -p "$PROJECT_ROOT/data/backups"
mkdir -p "$PROJECT_ROOT/hypothesis_export"

# Model storage (outside project for large models)
MODEL_DIR="${HOME}/models"
mkdir -p "$MODEL_DIR"
mkdir -p "${HOME}/workspace/temp"

print_success "Directory structure created"

#############################################################################
# Environment Configuration
#############################################################################

print_step "Configuring environment..."

ENV_FILE="$PROJECT_ROOT/.env"
ENV_TEMPLATE="$PROJECT_ROOT/deploy/m3/env.m3.example"

if [ -f "$ENV_FILE" ]; then
    print_warning ".env file already exists"
    read -p "Backup and create new from template? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cp "$ENV_FILE" "$ENV_FILE.backup"
        print_success "Backed up existing .env to .env.backup"
    fi
else
    if [ -f "$ENV_TEMPLATE" ]; then
        cp "$ENV_TEMPLATE" "$ENV_FILE"
        print_success "Created .env from template"
    fi
fi

# Prompt for configuration
echo ""
echo -e "${BLUE}=== Configuration ===${NC}"
read -p "Enter Mystery machine IP address: " MYSTERY_IP
read -p "Enter ChromaDB port on Mystery (default: 8000): " MYSTERY_PORT
MYSTERY_PORT="${MYSTERY_PORT:-8000}"
read -p "Enter Google API key: " GOOGLE_API_KEY
read -p "Enter Gemini API key (or press Enter to use same): " GEMINI_API_KEY
if [ -z "$GEMINI_API_KEY" ]; then
    GEMINI_API_KEY="$GOOGLE_API_KEY"
fi
read -p "Enter NCBI API key (optional, press Enter to skip): " NCBI_API_KEY

# Update .env file
if [ -f "$ENV_FILE" ]; then
    sed -i "s/MYSTERY_IP_ADDRESS/$MYSTERY_IP/g" "$ENV_FILE"
    sed -i "s/CHROMA_PORT=8000/CHROMA_PORT=$MYSTERY_PORT/g" "$ENV_FILE"
    sed -i "s/your_google_api_key_here/$GOOGLE_API_KEY/g" "$ENV_FILE"
    sed -i "s/your_gemini_api_key_here/$GEMINI_API_KEY/g" "$ENV_FILE"
    if [ -n "$NCBI_API_KEY" ]; then
        sed -i "s/your_ncbi_api_key_here/$NCBI_API_KEY/g" "$ENV_FILE"
    fi
    print_success "Environment configured"
fi

#############################################################################
# vLLM Model Selection
#############################################################################

print_step "Selecting LLM model..."

echo ""
echo "Available models for 198GB VRAM:"
echo "1) meta-llama/Meta-Llama-3.1-70B-Instruct (Recommended, ~140GB)"
echo "2) Qwen/Qwen2.5-72B-Instruct (Strong reasoning, ~145GB)"
echo "3) mistralai/Mixtral-8x22B-Instruct-v0.1 (MoE, ~160GB)"
echo "4) meta-llama/Meta-Llama-3.1-8B-Instruct (Smaller, ~16GB)"
echo "5) Custom (enter model name)"

read -p "Select model (1-5): " MODEL_CHOICE

case $MODEL_CHOICE in
    1)
        MODEL_NAME="meta-llama/Meta-Llama-3.1-70B-Instruct"
        ;;
    2)
        MODEL_NAME="Qwen/Qwen2.5-72B-Instruct"
        ;;
    3)
        MODEL_NAME="mistralai/Mixtral-8x22B-Instruct-v0.1"
        ;;
    4)
        MODEL_NAME="meta-llama/Meta-Llama-3.1-8B-Instruct"
        ;;
    5)
        read -p "Enter model name: " MODEL_NAME
        ;;
    *)
        MODEL_NAME="meta-llama/Meta-Llama-3.1-70B-Instruct"
        print_warning "Invalid choice, using default: $MODEL_NAME"
        ;;
esac

# Update config file
sed -i "s|meta-llama/Meta-Llama-3.1-70B-Instruct|$MODEL_NAME|g" "$PROJECT_ROOT/deploy/m3/config_m3.json"
sed -i "s|meta-llama/Meta-Llama-3.1-70B-Instruct|$MODEL_NAME|g" "$ENV_FILE"

print_success "Model configured: $MODEL_NAME"

#############################################################################
# Systemd Service Setup (Optional)
#############################################################################

if [ "$SUDO_AVAILABLE" = true ]; then
    print_step "Setting up systemd services (optional)..."

    read -p "Install vLLM as systemd service for auto-start? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        SERVICE_FILE="$PROJECT_ROOT/deploy/m3/systemd/vllm.service"
        
        # Update service file with actual paths
        sed "s|/home/user|$HOME|g" "$SERVICE_FILE" > "/tmp/vllm.service"
        sed -i "s|AHGA|$(basename $PROJECT_ROOT)|g" "/tmp/vllm.service"
        sed -i "s|%USER%|$USER|g" "/tmp/vllm.service"
        sed -i "s|meta-llama/Meta-Llama-3.1-70B-Instruct|$MODEL_NAME|g" "/tmp/vllm.service"
        
        sudo cp "/tmp/vllm.service" "/etc/systemd/system/vllm.service"
        sudo systemctl daemon-reload
        sudo systemctl enable vllm
        
        print_success "vLLM service installed"
        print_warning "Start with: sudo systemctl start vllm"
    else
        print_success "Skipped systemd service installation"
    fi
else
    print_warning "Skipping systemd service installation (requires sudo)"
    echo "To install manually later, see: deploy/m3/systemd/vllm.service"
fi

#############################################################################
# Connectivity Test
#############################################################################

print_step "Testing connectivity to Mystery machine..."

if [ -n "$MYSTERY_IP" ]; then
    if timeout 5 bash -c "curl -s http://$MYSTERY_IP:$MYSTERY_PORT/api/v1/heartbeat" &> /dev/null; then
        print_success "Successfully connected to ChromaDB on Mystery ($MYSTERY_IP:$MYSTERY_PORT)"
    else
        print_warning "Cannot connect to ChromaDB on Mystery ($MYSTERY_IP:$MYSTERY_PORT)"
        echo "Make sure ChromaDB server is running on Mystery machine"
    fi
fi

#############################################################################
# SSL/HTTPS Setup with Let's Encrypt (Optional)
#############################################################################

if [ "$SUDO_AVAILABLE" = true ]; then
    print_step "SSL/HTTPS Configuration..."

    read -p "Set up HTTPS with Let's Encrypt? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Install Certbot
        print_step "Installing Certbot for Let's Encrypt..."
        sudo apt-get update
        sudo apt-get install -y certbot python3-certbot-nginx

        read -p "Enter your domain name (e.g., research.example.com): " DOMAIN_NAME
        
        if [ -n "$DOMAIN_NAME" ]; then
            # Create SSL directory
            mkdir -p "$PROJECT_ROOT/nginx/ssl"
            
            # Create certbot webroot directory
            sudo mkdir -p /var/www/certbot
            
            echo ""
            echo -e "${BLUE}To obtain SSL certificate, run:${NC}"
            echo "sudo certbot certonly --webroot -w /var/www/certbot -d $DOMAIN_NAME"
            echo ""
            echo -e "${BLUE}Then copy certificates to nginx/ssl/:${NC}"
            echo "sudo cp /etc/letsencrypt/live/$DOMAIN_NAME/fullchain.pem $PROJECT_ROOT/nginx/ssl/"
            echo "sudo cp /etc/letsencrypt/live/$DOMAIN_NAME/privkey.pem $PROJECT_ROOT/nginx/ssl/"
            echo "sudo chown \$USER:users $PROJECT_ROOT/nginx/ssl/*.pem"
            echo ""
            echo -e "${BLUE}Set up auto-renewal:${NC}"
            echo "sudo certbot renew --dry-run"
            echo ""
            
            # Save domain to config
            echo "DOMAIN_NAME=$DOMAIN_NAME" >> "$ENV_FILE"
            
            print_success "Certbot installed. Follow the steps above to complete SSL setup."
        fi
    else
        print_warning "Skipping SSL setup. You can set it up later with Certbot."
    fi
fi

#############################################################################
# Generate SECRET_KEY
#############################################################################

print_step "Generating secure SECRET_KEY..."
SECRET_KEY=$(openssl rand -hex 32)
echo "SECRET_KEY=$SECRET_KEY" >> "$ENV_FILE"
echo "ENVIRONMENT=production" >> "$ENV_FILE"
print_success "SECRET_KEY generated and added to .env"

#############################################################################
# Installation Complete
#############################################################################

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Installation Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}Next Steps:${NC}"
echo "1. Activate virtual environment: source .venv/bin/activate"
echo "2. Start vLLM server: ./deploy/m3/start_services.sh"
echo "   OR: sudo systemctl start vllm (if installed as service)"
echo "3. Verify configuration: python -m src.cli.main config show --profile m3"
echo "4. Test connectivity: python scripts/test_distributed_setup.py"
echo "5. Run data pipeline: python -m src.cli.main scrape full"
echo "6. Start web application: ./scripts/start_web.sh"
echo ""
echo -e "${BLUE}Security:${NC}"
echo "- SECRET_KEY has been generated automatically"
echo "- Set up HTTPS with Let's Encrypt for production"
echo "- API keys should be set in .env (not keys.json)"
echo ""
echo -e "${BLUE}Important:${NC}"
echo "- Edit .env file to update API keys if needed"
echo "- Ensure Mystery machine is running ChromaDB server"
echo "- Monitor GPU usage with: watch nvidia-smi"
echo ""
echo -e "${BLUE}Documentation:${NC}"
echo "- M3 Setup: deploy/m3/README_M3.md"
echo "- Deployment Guide: deploy/README.md"
echo ""

# Save installation log
INSTALL_LOG="$PROJECT_ROOT/deploy/m3/install_$(date +%Y%m%d_%H%M%S).log"
echo "Installation completed at $(date)" > "$INSTALL_LOG"
echo "Python: $PYTHON_VERSION" >> "$INSTALL_LOG"
echo "Model: $MODEL_NAME" >> "$INSTALL_LOG"
echo "Mystery IP: $MYSTERY_IP:$MYSTERY_PORT" >> "$INSTALL_LOG"

print_success "Installation log saved to: $INSTALL_LOG"

