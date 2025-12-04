#!/bin/bash

#############################################################################
# AHGA Research Processor - Run Script
# CLI for starting the web application and editing configuration files
#############################################################################

set -e  # Exit on error

# Colors for output (consistent with install.sh)
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

# Editor preference (use $EDITOR if set, otherwise nano)
PREFERRED_EDITOR="${EDITOR:-nano}"

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
    echo "║                        Run Manager                               ║"
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

check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed or not in PATH"
        echo "Please install Docker: https://docs.docker.com/get-docker/"
        return 1
    fi
    
    if ! docker info &> /dev/null; then
        print_error "Docker daemon is not running"
        echo "Please start Docker and try again"
        return 1
    fi
    
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        print_error "Docker Compose is not installed"
        echo "Please install Docker Compose: https://docs.docker.com/compose/install/"
        return 1
    fi
    
    return 0
}

get_compose_cmd() {
    # Check if docker compose (v2) is available, otherwise use docker-compose (v1)
    if docker compose version &> /dev/null 2>&1; then
        echo "docker compose"
    else
        echo "docker-compose"
    fi
}

#############################################################################
# Website Functions
#############################################################################

start_website() {
    print_step "Starting AHGA Web Application..."
    
    if ! check_docker; then
        read -p "Press Enter to return to menu..."
        return
    fi
    
    cd "$PROJECT_ROOT"
    
    COMPOSE_CMD=$(get_compose_cmd)
    
    # Check if .env exists
    if [ ! -f ".env" ]; then
        if [ -f "env.example" ]; then
            print_warning ".env file not found. Creating from env.example..."
            cp env.example .env
            print_info "Please edit .env with your configuration before starting"
            read -p "Would you like to edit .env now? (y/n) " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                $PREFERRED_EDITOR .env
            fi
        else
            print_warning ".env file not found and no template available"
        fi
    fi
    
    print_step "Building and starting containers..."
    $COMPOSE_CMD up -d --build
    
    echo ""
    print_success "Website started successfully!"
    echo ""
    echo -e "${BOLD}Service Status:${NC}"
    $COMPOSE_CMD ps
    echo ""
    echo -e "${BLUE}Access the application:${NC}"
    echo "   Frontend:  http://localhost"
    echo "   API:       http://localhost/api/"
    echo "   API Docs:  http://localhost/api/docs"
    echo ""
    echo -e "${BLUE}View logs:${NC}"
    echo "   $COMPOSE_CMD logs -f"
    echo ""
    
    read -p "Press Enter to return to menu..."
}

stop_website() {
    print_step "Stopping AHGA Web Application..."
    
    if ! check_docker; then
        read -p "Press Enter to return to menu..."
        return
    fi
    
    cd "$PROJECT_ROOT"
    
    COMPOSE_CMD=$(get_compose_cmd)
    
    $COMPOSE_CMD down
    
    echo ""
    print_success "Website stopped successfully!"
    echo ""
    
    read -p "Press Enter to return to menu..."
}

show_website_status() {
    print_step "Website Status"
    
    if ! check_docker; then
        read -p "Press Enter to return to menu..."
        return
    fi
    
    cd "$PROJECT_ROOT"
    
    COMPOSE_CMD=$(get_compose_cmd)
    
    echo ""
    $COMPOSE_CMD ps
    echo ""
    
    read -p "Press Enter to return to menu..."
}

#############################################################################
# Config Editing Functions
#############################################################################

edit_config_file() {
    local file_path="$1"
    local file_desc="$2"
    
    if [ -f "$PROJECT_ROOT/$file_path" ]; then
        print_info "Opening $file_desc ($file_path) with $PREFERRED_EDITOR..."
        $PREFERRED_EDITOR "$PROJECT_ROOT/$file_path"
    else
        print_warning "File not found: $file_path"
        read -p "Would you like to create it? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            touch "$PROJECT_ROOT/$file_path"
            $PREFERRED_EDITOR "$PROJECT_ROOT/$file_path"
        fi
    fi
}

show_config_menu() {
    while true; do
        print_banner
        echo ""
        echo -e "${BOLD}Edit Configuration Files:${NC}"
        echo ""
        echo -e "${MAGENTA}┌─────────────────────────────────────────────────────────────────────┐${NC}"
        echo -e "${MAGENTA}│${NC}                                                                     ${MAGENTA}│${NC}"
        echo -e "${MAGENTA}│${NC}  ${CYAN}[1]${NC} API Keys              ${BLUE}(config/keys.json)${NC}                    ${MAGENTA}│${NC}"
        echo -e "${MAGENTA}│${NC}      └─ Google API, Gemini API, NCBI API keys                      ${MAGENTA}│${NC}"
        echo -e "${MAGENTA}│${NC}                                                                     ${MAGENTA}│${NC}"
        echo -e "${MAGENTA}│${NC}  ${CYAN}[2]${NC} LLM Settings          ${BLUE}(config/LLM_config.json)${NC}              ${MAGENTA}│${NC}"
        echo -e "${MAGENTA}│${NC}      └─ Model selection, temperature, embeddings                   ${MAGENTA}│${NC}"
        echo -e "${MAGENTA}│${NC}                                                                     ${MAGENTA}│${NC}"
        echo -e "${MAGENTA}│${NC}  ${CYAN}[3]${NC} Search Keywords       ${BLUE}(config/search_keywords_config.json)${NC}  ${MAGENTA}│${NC}"
        echo -e "${MAGENTA}│${NC}      └─ PubMed and Semantic Scholar search terms                   ${MAGENTA}│${NC}"
        echo -e "${MAGENTA}│${NC}                                                                     ${MAGENTA}│${NC}"
        echo -e "${MAGENTA}│${NC}  ${CYAN}[4]${NC} Network Settings      ${BLUE}(config/network_config.json)${NC}          ${MAGENTA}│${NC}"
        echo -e "${MAGENTA}│${NC}      └─ Proxy, timeout, retry settings                             ${MAGENTA}│${NC}"
        echo -e "${MAGENTA}│${NC}                                                                     ${MAGENTA}│${NC}"
        echo -e "${MAGENTA}│${NC}  ${CYAN}[5]${NC} Environment Variables ${BLUE}(.env)${NC}                                ${MAGENTA}│${NC}"
        echo -e "${MAGENTA}│${NC}      └─ ChromaDB host, LLM provider, execution mode                ${MAGENTA}│${NC}"
        echo -e "${MAGENTA}│${NC}                                                                     ${MAGENTA}│${NC}"
        echo -e "${MAGENTA}│${NC}  ${CYAN}[6]${NC} Critique Settings     ${BLUE}(config/critique_config.json)${NC}         ${MAGENTA}│${NC}"
        echo -e "${MAGENTA}│${NC}      └─ Hypothesis evaluation parameters                           ${MAGENTA}│${NC}"
        echo -e "${MAGENTA}│${NC}                                                                     ${MAGENTA}│${NC}"
        echo -e "${MAGENTA}│${NC}  ${CYAN}[7]${NC} Server Settings       ${BLUE}(config/server.yaml)${NC}                  ${MAGENTA}│${NC}"
        echo -e "${MAGENTA}│${NC}      └─ API host, port, CORS settings                              ${MAGENTA}│${NC}"
        echo -e "${MAGENTA}│${NC}                                                                     ${MAGENTA}│${NC}"
        echo -e "${MAGENTA}│${NC}  ${CYAN}[0]${NC} Back to Main Menu                                               ${MAGENTA}│${NC}"
        echo -e "${MAGENTA}│${NC}                                                                     ${MAGENTA}│${NC}"
        echo -e "${MAGENTA}└─────────────────────────────────────────────────────────────────────┘${NC}"
        echo ""
        echo -e "${BLUE}Editor: ${NC}$PREFERRED_EDITOR ${BLUE}(set \$EDITOR to change)${NC}"
        echo ""
        read -p "Enter your choice [0-7]: " choice
        
        case $choice in
            1) edit_config_file "config/keys.json" "API Keys" ;;
            2) edit_config_file "config/LLM_config.json" "LLM Settings" ;;
            3) edit_config_file "config/search_keywords_config.json" "Search Keywords" ;;
            4) edit_config_file "config/network_config.json" "Network Settings" ;;
            5) edit_config_file ".env" "Environment Variables" ;;
            6) edit_config_file "config/critique_config.json" "Critique Settings" ;;
            7) edit_config_file "config/server.yaml" "Server Settings" ;;
            0) return ;;
            *) print_warning "Invalid choice. Please enter 0-7." ;;
        esac
    done
}

#############################################################################
# Main Menu
#############################################################################

show_main_menu() {
    echo ""
    echo -e "${BOLD}Main Menu:${NC}"
    echo ""
    echo -e "${MAGENTA}┌─────────────────────────────────────────────────────────────────────┐${NC}"
    echo -e "${MAGENTA}│${NC}                                                                     ${MAGENTA}│${NC}"
    echo -e "${MAGENTA}│${NC}  ${CYAN}[1]${NC} Start Website                                                   ${MAGENTA}│${NC}"
    echo -e "${MAGENTA}│${NC}      └─ Build and start the web application with Docker            ${MAGENTA}│${NC}"
    echo -e "${MAGENTA}│${NC}                                                                     ${MAGENTA}│${NC}"
    echo -e "${MAGENTA}│${NC}  ${CYAN}[2]${NC} Stop Website                                                    ${MAGENTA}│${NC}"
    echo -e "${MAGENTA}│${NC}      └─ Stop all running containers                                ${MAGENTA}│${NC}"
    echo -e "${MAGENTA}│${NC}                                                                     ${MAGENTA}│${NC}"
    echo -e "${MAGENTA}│${NC}  ${CYAN}[3]${NC} Website Status                                                  ${MAGENTA}│${NC}"
    echo -e "${MAGENTA}│${NC}      └─ Show status of running containers                          ${MAGENTA}│${NC}"
    echo -e "${MAGENTA}│${NC}                                                                     ${MAGENTA}│${NC}"
    echo -e "${MAGENTA}│${NC}  ${CYAN}[4]${NC} Edit Config Files                                               ${MAGENTA}│${NC}"
    echo -e "${MAGENTA}│${NC}      └─ Modify API keys, LLM settings, search keywords             ${MAGENTA}│${NC}"
    echo -e "${MAGENTA}│${NC}                                                                     ${MAGENTA}│${NC}"
    echo -e "${MAGENTA}│${NC}  ${CYAN}[5]${NC} Exit                                                            ${MAGENTA}│${NC}"
    echo -e "${MAGENTA}│${NC}                                                                     ${MAGENTA}│${NC}"
    echo -e "${MAGENTA}└─────────────────────────────────────────────────────────────────────┘${NC}"
    echo ""
}

#############################################################################
# Main Loop
#############################################################################

main() {
    while true; do
        print_banner
        show_main_menu
        read -p "Enter your choice [1-5]: " choice
        
        case $choice in
            1) start_website ;;
            2) stop_website ;;
            3) show_website_status ;;
            4) show_config_menu ;;
            5)
                echo ""
                print_info "Goodbye!"
                exit 0
                ;;
            *)
                print_warning "Invalid choice. Please enter 1-5."
                sleep 1
                ;;
        esac
    done
}

# Run main
main "$@"

