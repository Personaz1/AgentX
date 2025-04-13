#!/bin/bash
# Remote Agent Installation Script for Ubuntu 22.04
# This script installs the remote agent and its dependencies
# Sets up the agent as a system service for automatic startup

set -e  # Exit on error

# Configure log output
log_file="/tmp/remote_agent_install.log"
exec > >(tee -a "$log_file") 2>&1

echo "=== Remote Agent Installation ==="
echo "$(date)"
echo "Starting installation process..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Error: This script must be run as root (use sudo)"
  exit 1
fi

# Function to display progress
progress() {
  echo "-> $1"
}

# Install system dependencies
progress "Installing system dependencies..."
apt-get update
apt-get install -y python3 python3-pip python3-venv python3-dev build-essential libssl-dev libffi-dev

# Create agent directory
AGENT_DIR="/opt/remote_agent"
progress "Creating agent directory at $AGENT_DIR..."
mkdir -p "$AGENT_DIR"
mkdir -p "$AGENT_DIR/shared"
mkdir -p "$AGENT_DIR/server"
mkdir -p "$AGENT_DIR/logs"

# Create virtual environment
progress "Setting up Python virtual environment..."
python3 -m venv "$AGENT_DIR/venv"
source "$AGENT_DIR/venv/bin/activate"

# Install Python dependencies
progress "Installing Python dependencies..."
pip install --upgrade pip
pip install requests
pip install cryptography
pip install psutil

# Copy files to the agent directory
progress "Copying agent files..."

# Get the directory of the current script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Check if files exist in current directory, otherwise prompt for manual copy
if [ -f "$SCRIPT_DIR/remote_agent.py" ] && [ -f "$SCRIPT_DIR/../shared/protocol.py" ] && [ -f "$SCRIPT_DIR/../shared/communication.py" ]; then
    # Copy files from script directory
    cp "$SCRIPT_DIR/remote_agent.py" "$AGENT_DIR/server/"
    cp "$SCRIPT_DIR/../shared/protocol.py" "$AGENT_DIR/shared/"
    cp "$SCRIPT_DIR/../shared/communication.py" "$AGENT_DIR/shared/"
    
    # Create empty __init__.py files
    touch "$AGENT_DIR/shared/__init__.py"
    touch "$AGENT_DIR/server/__init__.py"
else
    echo "Warning: Could not find agent files in the script directory."
    echo "Please manually copy the following files:"
    echo "- remote_agent.py -> $AGENT_DIR/server/"
    echo "- protocol.py -> $AGENT_DIR/shared/"
    echo "- communication.py -> $AGENT_DIR/shared/"
    echo "Then create empty __init__.py files in $AGENT_DIR/shared/ and $AGENT_DIR/server/"
    
    read -p "Press Enter after manually copying the files or Ctrl+C to cancel..."
    
    if [ ! -f "$AGENT_DIR/server/remote_agent.py" ] || [ ! -f "$AGENT_DIR/shared/protocol.py" ] || [ ! -f "$AGENT_DIR/shared/communication.py" ]; then
        echo "Error: Required files are missing. Installation aborted."
        exit 1
    fi
    
    # Create empty __init__.py files if they don't exist
    touch "$AGENT_DIR/shared/__init__.py"
    touch "$AGENT_DIR/server/__init__.py"
fi

# Create a systemd service file
progress "Creating systemd service..."
cat > /etc/systemd/system/remote-agent.service << EOL
[Unit]
Description=Remote Agent Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$AGENT_DIR
ExecStart=$AGENT_DIR/venv/bin/python $AGENT_DIR/server/remote_agent.py --host 0.0.0.0 --port 8765
Restart=on-failure
RestartSec=5
StandardOutput=append:$AGENT_DIR/logs/remote_agent.log
StandardError=append:$AGENT_DIR/logs/remote_agent_error.log
Environment="LLM_API_KEY="
Environment="ENCRYPTION_KEY="

[Install]
WantedBy=multi-user.target
EOL

# Set permissions
progress "Setting permissions..."
chmod +x "$AGENT_DIR/server/remote_agent.py"
chown -R root:root "$AGENT_DIR"
chmod 750 "$AGENT_DIR"

# Prompt for LLM API key
echo ""
read -p "Enter OpenAI API key (leave blank to configure later): " llm_api_key

if [ ! -z "$llm_api_key" ]; then
    # Update the service file with the API key
    sed -i "s/Environment=\"LLM_API_KEY=\"/Environment=\"LLM_API_KEY=$llm_api_key\"/" /etc/systemd/system/remote-agent.service
    echo "API key configured."
else
    echo "No API key provided. You can configure it later in the service file."
fi

# Generate a random encryption key
progress "Generating encryption key..."
encryption_key=$(openssl rand -base64 32)
sed -i "s/Environment=\"ENCRYPTION_KEY=\"/Environment=\"ENCRYPTION_KEY=$encryption_key\"/" /etc/systemd/system/remote-agent.service

echo "Generated encryption key: $encryption_key"
echo "IMPORTANT: Save this key securely for client connection!"

# Enable and start the service
progress "Enabling and starting the service..."
systemctl daemon-reload
systemctl enable remote-agent.service
systemctl start remote-agent.service

# Verify service status
progress "Checking service status..."
systemctl status remote-agent.service || true  # Don't exit on error

# Check firewall status
progress "Checking firewall status..."
if command -v ufw &> /dev/null && ufw status | grep -q "active"; then
    echo "Firewall is active. Opening port 8765..."
    ufw allow 8765/tcp
    ufw status
else
    echo "Firewall not active or ufw not installed. No need to open ports."
fi

echo ""
echo "=== Installation Complete ==="
echo "Remote Agent has been installed and configured!"
echo ""
echo "Important Information:"
echo "- Service name: remote-agent"
echo "- Installation directory: $AGENT_DIR"
echo "- Log files: $AGENT_DIR/logs/"
echo "- Port: 8765"
echo "- Encryption key: $encryption_key"
echo ""
echo "Service Management Commands:"
echo "- Check status: sudo systemctl status remote-agent"
echo "- Start service: sudo systemctl start remote-agent"
echo "- Stop service: sudo systemctl stop remote-agent"
echo "- View logs: sudo journalctl -u remote-agent"
echo ""
echo "To connect to this agent, use the following on your client machine:"
echo "./controller.py --host SERVER_IP --port 8765 --encryption-key \"$encryption_key\""
echo ""
echo "Installation log saved to: $log_file" 