#!/bin/bash

# NeuroRAT Monitor Starter
# Author: Mr. Thomas Anderson (iamnobodynothing@gmail.com)
# License: MIT

# Default settings
SERVER_HOST=${1:-"127.0.0.1"}
SERVER_PORT=${2:-"8000"}
API_PORT=${3:-"5000"}
LOG_DIR="logs"
LOG_FILE="${LOG_DIR}/monitor_$(date +%Y%m%d_%H%M%S).log"
DB_FILE="data/neurorat_monitor.db"

# Color settings
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Create directories if they don't exist
mkdir -p "$LOG_DIR"
mkdir -p "data"

# Banner
echo -e "${BLUE}"
echo "███╗   ██╗███████╗██╗   ██╗██████╗  ██████╗ ██████╗  █████╗ ████████╗"
echo "████╗  ██║██╔════╝██║   ██║██╔══██╗██╔═══██╗██╔══██╗██╔══██╗╚══██╔══╝"
echo "██╔██╗ ██║█████╗  ██║   ██║██████╔╝██║   ██║██████╔╝███████║   ██║   "
echo "██║╚██╗██║██╔══╝  ██║   ██║██╔══██╗██║   ██║██╔══██╗██╔══██║   ██║   "
echo "██║ ╚████║███████╗╚██████╔╝██║  ██║╚██████╔╝██║  ██║██║  ██║   ██║   "
echo "╚═╝  ╚═══╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝   "
echo -e "${NC}"
echo -e "${YELLOW}NeuroRAT Server Monitor${NC}"
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

# Check if monitor script exists
if [ ! -f "server_monitor.py" ]; then
    echo -e "${RED}Error: Monitor script 'server_monitor.py' not found.${NC}"
    deactivate
    exit 1
fi

# Start monitor
echo -e "${GREEN}Starting NeuroRAT Server Monitor...${NC}"
echo -e "${BLUE}Monitor configuration:${NC}"
echo "  Server:   $SERVER_HOST:$SERVER_PORT"
echo "  API Port: $API_PORT"
echo "  Database: $DB_FILE"
echo "  Log File: $LOG_FILE"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop the monitor${NC}"
echo ""

# Start monitor with logging
python server_monitor.py \
    --server "$SERVER_HOST" \
    --port "$SERVER_PORT" \
    --api-port "$API_PORT" \
    --db "$DB_FILE" \
    2>&1 | tee "$LOG_FILE"

# Deactivate virtual environment when done
deactivate 