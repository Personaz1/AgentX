# Secure Agent Communication Protocol

This project enables secure communication between an IDE agent and a remote server agent, allowing for remote command execution, file operations, and LLM API interactions.

## Overview

The system consists of two main components:

1. **Remote Agent** - Runs on a server (Ubuntu 22.04) and accepts commands for execution
2. **Controller** - Runs in the IDE and sends commands to the remote agent

Communication between the agents is secured using AES encryption with a shared key.

## Features

- **Secure Communication**: All messages are encrypted using AES-256-CBC
- **Command Execution**: Run shell commands on the remote server
- **File Operations**: Read, write, and list files on the remote server
- **LLM API Access**: Query language models via the remote agent
- **System Management**: Monitor system status, restart or shutdown the agent
- **Daemon Mode**: Run the remote agent as a background service
- **Automatic Installation**: Install script for easy deployment on Ubuntu

## Installation

### Remote Agent (Ubuntu Server)

1. Copy the `agent_protocol` directory to the server
2. Navigate to the server directory:
   ```
   cd agent_protocol/server
   ```
3. Make the installation script executable:
   ```
   chmod +x install.sh
   ```
4. Run the installation script as root:
   ```
   sudo ./install.sh
   ```
5. Follow the prompts to configure the agent (you'll need an OpenAI API key)
6. **IMPORTANT**: Save the encryption key displayed at the end of installation!

### Controller (IDE)

1. Install the required Python packages:
   ```
   pip install -r requirements.txt
   ```
2. Use the controller.py script to communicate with the remote agent

## Usage

### Controller CLI

The controller supports various operations:

```bash
# Execute a shell command
python client/controller.py --host SERVER_IP --port 8765 --encryption-key "YOUR_KEY" --command "ls -la"

# Query LLM API
python client/controller.py --host SERVER_IP --port 8765 --encryption-key "YOUR_KEY" --prompt "Write a hello world program in Python"

# Read a file
python client/controller.py --host SERVER_IP --port 8765 --encryption-key "YOUR_KEY" --read-file "/etc/hostname"

# Write a file
python client/controller.py --host SERVER_IP --port 8765 --encryption-key "YOUR_KEY" --write-file "/tmp/test.txt" --content "Hello, world!"

# List directory contents
python client/controller.py --host SERVER_IP --port 8765 --encryption-key "YOUR_KEY" --list-dir "/var/log"

# Get system information
python client/controller.py --host SERVER_IP --port 8765 --encryption-key "YOUR_KEY" --status

# Restart the agent
python client/controller.py --host SERVER_IP --port 8765 --encryption-key "YOUR_KEY" --restart

# Shutdown the agent
python client/controller.py --host SERVER_IP --port 8765 --encryption-key "YOUR_KEY" --shutdown
```

### Programmatic Usage

You can also use the AgentController class in your Python code:

```python
from client.controller import AgentController

# Create a controller
controller = AgentController(
    host="SERVER_IP",
    port=8765,
    encryption_key="YOUR_KEY"
)

# Connect to remote agent
if controller.connect():
    # Execute a command
    success, result = controller.execute_shell_command("ls -la")
    if success:
        print(result["stdout"])
    
    # Query LLM
    success, completion = controller.query_llm(
        "Write a hello world program in Python",
        model="gpt-3.5-turbo"
    )
    if success:
        print(completion)
    
    # Disconnect when done
    controller.disconnect()
```

## Security Considerations

- Always use secure channels (VPN or SSH tunnel) when connecting to the remote agent
- The encryption key should be kept secure and not shared
- Run the remote agent with the minimum required permissions
- Consider enabling SSL for enhanced security
- Regularly update the agent software and dependencies

## Troubleshooting

### Remote Agent Issues

- Check logs: `sudo journalctl -u remote-agent`
- Verify service status: `sudo systemctl status remote-agent`
- Check firewall: `sudo ufw status`
- Manual start: `sudo systemctl start remote-agent`

### Connection Issues

- Verify the encryption key is correct
- Check network connectivity: `ping SERVER_IP`
- Ensure port 8765 is open: `nc -zv SERVER_IP 8765`
- Check for firewall rules blocking the connection

## License

Open source - free to use and modify. 