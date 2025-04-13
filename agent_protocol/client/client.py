#!/usr/bin/env python3
"""
Клиентский модуль для взаимодействия с агентами.
"""

import os
import sys
import json
import time
import socket
import base64
import logging
import threading
from typing import Dict, List, Any, Optional, Union, Callable

# Добавляем путь к родительскому каталогу
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.protocol import Command, Response, CommandType
from shared.encryption import get_encryption_manager


# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('agent_client')


class AgentClient:
    """
    Клиент для взаимодействия с агентами через сервер.
    """
    
    def __init__(self, server_host: str = "localhost", server_port: int = 8888, 
                 use_encryption: bool = True, timeout: int = 10):
        """
        Инициализация клиента.
        
        Параметры:
        - server_host: Хост сервера (по умолчанию localhost)
        - server_port: Порт сервера (по умолчанию 8888)
        - use_encryption: Использовать ли шифрование (по умолчанию True)
        - timeout: Тайм-аут соединения в секундах (по умолчанию 10)
        """
        self.server_host = server_host
        self.server_port = server_port
        self.use_encryption = use_encryption
        self.timeout = timeout
        
        self.socket = None
        self.connected = False
        self.session_id = None
        self.agents = {}
        
        # Инициализация шифрования
        if use_encryption:
            self.encryption = get_encryption_manager()
        else:
            self.encryption = None
    
    def connect(self) -> bool:
        """
        Подключение к серверу.
        
        Возвращает:
        - True, если подключение успешно, иначе False
        """
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(self.timeout)
            self.socket.connect((self.server_host, self.server_port))
            
            # Создаем сессию
            if self._create_session():
                self.connected = True
                logger.info(f"Connected to server {self.server_host}:{self.server_port}")
                return True
            else:
                self.socket.close()
                self.socket = None
                logger.error("Failed to create session with server")
                return False
        except Exception as e:
            logger.error(f"Failed to connect to server: {e}")
            if self.socket:
                self.socket.close()
                self.socket = None
            return False
    
    def disconnect(self) -> None:
        """
        Отключение от сервера.
        """
        if self.socket:
            try:
                # Отправляем команду завершения сессии
                if self.connected:
                    self._send_command(CommandType.LOGOUT, {})
                
                self.socket.close()
            except Exception as e:
                logger.error(f"Error during disconnect: {e}")
            finally:
                self.socket = None
                self.connected = False
                self.session_id = None
    
    def _create_session(self) -> bool:
        """
        Создание сессии с сервером, включая обмен ключами шифрования.
        
        Возвращает:
        - True, если сессия создана успешно, иначе False
        """
        try:
            # Если шифрование включено, сначала выполняем обмен ключами
            if self.use_encryption:
                # Отправляем запрос на обмен ключами
                public_key = self.encryption.get_public_key()
                key_exchange_cmd = Command(CommandType.KEY_EXCHANGE, {"public_key": public_key})
                
                # Отправляем команду без шифрования
                self._send_raw(key_exchange_cmd.to_json())
                
                # Получаем ответ
                response_data = self._receive_raw()
                response = Response.from_json(response_data)
                
                if response.success:
                    # Устанавливаем публичный ключ сервера
                    server_public_key = response.data.get("public_key")
                    self.encryption.set_remote_public_key(server_public_key)
                    logger.debug("Key exchange completed successfully")
                else:
                    logger.error(f"Key exchange failed: {response.message}")
                    return False
            
            # Отправляем команду авторизации
            auth_data = {
                "client_id": f"client_{os.getpid()}",
                "version": "1.0"
            }
            
            response = self._send_command(CommandType.LOGIN, auth_data)
            
            if response.success:
                self.session_id = response.data.get("session_id")
                logger.info(f"Session created with ID: {self.session_id}")
                return True
            else:
                logger.error(f"Failed to authenticate: {response.message}")
                return False
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            return False
    
    def _send_raw(self, data: str) -> None:
        """
        Отправка сырых данных на сервер.
        
        Параметры:
        - data: Данные для отправки
        """
        if not self.socket:
            raise ConnectionError("Not connected to server")
        
        try:
            # Добавляем маркер конца сообщения
            data_bytes = (data + "\n").encode('utf-8')
            
            # Отправляем длину сообщения
            length = len(data_bytes)
            length_bytes = length.to_bytes(4, byteorder='big')
            self.socket.sendall(length_bytes)
            
            # Отправляем данные
            self.socket.sendall(data_bytes)
        except Exception as e:
            logger.error(f"Error sending data: {e}")
            raise ConnectionError(f"Error sending data: {e}")
    
    def _receive_raw(self) -> str:
        """
        Получение сырых данных от сервера.
        
        Возвращает:
        - Полученные данные в виде строки
        """
        if not self.socket:
            raise ConnectionError("Not connected to server")
        
        try:
            # Получаем длину сообщения
            length_bytes = self._receive_exactly(4)
            length = int.from_bytes(length_bytes, byteorder='big')
            
            # Получаем сообщение
            data_bytes = self._receive_exactly(length)
            
            # Декодируем и удаляем маркер конца сообщения
            data = data_bytes.decode('utf-8').strip()
            return data
        except Exception as e:
            logger.error(f"Error receiving data: {e}")
            raise ConnectionError(f"Error receiving data: {e}")
    
    def _receive_exactly(self, n: int) -> bytes:
        """
        Получение точно n байтов данных из сокета.
        
        Параметры:
        - n: Количество байтов для получения
        
        Возвращает:
        - Полученные байты
        """
        buffer = b''
        while len(buffer) < n:
            chunk = self.socket.recv(n - len(buffer))
            if not chunk:
                raise ConnectionError("Connection closed by server")
            buffer += chunk
        return buffer
    
    def _send_command(self, command_type: CommandType, data: Dict[str, Any]) -> Response:
        """
        Отправка команды на сервер и получение ответа.
        
        Параметры:
        - command_type: Тип команды
        - data: Данные команды
        
        Возвращает:
        - Ответ от сервера
        """
        if not self.connected and command_type != CommandType.LOGIN:
            raise ConnectionError("Not connected to server")
        
        # Создаем команду
        command = Command(command_type, data)
        
        if self.session_id and command_type != CommandType.LOGIN:
            command.session_id = self.session_id
        
        # Если шифрование включено, шифруем данные
        if self.use_encryption and command_type != CommandType.KEY_EXCHANGE:
            json_data = command.to_json()
            encrypted_data = self.encryption.encrypt(json_data)
            self._send_raw(encrypted_data)
        else:
            self._send_raw(command.to_json())
        
        # Получаем ответ
        response_data = self._receive_raw()
        
        # Если шифрование включено, расшифровываем данные
        if self.use_encryption and command_type != CommandType.KEY_EXCHANGE:
            decrypted_data = self.encryption.decrypt(response_data)
            response = Response.from_json(decrypted_data)
        else:
            response = Response.from_json(response_data)
        
        return response
    
    def list_agents(self) -> List[Dict[str, Any]]:
        """
        Получение списка доступных агентов.
        
        Возвращает:
        - Список доступных агентов с их метаданными
        """
        response = self._send_command(CommandType.LIST_AGENTS, {})
        
        if response.success:
            self.agents = {agent["agent_id"]: agent for agent in response.data.get("agents", [])}
            return response.data.get("agents", [])
        else:
            logger.error(f"Failed to get agent list: {response.message}")
            return []
    
    def execute_shell_command(self, agent_id: str, command: str, 
                             timeout: int = 60) -> Dict[str, Any]:
        """
        Выполнение shell-команды на агенте.
        
        Параметры:
        - agent_id: ID агента
        - command: Команда для выполнения
        - timeout: Тайм-аут выполнения в секундах
        
        Возвращает:
        - Результат выполнения команды
        """
        cmd_data = {
            "agent_id": agent_id,
            "command": command,
            "timeout": timeout
        }
        
        response = self._send_command(CommandType.SHELL, cmd_data)
        
        if response.success:
            return {
                "stdout": response.data.get("stdout", ""),
                "stderr": response.data.get("stderr", ""),
                "exit_code": response.data.get("exit_code", -1),
                "execution_time": response.data.get("execution_time", 0)
            }
        else:
            logger.error(f"Failed to execute shell command: {response.message}")
            return {
                "stdout": "",
                "stderr": response.message,
                "exit_code": -1,
                "execution_time": 0
            }
    
    def execute_python_code(self, agent_id: str, code: str, 
                           timeout: int = 60) -> Dict[str, Any]:
        """
        Выполнение Python-кода на агенте.
        
        Параметры:
        - agent_id: ID агента
        - code: Python-код для выполнения
        - timeout: Тайм-аут выполнения в секундах
        
        Возвращает:
        - Результат выполнения кода
        """
        cmd_data = {
            "agent_id": agent_id,
            "code": code,
            "timeout": timeout
        }
        
        response = self._send_command(CommandType.PYTHON, cmd_data)
        
        if response.success:
            return {
                "result": response.data.get("result", None),
                "output": response.data.get("output", ""),
                "error": response.data.get("error", ""),
                "execution_time": response.data.get("execution_time", 0)
            }
        else:
            logger.error(f"Failed to execute Python code: {response.message}")
            return {
                "result": None,
                "output": "",
                "error": response.message,
                "execution_time": 0
            }
    
    def upload_file(self, agent_id: str, local_path: str, 
                   remote_path: str) -> bool:
        """
        Загрузка файла на агент.
        
        Параметры:
        - agent_id: ID агента
        - local_path: Локальный путь к файлу
        - remote_path: Путь на агенте
        
        Возвращает:
        - True, если загрузка успешна, иначе False
        """
        try:
            # Читаем файл
            with open(local_path, 'rb') as f:
                file_data = f.read()
            
            # Кодируем в base64
            file_b64 = base64.b64encode(file_data).decode('utf-8')
            
            cmd_data = {
                "agent_id": agent_id,
                "remote_path": remote_path,
                "file_data": file_b64,
                "file_size": len(file_data)
            }
            
            response = self._send_command(CommandType.UPLOAD_FILE, cmd_data)
            
            if response.success:
                logger.info(f"File uploaded successfully to {remote_path}")
                return True
            else:
                logger.error(f"Failed to upload file: {response.message}")
                return False
        except Exception as e:
            logger.error(f"Error uploading file: {e}")
            return False
    
    def download_file(self, agent_id: str, remote_path: str, 
                     local_path: str) -> bool:
        """
        Скачивание файла с агента.
        
        Параметры:
        - agent_id: ID агента
        - remote_path: Путь на агенте
        - local_path: Локальный путь для сохранения
        
        Возвращает:
        - True, если скачивание успешно, иначе False
        """
        cmd_data = {
            "agent_id": agent_id,
            "remote_path": remote_path
        }
        
        response = self._send_command(CommandType.DOWNLOAD_FILE, cmd_data)
        
        if response.success:
            try:
                # Декодируем из base64
                file_data = base64.b64decode(response.data.get("file_data", ""))
                
                # Сохраняем файл
                with open(local_path, 'wb') as f:
                    f.write(file_data)
                
                logger.info(f"File downloaded successfully to {local_path}")
                return True
            except Exception as e:
                logger.error(f"Error saving downloaded file: {e}")
                return False
        else:
            logger.error(f"Failed to download file: {response.message}")
            return False
    
    def get_agent_status(self, agent_id: str) -> Dict[str, Any]:
        """
        Получение статуса агента.
        
        Параметры:
        - agent_id: ID агента
        
        Возвращает:
        - Статус агента
        """
        cmd_data = {
            "agent_id": agent_id
        }
        
        response = self._send_command(CommandType.STATUS, cmd_data)
        
        if response.success:
            return response.data
        else:
            logger.error(f"Failed to get agent status: {response.message}")
            return {}
    
    def kill_agent(self, agent_id: str) -> bool:
        """
        Завершение работы агента.
        
        Параметры:
        - agent_id: ID агента
        
        Возвращает:
        - True, если агент успешно завершен, иначе False
        """
        cmd_data = {
            "agent_id": agent_id
        }
        
        response = self._send_command(CommandType.KILL_AGENT, cmd_data)
        
        if response.success:
            logger.info(f"Agent {agent_id} terminated successfully")
            return True
        else:
            logger.error(f"Failed to terminate agent: {response.message}")
            return False
    
    def list_processes(self, agent_id: str) -> List[Dict[str, Any]]:
        """
        Получение списка процессов на агенте.
        
        Параметры:
        - agent_id: ID агента
        
        Возвращает:
        - Список процессов
        """
        cmd_data = {
            "agent_id": agent_id
        }
        
        response = self._send_command(CommandType.LIST_PROCESSES, cmd_data)
        
        if response.success:
            return response.data.get("processes", [])
        else:
            logger.error(f"Failed to get process list: {response.message}")
            return []
    
    def kill_process(self, agent_id: str, pid: int) -> bool:
        """
        Завершение процесса на агенте.
        
        Параметры:
        - agent_id: ID агента
        - pid: ID процесса
        
        Возвращает:
        - True, если процесс успешно завершен, иначе False
        """
        cmd_data = {
            "agent_id": agent_id,
            "pid": pid
        }
        
        response = self._send_command(CommandType.KILL_PROCESS, cmd_data)
        
        if response.success:
            logger.info(f"Process {pid} killed successfully on agent {agent_id}")
            return True
        else:
            logger.error(f"Failed to kill process: {response.message}")
            return False
    
    def __enter__(self):
        """
        Метод для использования контекстного менеджера.
        """
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Метод для использования контекстного менеджера.
        """
        self.disconnect()


class AsyncAgentClient(AgentClient):
    """
    Асинхронный клиент для взаимодействия с агентами через сервер.
    """
    
    def __init__(self, server_host: str = "localhost", server_port: int = 8888, 
                 use_encryption: bool = True, timeout: int = 10):
        """
        Инициализация асинхронного клиента.
        
        Параметры:
        - server_host: Хост сервера (по умолчанию localhost)
        - server_port: Порт сервера (по умолчанию 8888)
        - use_encryption: Использовать ли шифрование (по умолчанию True)
        - timeout: Тайм-аут соединения в секундах (по умолчанию 10)
        """
        super().__init__(server_host, server_port, use_encryption, timeout)
        self.callbacks = {}
        self.event_thread = None
        self.stop_event = threading.Event()
    
    def connect(self) -> bool:
        """
        Подключение к серверу.
        
        Возвращает:
        - True, если подключение успешно, иначе False
        """
        if super().connect():
            # Запускаем поток для обработки событий
            self.stop_event.clear()
            self.event_thread = threading.Thread(target=self._event_loop)
            self.event_thread.daemon = True
            self.event_thread.start()
            return True
        return False
    
    def disconnect(self) -> None:
        """
        Отключение от сервера.
        """
        # Останавливаем поток обработки событий
        if self.event_thread and self.event_thread.is_alive():
            self.stop_event.set()
            self.event_thread.join(timeout=2)
        
        super().disconnect()
    
    def _event_loop(self) -> None:
        """
        Цикл обработки событий от сервера.
        """
        logger.debug("Event loop started")
        
        try:
            # Подписываемся на события
            self._send_command(CommandType.SUBSCRIBE, {})
            
            while not self.stop_event.is_set() and self.connected:
                try:
                    # Пытаемся получить данные
                    self.socket.settimeout(0.5)  # Короткий тайм-аут для проверки stop_event
                    response_data = self._receive_raw()
                    
                    # Расшифровываем данные
                    if self.use_encryption:
                        decrypted_data = self.encryption.decrypt(response_data)
                        response = Response.from_json(decrypted_data)
                    else:
                        response = Response.from_json(response_data)
                    
                    # Обрабатываем событие
                    self._handle_event(response)
                except socket.timeout:
                    # Тайм-аут - продолжаем цикл
                    continue
                except ConnectionError as e:
                    logger.error(f"Connection error in event loop: {e}")
                    break
                except Exception as e:
                    logger.error(f"Error in event loop: {e}")
                    time.sleep(1)  # Пауза перед следующей попыткой
        except Exception as e:
            logger.error(f"Fatal error in event loop: {e}")
        finally:
            logger.debug("Event loop stopped")
    
    def _handle_event(self, response: Response) -> None:
        """
        Обработка события от сервера.
        
        Параметры:
        - response: Ответ от сервера
        """
        if not response.success:
            logger.error(f"Received error event: {response.message}")
            return
        
        event_type = response.data.get("event_type")
        event_data = response.data.get("event_data", {})
        
        if event_type in self.callbacks:
            try:
                # Вызываем все обработчики для данного типа события
                for callback in self.callbacks[event_type]:
                    callback(event_data)
            except Exception as e:
                logger.error(f"Error in event callback: {e}")
    
    def register_callback(self, event_type: str, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Регистрация обработчика события.
        
        Параметры:
        - event_type: Тип события
        - callback: Функция обратного вызова
        """
        if event_type not in self.callbacks:
            self.callbacks[event_type] = []
        
        self.callbacks[event_type].append(callback)
    
    def unregister_callback(self, event_type: str, callback: Optional[Callable[[Dict[str, Any]], None]] = None) -> None:
        """
        Отмена регистрации обработчика события.
        
        Параметры:
        - event_type: Тип события
        - callback: Функция обратного вызова (если None, то удаляются все обработчики)
        """
        if event_type in self.callbacks:
            if callback is None:
                # Удаляем все обработчики для данного типа события
                del self.callbacks[event_type]
            else:
                # Удаляем только указанный обработчик
                self.callbacks[event_type] = [cb for cb in self.callbacks[event_type] if cb != callback]


def main():
    """
    Пример использования клиента.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Agent Client')
    parser.add_argument('--host', default='localhost', help='Server host')
    parser.add_argument('--port', type=int, default=8888, help='Server port')
    parser.add_argument('--no-encryption', action='store_true', help='Disable encryption')
    
    args = parser.parse_args()
    
    with AgentClient(args.host, args.port, not args.no_encryption) as client:
        if not client.connected:
            print("Failed to connect to server")
            return
        
        print("Connected to server")
        
        # Получаем список агентов
        agents = client.list_agents()
        print(f"Found {len(agents)} agents:")
        
        for i, agent in enumerate(agents):
            print(f"{i+1}. {agent['agent_id']} - {agent.get('hostname', 'Unknown')}")
        
        if not agents:
            print("No agents available")
            return
        
        # Выбираем агент
        while True:
            try:
                choice = int(input("Select agent (number): "))
                if 1 <= choice <= len(agents):
                    break
                print("Invalid choice")
            except ValueError:
                print("Please enter a number")
        
        agent_id = agents[choice-1]['agent_id']
        print(f"Selected agent: {agent_id}")
        
        # Интерактивная консоль для выполнения команд
        print("Enter commands to execute (type 'exit' to quit):")
        
        while True:
            command = input(f"{agent_id}> ")
            
            if command.lower() == 'exit':
                break
            
            # Выполняем команду
            result = client.execute_shell_command(agent_id, command)
            
            print("--- STDOUT ---")
            print(result['stdout'])
            
            if result['stderr']:
                print("--- STDERR ---")
                print(result['stderr'])
            
            print(f"Exit code: {result['exit_code']}")
            print(f"Execution time: {result['execution_time']:.2f} seconds")


if __name__ == "__main__":
    main() 