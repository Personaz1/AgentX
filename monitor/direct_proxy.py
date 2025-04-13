#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NeuroRAT API Proxy - Перехват и логирование коммуникации между агентами и сервером
"""
import os
import time
import json
import logging
import datetime
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.request
import urllib.error
from urllib.parse import urlparse

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('neurorat_proxy.log')
    ]
)
logger = logging.getLogger("neurorat-proxy")

# Настройки прокси
LOCAL_PORT = 8888  # Порт, на котором будет работать прокси
TARGET_HOST = "localhost"  # Хост сервера NeuroRAT
TARGET_PORT = "5001"  # Порт сервера NeuroRAT
TARGET_URL = f"http://{TARGET_HOST}:{TARGET_PORT}"

# Журнал запросов
request_log = []

class ProxyHTTPRequestHandler(BaseHTTPRequestHandler):
    """Обработчик HTTP-запросов для проксирования и логирования"""
    
    def do_GET(self):
        """Обработка GET-запросов"""
        self._handle_request("GET")
    
    def do_POST(self):
        """Обработка POST-запросов"""
        self._handle_request("POST")
    
    def do_PUT(self):
        """Обработка PUT-запросов"""
        self._handle_request("PUT")
    
    def do_DELETE(self):
        """Обработка DELETE-запросов"""
        self._handle_request("DELETE")
    
    def _handle_request(self, method):
        """Обработка запроса любого типа"""
        url_parts = urlparse(self.path)
        target_path = url_parts.path
        
        # Если запрос идет к /proxy/, перенаправляем на целевой сервер
        if target_path.startswith("/proxy/"):
            target_path = target_path[7:]  # Удаляем /proxy/ из пути
            self._proxy_request(method, target_path, url_parts.query)
        # Если запрос к корню, показываем интерфейс логов
        elif target_path == "/" or target_path == "":
            self._serve_logs_interface()
        # Если запрос к /api/logs, возвращаем логи в формате JSON
        elif target_path == "/api/logs":
            self._serve_logs_json()
        # Если запрос к /api/clear, очищаем логи
        elif target_path == "/api/clear":
            self._clear_logs()
        else:
            self.send_error(404, "Файл не найден")
    
    def _proxy_request(self, method, target_path, query_string):
        """Проксирование запроса на целевой сервер"""
        target_url = f"{TARGET_URL}/{target_path}"
        if query_string:
            target_url += f"?{query_string}"
        
        # Считываем тело запроса, если оно есть
        content_length = int(self.headers.get('Content-Length', 0))
        request_body = self.rfile.read(content_length) if content_length > 0 else None
        
        # Логируем запрос
        request_entry = {
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "method": method,
            "path": target_path,
            "query": query_string,
            "headers": dict(self.headers.items()),
            "body": None
        }
        
        if request_body:
            try:
                request_entry["body"] = json.loads(request_body)
            except:
                request_entry["body"] = str(request_body)
        
        # Создаем запрос
        req = urllib.request.Request(
            url=target_url,
            data=request_body,
            headers={key: value for key, value in self.headers.items() if key.lower() != 'host'},
            method=method
        )
        
        try:
            # Отправляем запрос и получаем ответ
            with urllib.request.urlopen(req) as response:
                response_body = response.read()
                response_code = response.code
                response_headers = response.info()
                
                # Отправляем клиенту тот же код состояния
                self.send_response(response_code)
                
                # И те же заголовки
                for header, value in response_headers.items():
                    if header.lower() not in ('transfer-encoding', 'content-length'):
                        self.send_header(header, value)
                
                # Устанавливаем правильную длину ответа
                self.send_header('Content-Length', len(response_body))
                self.end_headers()
                
                # Отправляем тело ответа
                self.wfile.write(response_body)
                
                # Логируем ответ
                response_entry = {
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "status_code": response_code,
                    "headers": dict(response_headers.items()),
                    "body": None
                }
                
                try:
                    response_entry["body"] = json.loads(response_body)
                except:
                    response_entry["body"] = str(response_body)
                
                # Создаем запись в журнале
                log_entry = {
                    "id": len(request_log) + 1,
                    "request": request_entry,
                    "response": response_entry
                }
                
                # Добавляем в журнал
                request_log.append(log_entry)
                
                # Логируем в консоль
                logger.info(f"PROXY: {method} {target_path} -> {response_code}")
                
        except urllib.error.HTTPError as e:
            # В случае ошибки HTTP возвращаем клиенту тот же код ошибки
            self.send_response(e.code)
            for header, value in e.headers.items():
                if header.lower() not in ('transfer-encoding', 'content-length'):
                    self.send_header(header, value)
            self.end_headers()
            self.wfile.write(e.read())
            
            logger.error(f"PROXY ERROR: {method} {target_path} -> {e.code}")
            
        except Exception as e:
            # В случае других ошибок возвращаем ошибку 500
            self.send_error(500, str(e))
            logger.error(f"PROXY EXCEPTION: {method} {target_path} -> {str(e)}")
    
    def _serve_logs_interface(self):
        """Отдача веб-интерфейса для просмотра логов"""
        html = """
        <!DOCTYPE html>
        <html lang="ru">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>NeuroRAT API Proxy - Логи запросов</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background: #1e1e1e;
                    color: #ddd;
                }
                h1, h2 {
                    color: #ff5277;
                }
                .log-container {
                    margin-bottom: 20px;
                }
                .log-entry {
                    background: #252525;
                    border-radius: 5px;
                    padding: 15px;
                    margin-bottom: 15px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.3);
                }
                .request-info {
                    color: #5eba7d;
                    font-weight: bold;
                    border-bottom: 1px solid #444;
                    padding-bottom: 10px;
                    margin-bottom: 10px;
                }
                .response-info {
                    color: #569cd6;
                    font-weight: bold;
                    border-bottom: 1px solid #444;
                    padding-bottom: 10px;
                    margin-bottom: 10px;
                }
                .timestamp {
                    color: #888;
                    font-size: 0.8em;
                }
                pre {
                    background: #333;
                    padding: 10px;
                    border-radius: 3px;
                    overflow-x: auto;
                    white-space: pre-wrap;
                    word-wrap: break-word;
                }
                .controls {
                    margin-bottom: 20px;
                }
                button {
                    padding: 10px 15px;
                    background: #0078d7;
                    color: white;
                    border: none;
                    border-radius: 3px;
                    cursor: pointer;
                    margin-right: 10px;
                }
                button.danger {
                    background: #d74040;
                }
                button:hover {
                    opacity: 0.9;
                }
            </style>
        </head>
        <body>
            <h1>🧠 NeuroRAT API Proxy - Логи запросов</h1>
            
            <div class="controls">
                <button onclick="refreshLogs()">Обновить</button>
                <button class="danger" onclick="clearLogs()">Очистить логи</button>
            </div>
            
            <div id="logs-container" class="log-container">
                <p>Загрузка логов...</p>
            </div>
            
            <script>
                // Функция для загрузки логов
                function loadLogs() {
                    fetch('/api/logs')
                        .then(response => response.json())
                        .then(data => {
                            const container = document.getElementById('logs-container');
                            if (data.length === 0) {
                                container.innerHTML = '<p>Нет зарегистрированных запросов</p>';
                                return;
                            }
                            
                            let html = '';
                            data.reverse().forEach(entry => {
                                html += `
                                    <div class="log-entry">
                                        <div class="request-info">
                                            <span class="timestamp">${entry.request.timestamp}</span>
                                            <div>${entry.request.method} ${entry.request.path}</div>
                                        </div>
                                        <pre>${JSON.stringify(entry.request.body, null, 2)}</pre>
                                        
                                        <div class="response-info">
                                            <span class="timestamp">${entry.response.timestamp}</span>
                                            <div>Статус: ${entry.response.status_code}</div>
                                        </div>
                                        <pre>${JSON.stringify(entry.response.body, null, 2)}</pre>
                                    </div>
                                `;
                            });
                            
                            container.innerHTML = html;
                        })
                        .catch(error => {
                            console.error('Error loading logs:', error);
                            document.getElementById('logs-container').innerHTML = 
                                `<p>Ошибка загрузки логов: ${error.message}</p>`;
                        });
                }
                
                // Обновление логов
                function refreshLogs() {
                    loadLogs();
                }
                
                // Очистка логов
                function clearLogs() {
                    if (confirm('Вы уверены, что хотите очистить все логи?')) {
                        fetch('/api/clear', { method: 'POST' })
                            .then(() => {
                                loadLogs();
                            })
                            .catch(error => {
                                console.error('Error clearing logs:', error);
                                alert(`Ошибка очистки логов: ${error.message}`);
                            });
                    }
                }
                
                // Загружаем логи при загрузке страницы
                document.addEventListener('DOMContentLoaded', loadLogs);
                
                // Автоматическое обновление каждые 5 секунд
                setInterval(loadLogs, 5000);
            </script>
        </body>
        </html>
        """
        
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', len(html.encode('utf-8')))
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def _serve_logs_json(self):
        """Отдача логов в формате JSON"""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(request_log).encode('utf-8'))
    
    def _clear_logs(self):
        """Очистка логов"""
        global request_log
        request_log = []
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"status": "ok", "message": "Logs cleared"}).encode('utf-8'))

def run_proxy_server(port=LOCAL_PORT):
    """Запуск прокси-сервера"""
    server_address = ('', port)
    httpd = HTTPServer(server_address, ProxyHTTPRequestHandler)
    logger.info(f"Запуск NeuroRAT API Proxy на порту {port}")
    logger.info(f"Интерфейс логов доступен по адресу: http://localhost:{port}/")
    logger.info(f"Для использования прокси, направляйте запросы на: http://localhost:{port}/proxy/")
    httpd.serve_forever()

if __name__ == "__main__":
    try:
        run_proxy_server()
    except KeyboardInterrupt:
        logger.info("Остановка прокси-сервера по запросу пользователя")
    except Exception as e:
        logger.error(f"Ошибка при запуске прокси-сервера: {e}") 