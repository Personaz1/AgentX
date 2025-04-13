#!/usr/bin/env python3
import os
import sys
import json
import time
import logging
import argparse
from typing import Dict, Any, List, Optional, Union, Tuple
import base64

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.protocol import (
    Command, Response, ResponseStatus, CommandType,
    create_shell_command, create_llm_command, create_file_command, create_status_command
)
from shared.communication import CommunicationClient, SecureChannel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('agent_controller')

class AgentController:
    def __init__(
        self,
        host: str,
        port: int = 8765,
        encryption_key: Optional[str] = None,
        use_ssl: bool = False,
        cert_file: Optional[str] = None,
        timeout: int = 30
    ):
        # Create secure channel
        if encryption_key and encryption_key.startswith("base64:"):
            # Use base64 encoded key
            base64_key = encryption_key.split("base64:", 1)[1]
            secure_channel = SecureChannel.from_base64_key(base64_key)
        else:
            # Use plain text key
            secure_channel = SecureChannel(encryption_key) if encryption_key else SecureChannel()
            
        # Store base64 encoded key for reference
        self.encryption_key_base64 = secure_channel.get_key_base64()
        logger.info(f"Using encryption key (base64): {self.encryption_key_base64}")
        
        # Create communication client
        self.client = CommunicationClient(
            host=host,
            port=port,
            secure_channel=secure_channel,
            use_ssl=use_ssl,
            cert_file=cert_file
        )
        
        self.timeout = timeout
        self.host = host
        self.port = port
    
    def connect(self) -> bool:
        """Connect to the remote agent."""
        return self.client.connect()
    
    def disconnect(self):
        """Disconnect from the remote agent."""
        self.client.disconnect()
    
    def execute_shell_command(
        self, 
        command: str, 
        args: Optional[List[str]] = None,
        timeout: Optional[int] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """Execute a shell command on the remote agent."""
        cmd = create_shell_command(command, args)
        response = self.client.send_command(cmd)
        
        if not response:
            logger.error("Failed to get response from remote agent")
            return False, {"error": "No response from remote agent"}
        
        success = response.status == ResponseStatus.SUCCESS
        if not success:
            logger.error(f"Command failed: {response.error_message}")
        
        return success, response.data
    
    def query_llm(
        self,
        prompt: str,
        model: str = "gpt-3.5-turbo",
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> Tuple[bool, str]:
        """Query the LLM through the remote agent."""
        cmd = create_llm_command(prompt, model)
        cmd.payload["max_tokens"] = max_tokens
        cmd.payload["temperature"] = temperature
        
        response = self.client.send_command(cmd)
        
        if not response:
            logger.error("Failed to get response from remote agent")
            return False, "No response from remote agent"
        
        success = response.status == ResponseStatus.SUCCESS
        if not success:
            logger.error(f"LLM query failed: {response.error_message}")
            return False, response.error_message or "Unknown error"
        
        return True, response.data.get("completion", "")
    
    def read_file(self, path: str) -> Tuple[bool, str]:
        """Read a file from the remote agent."""
        cmd = create_file_command("read", path)
        response = self.client.send_command(cmd)
        
        if not response:
            logger.error("Failed to get response from remote agent")
            return False, "No response from remote agent"
        
        success = response.status == ResponseStatus.SUCCESS
        if not success:
            logger.error(f"File read failed: {response.error_message}")
            return False, response.error_message or "Unknown error"
        
        return True, response.data.get("content", "")
    
    def write_file(self, path: str, content: str) -> bool:
        """Write content to a file on the remote agent."""
        cmd = create_file_command("write", path, content)
        response = self.client.send_command(cmd)
        
        if not response:
            logger.error("Failed to get response from remote agent")
            return False
        
        success = response.status == ResponseStatus.SUCCESS
        if not success:
            logger.error(f"File write failed: {response.error_message}")
        
        return success
    
    def list_directory(self, path: str) -> Tuple[bool, List[Dict[str, Any]]]:
        """List contents of a directory on the remote agent."""
        cmd = create_file_command("list", path)
        response = self.client.send_command(cmd)
        
        if not response:
            logger.error("Failed to get response from remote agent")
            return False, []
        
        success = response.status == ResponseStatus.SUCCESS
        if not success:
            logger.error(f"Directory listing failed: {response.error_message}")
            return False, []
        
        return success, response.data.get("items", [])
    
    def get_system_info(self) -> Tuple[bool, Dict[str, Any]]:
        """Get system information from the remote agent."""
        cmd = create_status_command()
        response = self.client.send_command(cmd)
        
        if not response:
            logger.error("Failed to get response from remote agent")
            return False, {}
        
        success = response.status == ResponseStatus.SUCCESS
        if not success:
            logger.error(f"Status check failed: {response.error_message}")
            return False, {}
        
        return success, response.data.get("system_info", {})
    
    def restart_agent(self) -> bool:
        """Restart the remote agent."""
        cmd = Command(
            command_type=CommandType.SYSTEM,
            payload={"action": "restart"}
        )
        
        response = self.client.send_command(cmd)
        
        if not response:
            logger.error("Failed to get response from remote agent")
            return False
        
        success = response.status == ResponseStatus.SUCCESS
        if success:
            logger.info("Agent restart initiated")
            # Give some time for the agent to restart
            time.sleep(5)
        else:
            logger.error(f"Agent restart failed: {response.error_message}")
        
        return success
    
    def shutdown_agent(self) -> bool:
        """Shutdown the remote agent."""
        cmd = Command(
            command_type=CommandType.SYSTEM,
            payload={"action": "shutdown"}
        )
        
        response = self.client.send_command(cmd)
        
        if not response:
            logger.error("Failed to get response from remote agent")
            return False
        
        success = response.status == ResponseStatus.SUCCESS
        if success:
            logger.info("Agent shutdown initiated")
        else:
            logger.error(f"Agent shutdown failed: {response.error_message}")
        
        return success

def main():
    """Main function to parse arguments and start the controller."""
    parser = argparse.ArgumentParser(description="Remote Agent Controller")
    
    # Connection settings
    parser.add_argument("--host", required=True, help="Remote agent host")
    parser.add_argument("--port", type=int, default=8765, help="Remote agent port")
    parser.add_argument("--encryption-key", help="Encryption key")
    parser.add_argument("--use-ssl", action="store_true", help="Use SSL")
    parser.add_argument("--cert-file", help="SSL certificate file")
    
    # Command options
    parser.add_argument("--command", "-c", help="Shell command to execute")
    parser.add_argument("--args", nargs="+", help="Arguments for the shell command")
    
    parser.add_argument("--prompt", "-p", help="Prompt for LLM query")
    parser.add_argument("--model", default="gpt-3.5-turbo", help="Model to use for LLM query")
    
    parser.add_argument("--read-file", "-r", help="Path to read file from remote")
    parser.add_argument("--write-file", "-w", help="Path to write file to remote")
    parser.add_argument("--content", help="Content to write to file")
    parser.add_argument("--content-file", help="File containing content to write")
    
    parser.add_argument("--list-dir", "-l", help="Path to list directory contents")
    
    parser.add_argument("--status", "-s", action="store_true", help="Get remote system info")
    parser.add_argument("--restart", action="store_true", help="Restart the remote agent")
    parser.add_argument("--shutdown", action="store_true", help="Shutdown the remote agent")
    
    args = parser.parse_args()
    
    # Create controller
    controller = AgentController(
        host=args.host,
        port=args.port,
        encryption_key=args.encryption_key,
        use_ssl=args.use_ssl,
        cert_file=args.cert_file
    )
    
    # Connect to remote agent
    if not controller.connect():
        logger.error(f"Failed to connect to remote agent at {args.host}:{args.port}")
        return 1
    
    try:
        # Process commands based on arguments
        if args.command:
            success, data = controller.execute_shell_command(args.command, args.args)
            if success:
                print(f"Command executed successfully")
                if "stdout" in data:
                    print("\nStandard Output:")
                    print(data["stdout"])
                if "stderr" in data and data["stderr"]:
                    print("\nStandard Error:")
                    print(data["stderr"])
            else:
                print(f"Command failed: {data.get('error', 'Unknown error')}")
                return 1
        
        elif args.prompt:
            success, completion = controller.query_llm(args.prompt, args.model)
            if success:
                print(f"LLM Response:")
                print(completion)
            else:
                print(f"LLM query failed: {completion}")
                return 1
        
        elif args.read_file:
            success, content = controller.read_file(args.read_file)
            if success:
                print(content)
            else:
                print(f"File read failed: {content}")
                return 1
        
        elif args.write_file:
            # Get content from either --content or --content-file
            if args.content:
                content = args.content
            elif args.content_file:
                with open(args.content_file, "r") as f:
                    content = f.read()
            else:
                print("Error: --content or --content-file must be provided with --write-file")
                return 1
            
            success = controller.write_file(args.write_file, content)
            if success:
                print(f"File written successfully: {args.write_file}")
            else:
                print(f"File write failed")
                return 1
        
        elif args.list_dir:
            success, items = controller.list_directory(args.list_dir)
            if success:
                print(f"Contents of {args.list_dir}:")
                for item in items:
                    item_type = "DIR" if item["is_directory"] else "FILE"
                    size = "" if item["is_directory"] else f"{item['size']} bytes"
                    print(f"{item_type:<5} {item['name']:<40} {size}")
            else:
                print(f"Directory listing failed")
                return 1
        
        elif args.status:
            success, info = controller.get_system_info()
            if success:
                print("Remote System Information:")
                for key, value in info.items():
                    print(f"{key}: {value}")
            else:
                print(f"Failed to get system information")
                return 1
        
        elif args.restart:
            success = controller.restart_agent()
            if success:
                print("Agent restart initiated")
            else:
                print("Agent restart failed")
                return 1
        
        elif args.shutdown:
            success = controller.shutdown_agent()
            if success:
                print("Agent shutdown initiated")
            else:
                print("Agent shutdown failed")
                return 1
        
        else:
            print("No operation specified. Use --help to see available commands.")
            return 1
        
    finally:
        # Ensure we disconnect
        controller.disconnect()
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 