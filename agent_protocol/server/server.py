#!/usr/bin/env python3
"""
Сервер агентского протокола.
Обеспечивает безопасное API для выполнения команд агентами.
"""

import os
import json
import time
import logging
import threading
import traceback
from typing import Dict, Any, Optional, Callable, List, Union
from concurrent.futures import ThreadPoolExecutor
from flask import Flask, request, jsonify, Response as FlaskResponse
import base64

from ..shared.protocol import (
    Command, Response, CommandTypes, parse_command,
    create_error_response, create_success_response
)
from ..shared.encryption import EncryptionManager, DHKeyExchange, generate_secure_token
from ..shared.key_exchange import KeyExchange, RSAKeyExchange

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация Flask приложения
app = Flask(__name__)


class AgentServer:
    """
    Сервер для управления агентами.
    Обрабатывает команды от клиентов и поддерживает шифрованное соединение.
    """
    
    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 8000,
        max_workers: int = 10,
        auth_required: bool = False,
        auth_token: str = None,
        ssl_cert: str = None,
        ssl_key: str = None
    ):
        """
        Инициализация сервера.
        
        Параметры:
        - host: Хост для прослушивания
        - port: Порт для прослушивания
        - max_workers: Максимальное количество рабочих потоков
        - auth_required: Требуется ли аутентификация
        - auth_token: Токен аутентификации (генерируется, если не указан)
        - ssl_cert: Путь к SSL сертификату
        - ssl_key: Путь к SSL ключу
        """
        self.host = host
        self.port = port
        self.max_workers = max_workers
        self.auth_required = auth_required
        self.auth_token = auth_token or generate_secure_token(32)
        self.ssl_cert = ssl_cert
        self.ssl_key = ssl_key
        
        # Пул потоков для обработки команд
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        
        # Словарь для хранения обработчиков команд
        self.command_handlers = {}
        
        # Словарь для хранения соединений с агентами
        self.agent_connections = {}
        
        # Регистрация маршрутов API
        self._register_routes()
        
        # Регистрация обработчиков команд по умолчанию
        self._register_default_handlers()
        
        # Инициализация шифрования
        self.encryption_managers = {}  # Для хранения менеджеров шифрования для разных агентов
        
        # Статус сервера
        self.running = False
    
    def start(self):
        """
        Запуск сервера.
        """
        logger.info(f"Запуск сервера на {self.host}:{self.port}")
        self.running = True
        
        # Настройка SSL, если указаны сертификаты
        ssl_context = None
        if self.ssl_cert and self.ssl_key:
            ssl_context = (self.ssl_cert, self.ssl_key)
        
        # Запуск Flask приложения
        kwargs = {
            "host": self.host,
            "port": self.port,
            "ssl_context": ssl_context,
            "threaded": True,
            "debug": False
        }
        
        # Запуск в отдельном потоке для возможности остановки
        thread = threading.Thread(target=lambda: app.run(**kwargs))
        thread.daemon = True
        thread.start()
        
        return thread
    
    def stop(self):
        """
        Остановка сервера.
        """
        logger.info("Остановка сервера")
        self.running = False
        self.executor.shutdown(wait=False)
    
    def _register_routes(self):
        """
        Регистрация маршрутов REST API.
        """
        # Маршрут для приема команд
        @app.route('/api/command', methods=['POST'])
        def receive_command():
            try:
                # Получение данных команды
                command_data = request.json
                
                # Проверка формата данных
                if not isinstance(command_data, dict):
                    return self._create_error_response("Invalid command format", 400)
                
                # Парсинг команды
                command = parse_command(command_data)
                
                # Проверка аутентификации
                if self.auth_required:
                    if not command.auth_token or command.auth_token != self.auth_token:
                        return self._create_error_response("Authentication failed", 401)
                
                # Проверка наличия ID агента
                if not command.agent_id:
                    return self._create_error_response("Agent ID is required", 400)
                
                # Обработка команды обмена ключами
                if command.command_type == CommandTypes.KEYEXCHANGE:
                    return self._handle_key_exchange(command)
                
                # Дешифрование команды, если она зашифрована
                if command.encrypted:
                    encryption_manager = self.encryption_managers.get(command.agent_id)
                    if encryption_manager:
                        try:
                            command = command.decrypt(encryption_manager)
                        except Exception as e:
                            logger.error(f"Ошибка дешифрования: {e}")
                            return self._create_error_response(f"Decryption error: {str(e)}", 400)
                    else:
                        logger.error(f"Для агента {command.agent_id} не найден менеджер шифрования")
                        return self._create_error_response("Encrypted command received but no encryption key found", 400)
                
                # Проверка наличия обработчика для типа команды
                if command.command_type not in self.command_handlers:
                    return self._create_error_response(f"Unsupported command type: {command.command_type}", 400)
                
                # Асинхронная обработка команды
                future = self.executor.submit(
                    self._execute_command_handler,
                    command
                )
                
                # Получение результата
                response = future.result()
                
                # Шифрование ответа, если команда была зашифрована
                if command.encrypted:
                    encryption_manager = self.encryption_managers.get(command.agent_id)
                    if encryption_manager:
                        try:
                            response = response.encrypt(encryption_manager)
                        except Exception as e:
                            logger.error(f"Ошибка шифрования ответа: {e}")
                            return self._create_error_response(f"Response encryption error: {str(e)}", 500)
                
                # Возврат ответа
                return jsonify(response.to_dict())
            
            except Exception as e:
                logger.error(f"Ошибка обработки команды: {e}")
                logger.error(traceback.format_exc())
                return self._create_error_response(f"Server error: {str(e)}", 500)
        
        # Маршрут для проверки статуса сервера
        @app.route('/api/status', methods=['GET'])
        def server_status():
            return jsonify({
                "status": "running" if self.running else "stopped",
                "agents": list(self.agent_connections.keys()),
                "server_time": time.time()
            })
    
    def _handle_key_exchange(self, command: Command) -> FlaskResponse:
        """
        Обработка команды обмена ключами.
        
        Параметры:
        - command: Команда обмена ключами
        
        Возвращает:
        - HTTP-ответ с результатом обмена ключами
        """
        try:
            # Определяем алгоритм обмена ключами
            algorithm = command.data.get("algorithm", "diffie-hellman")
            
            if algorithm == "diffie-hellman":
                # Проверка наличия необходимых параметров
                if "dh_public_key" not in command.data:
                    return self._create_error_response("Missing DH public key", 400)
                
                # Получение публичного ключа клиента
                client_key_str = command.data["dh_public_key"]
                
                try:
                    # Десериализуем ключ клиента
                    client_public_key = KeyExchange.deserialize_public_key(client_key_str)
                    
                    # Проверяем безопасность ключа клиента
                    if not KeyExchange.validate_dh_key(client_public_key):
                        return self._create_error_response("Invalid DH public key", 400)
                    
                    # Генерируем свою пару ключей
                    private_key, public_key = KeyExchange.generate_dh_keypair()
                    public_key_str = KeyExchange.serialize_public_key(public_key)
                    
                    # Вычисляем общий секретный ключ
                    shared_key = KeyExchange.compute_shared_key(private_key, client_public_key)
                    
                    # Получаем отпечаток ключа
                    key_fingerprint = KeyExchange.get_key_fingerprint(shared_key)
                    
                    # Создаем менеджер шифрования для этого агента
                    encryption_manager = EncryptionManager()
                    encryption_manager.set_key(shared_key)
                    
                    # Сохраняем менеджер шифрования для этого агента
                    self.encryption_managers[command.agent_id] = encryption_manager
                    
                    # Создаем ответ
                    response = Response(
                        command_id=command.command_id,
                        success=True,
                        data={
                            "algorithm": "diffie-hellman",
                            "dh_public_key": public_key_str
                        },
                        message=f"DH key exchange successful"
                    )
                    
                    logger.info(f"DH key exchange completed for agent {command.agent_id}. Key fingerprint: {key_fingerprint}")
                    return jsonify(response.to_dict()), 200
                    
                except Exception as e:
                    return self._create_error_response(f"DH key processing error: {str(e)}", 400)
                    
            elif algorithm == "rsa":
                # Существующая логика для RSA
                if "public_key" not in command.data:
                    return self._create_error_response("Missing RSA public key", 400)
                
                client_key = command.data["public_key"]
                
                try:
                    # Создание объекта для обмена ключами по RSA
                    rsa_key_exchange = RSAKeyExchange()
                    
                    # Загрузка публичного ключа клиента
                    rsa_key_exchange.load_peer_public_key(client_key)
                    
                    # Генерация AES-ключа и шифрование его с помощью RSA
                    aes_key = os.urandom(32)  # 256-bit
                    encrypted_key = rsa_key_exchange.encrypt_aes_key(aes_key)
                    
                    # Создание менеджера шифрования для этого агента
                    encryption_manager = EncryptionManager()
                    encryption_manager.set_key(aes_key)
                    
                    # Сохранение менеджера шифрования для этого агента
                    self.encryption_managers[command.agent_id] = encryption_manager
                    
                    # Создаем ответ
                    response = Response(
                        command_id=command.command_id,
                        success=True,
                        data={
                            "algorithm": "rsa",
                            "encrypted_key": base64.b64encode(encrypted_key).decode('utf-8')
                        },
                        message="RSA key exchange successful"
                    )
                    
                    logger.info(f"RSA key exchange completed for agent {command.agent_id}")
                    return jsonify(response.to_dict()), 200
                    
                except Exception as e:
                    return self._create_error_response(f"RSA key processing error: {str(e)}", 400)
                
            else:
                return self._create_error_response(f"Unsupported key exchange algorithm: {algorithm}", 400)
                
        except Exception as e:
            logger.error(f"Key exchange error: {str(e)}")
            return self._create_error_response(f"Key exchange error: {str(e)}", 500)
    
    def _create_error_response(self, message: str, status_code: int) -> FlaskResponse:
        """
        Создание ответа с ошибкой.
        
        Параметры:
        - message: Сообщение об ошибке
        - status_code: HTTP код ошибки
        
        Возвращает:
        - HTTP-ответ с ошибкой
        """
        return jsonify({
            "status": "error",
            "message": message
        }), status_code
    
    def _execute_command_handler(self, command: Command) -> Response:
        """
        Выполнение обработчика команды.
        
        Параметры:
        - command: Команда для обработки
        
        Возвращает:
        - Объект ответа
        """
        try:
            # Получение обработчика команды
            handler = self.command_handlers.get(command.command_type)
            
            # Обновление времени последнего подключения агента
            if command.agent_id in self.agent_connections:
                self.agent_connections[command.agent_id]["last_seen"] = time.time()
            else:
                # Добавление нового агента
                self.agent_connections[command.agent_id] = {
                    "last_seen": time.time(),
                    "encryption": False
                }
            
            # Выполнение обработчика
            if handler:
                return handler(command)
            else:
                return create_error_response(
                    command=command,
                    error_message=f"No handler for command type: {command.command_type}",
                    error_code=400
                )
        
        except Exception as e:
            logger.error(f"Ошибка при выполнении команды: {e}")
            logger.error(traceback.format_exc())
            return create_error_response(
                command=command,
                error_message=f"Command execution error: {str(e)}",
                error_code=500
            )
    
    def register_command_handler(self, command_type: str, handler: Callable[[Command], Response]):
        """
        Регистрация обработчика команды.
        
        Параметры:
        - command_type: Тип команды
        - handler: Функция-обработчик, принимающая команду и возвращающая ответ
        """
        self.command_handlers[command_type] = handler
        logger.info(f"Зарегистрирован обработчик для команды {command_type}")
    
    def _register_default_handlers(self):
        """
        Регистрация обработчиков команд по умолчанию.
        """
        # Обработчик для команды HEARTBEAT
        def handle_heartbeat(command: Command) -> Response:
            return create_success_response(
                command=command,
                data={"timestamp": time.time()}
            )
        
        # Обработчик для команды STATUS
        def handle_status(command: Command) -> Response:
            return create_success_response(
                command=command,
                data={
                    "server_status": "running" if self.running else "stopped",
                    "agent_id": command.agent_id,
                    "connected_agents": len(self.agent_connections),
                    "server_time": time.time(),
                    "encryption": command.agent_id in self.encryption_managers
                }
            )
        
        # Обработчик для команды SHELL
        def handle_shell(command: Command) -> Response:
            try:
                if "command" not in command.data:
                    return create_error_response(
                        command=command,
                        error_message="Shell command not provided",
                        error_code=400
                    )
                
                shell_command = command.data["command"]
                import subprocess
                
                # Выполнение команды и получение результата
                process = subprocess.Popen(
                    shell_command,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                # Получение вывода команды
                stdout, stderr = process.communicate(timeout=command.data.get("timeout", 60))
                
                return create_success_response(
                    command=command,
                    data={
                        "stdout": stdout,
                        "stderr": stderr,
                        "exit_code": process.returncode
                    }
                )
            
            except subprocess.TimeoutExpired:
                return create_error_response(
                    command=command,
                    error_message="Command execution timed out",
                    error_code=500
                )
            
            except Exception as e:
                logger.error(f"Ошибка при выполнении shell-команды: {e}")
                return create_error_response(
                    command=command,
                    error_message=f"Shell command execution error: {str(e)}",
                    error_code=500
                )
        
        # Обработчик для команды FILE
        def handle_file(command: Command) -> Response:
            try:
                if "operation" not in command.data or "file_path" not in command.data:
                    return create_error_response(
                        command=command,
                        error_message="Missing required file operation parameters",
                        error_code=400
                    )
                
                operation = command.data["operation"]
                file_path = command.data["file_path"]
                
                # Операция чтения файла
                if operation == "read":
                    if not os.path.exists(file_path):
                        return create_error_response(
                            command=command,
                            error_message=f"File not found: {file_path}",
                            error_code=404
                        )
                    
                    with open(file_path, 'r') as f:
                        content = f.read()
                    
                    return create_success_response(
                        command=command,
                        data={
                            "content": content,
                            "size": len(content),
                            "path": file_path
                        }
                    )
                
                # Операция записи файла
                elif operation == "write":
                    if "content" not in command.data:
                        return create_error_response(
                            command=command,
                            error_message="Content parameter required for write operation",
                            error_code=400
                        )
                    
                    content = command.data["content"]
                    
                    # Создание директории, если не существует
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    
                    with open(file_path, 'w') as f:
                        f.write(content)
                    
                    return create_success_response(
                        command=command,
                        data={
                            "size": len(content),
                            "path": file_path
                        }
                    )
                
                # Операция удаления файла
                elif operation == "delete":
                    if not os.path.exists(file_path):
                        return create_error_response(
                            command=command,
                            error_message=f"File not found: {file_path}",
                            error_code=404
                        )
                    
                    os.remove(file_path)
                    
                    return create_success_response(
                        command=command,
                        data={
                            "path": file_path,
                            "deleted": True
                        }
                    )
                
                # Операция получения списка файлов в директории
                elif operation == "list":
                    if not os.path.exists(file_path) or not os.path.isdir(file_path):
                        return create_error_response(
                            command=command,
                            error_message=f"Directory not found: {file_path}",
                            error_code=404
                        )
                    
                    # Получение списка файлов и директорий
                    items = []
                    for item in os.listdir(file_path):
                        item_path = os.path.join(file_path, item)
                        items.append({
                            "name": item,
                            "path": item_path,
                            "size": os.path.getsize(item_path) if os.path.isfile(item_path) else 0,
                            "type": "file" if os.path.isfile(item_path) else "directory",
                            "modified": os.path.getmtime(item_path)
                        })
                    
                    return create_success_response(
                        command=command,
                        data={
                            "path": file_path,
                            "items": items
                        }
                    )
                
                else:
                    return create_error_response(
                        command=command,
                        error_message=f"Unsupported file operation: {operation}",
                        error_code=400
                    )
            
            except Exception as e:
                logger.error(f"Ошибка при выполнении файловой операции: {e}")
                return create_error_response(
                    command=command,
                    error_message=f"File operation error: {str(e)}",
                    error_code=500
                )
        
        # Обработчик для команды PROCESS
        def handle_process(command: Command) -> Response:
            try:
                if "operation" not in command.data:
                    return create_error_response(
                        command=command,
                        error_message="Missing process operation parameter",
                        error_code=400
                    )
                
                operation = command.data["operation"]
                
                # Операция запуска процесса
                if operation == "start":
                    if "command" not in command.data:
                        return create_error_response(
                            command=command,
                            error_message="Command parameter required for start operation",
                            error_code=400
                        )
                    
                    process_command = command.data["command"]
                    import subprocess
                    
                    # Запуск процесса
                    process = subprocess.Popen(
                        process_command,
                        shell=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                    
                    return create_success_response(
                        command=command,
                        data={
                            "pid": process.pid,
                            "command": process_command
                        }
                    )
                
                # Операция остановки процесса
                elif operation == "stop":
                    if "process_id" not in command.data:
                        return create_error_response(
                            command=command,
                            error_message="Process ID required for stop operation",
                            error_code=400
                        )
                    
                    process_id = command.data["process_id"]
                    import signal
                    
                    # Отправка сигнала SIGTERM процессу
                    os.kill(process_id, signal.SIGTERM)
                    
                    return create_success_response(
                        command=command,
                        data={
                            "pid": process_id,
                            "stopped": True
                        }
                    )
                
                # Операция получения списка процессов
                elif operation == "list":
                    import psutil
                    
                    # Получение списка процессов
                    processes = []
                    for process in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent']):
                        try:
                            process_info = process.info
                            processes.append({
                                "pid": process_info["pid"],
                                "name": process_info["name"],
                                "user": process_info["username"],
                                "cpu": process_info["cpu_percent"],
                                "memory": process_info["memory_percent"]
                            })
                        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                            pass
                    
                    return create_success_response(
                        command=command,
                        data={
                            "processes": processes
                        }
                    )
                
                else:
                    return create_error_response(
                        command=command,
                        error_message=f"Unsupported process operation: {operation}",
                        error_code=400
                    )
            
            except Exception as e:
                logger.error(f"Ошибка при выполнении операции с процессом: {e}")
                return create_error_response(
                    command=command,
                    error_message=f"Process operation error: {str(e)}",
                    error_code=500
                )
        
        # Регистрация обработчиков
        self.register_command_handler(CommandTypes.HEARTBEAT, handle_heartbeat)
        self.register_command_handler(CommandTypes.STATUS, handle_status)
        self.register_command_handler(CommandTypes.SHELL, handle_shell)
        self.register_command_handler(CommandTypes.FILE, handle_file)
        self.register_command_handler(CommandTypes.PROCESS, handle_process)


# Пример использования сервера
if __name__ == "__main__":
    server = AgentServer(host="0.0.0.0", port=8000, auth_required=True)
    server_thread = server.start()
    
    try:
        # Вывод информации о сервере
        print(f"Сервер запущен на http://{server.host}:{server.port}")
        print(f"Токен аутентификации: {server.auth_token}")
        
        # Ожидание завершения сервера (например, по Ctrl+C)
        server_thread.join()
    
    except KeyboardInterrupt:
        print("Остановка сервера...")
        server.stop() 