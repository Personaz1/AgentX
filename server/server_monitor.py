#!/usr/bin/env python3
"""
NeuroRAT Server Monitor - Additional monitoring capabilities for the C2 server
"""

import os
import sys
import time
import json
import logging
import threading
import argparse
import datetime
from typing import Dict, Any, List, Optional, Union
import sqlite3
import socket
import requests
import platform

# Add parent directory to import agent_protocol
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('server_monitor.log')
    ]
)
logger = logging.getLogger('server_monitor')

class NeuroRATMonitor:
    """Monitor for NeuroRAT C2 server"""
    
    def __init__(self, server_host: str, server_port: int, api_port: int = 5000, 
                db_path: str = "neurorat_monitor.db"):
        """
        Initialize the monitor.
        
        Args:
            server_host: C2 server host
            server_port: C2 server port
            api_port: Web API port
            db_path: Path to SQLite database
        """
        self.server_host = server_host
        self.server_port = server_port
        self.api_port = api_port
        self.db_path = db_path
        
        # Connection to the database
        self.db_conn = None
        
        # Initialize the database
        self._init_database()
        
        # Monitor state
        self.running = False
        self.monitor_thread = None
        
        # Statistics
        self.stats = {
            "server_uptime": 0,
            "connected_agents": 0,
            "total_agents": 0,
            "commands_sent": 0,
            "data_exfiltrated": 0,
            "last_command_time": 0,
            "server_load": 0.0
        }
    
    def _init_database(self) -> None:
        """Initialize the SQLite database"""
        try:
            self.db_conn = sqlite3.connect(self.db_path)
            cursor = self.db_conn.cursor()
            
            # Create tables if they don't exist
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS agents (
                agent_id TEXT PRIMARY KEY,
                first_seen REAL,
                last_seen REAL,
                os TEXT,
                hostname TEXT,
                username TEXT,
                ip_address TEXT,
                status TEXT
            )
            ''')
            
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS commands (
                command_id TEXT PRIMARY KEY,
                agent_id TEXT,
                command_type TEXT,
                command_data TEXT,
                timestamp REAL,
                status TEXT,
                response TEXT,
                FOREIGN KEY (agent_id) REFERENCES agents (agent_id)
            )
            ''')
            
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS events (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT,
                agent_id TEXT,
                event_data TEXT,
                timestamp REAL,
                FOREIGN KEY (agent_id) REFERENCES agents (agent_id)
            )
            ''')
            
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS files (
                file_id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT,
                filename TEXT,
                file_path TEXT,
                file_size INTEGER,
                file_hash TEXT,
                timestamp REAL,
                direction TEXT,
                FOREIGN KEY (agent_id) REFERENCES agents (agent_id)
            )
            ''')
            
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS server_stats (
                timestamp REAL PRIMARY KEY,
                connected_agents INTEGER,
                cpu_usage REAL,
                memory_usage REAL,
                network_in REAL,
                network_out REAL
            )
            ''')
            
            self.db_conn.commit()
            logger.info("Database initialized")
        except sqlite3.Error as e:
            logger.error(f"Database initialization error: {str(e)}")
            raise
    
    def start(self) -> None:
        """Start the monitor"""
        if self.running:
            logger.warning("Monitor is already running")
            return
        
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
        logger.info(f"Server monitor started. Monitoring {self.server_host}:{self.server_port}")
    
    def stop(self) -> None:
        """Stop the monitor"""
        if not self.running:
            logger.warning("Monitor is not running")
            return
        
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        
        if self.db_conn:
            self.db_conn.close()
            
        logger.info("Server monitor stopped")
    
    def _monitor_loop(self) -> None:
        """Main monitoring loop"""
        start_time = time.time()
        last_stats_time = 0
        
        while self.running:
            try:
                current_time = time.time()
                
                # Update server uptime
                self.stats["server_uptime"] = int(current_time - start_time)
                
                # Get agent data from API every 5 seconds
                if current_time - last_stats_time >= 5:
                    self._update_stats()
                    last_stats_time = current_time
                    
                    # Record stats in database
                    self._record_server_stats()
                
                # Check server status every minute
                if int(current_time) % 60 == 0:
                    self._check_server_status()
                
                # Sleep for a short time
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error in monitor loop: {str(e)}")
                time.sleep(5)  # Wait a bit before retrying
    
    def _update_stats(self) -> None:
        """Update statistics from the server API"""
        try:
            # Get agents information
            response = requests.get(f"http://{self.server_host}:{self.api_port}/api/agents")
            if response.status_code == 200:
                agents = response.json()
                self.stats["connected_agents"] = len(agents)
                self.stats["total_agents"] = len(agents)
                
                # Update agents in database
                for agent_id in agents:
                    self._update_agent(agent_id)
            
            # Get system information
            self.stats["server_load"] = self._get_system_load()
            
        except requests.RequestException as e:
            logger.error(f"Error updating stats from API: {str(e)}")
    
    def _update_agent(self, agent_id: str) -> None:
        """Update agent information in the database"""
        try:
            # Get agent details from API
            response = requests.get(f"http://{self.server_host}:{self.api_port}/api/agent/{agent_id}")
            if response.status_code != 200:
                logger.warning(f"Failed to get details for agent {agent_id}")
                return
                
            agent_data = response.json()
            
            # Check if agent exists in database
            cursor = self.db_conn.cursor()
            cursor.execute("SELECT agent_id FROM agents WHERE agent_id = ?", (agent_id,))
            exists = cursor.fetchone()
            
            if exists:
                # Update existing agent
                cursor.execute('''
                UPDATE agents SET
                    last_seen = ?,
                    os = ?,
                    hostname = ?,
                    username = ?,
                    ip_address = ?,
                    status = ?
                WHERE agent_id = ?
                ''', (
                    time.time(),
                    agent_data.get("system_info", {}).get("os", "unknown"),
                    agent_data.get("system_info", {}).get("hostname", "unknown"),
                    agent_data.get("system_info", {}).get("username", "unknown"),
                    agent_data.get("system_info", {}).get("network", {}).get("ip_address", "unknown"),
                    "active" if time.time() - agent_data.get("last_active", 0) < 300 else "inactive",
                    agent_id
                ))
            else:
                # Insert new agent
                cursor.execute('''
                INSERT INTO agents (
                    agent_id, first_seen, last_seen, os, hostname, username, ip_address, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    agent_id,
                    agent_data.get("first_seen", time.time()),
                    time.time(),
                    agent_data.get("system_info", {}).get("os", "unknown"),
                    agent_data.get("system_info", {}).get("hostname", "unknown"),
                    agent_data.get("system_info", {}).get("username", "unknown"),
                    agent_data.get("system_info", {}).get("network", {}).get("ip_address", "unknown"),
                    "active" if time.time() - agent_data.get("last_active", 0) < 300 else "inactive"
                ))
            
            self.db_conn.commit()
            
        except Exception as e:
            logger.error(f"Error updating agent {agent_id}: {str(e)}")
    
    def _check_server_status(self) -> None:
        """Check if the server is running"""
        try:
            # Check if port is open
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((self.server_host, self.server_port))
            if result == 0:
                logger.debug("Server is running")
            else:
                logger.warning(f"Server is not responding on port {self.server_port}")
                self._record_event("server_down", None, {"port": self.server_port})
            sock.close()
            
            # Check web API
            try:
                response = requests.get(f"http://{self.server_host}:{self.api_port}/")
                if response.status_code == 200:
                    logger.debug("Web API is running")
                else:
                    logger.warning(f"Web API returned status code {response.status_code}")
                    self._record_event("api_error", None, {"status_code": response.status_code})
            except requests.RequestException:
                logger.warning("Web API is not responding")
                self._record_event("api_down", None, {"port": self.api_port})
                
        except Exception as e:
            logger.error(f"Error checking server status: {str(e)}")
    
    def _get_system_load(self) -> float:
        """Get system load average"""
        try:
            if platform.system() == "Windows":
                # On Windows, use a simple CPU usage metric
                import psutil
                return psutil.cpu_percent(interval=0.1)
            else:
                # On Unix-like systems, get load average
                return os.getloadavg()[0]
        except:
            return 0.0
    
    def _record_server_stats(self) -> None:
        """Record server statistics in the database"""
        try:
            # Get system stats
            import psutil
            
            # Get stats
            cpu_usage = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            memory_usage = memory.percent
            
            # Get network stats (simplified)
            net_io = psutil.net_io_counters()
            network_in = net_io.bytes_recv
            network_out = net_io.bytes_sent
            
            # Record in database
            cursor = self.db_conn.cursor()
            cursor.execute('''
            INSERT INTO server_stats (
                timestamp, connected_agents, cpu_usage, memory_usage, network_in, network_out
            ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                time.time(),
                self.stats["connected_agents"],
                cpu_usage,
                memory_usage,
                network_in,
                network_out
            ))
            
            self.db_conn.commit()
            
        except Exception as e:
            logger.error(f"Error recording server stats: {str(e)}")
    
    def _record_event(self, event_type: str, agent_id: Optional[str], event_data: Dict[str, Any]) -> None:
        """Record an event in the database"""
        try:
            cursor = self.db_conn.cursor()
            cursor.execute('''
            INSERT INTO events (event_type, agent_id, event_data, timestamp)
            VALUES (?, ?, ?, ?)
            ''', (
                event_type,
                agent_id,
                json.dumps(event_data),
                time.time()
            ))
            
            self.db_conn.commit()
            
        except Exception as e:
            logger.error(f"Error recording event: {str(e)}")
    
    def get_agent_stats(self) -> Dict[str, Any]:
        """Get agent statistics"""
        stats = {
            "total": 0,
            "active": 0,
            "inactive": 0,
            "by_os": {},
            "newest": None,
            "oldest": None
        }
        
        try:
            cursor = self.db_conn.cursor()
            
            # Get total agents
            cursor.execute("SELECT COUNT(*) FROM agents")
            stats["total"] = cursor.fetchone()[0]
            
            # Get active agents (seen in the last 5 minutes)
            cursor.execute("SELECT COUNT(*) FROM agents WHERE last_seen > ?", (time.time() - 300,))
            stats["active"] = cursor.fetchone()[0]
            
            # Calculate inactive
            stats["inactive"] = stats["total"] - stats["active"]
            
            # Get OS breakdown
            cursor.execute("SELECT os, COUNT(*) FROM agents GROUP BY os")
            for row in cursor.fetchall():
                stats["by_os"][row[0]] = row[1]
            
            # Get newest agent
            cursor.execute("SELECT agent_id, first_seen FROM agents ORDER BY first_seen DESC LIMIT 1")
            newest = cursor.fetchone()
            if newest:
                stats["newest"] = {
                    "agent_id": newest[0],
                    "first_seen": newest[1]
                }
            
            # Get oldest agent
            cursor.execute("SELECT agent_id, first_seen FROM agents ORDER BY first_seen ASC LIMIT 1")
            oldest = cursor.fetchone()
            if oldest:
                stats["oldest"] = {
                    "agent_id": oldest[0],
                    "first_seen": oldest[1]
                }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting agent stats: {str(e)}")
            return stats
    
    def get_agent_details(self, agent_id: str) -> Dict[str, Any]:
        """Get details for a specific agent"""
        try:
            cursor = self.db_conn.cursor()
            cursor.execute("SELECT * FROM agents WHERE agent_id = ?", (agent_id,))
            agent = cursor.fetchone()
            
            if not agent:
                return {"error": "Agent not found"}
            
            # Get column names
            columns = [description[0] for description in cursor.description]
            agent_dict = dict(zip(columns, agent))
            
            # Get command history
            cursor.execute('''
            SELECT command_id, command_type, timestamp, status
            FROM commands
            WHERE agent_id = ?
            ORDER BY timestamp DESC
            LIMIT 20
            ''', (agent_id,))
            
            commands = []
            for row in cursor.fetchall():
                commands.append({
                    "command_id": row[0],
                    "command_type": row[1],
                    "timestamp": row[2],
                    "status": row[3]
                })
            
            agent_dict["commands"] = commands
            
            # Get file transfers
            cursor.execute('''
            SELECT filename, file_size, timestamp, direction
            FROM files
            WHERE agent_id = ?
            ORDER BY timestamp DESC
            LIMIT 10
            ''', (agent_id,))
            
            files = []
            for row in cursor.fetchall():
                files.append({
                    "filename": row[0],
                    "file_size": row[1],
                    "timestamp": row[2],
                    "direction": row[3]
                })
            
            agent_dict["files"] = files
            
            return agent_dict
            
        except Exception as e:
            logger.error(f"Error getting agent details: {str(e)}")
            return {"error": str(e)}
    
    def get_server_stats(self, timeframe: str = "hour") -> Dict[str, Any]:
        """Get server statistics for the specified timeframe"""
        stats = {
            "timestamps": [],
            "cpu_usage": [],
            "memory_usage": [],
            "connected_agents": [],
            "network_in": [],
            "network_out": []
        }
        
        try:
            cursor = self.db_conn.cursor()
            
            # Determine time range
            now = time.time()
            if timeframe == "hour":
                start_time = now - 3600
            elif timeframe == "day":
                start_time = now - 86400
            elif timeframe == "week":
                start_time = now - 604800
            else:
                start_time = now - 3600  # Default to hour
            
            # Get stats from database
            cursor.execute('''
            SELECT timestamp, cpu_usage, memory_usage, connected_agents, network_in, network_out
            FROM server_stats
            WHERE timestamp > ?
            ORDER BY timestamp ASC
            ''', (start_time,))
            
            for row in cursor.fetchall():
                stats["timestamps"].append(row[0])
                stats["cpu_usage"].append(row[1])
                stats["memory_usage"].append(row[2])
                stats["connected_agents"].append(row[3])
                stats["network_in"].append(row[4])
                stats["network_out"].append(row[5])
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting server stats: {str(e)}")
            return stats
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate a comprehensive report"""
        report = {
            "timestamp": time.time(),
            "server": {
                "host": self.server_host,
                "port": self.server_port,
                "uptime": self.stats["server_uptime"],
                "stats": self.get_server_stats("day")
            },
            "agents": {
                "stats": self.get_agent_stats(),
                "active": []
            },
            "events": []
        }
        
        try:
            cursor = self.db_conn.cursor()
            
            # Get active agents
            cursor.execute('''
            SELECT agent_id, os, hostname, username, ip_address, last_seen
            FROM agents
            WHERE last_seen > ?
            ORDER BY last_seen DESC
            ''', (time.time() - 300,))
            
            for row in cursor.fetchall():
                report["agents"]["active"].append({
                    "agent_id": row[0],
                    "os": row[1],
                    "hostname": row[2],
                    "username": row[3],
                    "ip_address": row[4],
                    "last_seen": row[5]
                })
            
            # Get recent events
            cursor.execute('''
            SELECT event_id, event_type, agent_id, event_data, timestamp
            FROM events
            ORDER BY timestamp DESC
            LIMIT 50
            ''')
            
            for row in cursor.fetchall():
                report["events"].append({
                    "event_id": row[0],
                    "event_type": row[1],
                    "agent_id": row[2],
                    "event_data": json.loads(row[3]) if row[3] else {},
                    "timestamp": row[4]
                })
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating report: {str(e)}")
            return report


def main():
    """Main entry point"""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="NeuroRAT Server Monitor")
    parser.add_argument("--server", default="localhost", help="C2 server host")
    parser.add_argument("--port", type=int, default=8000, help="C2 server port")
    parser.add_argument("--api-port", type=int, default=5000, help="Web API port")
    parser.add_argument("--db", default="neurorat_monitor.db", help="Database file path")
    parser.add_argument("--report", action="store_true", help="Generate and print a report")
    
    args = parser.parse_args()
    
    # Create and start the monitor
    monitor = NeuroRATMonitor(
        server_host=args.server,
        server_port=args.port,
        api_port=args.api_port,
        db_path=args.db
    )
    
    if args.report:
        # Generate and print a report
        report = monitor.generate_report()
        print(json.dumps(report, indent=2))
        return
    
    try:
        monitor.start()
        
        print(f"Monitoring NeuroRAT server at {args.server}:{args.port}")
        print("Press Ctrl+C to stop")
        
        # Keep the main thread running
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nStopping monitor...")
    finally:
        monitor.stop()


if __name__ == "__main__":
    main() 