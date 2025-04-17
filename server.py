#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import logging
from flask import Flask, render_template, request, jsonify, redirect, url_for, send_from_directory

# Добавляем пути для импорта модулей
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'core'))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'server'))

# Настройка логирования
if not os.path.exists('logs'):
    os.makedirs('logs')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/server.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Определяем путь к UI
FRONTEND_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'neurorat-ui/dist')
if not os.path.exists(FRONTEND_PATH):
    logger.warning(f"Путь к UI не найден: {FRONTEND_PATH}")
    logger.warning("Возможно, UI не был скомпилирован. Запустите 'cd neurorat-ui && npm run build'")

app = Flask(__name__, static_folder=FRONTEND_PATH, static_url_path='')

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/admin')
def admin():
    return app.send_static_file('index.html')

@app.route('/assets/<path:path>')
def serve_assets(path):
    return send_from_directory(os.path.join(FRONTEND_PATH, 'assets'), path)

@app.route('/api/status')
def status():
    return jsonify({'status': 'ok', 'version': '1.0.0'})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    # Заглушка для аутентификации
    if username == 'admin' and password == 'admin':
        return jsonify({'status': 'success', 'token': 'dummy_token'})
    return jsonify({'status': 'error', 'message': 'Invalid credentials'}), 401

@app.route('/api/zonds')
def get_zonds():
    # Заглушка для получения списка зондов
    zonds = [
        {
            'id': 'zond-1',
            'name': 'Test Zond 1',
            'status': 'ACTIVE',
            'ipAddress': '192.168.1.100',
            'os': 'Linux',
            'lastSeen': '2023-04-14T10:30:00Z'
        },
        {
            'id': 'zond-2',
            'name': 'Test Zond 2',
            'status': 'INACTIVE',
            'ipAddress': '192.168.1.101',
            'os': 'Windows',
            'lastSeen': '2023-04-14T09:15:00Z'
        }
    ]
    return jsonify(zonds)

@app.route('/api/tasks')
def get_tasks():
    # Заглушка для получения списка задач
    tasks = [
        {
            'id': 'task-1',
            'zondId': 'zond-1',
            'command': 'scan_network',
            'status': 'COMPLETED',
            'createdAt': '2023-04-14T08:30:00Z',
            'completedAt': '2023-04-14T08:35:00Z'
        },
        {
            'id': 'task-2',
            'zondId': 'zond-2',
            'command': 'gather_credentials',
            'status': 'PENDING',
            'createdAt': '2023-04-14T09:20:00Z',
            'completedAt': None
        }
    ]
    return jsonify(tasks)

if __name__ == '__main__':
    logger.info("Starting server...")
    app.run(host='0.0.0.0', port=8080, debug=True) 