# Agent Protocol Usage Guide

This guide shows how to use the agent communication protocol for various tasks.

## Setup Process

### Step 1: Deploy Remote Agent

First, set up the remote agent on your Ubuntu 22.04 server:

```bash
# Copy the agent_protocol directory to your server
scp -r agent_protocol user@your-server-ip:~

# SSH into your server
ssh user@your-server-ip

# Install the remote agent
cd ~/agent_protocol/server
chmod +x install.sh
sudo ./install.sh

# Note the encryption key displayed at the end of installation
# IMPORTANT: Save this key securely!
```

### Step 2: Set Up Controller

On your local machine:

```bash
# Install dependencies
cd agent_protocol
pip install -r requirements.txt
```

## Basic Operations

### Testing Connection

Verify that you can connect to the remote agent:

```bash
python client/controller.py --host SERVER_IP --port 8765 --encryption-key "YOUR_KEY" --status
```

You should see system information if the connection is successful.

### Shell Command Execution

Run commands on the remote server:

```bash
# Simple command
python client/controller.py --host SERVER_IP --port 8765 --encryption-key "YOUR_KEY" --command "ls -la"

# Command with arguments
python client/controller.py --host SERVER_IP --port 8765 --encryption-key "YOUR_KEY" --command "find" --args "/" "-name" "*.log" "-type" "f" "-mtime" "-1"
```

### File Operations

```bash
# Read a file
python client/controller.py --host SERVER_IP --port 8765 --encryption-key "YOUR_KEY" --read-file "/etc/os-release"

# Write a file
python client/controller.py --host SERVER_IP --port 8765 --encryption-key "YOUR_KEY" --write-file "/tmp/hello.txt" --content "Hello, Remote World!"

# Read the file you just wrote
python client/controller.py --host SERVER_IP --port 8765 --encryption-key "YOUR_KEY" --read-file "/tmp/hello.txt"

# List directory contents
python client/controller.py --host SERVER_IP --port 8765 --encryption-key "YOUR_KEY" --list-dir "/var/log"
```

### LLM API Interaction

Query language models through the remote agent (requires configured API key):

```bash
# Simple query
python client/controller.py --host SERVER_IP --port 8765 --encryption-key "YOUR_KEY" --prompt "Write a short story about AI agents"

# With specific model
python client/controller.py --host SERVER_IP --port 8765 --encryption-key "YOUR_KEY" --prompt "Explain quantum computing" --model "gpt-4"
```

## Advanced Use Cases

### Running as a Background Process

The remote agent already runs as a system service. Manage it using:

```bash
# Check status
sudo systemctl status remote-agent

# Restart
sudo systemctl restart remote-agent

# Stop
sudo systemctl stop remote-agent

# View logs
sudo journalctl -u remote-agent
```

### Integrating with IDE

To use the agent controller in your code:

```python
from client.controller import AgentController

# Create controller
controller = AgentController(
    host="SERVER_IP",
    port=8765,
    encryption_key="YOUR_KEY"
)

# Connect
if controller.connect():
    # Execute command
    success, result = controller.execute_shell_command("uptime")
    if success:
        uptime = result["stdout"].strip()
        print(f"Server uptime: {uptime}")
    
    # Disconnect
    controller.disconnect()
```

### Using with SSH Tunneling for Additional Security

For enhanced security, use SSH tunneling:

```bash
# Set up SSH tunnel
ssh -L 8765:localhost:8765 user@your-server-ip -N

# Then connect to localhost
python client/controller.py --host localhost --port 8765 --encryption-key "YOUR_KEY" --status
```

### Using Demo Script

Run the demo script to see the full capabilities:

```bash
python demo.py --host SERVER_IP --port 8765 --encryption-key "YOUR_KEY"
```

## Troubleshooting

### Cannot Connect to Agent

1. Check that the remote agent service is running:
   ```bash
   sudo systemctl status remote-agent
   ```

2. Verify the port is open:
   ```bash
   sudo ufw status
   ```

3. Try restarting the agent:
   ```bash
   sudo systemctl restart remote-agent
   ```

### API Key Issues

If LLM queries fail, check your API key configuration:

```bash
# Check the environment variables in the service file
sudo cat /etc/systemd/system/remote-agent.service

# Update the API key if needed
sudo systemctl edit remote-agent.service
# Add: Environment="LLM_API_KEY=your-new-key"

# Reload and restart
sudo systemctl daemon-reload
sudo systemctl restart remote-agent
```

### Encryption Key Problems

If you see encryption-related errors, verify that you're using the correct key:

```bash
# View the encryption key stored in the service file
sudo grep ENCRYPTION_KEY /etc/systemd/system/remote-agent.service
```

Use the exact key when connecting with the controller.

## Advanced Security

For production use, consider:

1. Using SSL certificates:
   ```bash
   # Generate self-signed certificate
   openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes
   
   # Update the service file to use SSL
   sudo systemctl edit remote-agent.service
   # Add: ExecStart=/opt/remote_agent/venv/bin/python /opt/remote_agent/server/remote_agent.py --host 0.0.0.0 --port 8765 --use-ssl --cert-file /path/to/cert.pem --key-file /path/to/key.pem
   
   # Restart the service
   sudo systemctl daemon-reload
   sudo systemctl restart remote-agent
   
   # Connect with SSL from client
   python client/controller.py --host SERVER_IP --port 8765 --encryption-key "YOUR_KEY" --use-ssl --cert-file /path/to/cert.pem --status
   ```

2. Restricting access to specific IP addresses using firewall rules:
   ```bash
   sudo ufw allow from YOUR_IP_ADDRESS to any port 8765
   ```

3. Running the agent as a non-root user with limited permissions. 