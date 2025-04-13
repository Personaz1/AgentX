#!/usr/bin/env python3
import os
import sys
import json
import time
import subprocess
import shlex
import logging
import argparse
import signal
import requests
from typing import Dict, Any, List, Optional, Union
import threading
import base64

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.protocol import (
    Command, Response, ResponseStatus, CommandType,
    create_shell_command, create_llm_command, create_file_command
)
from shared.communication import CommunicationServer, SecureChannel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("remote_agent.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('remote_agent')

class RemoteAgent:
    def __init__(
        self,
        host: str = '0.0.0.0',
        port: int = 8765,
        llm_api_key: Optional[str] = None,
        llm_api_url: str = "https://api.openai.com/v1/chat/completions",
        encryption_key: Optional[str] = None,
        use_ssl: bool = False,
        cert_file: Optional[str] = None,
        key_file: Optional[str] = None
    ):
        self.llm_api_key = llm_api_key
        self.llm_api_url = llm_api_url
        
        # Create secure channel
        secure_channel = SecureChannel(encryption_key) if encryption_key else SecureChannel()
        logger.info(f"Encryption key: {secure_channel.get_key_base64()}")
        
        # Create communication server
        self.server = CommunicationServer(
            host=host,
            port=port,
            secure_channel=secure_channel,
            use_ssl=use_ssl,
            cert_file=cert_file,
            key_file=key_file
        )
        
        # Register command handlers
        self.register_command_handlers()
        
        # Signal handling
        self._setup_signal_handling()
        
    def _setup_signal_handling(self):
        """Set up signal handling for graceful shutdown."""
        def signal_handler(sig, frame):
            logger.info(f"Received signal {sig}, shutting down...")
            self.stop()
            sys.exit(0)
            
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def register_command_handlers(self):
        """Register handlers for different command types."""
        self.server.register_command_handler(CommandType.SHELL.value, self.handle_shell_command)
        self.server.register_command_handler(CommandType.LLM.value, self.handle_llm_command)
        self.server.register_command_handler(CommandType.FILE.value, self.handle_file_command)
        self.server.register_command_handler(CommandType.STATUS.value, self.handle_status_command)
        self.server.register_command_handler(CommandType.SYSTEM.value, self.handle_system_command)
    
    def start(self):
        """Start the remote agent."""
        logger.info("Starting Remote Agent")
        self.server.start()
        logger.info(f"Agent listening on {self.server.host}:{self.server.port}")
        
        # Keep the main thread alive
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()
    
    def stop(self):
        """Stop the remote agent."""
        logger.info("Stopping Remote Agent")
        self.server.stop()
    
    def handle_shell_command(self, command: Command) -> Response:
        """Handle shell command execution."""
        cmd = command.payload.get("command", "")
        args = command.payload.get("args", [])
        timeout = command.payload.get("timeout", 60)  # Default timeout: 60 seconds
        
        if not cmd:
            return Response(
                command_id=command.command_id,
                status=ResponseStatus.ERROR,
                data={},
                error_message="No command specified"
            )
        
        # Construct the full command
        full_cmd = cmd
        if args:
            full_cmd += " " + " ".join([shlex.quote(arg) for arg in args])
        
        logger.info(f"Executing shell command: {full_cmd}")
        
        try:
            # Execute the command
            process = subprocess.Popen(
                full_cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            try:
                stdout, stderr = process.communicate(timeout=timeout)
                return Response(
                    command_id=command.command_id,
                    status=ResponseStatus.SUCCESS if process.returncode == 0 else ResponseStatus.ERROR,
                    data={
                        "stdout": stdout,
                        "stderr": stderr,
                        "return_code": process.returncode
                    },
                    error_message=stderr if process.returncode != 0 else None
                )
            except subprocess.TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate()
                return Response(
                    command_id=command.command_id,
                    status=ResponseStatus.ERROR,
                    data={
                        "stdout": stdout,
                        "stderr": stderr,
                        "return_code": -1
                    },
                    error_message=f"Command timed out after {timeout} seconds"
                )
                
        except Exception as e:
            logger.error(f"Error executing shell command: {e}")
            return Response(
                command_id=command.command_id,
                status=ResponseStatus.ERROR,
                data={},
                error_message=str(e)
            )
    
    def handle_llm_command(self, command: Command) -> Response:
        """Handle LLM API interactions."""
        if not self.llm_api_key:
            return Response(
                command_id=command.command_id,
                status=ResponseStatus.ERROR,
                data={},
                error_message="LLM API key not configured"
            )
        
        prompt = command.payload.get("prompt", "")
        model = command.payload.get("model", "gpt-3.5-turbo")
        max_tokens = command.payload.get("max_tokens", 1000)
        temperature = command.payload.get("temperature", 0.7)
        
        if not prompt:
            return Response(
                command_id=command.command_id,
                status=ResponseStatus.ERROR,
                data={},
                error_message="No prompt specified"
            )
        
        logger.info(f"Sending prompt to LLM API: {prompt[:50]}...")
        
        try:
            # Build OpenAI API request
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.llm_api_key}"
            }
            
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": temperature
            }
            
            # Make the API request
            response = requests.post(self.llm_api_url, headers=headers, json=payload)
            response.raise_for_status()
            
            # Parse response
            response_data = response.json()
            completion = response_data["choices"][0]["message"]["content"]
            
            return Response(
                command_id=command.command_id,
                status=ResponseStatus.SUCCESS,
                data={
                    "completion": completion,
                    "model": model,
                    "usage": response_data.get("usage", {})
                }
            )
            
        except Exception as e:
            logger.error(f"Error calling LLM API: {e}")
            return Response(
                command_id=command.command_id,
                status=ResponseStatus.ERROR,
                data={},
                error_message=str(e)
            )
    
    def handle_file_command(self, command: Command) -> Response:
        """Handle file operations."""
        action = command.payload.get("action", "")
        path = command.payload.get("path", "")
        content = command.payload.get("content")
        
        if not action or not path:
            return Response(
                command_id=command.command_id,
                status=ResponseStatus.ERROR,
                data={},
                error_message="Missing action or path"
            )
        
        logger.info(f"File operation: {action} on {path}")
        
        try:
            if action == "read":
                # Read file
                if not os.path.exists(path):
                    return Response(
                        command_id=command.command_id,
                        status=ResponseStatus.ERROR,
                        data={},
                        error_message=f"File not found: {path}"
                    )
                
                with open(path, "r") as f:
                    content = f.read()
                
                return Response(
                    command_id=command.command_id,
                    status=ResponseStatus.SUCCESS,
                    data={"content": content}
                )
                
            elif action == "write":
                # Write file
                if content is None:
                    return Response(
                        command_id=command.command_id,
                        status=ResponseStatus.ERROR,
                        data={},
                        error_message="No content provided"
                    )
                
                # Ensure directory exists
                os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
                
                with open(path, "w") as f:
                    f.write(content)
                
                return Response(
                    command_id=command.command_id,
                    status=ResponseStatus.SUCCESS,
                    data={"bytes_written": len(content)}
                )
                
            elif action == "append":
                # Append to file
                if content is None:
                    return Response(
                        command_id=command.command_id,
                        status=ResponseStatus.ERROR,
                        data={},
                        error_message="No content provided"
                    )
                
                # Ensure directory exists
                os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
                
                with open(path, "a") as f:
                    f.write(content)
                
                return Response(
                    command_id=command.command_id,
                    status=ResponseStatus.SUCCESS,
                    data={"bytes_appended": len(content)}
                )
                
            elif action == "delete":
                # Delete file
                if not os.path.exists(path):
                    return Response(
                        command_id=command.command_id,
                        status=ResponseStatus.ERROR,
                        data={},
                        error_message=f"File not found: {path}"
                    )
                
                os.remove(path)
                
                return Response(
                    command_id=command.command_id,
                    status=ResponseStatus.SUCCESS,
                    data={}
                )
                
            elif action == "exists":
                # Check if file exists
                exists = os.path.exists(path)
                
                return Response(
                    command_id=command.command_id,
                    status=ResponseStatus.SUCCESS,
                    data={"exists": exists}
                )
                
            elif action == "list":
                # List directory contents
                if not os.path.isdir(path):
                    return Response(
                        command_id=command.command_id,
                        status=ResponseStatus.ERROR,
                        data={},
                        error_message=f"Not a directory: {path}"
                    )
                
                items = os.listdir(path)
                full_paths = [os.path.join(path, item) for item in items]
                
                # Get metadata
                result = []
                for i, item_path in enumerate(full_paths):
                    is_dir = os.path.isdir(item_path)
                    result.append({
                        "name": items[i],
                        "path": item_path,
                        "is_directory": is_dir,
                        "size": os.path.getsize(item_path) if not is_dir else 0
                    })
                
                return Response(
                    command_id=command.command_id,
                    status=ResponseStatus.SUCCESS,
                    data={"items": result}
                )
                
            else:
                return Response(
                    command_id=command.command_id,
                    status=ResponseStatus.ERROR,
                    data={},
                    error_message=f"Unsupported file action: {action}"
                )
                
        except Exception as e:
            logger.error(f"Error during file operation: {e}")
            return Response(
                command_id=command.command_id,
                status=ResponseStatus.ERROR,
                data={},
                error_message=str(e)
            )
    
    def handle_status_command(self, command: Command) -> Response:
        """Handle status check command."""
        import platform
        import psutil
        
        # Gather system information
        system_info = {
            "hostname": platform.node(),
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage('/').percent,
            "uptime": time.time() - psutil.boot_time()
        }
        
        return Response(
            command_id=command.command_id,
            status=ResponseStatus.SUCCESS,
            data={"system_info": system_info}
        )
    
    def handle_system_command(self, command: Command) -> Response:
        """Handle system-level commands."""
        action = command.payload.get("action", "")
        
        if action == "restart":
            # Schedule agent restart
            threading.Thread(target=self._restart_agent, daemon=True).start()
            
            return Response(
                command_id=command.command_id,
                status=ResponseStatus.SUCCESS,
                data={"message": "Agent restart initiated"}
            )
            
        elif action == "shutdown":
            # Schedule agent shutdown
            threading.Thread(target=self._shutdown_agent, daemon=True).start()
            
            return Response(
                command_id=command.command_id,
                status=ResponseStatus.SUCCESS,
                data={"message": "Agent shutdown initiated"}
            )
            
        else:
            return Response(
                command_id=command.command_id,
                status=ResponseStatus.ERROR,
                data={},
                error_message=f"Unsupported system action: {action}"
            )
    
    def _restart_agent(self):
        """Restart the agent."""
        logger.info("Restarting agent...")
        time.sleep(1)  # Brief delay to allow response to be sent
        
        # Stop the server
        self.stop()
        
        # Execute the restart command
        os.execv(sys.executable, [sys.executable] + sys.argv)
    
    def _shutdown_agent(self):
        """Shutdown the agent."""
        logger.info("Shutting down agent...")
        time.sleep(1)  # Brief delay to allow response to be sent
        
        # Stop the server
        self.stop()
        
        # Exit
        sys.exit(0)

def create_daemon():
    """Create a daemon process."""
    # First fork
    try:
        pid = os.fork()
        if pid > 0:
            # Exit first parent
            sys.exit(0)
    except OSError as e:
        logger.error(f"Fork #1 failed: {e}")
        sys.exit(1)
    
    # Decouple from parent environment
    os.chdir('/')
    os.setsid()
    os.umask(0)
    
    # Second fork
    try:
        pid = os.fork()
        if pid > 0:
            # Exit second parent
            sys.exit(0)
    except OSError as e:
        logger.error(f"Fork #2 failed: {e}")
        sys.exit(1)
    
    # Redirect standard file descriptors
    sys.stdout.flush()
    sys.stderr.flush()
    
    with open('/dev/null', 'r') as f:
        os.dup2(f.fileno(), sys.stdin.fileno())
    
    with open('/var/log/remote_agent.log', 'a+') as f:
        os.dup2(f.fileno(), sys.stdout.fileno())
    
    with open('/var/log/remote_agent_error.log', 'a+') as f:
        os.dup2(f.fileno(), sys.stderr.fileno())
    
    # Write PID file
    with open('/var/run/remote_agent.pid', 'w') as f:
        f.write(str(os.getpid()))

def main():
    """Main function to parse arguments and start the agent."""
    parser = argparse.ArgumentParser(description="Remote Agent Server")
    
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8765, help="Port to listen on")
    parser.add_argument("--llm-api-key", help="API key for LLM service")
    parser.add_argument("--llm-api-url", default="https://api.openai.com/v1/chat/completions", help="URL for LLM API")
    parser.add_argument("--encryption-key", help="Base64 encoded encryption key")
    parser.add_argument("--use-ssl", action="store_true", help="Use SSL for secure communication")
    parser.add_argument("--cert-file", help="SSL certificate file")
    parser.add_argument("--key-file", help="SSL key file")
    parser.add_argument("--daemon", action="store_true", help="Run as a daemon")
    
    args = parser.parse_args()
    
    # If API key not provided as argument, try to get it from environment
    if not args.llm_api_key:
        args.llm_api_key = os.environ.get("LLM_API_KEY")
    
    # If encryption key not provided as argument, try to get it from environment
    if not args.encryption_key:
        args.encryption_key = os.environ.get("ENCRYPTION_KEY")
    
    # Run as daemon if requested
    if args.daemon:
        create_daemon()
    
    # Create and start the agent
    agent = RemoteAgent(
        host=args.host,
        port=args.port,
        llm_api_key=args.llm_api_key,
        llm_api_url=args.llm_api_url,
        encryption_key=args.encryption_key,
        use_ssl=args.use_ssl,
        cert_file=args.cert_file,
        key_file=args.key_file
    )
    
    agent.start()

if __name__ == "__main__":
    main() 