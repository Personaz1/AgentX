#!/usr/bin/env python3
"""
Клиентский модуль для управления агентами и отправки команд.
"""

import time
import uuid
import json
import logging
import threading
from typing import Dict, List, Any, Optional, Callable

from .shared.protocol import Command, Response, CommandType, create_keyexchange_command, complete_keyexchange
from .shared.encryption import EncryptionManager

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('client.log')
    ]
)
logger = logging.getLogger('client')


class AgentClient:
    """
    Клиент для управления агентами и отправки команд.
    
    Позволяет устанавливать соединение с агентами, отправлять команды и получать ответы.
    """
    
    def __init__(
        self, 
        server_host: str,
        server_port: int,
        admin_token: Optional[str] = None,
        use_ssl: bool = True,
        use_encryption: bool = True
    ):
        """
        Инициализация клиента.
        
        Параметры:
        - server_host: Хост сервера
        - server_port: Порт сервера
        - admin_token: Токен администратора для аутентификации
        - use_ssl: Использовать ли SSL для соединения
        - use_encryption: Использовать ли шифрование данных
        """
        self.server_host = server_host
        self.server_port = server_port
        self.admin_token = admin_token
        self.use_ssl = use_ssl
        self.use_encryption = use_encryption
        
        # Инициализация шифрования
        if use_encryption:
            self.encryption_manager = EncryptionManager()
        else:
            self.encryption_manager = None
        
        # Установка соединения с сервером
        self.connected = False
        self.connection = None
        
        # Кэш агентов
        self.agents_cache = {}
        self.agents_cache_timestamp = 0
        self.agents_cache_ttl = 60  # seconds
    
    def connect(self) -> bool:
        """
        Установка соединения с сервером.
        
        Возвращает:
        - Успешность подключения
        """
        import socket
        import ssl
        
        try:
            # Создаем сокет
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            
            # Настраиваем SSL, если нужно
            if self.use_ssl:
                context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
                sock = context.wrap_socket(sock, server_hostname=self.server_host)
            
            # Подключаемся к серверу
            sock.connect((self.server_host, self.server_port))
            self.connection = sock
            self.connected = True
            logger.info(f"Подключен к серверу {self.server_host}:{self.server_port}")
            
            # Если используем шифрование, выполняем обмен ключами
            if self.use_encryption and self.encryption_manager:
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
        
        if self.connection:
            try:
                self.connection.close()
            except Exception as e:
                logger.error(f"Ошибка при закрытии соединения: {str(e)}")
            
            self.connection = None
    
    def _perform_key_exchange(self) -> bool:
        """
        Выполнение обмена ключами с сервером.
        
        Возвращает:
        - Успешность обмена ключами
        """
        try:
            # Создаем команду для обмена ключами
            client_id = str(uuid.uuid4())
            key_exchange_cmd = create_keyexchange_command(
                client_id,
                self.encryption_manager,
                self.admin_token
            )
            
            # Отправляем команду
            key_exchange_json = key_exchange_cmd.to_json()
            self.connection.sendall(f"{key_exchange_json}\n".encode('utf-8'))
            
            # Получаем ответ
            response_json = self._receive_data()
            if not response_json:
                return False
            
            # Парсим ответ
            response = Response.from_json(response_json)
            
            # Завершаем обмен ключами
            return complete_keyexchange(response, self.encryption_manager)
            
        except Exception as e:
            logger.error(f"Ошибка при обмене ключами: {str(e)}")
            return False
    
    def _receive_data(self) -> Optional[str]:
        """
        Получение данных от сервера.
        
        Возвращает:
        - Полученные данные или None в случае ошибки
        """
        try:
            buffer = b""
            while self.connected:
                data = self.connection.recv(4096)
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
    
    def send_command(
        self, 
        cmd_type: str, 
        agent_id: Optional[str] = None, 
        data: Any = None,
        timeout: int = 60
    ) -> Optional[Response]:
        """
        Отправка команды на сервер.
        
        Параметры:
        - cmd_type: Тип команды
        - agent_id: Идентификатор агента (None для команд серверу)
        - data: Данные команды
        - timeout: Таймаут ожидания ответа в секундах
        
        Возвращает:
        - Ответ от сервера или None в случае ошибки
        """
        if not self.connected:
            if not self.connect():
                logger.error("Не удалось подключиться к серверу")
                return None
        
        # Создаем команду
        command = Command(
            cmd_type=cmd_type,
            agent_id=agent_id,
            data=data,
            auth_token=self.admin_token
        )
        
        # Шифруем, если нужно
        if self.use_encryption and self.encryption_manager:
            command = command.encrypt(self.encryption_manager)
        
        try:
            # Отправляем команду
            command_json = command.to_json()
            self.connection.sendall(f"{command_json}\n".encode('utf-8'))
            
            # Получаем ответ с таймаутом
            self.connection.settimeout(timeout)
            response_json = self._receive_data()
            self.connection.settimeout(None)
            
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
            return None
    
    def get_agents(self, force_refresh: bool = False) -> Optional[List[Dict]]:
        """
        Получение списка агентов.
        
        Параметры:
        - force_refresh: Принудительное обновление кэша
        
        Возвращает:
        - Список агентов или None в случае ошибки
        """
        # Проверяем кэш
        current_time = time.time()
        if not force_refresh and self.agents_cache and (current_time - self.agents_cache_timestamp) < self.agents_cache_ttl:
            return self.agents_cache
        
        # Отправляем команду серверу
        response = self.send_command(CommandType.LIST_AGENTS)
        
        if not response or not response.status:
            logger.error(f"Ошибка при получении списка агентов: {response.error_msg if response else 'Нет ответа'}")
            return None
        
        # Обновляем кэш
        self.agents_cache = response.data.get("agents", [])
        self.agents_cache_timestamp = current_time
        
        return self.agents_cache
    
    def get_agent_status(self, agent_id: str) -> Optional[Dict]:
        """
        Получение статуса агента.
        
        Параметры:
        - agent_id: Идентификатор агента
        
        Возвращает:
        - Статус агента или None в случае ошибки
        """
        response = self.send_command(CommandType.STATUS, agent_id)
        
        if not response or not response.status:
            logger.error(f"Ошибка при получении статуса агента: {response.error_msg if response else 'Нет ответа'}")
            return None
        
        return response.data
    
    def execute_shell_command(self, agent_id: str, command: str, timeout: int = 60) -> Optional[Dict]:
        """
        Выполнение shell-команды на агенте.
        
        Параметры:
        - agent_id: Идентификатор агента
        - command: Команда для выполнения
        - timeout: Таймаут выполнения в секундах
        
        Возвращает:
        - Результат выполнения команды или None в случае ошибки
        """
        response = self.send_command(
            CommandType.SHELL, 
            agent_id, 
            {
                "command": command,
                "timeout": timeout
            },
            timeout=timeout + 5  # Добавляем запас к таймауту
        )
        
        if not response:
            logger.error("Нет ответа от сервера при выполнении shell-команды")
            return None
        
        if not response.status:
            logger.error(f"Ошибка при выполнении shell-команды: {response.error_msg}")
            return {
                "success": False,
                "error": response.error_msg,
                "stdout": response.data.get("stdout", "") if response.data else "",
                "stderr": response.data.get("stderr", "") if response.data else "",
                "exit_code": -1
            }
        
        return {
            "success": True,
            "stdout": response.data.get("stdout", ""),
            "stderr": response.data.get("stderr", ""),
            "exit_code": response.data.get("exit_code", 0)
        }
    
    def read_file(self, agent_id: str, file_path: str) -> Optional[bytes]:
        """
        Чтение файла с агента.
        
        Параметры:
        - agent_id: Идентификатор агента
        - file_path: Путь к файлу
        
        Возвращает:
        - Содержимое файла или None в случае ошибки
        """
        import base64
        
        response = self.send_command(
            CommandType.FILE,
            agent_id,
            {
                "operation": "read",
                "path": file_path
            }
        )
        
        if not response:
            logger.error("Нет ответа от сервера при чтении файла")
            return None
        
        if not response.status:
            logger.error(f"Ошибка при чтении файла: {response.error_msg}")
            return None
        
        # Декодируем содержимое из base64
        content_b64 = response.data.get("content", "")
        if not content_b64:
            logger.error("Пустое содержимое файла")
            return None
        
        try:
            content = base64.b64decode(content_b64)
            return content
        except Exception as e:
            logger.error(f"Ошибка при декодировании содержимого файла: {str(e)}")
            return None
    
    def write_file(self, agent_id: str, file_path: str, content: bytes) -> bool:
        """
        Запись файла на агент.
        
        Параметры:
        - agent_id: Идентификатор агента
        - file_path: Путь к файлу
        - content: Содержимое файла
        
        Возвращает:
        - Успешность операции
        """
        import base64
        
        # Кодируем содержимое в base64
        content_b64 = base64.b64encode(content).decode('utf-8')
        
        response = self.send_command(
            CommandType.FILE,
            agent_id,
            {
                "operation": "write",
                "path": file_path,
                "content": content_b64
            }
        )
        
        if not response:
            logger.error("Нет ответа от сервера при записи файла")
            return False
        
        if not response.status:
            logger.error(f"Ошибка при записи файла: {response.error_msg}")
            return False
        
        return True
    
    def delete_file(self, agent_id: str, file_path: str) -> bool:
        """
        Удаление файла на агенте.
        
        Параметры:
        - agent_id: Идентификатор агента
        - file_path: Путь к файлу
        
        Возвращает:
        - Успешность операции
        """
        response = self.send_command(
            CommandType.FILE,
            agent_id,
            {
                "operation": "delete",
                "path": file_path
            }
        )
        
        if not response:
            logger.error("Нет ответа от сервера при удалении файла")
            return False
        
        if not response.status:
            logger.error(f"Ошибка при удалении файла: {response.error_msg}")
            return False
        
        return True
    
    def list_directory(self, agent_id: str, directory_path: str) -> Optional[List[Dict]]:
        """
        Получение списка файлов и директорий на агенте.
        
        Параметры:
        - agent_id: Идентификатор агента
        - directory_path: Путь к директории
        
        Возвращает:
        - Список файлов и директорий или None в случае ошибки
        """
        response = self.send_command(
            CommandType.FILE,
            agent_id,
            {
                "operation": "list",
                "path": directory_path
            }
        )
        
        if not response:
            logger.error("Нет ответа от сервера при получении списка файлов")
            return None
        
        if not response.status:
            logger.error(f"Ошибка при получении списка файлов: {response.error_msg}")
            return None
        
        return response.data.get("items", [])
    
    def list_processes(self, agent_id: str) -> Optional[List[Dict]]:
        """
        Получение списка процессов на агенте.
        
        Параметры:
        - agent_id: Идентификатор агента
        
        Возвращает:
        - Список процессов или None в случае ошибки
        """
        response = self.send_command(
            CommandType.PROCESS,
            agent_id,
            {
                "operation": "list"
            }
        )
        
        if not response:
            logger.error("Нет ответа от сервера при получении списка процессов")
            return None
        
        if not response.status:
            logger.error(f"Ошибка при получении списка процессов: {response.error_msg}")
            return None
        
        return response.data.get("processes", [])
    
    def get_process_info(self, agent_id: str, pid: int) -> Optional[Dict]:
        """
        Получение информации о процессе на агенте.
        
        Параметры:
        - agent_id: Идентификатор агента
        - pid: PID процесса
        
        Возвращает:
        - Информация о процессе или None в случае ошибки
        """
        response = self.send_command(
            CommandType.PROCESS,
            agent_id,
            {
                "operation": "info",
                "pid": pid
            }
        )
        
        if not response:
            logger.error("Нет ответа от сервера при получении информации о процессе")
            return None
        
        if not response.status:
            logger.error(f"Ошибка при получении информации о процессе: {response.error_msg}")
            return None
        
        return response.data
    
    def start_process(self, agent_id: str, command: str, shell: bool = True, cwd: Optional[str] = None, env: Optional[Dict] = None) -> Optional[int]:
        """
        Запуск процесса на агенте.
        
        Параметры:
        - agent_id: Идентификатор агента
        - command: Команда для запуска
        - shell: Использовать ли оболочку
        - cwd: Рабочая директория
        - env: Переменные окружения
        
        Возвращает:
        - PID запущенного процесса или None в случае ошибки
        """
        response = self.send_command(
            CommandType.PROCESS,
            agent_id,
            {
                "operation": "start",
                "command": command,
                "shell": shell,
                "cwd": cwd,
                "env": env
            }
        )
        
        if not response:
            logger.error("Нет ответа от сервера при запуске процесса")
            return None
        
        if not response.status:
            logger.error(f"Ошибка при запуске процесса: {response.error_msg}")
            return None
        
        return response.data.get("pid")
    
    def stop_process(self, agent_id: str, pid: int) -> bool:
        """
        Остановка процесса на агенте.
        
        Параметры:
        - agent_id: Идентификатор агента
        - pid: PID процесса
        
        Возвращает:
        - Успешность операции
        """
        response = self.send_command(
            CommandType.PROCESS,
            agent_id,
            {
                "operation": "stop",
                "pid": pid
            }
        )
        
        if not response:
            logger.error("Нет ответа от сервера при остановке процесса")
            return False
        
        if not response.status:
            logger.error(f"Ошибка при остановке процесса: {response.error_msg}")
            return False
        
        return True


class CommandRunner:
    """
    Класс для выполнения команд и получения результатов.
    
    Позволяет управлять агентами, выполнять команды и получать результаты.
    """
    
    def __init__(
        self,
        server_host: str,
        server_port: int,
        admin_token: Optional[str] = None,
        use_ssl: bool = True,
        use_encryption: bool = True
    ):
        """
        Инициализация исполнителя команд.
        
        Параметры:
        - server_host: Хост сервера
        - server_port: Порт сервера
        - admin_token: Токен администратора для аутентификации
        - use_ssl: Использовать ли SSL для соединения
        - use_encryption: Использовать ли шифрование данных
        """
        self.client = AgentClient(
            server_host,
            server_port,
            admin_token,
            use_ssl,
            use_encryption
        )
    
    def run_command_on_all_agents(
        self,
        command: str,
        callback: Optional[Callable[[str, Dict], None]] = None
    ) -> Dict[str, Dict]:
        """
        Выполнение команды на всех доступных агентах.
        
        Параметры:
        - command: Команда для выполнения
        - callback: Функция обратного вызова для обработки результатов
        
        Возвращает:
        - Словарь с результатами выполнения команды для каждого агента
        """
        # Получаем список агентов
        agents = self.client.get_agents()
        if not agents:
            logger.error("Не удалось получить список агентов")
            return {}
        
        results = {}
        threads = []
        
        # Выполняем команду на каждом агенте в отдельном потоке
        for agent in agents:
            agent_id = agent.get("agent_id")
            if not agent_id:
                continue
            
            thread = threading.Thread(
                target=self._run_command_on_agent_thread,
                args=(agent_id, command, results, callback)
            )
            thread.start()
            threads.append(thread)
        
        # Ждем завершения всех потоков
        for thread in threads:
            thread.join()
        
        return results
    
    def _run_command_on_agent_thread(
        self,
        agent_id: str,
        command: str,
        results: Dict[str, Dict],
        callback: Optional[Callable[[str, Dict], None]]
    ):
        """
        Функция выполнения команды на агенте в отдельном потоке.
        
        Параметры:
        - agent_id: Идентификатор агента
        - command: Команда для выполнения
        - results: Словарь для хранения результатов
        - callback: Функция обратного вызова для обработки результатов
        """
        try:
            # Выполняем команду
            result = self.client.execute_shell_command(agent_id, command)
            
            # Добавляем результат в словарь
            results[agent_id] = result
            
            # Вызываем функцию обратного вызова, если она указана
            if callback and result:
                callback(agent_id, result)
                
        except Exception as e:
            logger.error(f"Ошибка при выполнении команды {command} на агенте {agent_id}: {str(e)}")
            results[agent_id] = {
                "success": False,
                "error": str(e),
                "stdout": "",
                "stderr": "",
                "exit_code": -1
            }
    
    def gather_info_from_all_agents(self) -> Dict[str, Dict]:
        """
        Сбор информации со всех агентов.
        
        Возвращает:
        - Словарь с информацией о каждом агенте
        """
        # Получаем список агентов
        agents = self.client.get_agents()
        if not agents:
            logger.error("Не удалось получить список агентов")
            return {}
        
        info = {}
        threads = []
        
        # Собираем информацию с каждого агента в отдельном потоке
        for agent in agents:
            agent_id = agent.get("agent_id")
            if not agent_id:
                continue
            
            thread = threading.Thread(
                target=self._gather_agent_info_thread,
                args=(agent_id, info)
            )
            thread.start()
            threads.append(thread)
        
        # Ждем завершения всех потоков
        for thread in threads:
            thread.join()
        
        return info
    
    def _gather_agent_info_thread(self, agent_id: str, info: Dict[str, Dict]):
        """
        Функция сбора информации с агента в отдельном потоке.
        
        Параметры:
        - agent_id: Идентификатор агента
        - info: Словарь для хранения информации
        """
        try:
            # Получаем статус агента
            status = self.client.get_agent_status(agent_id)
            
            # Получаем список процессов
            processes = self.client.list_processes(agent_id)
            
            # Получаем информацию о файловой системе
            fs_info = self.client.list_directory(agent_id, "/")
            
            # Собираем информацию
            agent_info = {
                "status": status,
                "processes": processes,
                "filesystem": fs_info
            }
            
            # Добавляем информацию в словарь
            info[agent_id] = agent_info
                
        except Exception as e:
            logger.error(f"Ошибка при сборе информации с агента {agent_id}: {str(e)}")
            info[agent_id] = {
                "error": str(e)
            }
    
    def execute_script_on_agent(self, agent_id: str, script_path: str) -> Optional[Dict]:
        """
        Выполнение скрипта на агенте.
        
        Параметры:
        - agent_id: Идентификатор агента
        - script_path: Путь к скрипту
        
        Возвращает:
        - Результат выполнения скрипта или None в случае ошибки
        """
        try:
            # Читаем скрипт
            with open(script_path, 'rb') as f:
                script_content = f.read()
            
            # Генерируем временный путь на агенте
            import os
            remote_path = f"/tmp/script_{uuid.uuid4().hex}{os.path.splitext(script_path)[1]}"
            
            # Загружаем скрипт на агент
            if not self.client.write_file(agent_id, remote_path, script_content):
                logger.error(f"Не удалось загрузить скрипт на агент {agent_id}")
                return None
            
            # Делаем скрипт исполняемым
            self.client.execute_shell_command(agent_id, f"chmod +x {remote_path}")
            
            # Выполняем скрипт
            result = self.client.execute_shell_command(agent_id, remote_path)
            
            # Удаляем скрипт
            self.client.delete_file(agent_id, remote_path)
            
            return result
            
        except Exception as e:
            logger.error(f"Ошибка при выполнении скрипта {script_path} на агенте {agent_id}: {str(e)}")
            return None
    
    def transfer_file(self, src_agent_id: str, src_path: str, dst_agent_id: str, dst_path: str) -> bool:
        """
        Передача файла между агентами.
        
        Параметры:
        - src_agent_id: Идентификатор исходного агента
        - src_path: Путь к файлу на исходном агенте
        - dst_agent_id: Идентификатор целевого агента
        - dst_path: Путь к файлу на целевом агенте
        
        Возвращает:
        - Успешность операции
        """
        try:
            # Читаем файл с исходного агента
            content = self.client.read_file(src_agent_id, src_path)
            if not content:
                logger.error(f"Не удалось прочитать файл {src_path} с агента {src_agent_id}")
                return False
            
            # Записываем файл на целевой агент
            if not self.client.write_file(dst_agent_id, dst_path, content):
                logger.error(f"Не удалось записать файл {dst_path} на агент {dst_agent_id}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при передаче файла с агента {src_agent_id} на агент {dst_agent_id}: {str(e)}")
            return False 