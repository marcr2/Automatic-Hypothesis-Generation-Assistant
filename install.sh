#!/bin/bash

#############################################################################
# AHGA Research Processor - Unified Installer
# Supports: Mystery (ChromaDB), M3 (Processing), Local (Single Machine)
#############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Get project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

#############################################################################
# Helper Functions
#############################################################################

print_banner() {
    clear
    echo -e "${CYAN}"
    echo "╔══════════════════════════════════════════════════════════════════╗"
    echo "║                                                                  ║"
    echo "║     █████╗ ██╗  ██╗ ██████╗  █████╗                             ║"
    echo "║    ██╔══██╗██║  ██║██╔════╝ ██╔══██╗                            ║"
    echo "║    ███████║███████║██║  ███╗███████║                            ║"
    echo "║    ██╔══██║██╔══██║██║   ██║██╔══██║                            ║"
    echo "║    ██║  ██║██║  ██║╚██████╔╝██║  ██║                            ║"
    echo "║    ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝                            ║"
    echo "║                                                                  ║"
    echo "║           Automated Hypothesis Generation Assistant              ║"
    echo "║                      Research Processor                          ║"
    echo "║                                                                  ║"
    echo "╚══════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

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

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

#############################################################################
# Installation Menu
#############################################################################

show_menu() {
    echo ""
    echo -e "${BOLD}Select Installation Type:${NC}"
    echo ""
    echo -e "${MAGENTA}┌─────────────────────────────────────────────────────────────────────┐${NC}"
    echo -e "${MAGENTA}│${NC}                                                                     ${MAGENTA}│${NC}"
    echo -e "${MAGENTA}│${NC}  ${CYAN}[1] Mystery Machine${NC} - Vector Database Server                      ${MAGENTA}│${NC}"
    echo -e "${MAGENTA}│${NC}      └─ ChromaDB only, requires 100GB+ RAM                          ${MAGENTA}│${NC}"
    echo -e "${MAGENTA}│${NC}      └─ Lightweight install, serves vector database to M3           ${MAGENTA}│${NC}"
    echo -e "${MAGENTA}│${NC}                                                                     ${MAGENTA}│${NC}"
    echo -e "${MAGENTA}│${NC}  ${CYAN}[2] M3 Machine${NC} - Main Processing Server                           ${MAGENTA}│${NC}"
    echo -e "${MAGENTA}│${NC}      └─ Full application + vLLM, requires GPU with 16GB+ VRAM       ${MAGENTA}│${NC}"
    echo -e "${MAGENTA}│${NC}      └─ Runs scraping, embedding generation, hypothesis creation    ${MAGENTA}│${NC}"
    echo -e "${MAGENTA}│${NC}                                                                     ${MAGENTA}│${NC}"
    echo -e "${MAGENTA}│${NC}  ${CYAN}[3] Local Development${NC} - Single Machine Setup                      ${MAGENTA}│${NC}"
    echo -e "${MAGENTA}│${NC}      └─ Everything on one machine (uses cloud APIs)                 ${MAGENTA}│${NC}"
    echo -e "${MAGENTA}│${NC}      └─ Good for testing or smaller datasets                        ${MAGENTA}│${NC}"
    echo -e "${MAGENTA}│${NC}                                                                     ${MAGENTA}│${NC}"
    echo -e "${MAGENTA}│${NC}  ${CYAN}[4] Show Architecture Diagram${NC}                                     ${MAGENTA}│${NC}"
    echo -e "${MAGENTA}│${NC}                                                                     ${MAGENTA}│${NC}"
    echo -e "${MAGENTA}│${NC}  ${CYAN}[5] Exit${NC}                                                          ${MAGENTA}│${NC}"
    echo -e "${MAGENTA}│${NC}                                                                     ${MAGENTA}│${NC}"
    echo -e "${MAGENTA}└─────────────────────────────────────────────────────────────────────┘${NC}"
    echo ""
}

show_architecture() {
    echo ""
    echo -e "${BOLD}Distributed Architecture Overview:${NC}"
    echo ""
    echo -e "${BLUE}┌───────────────────────────────────┐       ┌───────────────────────────────────┐${NC}"
    echo -e "${BLUE}│${NC}         ${CYAN}M3 MACHINE${NC}                ${BLUE}│${NC}       ${BLUE}│${NC}       ${CYAN}MYSTERY MACHINE${NC}            ${BLUE}│${NC}"
    echo -e "${BLUE}│${NC}      (Main Processing)            ${BLUE}│${NC}       ${BLUE}│${NC}      (Vector Database)           ${BLUE}│${NC}"
    echo -e "${BLUE}├───────────────────────────────────┤${NC}       ${BLUE}├───────────────────────────────────┤${NC}"
    echo -e "${BLUE}│${NC}                                   ${BLUE}│${NC}       ${BLUE}│${NC}                                   ${BLUE}│${NC}"
    echo -e "${BLUE}│${NC}  ${GREEN}✓${NC} Python Application            ${BLUE}│${NC}       ${BLUE}│${NC}  ${GREEN}✓${NC} ChromaDB Server              ${BLUE}│${NC}"
    echo -e "${BLUE}│${NC}  ${GREEN}✓${NC} vLLM (Local LLM Server)       ${BLUE}│${NC}       ${BLUE}│${NC}                                   ${BLUE}│${NC}"
    echo -e "${BLUE}│${NC}  ${GREEN}✓${NC} Data Scraping                 ${BLUE}│${NC}       ${BLUE}│${NC}  Requirements:                    ${BLUE}│${NC}"
    echo -e "${BLUE}│${NC}  ${GREEN}✓${NC} Embedding Generation          ${BLUE}│${NC}       ${BLUE}│${NC}    - 100GB+ RAM                   ${BLUE}│${NC}"
    echo -e "${BLUE}│${NC}  ${GREEN}✓${NC} Hypothesis Generation         ${BLUE}│${NC}       ${BLUE}│${NC}    - 50GB+ Storage                ${BLUE}│${NC}"
    echo -e "${BLUE}│${NC}                                   ${BLUE}│${NC}       ${BLUE}│${NC}                                   ${BLUE}│${NC}"
    echo -e "${BLUE}│${NC}  Requirements:                    ${BLUE}│${NC}       ${BLUE}│${NC}  Stores:                          ${BLUE}│${NC}"
    echo -e "${BLUE}│${NC}    - GPU with 16GB+ VRAM          ${BLUE}│${NC}       ${BLUE}│${NC}    - Vector embeddings             ${BLUE}│${NC}"
    echo -e "${BLUE}│${NC}    - 100GB+ Storage               ${BLUE}│${NC}       ${BLUE}│${NC}                                   ${BLUE}│${NC}"
    echo -e "${BLUE}│${NC}                                   ${BLUE}│${NC}       ${BLUE}│${NC}                                   ${BLUE}│${NC}"
    echo -e "${BLUE}│${NC}  Stores:                          ${BLUE}│${NC}       ${BLUE}│${NC}                                   ${BLUE}│${NC}"
    echo -e "${BLUE}│${NC}    - Scraped papers               ${BLUE}│${NC}◄──────${BLUE}│${NC}  Port: 8000                       ${BLUE}│${NC}"
    echo -e "${BLUE}│${NC}    - Embeddings (JSON)            ${BLUE}│${NC} API   ${BLUE}│${NC}                                   ${BLUE}│${NC}"
    echo -e "${BLUE}│${NC}    - LLM Models                   ${BLUE}│${NC}       ${BLUE}│${NC}                                   ${BLUE}│${NC}"
    echo -e "${BLUE}│${NC}    - Hypothesis exports           ${BLUE}│${NC}       ${BLUE}│${NC}                                   ${BLUE}│${NC}"
    echo -e "${BLUE}│${NC}                                   ${BLUE}│${NC}       ${BLUE}│${NC}                                   ${BLUE}│${NC}"
    echo -e "${BLUE}└───────────────────────────────────┘${NC}       ${BLUE}└───────────────────────────────────┘${NC}"
    echo ""
    echo -e "${YELLOW}Install Mystery first, then M3. M3 needs Mystery's IP address.${NC}"
    echo ""
    read -p "Press Enter to return to menu..."
}

#############################################################################
# Installation Functions
#############################################################################

install_mystery() {
    print_step "Starting Mystery Machine Installation..."
    echo ""
    echo -e "${CYAN}Mystery Machine Setup:${NC}"
    echo "  - ChromaDB vector database server"
    echo "  - Minimal footprint, maximum RAM utilization"
    echo "  - Will be accessed by M3 machine on port 8000"
    echo ""
    
    if [ -f "$PROJECT_ROOT/deploy/mystery/install_mystery.sh" ]; then
        read -p "Continue with Mystery installation? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            bash "$PROJECT_ROOT/deploy/mystery/install_mystery.sh"
        else
            print_warning "Installation cancelled"
        fi
    else
        print_error "Mystery install script not found at: $PROJECT_ROOT/deploy/mystery/install_mystery.sh"
        exit 1
    fi
}

install_m3() {
    print_step "Starting M3 Machine Installation..."
    echo ""
    echo -e "${CYAN}M3 Machine Setup:${NC}"
    echo "  - Full Python application"
    echo "  - vLLM server for local LLM inference"
    echo "  - Data scraping and processing"
    echo "  - Connects to Mystery machine for vector storage"
    echo ""
    
    if [ -f "$PROJECT_ROOT/deploy/m3/install_m3.sh" ]; then
        read -p "Continue with M3 installation? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            bash "$PROJECT_ROOT/deploy/m3/install_m3.sh"
        else
            print_warning "Installation cancelled"
        fi
    else
        print_error "M3 install script not found at: $PROJECT_ROOT/deploy/m3/install_m3.sh"
        exit 1
    fi
}

install_local() {
    print_step "Starting Local Development Installation..."
    echo ""
    echo -e "${CYAN}Local Development Setup:${NC}"
    echo "  - Everything on one machine"
    echo "  - Uses cloud APIs (Google/OpenAI) for LLM"
    echo "  - Local ChromaDB instance"
    echo "  - Good for testing and smaller datasets"
    echo ""
    
    read -p "Continue with local installation? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_warning "Installation cancelled"
        return
    fi
    
    # Pre-installation checks
    print_step "Performing pre-installation checks..."
    
    # Check Python
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        print_success "Python $PYTHON_VERSION detected"
    else
        print_error "Python 3 not found. Please install Python 3.8+"
        exit 1
    fi
    
    # Check for existing venv
    VENV_PATH="$PROJECT_ROOT/.venv"
    
    if [ -d "$VENV_PATH" ]; then
        print_warning "Virtual environment already exists at $VENV_PATH"
        read -p "Remove and recreate? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf "$VENV_PATH"
        else
            print_info "Using existing virtual environment"
        fi
    fi
    
    # Create virtual environment
    if [ ! -d "$VENV_PATH" ]; then
        print_step "Creating virtual environment..."
        python3 -m venv "$VENV_PATH"
        print_success "Virtual environment created"
    fi
    
    # Activate and install
    print_step "Activating virtual environment..."
    source "$VENV_PATH/bin/activate"
    
    print_step "Upgrading pip..."
    pip install --upgrade pip setuptools wheel
    
    print_step "Installing Python dependencies..."
    if [ -f "$PROJECT_ROOT/requirements.txt" ]; then
        pip install -r "$PROJECT_ROOT/requirements.txt"
        print_success "Dependencies installed"
    else
        print_error "requirements.txt not found"
        exit 1
    fi
    
    # Create directories
    print_step "Creating directory structure..."
    mkdir -p "$PROJECT_ROOT/data/logs"
    mkdir -p "$PROJECT_ROOT/data/vector_db/chroma_db"
    mkdir -p "$PROJECT_ROOT/data/scraped_data"
    mkdir -p "$PROJECT_ROOT/data/embeddings/xrvix_embeddings"/{biorxiv,medrxiv,pubmed,semantic_scholar}
    mkdir -p "$PROJECT_ROOT/data/exports"
    mkdir -p "$PROJECT_ROOT/hypothesis_export"
    print_success "Directories created"
    
    # Environment file
    print_step "Configuring environment..."
    ENV_FILE="$PROJECT_ROOT/.env"
    
    if [ ! -f "$ENV_FILE" ]; then
        if [ -f "$PROJECT_ROOT/env.example" ]; then
            cp "$PROJECT_ROOT/env.example" "$ENV_FILE"
            print_success "Created .env from template"
        else
            cat > "$ENV_FILE" <<EOF
# AHGA Local Development Configuration
MACHINE_PROFILE=local
EXECUTION_MODE=local

# ChromaDB (local)
CHROMA_HOST=localhost
CHROMA_PORT=8000

# LLM (cloud API)
LLM_PROVIDER=google
# Add your API keys below:
GOOGLE_API_KEY=your_google_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here

# Optional
NCBI_API_KEY=your_ncbi_api_key_here
EOF
            print_success "Created default .env file"
        fi
        
        print_info "Edit .env file with your API keys"
    else
        print_warning ".env file already exists"
    fi
    
    # Installation complete
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}   Local Installation Complete!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo -e "${BLUE}Next Steps:${NC}"
    echo "1. Edit .env file with your API keys:"
    echo "   nano .env"
    echo ""
    echo "2. Activate virtual environment:"
    echo "   source .venv/bin/activate"
    echo ""
    echo "3. Start local ChromaDB (in separate terminal):"
    echo "   chroma run --host localhost --port 8000 --path data/vector_db/chroma_db"
    echo ""
    echo "4. Run the CLI:"
    echo "   python -m src.cli.main --help"
    echo ""
    echo -e "${BLUE}Documentation:${NC}"
    echo "  README.md - Project overview"
    echo "  INSTALL_UBUNTU.md - Detailed Ubuntu setup"
    echo ""
}

#############################################################################
# Main Menu Loop
#############################################################################

main() {
    print_banner
    
    while true; do
        show_menu
        read -p "Enter your choice [1-5]: " choice
        
        case $choice in
            1)
                install_mystery
                break
                ;;
            2)
                install_m3
                break
                ;;
            3)
                install_local
                break
                ;;
            4)
                show_architecture
                print_banner
                ;;
            5)
                echo ""
                print_info "Exiting installer. Goodbye!"
                exit 0
                ;;
            *)
                print_warning "Invalid choice. Please enter 1-5."
                ;;
        esac
    done
}

# Run main
main "$@"

