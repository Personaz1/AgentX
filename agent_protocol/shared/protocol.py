#!/usr/bin/env python3
"""
Протокол обмена данными между клиентом и сервером.
"""

import json
import time
import enum
import uuid
from typing import Dict, Any, Optional, List, Union


class CommandType(str, enum.Enum):
    """
    Типы команд, поддерживаемые протоколом.
    """
    LOGIN = "login"              # Аутентификация клиента
    LOGOUT = "logout"            # Завершение сессии
    KEY_EXCHANGE = "key_exchange"  # Обмен ключами шифрования
    SUBSCRIBE = "subscribe"      # Подписка на события

    SHELL = "shell"              # Выполнение shell-команды
    PYTHON = "python"            # Выполнение Python-кода
    
    UPLOAD_FILE = "upload_file"  # Загрузка файла на агент
    DOWNLOAD_FILE = "download_file"  # Скачивание файла с агента
    
    LIST_AGENTS = "list_agents"  # Получение списка агентов
    STATUS = "status"            # Получение статуса агента
    KILL_AGENT = "kill_agent"    # Завершение работы агента
    
    LIST_PROCESSES = "list_processes"  # Получение списка процессов
    KILL_PROCESS = "kill_process"  # Завершение процесса
    
    EVENT = "event"              # События от сервера

    HEARTBEAT = "heartbeat"
    FILE = "file"
    PROCESS = "process"
    KEYEXCHANGE = "keyexchange"
    LLM_QUERY = "llm_query"  # Новый тип для запросов к LLM

    @classmethod
    def from_string(cls, value: str) -> 'CommandType':
        """Преобразование строки в тип команды."""
        if value == cls.HEARTBEAT:
            return cls.HEARTBEAT
        elif value == cls.STATUS:
            return cls.STATUS
        elif value == cls.SHELL:
            return cls.SHELL
        elif value == cls.FILE:
            return cls.FILE
        elif value == cls.PROCESS:
            return cls.PROCESS
        elif value == cls.KEYEXCHANGE:
            return cls.KEYEXCHANGE
        elif value == cls.LLM_QUERY:
            return cls.LLM_QUERY
        else:
            raise ValueError(f"Unknown command type: {value}")


class Command:
    """
    Команда, отправляемая клиентом серверу.
    """
    
    def __init__(self, command_type: Union[CommandType, str], data: Dict[str, Any] = None, 
                 command_id: Optional[str] = None, session_id: Optional[str] = None):
        """
        Инициализация команды.
        
        Параметры:
        - command_type: Тип команды
        - data: Данные команды
        - command_id: Уникальный идентификатор команды (генерируется, если не указан)
        - session_id: Идентификатор сессии
        """
        self.command_type = command_type if isinstance(command_type, CommandType) else CommandType(command_type)
        self.data = data or {}
        self.command_id = command_id or str(uuid.uuid4())
        self.session_id = session_id
        self.timestamp = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Преобразование команды в словарь.
        
        Возвращает:
        - Словарь с данными команды
        """
        result = {
            "command_type": self.command_type.value,
            "command_id": self.command_id,
            "data": self.data,
            "timestamp": self.timestamp
        }
        
        if self.session_id:
            result["session_id"] = self.session_id
        
        return result
    
    def to_json(self) -> str:
        """
        Преобразование команды в JSON-строку.
        
        Возвращает:
        - JSON-строка
        """
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Command':
        """
        Создание команды из словаря.
        
        Параметры:
        - data: Словарь с данными команды
        
        Возвращает:
        - Объект команды
        """
        command_type = data.get("command_type")
        command_data = data.get("data", {})
        command_id = data.get("command_id")
        session_id = data.get("session_id")
        
        command = cls(command_type, command_data, command_id, session_id)
        command.timestamp = data.get("timestamp", time.time())
        
        return command
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Command':
        """
        Создание команды из JSON-строки.
        
        Параметры:
        - json_str: JSON-строка
        
        Возвращает:
        - Объект команды
        """
        data = json.loads(json_str)
        return cls.from_dict(data)


class Response:
    """
    Ответ, отправляемый сервером клиенту.
    """
    
    def __init__(self, command_id: str, success: bool = True, 
                 data: Dict[str, Any] = None, message: str = "", 
                 error_code: Optional[int] = None):
        """
        Инициализация ответа.
        
        Параметры:
        - command_id: Идентификатор команды
        - success: Флаг успешного выполнения
        - data: Данные ответа
        - message: Сообщение (обычно об ошибке)
        - error_code: Код ошибки
        """
        self.command_id = command_id
        self.success = success
        self.data = data or {}
        self.message = message
        self.error_code = error_code
        self.timestamp = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Преобразование ответа в словарь.
        
        Возвращает:
        - Словарь с данными ответа
        """
        result = {
            "command_id": self.command_id,
            "success": self.success,
            "data": self.data,
            "message": self.message,
            "timestamp": self.timestamp
        }
        
        if self.error_code is not None:
            result["error_code"] = self.error_code
        
        return result
    
    def to_json(self) -> str:
        """
        Преобразование ответа в JSON-строку.
        
        Возвращает:
        - JSON-строка
        """
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Response':
        """
        Создание ответа из словаря.
        
        Параметры:
        - data: Словарь с данными ответа
        
        Возвращает:
        - Объект ответа
        """
        command_id = data.get("command_id", "")
        success = data.get("success", False)
        response_data = data.get("data", {})
        message = data.get("message", "")
        error_code = data.get("error_code")
        
        response = cls(command_id, success, response_data, message, error_code)
        response.timestamp = data.get("timestamp", time.time())
        
        return response
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Response':
        """
        Создание ответа из JSON-строки.
        
        Параметры:
        - json_str: JSON-строка
        
        Возвращает:
        - Объект ответа
        """
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    @classmethod
    def create_error(cls, command: Command, message: str, error_code: int = 500) -> 'Response':
        """
        Создание ответа с ошибкой.
        
        Параметры:
        - command: Команда, на которую создается ответ
        - message: Сообщение об ошибке
        - error_code: Код ошибки
        
        Возвращает:
        - Объект ответа с ошибкой
        """
        return cls(
            command_id=command.command_id,
            success=False,
            message=message,
            error_code=error_code
        )
    
    @classmethod
    def create_success(cls, command: Command, data: Dict[str, Any] = None, 
                      message: str = "Command executed successfully") -> 'Response':
        """
        Создание успешного ответа.
        
        Параметры:
        - command: Команда, на которую создается ответ
        - data: Данные ответа
        - message: Сообщение
        
        Возвращает:
        - Объект успешного ответа
        """
        return cls(
            command_id=command.command_id,
            success=True,
            data=data or {},
            message=message
        )


class Event:
    """
    Событие, отправляемое сервером клиентам.
    """
    
    def __init__(self, event_type: str, event_data: Dict[str, Any] = None, 
                 event_id: Optional[str] = None, session_id: Optional[str] = None):
        """
        Инициализация события.
        
        Параметры:
        - event_type: Тип события
        - event_data: Данные события
        - event_id: Идентификатор события
        - session_id: Идентификатор сессии
        """
        self.event_type = event_type
        self.event_data = event_data or {}
        self.event_id = event_id or str(uuid.uuid4())
        self.session_id = session_id
        self.timestamp = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Преобразование события в словарь.
        
        Возвращает:
        - Словарь с данными события
        """
        result = {
            "event_type": self.event_type,
            "event_id": self.event_id,
            "event_data": self.event_data,
            "timestamp": self.timestamp
        }
        
        if self.session_id:
            result["session_id"] = self.session_id
        
        return result
    
    def to_response(self) -> Response:
        """
        Преобразование события в ответ для отправки клиенту.
        
        Возвращает:
        - Объект ответа
        """
        return Response(
            command_id=self.event_id,
            success=True,
            data={
                "event_type": self.event_type,
                "event_data": self.event_data
            },
            message="Event notification"
        )
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Event':
        """
        Создание события из словаря.
        
        Параметры:
        - data: Словарь с данными события
        
        Возвращает:
        - Объект события
        """
        event_type = data.get("event_type", "unknown")
        event_data = data.get("event_data", {})
        event_id = data.get("event_id")
        session_id = data.get("session_id")
        
        event = cls(event_type, event_data, event_id, session_id)
        event.timestamp = data.get("timestamp", time.time())
        
        return event


# Типы событий
class EventType:
    """
    Типы событий, отправляемых сервером.
    """
    AGENT_CONNECTED = "agent_connected"        # Агент подключился
    AGENT_DISCONNECTED = "agent_disconnected"  # Агент отключился
    AGENT_STATUS_CHANGED = "agent_status_changed"  # Изменение статуса агента
    
    COMMAND_STARTED = "command_started"        # Начало выполнения команды
    COMMAND_FINISHED = "command_finished"      # Завершение выполнения команды
    COMMAND_OUTPUT = "command_output"          # Вывод команды
    
    FILE_TRANSFERRED = "file_transferred"      # Файл передан
    
    PROCESS_STARTED = "process_started"        # Процесс запущен
    PROCESS_FINISHED = "process_finished"      # Процесс завершен


def create_command(command_type: Union[CommandType, str], data: Dict[str, Any] = None, 
                  session_id: Optional[str] = None) -> Command:
    """
    Создание команды.
    
    Параметры:
    - command_type: Тип команды
    - data: Данные команды
    - session_id: Идентификатор сессии
    
    Возвращает:
    - Объект команды
    """
    return Command(command_type, data, session_id=session_id)


def create_response(command: Command, success: bool = True, data: Dict[str, Any] = None, 
                   message: str = "", error_code: Optional[int] = None) -> Response:
    """
    Создание ответа на команду.
    
    Параметры:
    - command: Команда, на которую создается ответ
    - success: Флаг успешного выполнения
    - data: Данные ответа
    - message: Сообщение
    - error_code: Код ошибки
    
    Возвращает:
    - Объект ответа
    """
    return Response(command.command_id, success, data, message, error_code)


def create_event(event_type: str, event_data: Dict[str, Any] = None, 
                session_id: Optional[str] = None) -> Event:
    """
    Создание события.
    
    Параметры:
    - event_type: Тип события
    - event_data: Данные события
    - session_id: Идентификатор сессии
    
    Возвращает:
    - Объект события
    """
    return Event(event_type, event_data, session_id=session_id)


def create_keyexchange_command(public_key: str, session_id: Optional[str] = None) -> Command:
    """
    Создание команды для обмена ключами шифрования.
    
    Параметры:
    - public_key: Публичный ключ для обмена
    - session_id: Идентификатор сессии
    
    Возвращает:
    - Объект команды обмена ключами
    """
    return Command(
        command_type=CommandType.KEY_EXCHANGE,
        data={"public_key": public_key},
        session_id=session_id
    )


def complete_keyexchange(response: Response, dh_manager) -> bool:
    """
    Завершение процесса обмена ключами на основе полученного ответа.
    
    Параметры:
    - response: Ответ от сервера/клиента с данными для завершения обмена ключами
    - dh_manager: Экземпляр DiffieHellmanManager для управления ключами
    
    Возвращает:
    - True, если обмен ключами успешно завершен
    """
    if not response.success:
        return False
    
    try:
        # Получаем публичный ключ из ответа
        peer_public_key = response.data.get("public_key")
        if not peer_public_key:
            return False
        
        # Обрабатываем полученный ключ
        return dh_manager.process_peer_key(peer_public_key)
    except Exception as e:
        print(f"Error completing key exchange: {str(e)}")
        return False


def process_keyexchange_command(command: Command, encryption_manager) -> Response:
    """
    Обработка команды обмена ключами.
    
    Параметры:
    - command: Команда обмена ключами
    - encryption_manager: Менеджер шифрования
    
    Возвращает:
    - Ответ на команду обмена ключами
    """
    try:
        # Получаем публичный ключ из данных команды
        client_public_key = command.data.get("public_key")
        if not client_public_key:
            return Response(
                command_id=command.command_id,
                success=False,
                message="Public key missing from key exchange command"
            )
        
        # Инициализируем менеджер диффи-хеллмана, если он еще не инициализирован
        if not hasattr(encryption_manager, 'dh_manager') or encryption_manager.dh_manager is None:
            from agent_protocol.shared.key_exchange import DiffieHellmanManager
            encryption_manager.dh_manager = DiffieHellmanManager()
            encryption_manager.dh_manager.initialize()
        
        # Устанавливаем публичный ключ клиента и получаем общий ключ
        result = encryption_manager.dh_manager.process_peer_key(client_public_key)
        
        if result:
            # Обмен ключами успешен
            return Response(
                command_id=command.command_id,
                success=True,
                data={
                    "public_key": encryption_manager.dh_manager.get_public_key_str(),
                    "fingerprint": encryption_manager.dh_manager.get_key_fingerprint()
                },
                message="Key exchange successful"
            )
        else:
            # Ошибка обмена ключами
            return Response(
                command_id=command.command_id,
                success=False,
                message="Failed to process client key"
            )
    except Exception as e:
        # Ошибка обработки команды
        return Response(
            command_id=command.command_id,
            success=False,
            message=f"Error processing key exchange: {str(e)}"
        ) 