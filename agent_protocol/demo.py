#!/usr/bin/env python3
"""
Demo script to demonstrate agent communication.
This shows how to use the controller to communicate with the remote agent.
"""

import os
import sys
import time
import argparse
import logging

from client.controller import AgentController

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('agent_demo')

def run_demo(host, port, encryption_key):
    """Run the demo sequence to demonstrate agent communication."""
    print(f"Connecting to remote agent at {host}:{port}...")
    
    # Create controller
    controller = AgentController(
        host=host,
        port=port,
        encryption_key=encryption_key
    )
    
    # Connect to the remote agent
    if not controller.connect():
        print("Failed to connect to remote agent. Check your connection settings.")
        return 1
    
    try:
        print("\n===== AGENT COMMUNICATION DEMO =====\n")
        
        # 1. Get system information
        print("\n[1] Getting system information...")
        success, info = controller.get_system_info()
        if success:
            print("Remote system information:")
            for key, value in info.items():
                print(f"  {key}: {value}")
        else:
            print("Failed to get system information")
        
        input("\nPress Enter to continue...")
        
        # 2. Execute shell command
        print("\n[2] Executing shell commands...")
        success, result = controller.execute_shell_command("uname -a")
        if success:
            print(f"Command output: {result['stdout']}")
        else:
            print("Failed to execute command")
            
        # Execute another command
        success, result = controller.execute_shell_command("ls -la /tmp")
        if success:
            print(f"\nFiles in /tmp directory:")
            print(result['stdout'])
        
        input("\nPress Enter to continue...")
        
        # 3. Write a file
        print("\n[3] Writing a file on remote system...")
        content = """#!/bin/bash
echo "Hello from the remote agent!"
echo "Current time: $(date)"
echo "Hostname: $(hostname)"
"""
        success = controller.write_file("/tmp/agent_demo.sh", content)
        if success:
            print("File written successfully to /tmp/agent_demo.sh")
            
            # Make it executable and run it
            success, _ = controller.execute_shell_command("chmod +x /tmp/agent_demo.sh")
            if success:
                print("\nExecuting the script...")
                success, result = controller.execute_shell_command("/tmp/agent_demo.sh")
                if success:
                    print(f"Script output:\n{result['stdout']}")
        else:
            print("Failed to write file")
        
        input("\nPress Enter to continue...")
        
        # 4. Query LLM
        print("\n[4] Querying LLM API through remote agent...")
        success, completion = controller.query_llm(
            prompt="Write a short poem about AI agents working remotely.",
            model="gpt-3.5-turbo"
        )
        if success:
            print("LLM Response:")
            print(completion)
        else:
            print(f"LLM query failed: {completion}")
            print("Note: This requires a valid API key to be configured on the remote agent.")
        
        input("\nPress Enter to continue...")
        
        # 5. List directory
        print("\n[5] Listing directory contents...")
        success, items = controller.list_directory("/etc")
        if success:
            print("Files in /etc directory:")
            # Show just the first 10 items
            for item in items[:10]:
                item_type = "DIR " if item["is_directory"] else "FILE"
                size = "" if item["is_directory"] else f"{item['size']} bytes"
                print(f"  {item_type} {item['name']:<30} {size}")
            print(f"  ... and {len(items) - 10} more items")
        else:
            print("Failed to list directory")
        
        print("\n===== DEMO COMPLETED SUCCESSFULLY =====")
        
    except KeyboardInterrupt:
        print("\nDemo interrupted by user")
    except Exception as e:
        print(f"\nError during demo: {e}")
    finally:
        # Ensure we disconnect
        controller.disconnect()
        print("\nDisconnected from remote agent")
    
    return 0

def main():
    """Main function to parse arguments and run the demo."""
    parser = argparse.ArgumentParser(description="Agent Communication Demo")
    
    parser.add_argument("--host", required=True, help="Remote agent host")
    parser.add_argument("--port", type=int, default=8765, help="Remote agent port")
    parser.add_argument("--encryption-key", required=True, help="Encryption key")
    
    args = parser.parse_args()
    
    return run_demo(args.host, args.port, args.encryption_key)

if __name__ == "__main__":
    sys.exit(main()) 