# NeuroRAT Architecture

## Overview

NeuroRAT is an advanced remote access tool designed for penetration testing and security research. It combines traditional RAT capabilities with artificial intelligence through LLM (Large Language Model) integration, enabling autonomous decision-making and natural language command interpretation.

## Core Components

The system consists of four primary components:

1. **Command & Control (C2) Server**
2. **Agent Module**
3. **LLM Processor**
4. **Agent Builder**

![NeuroRAT Architecture](docs/images/architecture_diagram.svg)

## Component Details

### 1. Command & Control (C2) Server

The central management component that orchestrates all operations.

**Responsibilities:**
- Agent registration and management
- Command distribution
- Data collection and storage
- Web interface for operator control
- API endpoints for integrations

**Key Modules:**
- `server/`: Contains the server implementation
- `server/api/`: REST API endpoints
- `server/database/`: Data persistence
- `server/web_interface/`: Admin dashboard

**Communication:**
- HTTPS for secure command and data transmission
- WebSockets for real-time updates
- Customizable communication protocols

### 2. Agent Module

The client-side component that runs on target systems.

**Responsibilities:**
- System reconnaissance
- Command execution
- Data exfiltration
- Persistence mechanisms
- Stealth operations

**Key Modules:**
- `agent_protocol/`: Communication protocol implementation
- `agent_modules/`: Individual capability modules:
  - `keylogger.py`: Captures keystrokes
  - `screen_capture.py`: Takes screenshots and records screen
  - `browser_stealer.py`: Extracts browser data (cookies, history, passwords)
  - `crypto_stealer.py`: Extracts cryptocurrency wallets and keys
  - `system_stealer.py`: Gathers system information
  - More modules can be added as plugins

**Features:**
- Cross-platform compatibility (Windows, macOS, Linux)
- Small footprint and minimal resource usage
- Encrypted communications
- Anti-detection mechanisms

### 3. LLM Processor

The AI component that enables autonomous operation and natural language processing.

**Responsibilities:**
- Interpret natural language commands
- Make autonomous decisions
- Generate human-like responses
- Adapt to different operational contexts

**Key Modules:**
- `llm_processor/`: Core LLM integration
- `llm_processor/apis/`: Connectors for various LLM services
- `llm_processor/prompts/`: Task-specific prompting templates
- `llm_processor/local/`: Local model implementation (placeholder)

**Supported LLM Services:**
- OpenAI GPT models
- Anthropic Claude
- Local models (planned)
- Custom API integration

### 4. Agent Builder

The utility for packaging and deploying agents.

**Responsibilities:**
- Agent compilation for different platforms
- Configuration and customization
- Obfuscation and anti-analysis features
- Deployment automation

**Key Files:**
- `build_agent.py`: Main builder script
- `obfuscation/`: Code obfuscation utilities
- `templates/`: Agent templates for different configurations

## Data Flow

1. **Command Issuance**:
   - Operator issues command through web interface or API
   - Command is processed by C2 server
   - Command is transformed into:
     - Direct execution command
     - Natural language instruction for LLM processing

2. **Command Execution**:
   - C2 server sends command to target agent(s)
   - Agent receives and validates command
   - If LLM processing is required, agent forwards to LLM processor
   - Command is executed by the appropriate agent module
   - Results are collected and prepared for exfiltration

3. **Data Exfiltration**:
   - Agent packages collected data
   - Data is encrypted using session keys
   - Data is transmitted to C2 using configured protocol
   - C2 server receives, decrypts, and stores data
   - Data is made available through the web interface or API

4. **LLM Processing**:
   - Natural language commands are sent to LLM processor
   - LLM interprets command intent and required actions
   - LLM may request additional context from agent
   - LLM generates structured commands for agent execution
   - LLM can provide human-like responses to interaction

## Security Features

- **End-to-end encryption**: All communications are encrypted
- **Certificate pinning**: Prevents MITM attacks
- **Anti-forensics**: Minimal disk footprint and memory artifacts
- **Defense evasion**: Techniques to bypass common security tools
- **Self-destruction**: Capability to remove all traces upon command

## Plugin Architecture

NeuroRAT uses a modular design that allows easy extension:

1. **Agent Modules**: Each capability is implemented as a separate module
2. **LLM Connectors**: Adapters for different LLM services
3. **Protocol Handlers**: Support for custom communication protocols
4. **Data Processors**: Plugins for specialized data handling

Developers can create new modules by implementing standard interfaces:

```python
class BaseModule:
    def __init__(self, config):
        self.config = config
    
    def execute(self, command):
        # Implementation
        pass
    
    def collect_data(self):
        # Implementation
        pass
```

## Deployment Models

1. **Standalone**: C2 server and agent operate independently
2. **Distributed**: Multiple C2 servers in a hierarchical structure
3. **Mesh**: Peer-to-peer communication between agents
4. **Hybrid**: Combination of approaches for resilience

## Future Architecture Extensions

- **Swarm Intelligence**: Collective decision-making between agents
- **Edge AI**: Local LLM processing on the agent
- **Blockchain C2**: Decentralized command and control
- **Adversarial ML**: Machine learning for defense evasion 