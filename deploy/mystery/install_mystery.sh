#!/bin/bash

#############################################################################
# Mystery Machine Installation Script
# RAM-heavy machine with 100GB+ RAM
# Installs: ChromaDB server only (minimal dependencies)
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
REQUIRED_RAM_GB=16  # Minimum (100GB+ recommended)
CHROMADB_DATA_DIR="${HOME}/chromadb_data"
CHROMADB_LOGS_DIR="${HOME}/chromadb_logs"
CHROMADB_PORT="${CHROMA_PORT:-8000}"  # Default to 8000, can be overridden

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Mystery Machine Installation Script${NC}"
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
        echo "     sudo apt-get install python3-pip python3-venv curl wget htop"
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

# Check RAM
TOTAL_RAM_GB=$(free -g | awk '/^Mem:/{print $2}')
if [ "$TOTAL_RAM_GB" -ge "$REQUIRED_RAM_GB" ]; then
    print_success "RAM: ${TOTAL_RAM_GB}GB available"
else
    print_warning "Only ${TOTAL_RAM_GB}GB RAM detected (recommended: 100GB+)"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check disk space
AVAILABLE_SPACE=$(df "$HOME" | tail -1 | awk '{print int($4/1024/1024)}')
if [ "$AVAILABLE_SPACE" -ge 50 ]; then
    print_success "Disk space: ${AVAILABLE_SPACE}GB available"
else
    print_warning "Only ${AVAILABLE_SPACE}GB available (recommended: 50GB+ for ChromaDB)"
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
        curl \
        wget \
        htop

    print_success "System dependencies installed"
else
    print_warning "Skipping system dependencies (no sudo access)"
    echo "Make sure these are installed: python3-pip python3-venv curl wget htop"
fi

#############################################################################
# Python Virtual Environment
#############################################################################

print_step "Setting up Python virtual environment..."

VENV_PATH="${HOME}/chromadb_venv"

if [ -d "$VENV_PATH" ]; then
    print_warning "Virtual environment already exists at $VENV_PATH"
else
    python3 -m venv "$VENV_PATH"
    print_success "Virtual environment created"
fi

source "$VENV_PATH/bin/activate"

# Upgrade pip
pip install --upgrade pip setuptools wheel

print_success "Python virtual environment ready"

#############################################################################
# Install ChromaDB
#############################################################################

print_step "Installing ChromaDB..."

pip install chromadb

print_success "ChromaDB installed"

# Verify installation
CHROMA_VERSION=$(python -c "import chromadb; print(chromadb.__version__)" 2>/dev/null || echo "unknown")
echo "ChromaDB version: $CHROMA_VERSION"

#############################################################################
# Directory Structure
#############################################################################

print_step "Creating directory structure..."

mkdir -p "$CHROMADB_DATA_DIR"
mkdir -p "$CHROMADB_LOGS_DIR"

print_success "Directory structure created"
echo "Data directory: $CHROMADB_DATA_DIR"
echo "Logs directory: $CHROMADB_LOGS_DIR"

#############################################################################
# Firewall Configuration
#############################################################################

if [ "$SUDO_AVAILABLE" = true ]; then
    print_step "Configuring firewall..."

    read -p "Enter ChromaDB port (default: 8000): " USER_PORT
    CHROMADB_PORT="${USER_PORT:-8000}"

    if check_command ufw; then
        sudo ufw allow "${CHROMADB_PORT}/tcp"
        print_success "Firewall configured (port ${CHROMADB_PORT} opened)"
    else
        print_warning "ufw not found, skipping firewall configuration"
        echo "Make sure port ${CHROMADB_PORT} is accessible from M3 machine"
    fi
else
    print_warning "Skipping firewall configuration (requires sudo)"
    echo "To configure manually: sudo ufw allow ${CHROMADB_PORT}/tcp"
fi

#############################################################################
# Systemd Service Setup
#############################################################################

if [ "$SUDO_AVAILABLE" = true ]; then
    print_step "Setting up systemd service..."

    read -p "Install ChromaDB as systemd service for auto-start? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Create service file
        sudo tee /etc/systemd/system/chromadb.service > /dev/null <<EOF
[Unit]
Description=ChromaDB Vector Database Server
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$HOME
Environment="PATH=$VENV_PATH/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=$VENV_PATH/bin/chroma run --host 0.0.0.0 --port $CHROMADB_PORT --path $CHROMADB_DATA_DIR
Restart=always
RestartSec=10
StandardOutput=append:$CHROMADB_LOGS_DIR/chromadb.log
StandardError=append:$CHROMADB_LOGS_DIR/chromadb.log

[Install]
WantedBy=multi-user.target
EOF

        sudo systemctl daemon-reload
        sudo systemctl enable chromadb
        
        print_success "ChromaDB service installed"
        
        read -p "Start ChromaDB service now? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            sudo systemctl start chromadb
            sleep 3
            
            if sudo systemctl is-active --quiet chromadb; then
                print_success "ChromaDB service is running"
            else
                print_error "ChromaDB service failed to start"
                echo "Check logs: sudo journalctl -u chromadb -n 50"
            fi
        fi
    else
        print_success "Skipped systemd service installation"
        echo "To start ChromaDB manually:"
        echo "  source $VENV_PATH/bin/activate"
        echo "  chroma run --host 0.0.0.0 --port $CHROMADB_PORT --path $CHROMADB_DATA_DIR"
    fi
else
    print_warning "Skipping systemd service installation (requires sudo)"
    echo "To install manually later, see: deploy/mystery/systemd/chromadb.service"
    echo ""
    echo "To start ChromaDB manually:"
    echo "  source $VENV_PATH/bin/activate"
    echo "  chroma run --host 0.0.0.0 --port $CHROMADB_PORT --path $CHROMADB_DATA_DIR"
fi

#############################################################################
# Test ChromaDB Server
#############################################################################

print_step "Testing ChromaDB server..."

sleep 2

if curl -s http://localhost:${CHROMADB_PORT}/api/v1/heartbeat &> /dev/null; then
    print_success "ChromaDB server is responding on port ${CHROMADB_PORT}"
    
    # Get server info
    echo -e "\nServer Information:"
    curl -s http://localhost:${CHROMADB_PORT}/api/v1/heartbeat | python3 -m json.tool 2>/dev/null || echo "Heartbeat OK"
else
    print_warning "Cannot connect to ChromaDB server on port ${CHROMADB_PORT}"
    echo "If you installed as a service, check: sudo systemctl status chromadb"
    echo "Otherwise, start manually with the command shown above"
fi

#############################################################################
# Network Information
#############################################################################

print_step "Network configuration..."

echo -e "\nMystery machine IP addresses:"
hostname -I

echo -e "\nProvide one of these IP addresses to M3 machine configuration"
echo "The M3 machine will connect to: http://MYSTERY_IP:8000"

#############################################################################
# Installation Complete
#############################################################################

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Installation Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}ChromaDB Server Information:${NC}"
echo "  Host: 0.0.0.0 (all interfaces)"
echo "  Port: ${CHROMADB_PORT}"
echo "  Data directory: $CHROMADB_DATA_DIR"
echo "  Logs directory: $CHROMADB_LOGS_DIR"
echo ""
echo -e "${BLUE}Service Management:${NC}"
echo "  Start:   sudo systemctl start chromadb"
echo "  Stop:    sudo systemctl stop chromadb"
echo "  Restart: sudo systemctl restart chromadb"
echo "  Status:  sudo systemctl status chromadb"
echo "  Logs:    sudo journalctl -u chromadb -f"
echo ""
echo -e "${BLUE}Manual Start:${NC}"
echo "  source $VENV_PATH/bin/activate"
echo "  chroma run --host 0.0.0.0 --port ${CHROMADB_PORT} --path $CHROMADB_DATA_DIR"
echo ""
echo -e "${BLUE}Testing from M3:${NC}"
echo "  curl http://MYSTERY_IP:${CHROMADB_PORT}/api/v1/heartbeat"
echo ""
echo -e "${BLUE}Next Steps:${NC}"
echo "1. Note the IP address shown above"
echo "2. Configure M3 machine with this IP"
echo "3. Ensure firewall allows connections from M3"
echo "4. Monitor ChromaDB: htop or journalctl -u chromadb -f"
echo ""
echo -e "${BLUE}Documentation:${NC}"
echo "- Mystery Setup: deploy/mystery/README_MYSTERY.md"
echo "- Deployment Guide: deploy/README.md"
echo ""

# Save installation log
INSTALL_LOG="${HOME}/chromadb_install_$(date +%Y%m%d_%H%M%S).log"
cat > "$INSTALL_LOG" <<EOF
Mystery Machine Installation Log
================================
Date: $(date)
Python: $PYTHON_VERSION
ChromaDB: $CHROMA_VERSION
RAM: ${TOTAL_RAM_GB}GB
Port: ${CHROMADB_PORT}
Data Dir: $CHROMADB_DATA_DIR
Logs Dir: $CHROMADB_LOGS_DIR
IP Addresses: $(hostname -I)
EOF

print_success "Installation log saved to: $INSTALL_LOG"

