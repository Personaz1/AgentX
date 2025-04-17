# NeuroZond

Agent component of the AgentX framework, designed for covert deployment on target systems.

## Overview

NeuroZond is the lightweight agent module of the AgentX C2 framework. It functions as a loader that receives, decodes, and executes commands from the C1 command center. The agent is designed with a focus on stealth, reliability, and minimal resource usage.

## Key Features

- **Covert Communication Channels** - DNS, HTTPS, and ICMP-based communication
- **Strong Cryptography** - Multiple encryption algorithms (XOR, AES-256, ChaCha20)
- **Cross-Platform Support** - Linux, macOS, and Windows compatibility
- **Command Execution** - Secure and configurable command execution system
- **Modular Architecture** - Easy extension through additional modules
- **Extendable with CODEX** - Optional integration with LLM-based code analysis capabilities

## Directory Structure

```
neurozond/
├── include/           # Header files
│   ├── agent/         # Agent loop and sandbox headers
│   ├── codex/         # CODEX module headers
│   ├── command_executor.h
│   └── covert_channel.h
├── src/               # Source code
│   ├── codex/         # CODEX module implementation
│   └── ...
├── network/           # Network communication implementations
│   ├── dns_channel.c
│   ├── https_channel.c
│   └── icmp_channel.c
├── crypto/            # Cryptographic operations
├── command/           # Command execution
├── core/              # Core agent functionality
├── tests/             # Unit and integration tests
├── examples/          # Example usage scenarios
├── docs/              # Documentation
├── build.sh           # Build script
├── covert_channel.c   # Main covert channel implementation
├── main.c             # Agent entry point
└── Makefile           # Build configuration
```

## Building NeuroZond

### Prerequisites

- GCC 10+ or equivalent C compiler
- Make build system
- OpenSSL development libraries
- libcurl
- jansson (JSON library)

### Compilation

Basic build:
```bash
make
```

With CODEX module support:
```bash
make ENABLE_CODEX=1
```

Build for specific platform:
```bash
make TARGET=linux64    # Linux x86_64
make TARGET=win64      # Windows x86_64
make TARGET=macos      # macOS
```

## Architecture

### Main Components

1. **Covert Channel Module** - Manages communication with C1 server
   - DNS tunneling
   - HTTPS communication
   - ICMP-based channel

2. **Cryptographic Module** - Handles encryption and decryption
   - XOR encryption (lightweight)
   - AES-256 encryption (standard)
   - ChaCha20 (fast stream cipher)

3. **Command Execution Module** - Executes commands securely
   - Shell command execution
   - Process execution with custom flags
   - Output capture and redirection

4. **CODEX Module** (Optional) - Provides code analysis capabilities
   - Code scanning and analysis
   - Vulnerability detection
   - LLM-based code operation

### Communication Flow

1. Agent initiates connection to C1 server through a covert channel
2. Commands are received, decrypted and validated
3. Commands are executed with appropriate security measures
4. Results are encrypted and sent back to C1
5. Communication jitter is applied to evade detection

## Integration with C1

NeuroZond is designed to work seamlessly with the C1 command center from the AgentX framework. The agent:

- Registers with C1 on first connection
- Receives encrypted commands
- Returns execution results
- Supports heartbeat for connection verification
- Can be dynamically configured by C1

## Advanced Usage

### Jitter Configuration

```c
covert_channel_set_jitter(channel, 100, 3000);  // Min: 100ms, Max: 3000ms
```

### Channel Selection Based on Environment

```c
// Example logic for selecting optimal channel
covert_channel_type selected_type;

if (dns_available())
    selected_type = COVERT_CHANNEL_DNS;
else if (https_available())
    selected_type = COVERT_CHANNEL_HTTPS;
else
    selected_type = COVERT_CHANNEL_ICMP;
```

### Command Execution with Different Flags

```c
Command* cmd = command_create(COMMAND_TYPE_SHELL);
command_set_command_line(cmd, "systeminfo");
command_set_flags(cmd, COMMAND_FLAG_HIDDEN);
CommandResult* result = command_execute(cmd);
```

## Security Notes

- All strings are obfuscated in final builds
- Configuration files and artifacts are encrypted on disk
- Dynamic signature changes in network communications
- Capabilities for detecting analysis attempts
- Self-destruction mechanism when analysis is detected

## Testing

Run the test suite:
```bash
make test
```

For specific test components:
```bash
make test_covert_channel
make test_crypto
make test_command_executor
```

## Relationship to AgentX Framework

NeuroZond is a critical component of the AgentX framework, serving as the deployment agent on target systems. While it can function independently, it is designed to communicate with the C1 command center for full operational capability. 