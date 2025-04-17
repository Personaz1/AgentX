# AgentX: Advanced Autonomous C2 Framework

AgentX is a comprehensive Command and Control (C2) framework designed for professional security researchers and penetration testers. It provides a sophisticated infrastructure for secure covert communication, autonomous decision-making, and advanced threat modeling through a two-tier architecture.

## Architecture Overview

The framework consists of two main components:

1. **C1 (NeuroNet)** - Central Command server with autonomous intelligence
2. **NeuroZond** - Lightweight agent deployments on target systems

This architecture enables efficient operation, with C1 handling strategic decisions and NeuroZond executing commands with minimal footprint.

## Key Features

### C1 (Command Center)
- **C1 Brain** - LLM-powered autonomous decision-making module
- **Botnet Controller** - Manages all active zonds and their tasks
- **WebSocket Terminal** - Real-time command execution interface
- **Modern React UI** - Advanced dashboard with analytics and control panels
- **LLM Chat Interface** - Natural language interaction with the system

### NeuroZond (Agent)
- **Advanced Covert Channels** - DNS, HTTPS, and ICMP communication methods
- **Military-grade Cryptography** - AES-256 with key rotation
- **Cross-platform Compatibility** - Linux, macOS, Windows support
- **Modular Architecture** - Easily extensible through additional modules
- **CODEX Module** - Optional LLM-based code analysis and exploitation

### Security Features
- **Traffic Obfuscation** - Jitter and pattern randomization
- **Multi-layered Encryption** - End-to-end encryption for all communications
- **Anti-forensic Capabilities** - Minimal on-disk and memory footprint
- **EDR/XDR Evasion** - Advanced techniques to bypass security solutions
- **Sandbox Detection** - Automatic environment analysis

## Components

### Core System
- `/core/` - Core C1 server components
  - `botnet_controller.py` - Main controller for zond management
  - `c1_brain.py` - Autonomous decision-making module
  - `zond_protocol.py` - Communication protocol implementation

### Server Components
- `/server/` - API and communication servers
  - `server_api.py` - FastAPI server with REST endpoints
  - `tcp_server.py` - TCP server for direct agent communication

### NeuroZond
- `/neurozond/` - Agent implementation
  - `/network/` - Covert communication channels
  - `/crypto/` - Cryptographic operations
  - `/command/` - Command execution modules
  - `/src/codex/` - CODEX module for code analysis (optional)

### User Interface
- `/neurorat-ui/` - React-based administrative interface
  - Modern dashboard with real-time analytics
  - Terminal emulation with color support
  - Agent management and task assignment
  - LLM interaction and reasoning visualization

## Installation

### Prerequisites
- Python 3.9+
- Node.js 16+
- C/C++ compiler (GCC 10+ or equivalent)
- OpenSSL, libcurl, jansson development libraries

### Server Setup
```bash
# Clone the repository
git clone https://github.com/Personaz1/AgentX.git
cd AgentX

# Install dependencies
pip install -r requirements.txt

# Start the server
./start.sh
```

### Agent Compilation
```bash
cd neurozond
make
```

## Usage

### Web Interface
The web interface is available at `http://localhost:8080` after server startup.

### API Access
The REST API is accessible at `http://localhost:8080/api`.

### Creating a New Agent
```bash
# Generate agent binary
cd builders
./build_agent.sh --platform linux64 --output ../bin/agent

# Deploy to target system
# (Deployment methods vary based on context)
```

### Agent Control
Commands can be issued through:
- Web interface terminal
- REST API
- Direct CLI interface

### Command Examples
```python
# Python API example
from agentx import client

# Connect to C1 server
c1 = client.C1Client("https://c1-server:8080", api_key="your_api_key")

# Get list of active agents
agents = c1.get_agents()

# Execute command on agent
result = c1.execute_command("agent-id-123", "systeminfo")
print(result)
```

## Advanced Features

### Autonomous Operations
C1 Brain enables autonomous operations through:
- Environment analysis and contextual awareness
- Adaptive command generation
- Risk assessment and decision-making
- Continuous learning from operational results

### CODEX Module
The optional CODEX module extends NeuroZond with:
- Source code analysis for vulnerability detection
- Automatic exploit generation
- Code modification capabilities
- LLM-based programming assistance

### Covert Communications
Multiple covert channel implementations:
- DNS tunneling with domain rotation
- HTTPS with traffic pattern randomization
- ICMP with timing manipulation
- Automatic fallback mechanisms

## Security Measures

The framework implements multiple security features:
- Encrypted communications with perfect forward secrecy
- Anti-debugging and anti-analysis techniques
- Memory protection and secure credential storage
- Minimal and obfuscated disk footprint
- Dynamic binary protection

## Development

### Project Structure
```
/
├── core/               # Core C1 components
├── server/             # API and network servers
├── neurozond/          # Agent source code
├── neurorat-ui/        # Web interface
├── builders/           # Build and deployment tools
├── tests/              # Test suite
├── config/             # Configuration files
└── assets/             # Static assets
```

### Adding New Modules
The modular architecture allows for easy extension:
1. Create module in appropriate directory
2. Implement standard interface
3. Register with core system
4. Update documentation

## Legal Disclaimer

This software is provided for authorized security testing and research purposes only. Users are responsible for complying with applicable laws and obtaining proper authorization before deployment in any environment.

## License

Proprietary - All rights reserved.

Copyright (c) 2025 [Organization] 