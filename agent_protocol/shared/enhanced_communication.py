#!/usr/bin/env python3
"""
Улучшенный модуль для безопасной коммуникации между агентами и сервером.
Поддерживает обмен ключами Диффи-Хеллмана и RSA для первого подключения.
"""

import os
import json
import time
import logging
import socket
import ssl
import threading
import base64
from typing import Dict, Any, Optional, Callable, Tuple, List, Union

from agent_protocol.shared.protocol import Command, Response, ResponseStatus, create_status_command
from agent_protocol.shared.communication import SecureChannel
from agent_protocol.shared.key_exchange import KeyExchange, RSAKeyExchange, perform_key_exchange, secure_first_contact

# Настройка логирования
logger = logging.getLogger('enhanced_communication')

class HandshakeType:
    """Типы возможных процедур рукопожатия."""
    NONE = "none"
    DIFFIE_HELLMAN = "dh"
    RSA = "rsa"

class EnhancedSecureChannel(SecureChannel):
    """
    Расширенный защищенный канал с поддержкой обмена ключами.
    """
    def __init__(self, key: Optional[str] = None, handshake_type: str = HandshakeType.NONE):
        """
        Инициализация защищенного канала.
        
        Параметры:
        - key: Предварительно согласованный ключ шифрования (опционально)
        - handshake_type: Тип рукопожатия для обмена ключами
        """
        self.handshake_type = handshake_type
        self.handshake_complete = False
        self.rsa_private_key_str = None
        self.rsa_public_key_str = None
        self.dh_private_key = None
        self.dh_public_key = None
        
        # Если ключ не предоставлен и требуется рукопожатие, 
        # создаем временный ключ для начального обмена
        if not key and handshake_type != HandshakeType.NONE:
            # Создаем временный ключ
            key = base64.b64encode(os.urandom(32)).decode('utf-8')
            
            # Генерируем пару ключей RSA, если нужно
            if handshake_type == HandshakeType.RSA:
                self.rsa_private_key_str, self.rsa_public_key_str = RSAKeyExchange.generate_agent_keypair()
            
        # Инициализируем базовый канал с временным или предоставленным ключом
        super().__init__(key)
    
    def prepare_handshake(self, is_server: bool = False) -> Dict[str, Any]:
        """
        Подготовка данных для рукопожатия.
        
        Параметры:
        - is_server: True, если вызывается на стороне сервера
        
        Возвращает:
        - Словарь с данными для рукопожатия
        """
        if self.handshake_type == HandshakeType.DIFFIE_HELLMAN:
            # Генерация ключей Диффи-Хеллмана
            self.dh_private_key, self.dh_public_key = KeyExchange.generate_dh_keypair()
            dh_public_key_str = KeyExchange.serialize_public_key(self.dh_public_key)
            
            return {
                "type": HandshakeType.DIFFIE_HELLMAN,
                "public_key": dh_public_key_str,
            }
            
        elif self.handshake_type == HandshakeType.RSA:
            # Для RSA, возвращаем публичный ключ
            if not self.rsa_public_key_str:
                self.rsa_private_key_str, self.rsa_public_key_str = RSAKeyExchange.generate_agent_keypair()
                
            return {
                "type": HandshakeType.RSA,
                "public_key": self.rsa_public_key_str,
                "is_server": is_server
            }
            
        else:
            return {
                "type": HandshakeType.NONE
            }
    
    def complete_dh_handshake(self, peer_public_key_str: str) -> None:
        """
        Завершение процедуры рукопожатия Диффи-Хеллмана.
        
        Параметры:
        - peer_public_key_str: Публичный ключ партнера в строковом представлении
        """
        try:
            # Преобразуем строку публичного ключа партнера в объект
            peer_public_key = KeyExchange.deserialize_public_key(peer_public_key_str)
            
            # Вычисляем общий секретный ключ
            shared_key = KeyExchange.compute_shared_key(self.dh_private_key, peer_public_key)
            
            # Получаем отпечаток ключа для проверки
            key_fingerprint = KeyExchange.get_key_fingerprint(shared_key)
            
            # Устанавливаем общий ключ для шифрования
            self.set_key(shared_key)
            
            logger.info(f"Установлен защищенный канал DH. Отпечаток ключа: {key_fingerprint}")
        except Exception as e:
            logger.error(f"Ошибка при завершении рукопожатия DH: {str(e)}")
            raise ValueError(f"Не удалось завершить рукопожатие: {str(e)}")
    
    def complete_rsa_handshake(self, data: Dict[str, Any]) -> None:
        """
        Завершение рукопожатия RSA.
        
        Параметры:
        - data: Данные для завершения рукопожатия
        """
        if self.handshake_complete:
            return
            
        if "encrypted_key" in data:
            # Мы - сервер, расшифровываем ключ клиента
            if not self.rsa_private_key_str:
                raise ValueError("RSA private key is not initialized")
                
            # Десериализуем закрытый ключ
            private_key = RSAKeyExchange.deserialize_private_key(self.rsa_private_key_str)
            
            # Расшифровываем ключ
            encrypted_key = base64.b64decode(data["encrypted_key"])
            decrypted_key = RSAKeyExchange.decrypt_key(encrypted_key, private_key)
            
            # Устанавливаем новый ключ
            self.key = decrypted_key
            self.handshake_complete = True
            
            # Очищаем временные ключи
            self.rsa_private_key_str = None
            
            # Логируем отпечаток ключа
            key_fingerprint = KeyExchange.get_key_fingerprint(decrypted_key)
            logger.info(f"RSA handshake completed (server). Key fingerprint: {key_fingerprint}")
            
        elif "server_public_key" in data:
            # Мы - клиент, шифруем и отправляем новый AES-ключ
            server_public_key_str = data["server_public_key"]
            
            # Генерируем новый AES-ключ
            aes_key = os.urandom(32)
            
            # Шифруем ключ с помощью публичного ключа сервера
            encrypted_key = secure_first_contact(server_public_key_str, aes_key)
            
            # Устанавливаем новый ключ
            self.key = aes_key
            self.handshake_complete = True
            
            # Логируем отпечаток ключа
            key_fingerprint = KeyExchange.get_key_fingerprint(aes_key)
            logger.info(f"RSA handshake completed (client). Key fingerprint: {key_fingerprint}")
            
            # Возвращаем зашифрованный ключ для отправки серверу
            return base64.b64encode(encrypted_key).decode('utf-8')
            
        else:
            raise ValueError("Invalid RSA handshake data")

class EnhancedServer:
    """
    Расширенный сервер с поддержкой безопасного обмена ключами.
    """
    def __init__(
        self,
        host: str = '0.0.0.0',
        port: int = 8765,
        handshake_type: str = HandshakeType.DIFFIE_HELLMAN,
        encryption_key: Optional[str] = None,
        use_ssl: bool = False,
        cert_file: Optional[str] = None,
        key_file: Optional[str] = None
    ):
        """
        Инициализация сервера.
        
        Параметры:
        - host: Хост для привязки
        - port: Порт для прослушивания
        - handshake_type: Тип рукопожатия для обмена ключами
        - encryption_key: Предварительно согласованный ключ шифрования (опционально)
        - use_ssl: Использовать SSL для защиты соединения
        - cert_file: Путь к файлу сертификата SSL
        - key_file: Путь к файлу ключа SSL
        """
        self.host = host
        self.port = port
        self.handshake_type = handshake_type
        self.encryption_key = encryption_key
        self.use_ssl = use_ssl
        self.cert_file = cert_file
        self.key_file = key_file
        
        # Создаем защищенный канал
        self.secure_channel = EnhancedSecureChannel(encryption_key, handshake_type)
        
        # Состояние сервера
        self.running = False
        self.server_socket = None
        self.clients = []
        self.client_channels = {}  # Хранение каналов для каждого клиента
        self.command_handlers = {}
        
    def start(self):
        """Запуск сервера."""
        if self.running:
            logger.warning("Server is already running")
            return
            
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Разрешить повторное использование порта
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        
        if self.use_ssl and self.cert_file and self.key_file:
            context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            context.load_cert_chain(certfile=self.cert_file, keyfile=self.key_file)
            self.server_socket = context.wrap_socket(self.server_socket, server_side=True)
        
        self.running = True
        logger.info(f"Enhanced server started on {self.host}:{self.port}")
        
        # Принимаем соединения в отдельном потоке
        threading.Thread(target=self._accept_connections, daemon=True).start()
    
    def stop(self):
        """Остановка сервера."""
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        
        for client in self.clients:
            try:
                client.close()
            except:
                pass
        
        self.clients = []
        self.client_channels = {}
        logger.info("Enhanced server stopped")
    
    def _accept_connections(self):
        """Принятие клиентских соединений."""
        while self.running:
            try:
                client_socket, addr = self.server_socket.accept()
                self.clients.append(client_socket)
                
                # Создаем новый защищенный канал для клиента
                if self.handshake_type != HandshakeType.NONE:
                    client_channel = EnhancedSecureChannel(self.encryption_key, self.handshake_type)
                else:
                    client_channel = self.secure_channel
                    
                self.client_channels[client_socket] = client_channel
                
                logger.info(f"Client connected: {addr}")
                
                # Обрабатываем клиента в отдельном потоке
                threading.Thread(
                    target=self._handle_client,
                    args=(client_socket, addr),
                    daemon=True
                ).start()
            except Exception as e:
                if self.running:
                    logger.error(f"Error accepting connection: {e}")
                    time.sleep(0.1)
    
    def _handle_client(self, client_socket, addr):
        """
        Обработка клиентского соединения.
        
        Параметры:
        - client_socket: Сокет клиента
        - addr: Адрес клиента
        """
        try:
            # Получаем защищенный канал для этого клиента
            secure_channel = self.client_channels[client_socket]
            
            # Если требуется рукопожатие, выполняем его
            if self.handshake_type != HandshakeType.NONE and not secure_channel.handshake_complete:
                self._perform_handshake(client_socket, secure_channel)
            
            # Основной цикл обработки сообщений
            while self.running:
                # Получаем размер сообщения (4 байта для длины сообщения)
                header = client_socket.recv(4)
                if not header:
                    break
                
                message_size = int.from_bytes(header, byteorder='big')
                encrypted_data = b''
                
                # Получаем полное сообщение
                remaining = message_size
                while remaining > 0:
                    chunk = client_socket.recv(min(remaining, 4096))
                    if not chunk:
                        break
                    encrypted_data += chunk
                    remaining -= len(chunk)
                
                if not encrypted_data:
                    break
                
                # Расшифровываем сообщение
                json_data = secure_channel.decrypt(encrypted_data)
                command = Command.from_json(json_data)
                
                # Обрабатываем команду
                response = self._process_command(command)
                
                # Отправляем ответ
                self._send_response(client_socket, secure_channel, response)
                
        except Exception as e:
            logger.error(f"Error handling client {addr}: {e}")
        finally:
            # Очистка
            try:
                client_socket.close()
                self.clients.remove(client_socket)
                self.client_channels.pop(client_socket, None)
                logger.info(f"Client disconnected: {addr}")
            except:
                pass
    
    def _perform_handshake(self, client_socket, secure_channel: EnhancedSecureChannel):
        """
        Выполнение процедуры рукопожатия с клиентом.
        
        Параметры:
        - client_socket: Сокет клиента
        - secure_channel: Защищенный канал
        """
        try:
            logger.info("Starting handshake with client")
            
            # Подготавливаем данные для рукопожатия (серверная сторона)
            handshake_data = secure_channel.prepare_handshake(is_server=True)
            
            # Если используется DH
            if handshake_data["type"] == HandshakeType.DIFFIE_HELLMAN:
                # Отправляем свой публичный ключ
                self._send_handshake_data(client_socket, secure_channel, handshake_data)
                
                # Получаем публичный ключ клиента
                client_handshake_data = self._receive_handshake_data(client_socket, secure_channel)
                
                if client_handshake_data["type"] != HandshakeType.DIFFIE_HELLMAN:
                    raise ValueError("Client is using different handshake type")
                
                # Проверяем публичный ключ клиента на безопасность
                client_public_key = KeyExchange.deserialize_public_key(client_handshake_data["public_key"])
                if not KeyExchange.validate_dh_key(client_public_key):
                    logger.error("Client's DH key failed security validation")
                    raise ValueError("Received invalid DH key from client")
                
                # Завершаем рукопожатие
                secure_channel.complete_dh_handshake(client_handshake_data["public_key"])
                logger.info("Диффи-Хеллман рукопожатие успешно завершено")
            
            # Если используется RSA
            elif handshake_data["type"] == HandshakeType.RSA:
                # Отправляем свой публичный ключ
                self._send_handshake_data(client_socket, secure_channel, handshake_data)
                
                # Получаем зашифрованный AES-ключ от клиента
                client_handshake_data = self._receive_handshake_data(client_socket, secure_channel)
                
                if client_handshake_data["type"] != HandshakeType.RSA:
                    raise ValueError("Client is using different handshake type")
                
                # Завершаем рукопожатие
                secure_channel.complete_rsa_handshake(client_handshake_data)
                
            logger.info(f"Handshake completed with client")
            
        except Exception as e:
            logger.error(f"Handshake error: {str(e)}")
            raise
    
    def _send_handshake_data(self, client_socket, secure_channel: EnhancedSecureChannel, data: Dict[str, Any]):
        """
        Отправка данных рукопожатия клиенту.
        
        Параметры:
        - client_socket: Сокет клиента
        - secure_channel: Защищенный канал
        - data: Данные для отправки
        """
        # Сериализуем и шифруем данные
        json_data = json.dumps(data)
        encrypted_data = secure_channel.encrypt(json_data)
        
        # Отправляем размер сообщения, затем само сообщение
        message_size = len(encrypted_data)
        client_socket.send(message_size.to_bytes(4, byteorder='big'))
        client_socket.send(encrypted_data)
    
    def _receive_handshake_data(self, client_socket, secure_channel: EnhancedSecureChannel) -> Dict[str, Any]:
        """
        Получение данных рукопожатия от клиента.
        
        Параметры:
        - client_socket: Сокет клиента
        - secure_channel: Защищенный канал
        
        Возвращает:
        - Словарь с данными рукопожатия
        """
        # Получаем размер сообщения
        header = client_socket.recv(4)
        if not header:
            raise ConnectionError("Connection closed during handshake")
        
        message_size = int.from_bytes(header, byteorder='big')
        encrypted_data = b''
        
        # Получаем полное сообщение
        remaining = message_size
        while remaining > 0:
            chunk = client_socket.recv(min(remaining, 4096))
            if not chunk:
                raise ConnectionError("Connection closed during handshake")
            encrypted_data += chunk
            remaining -= len(chunk)
        
        # Расшифровываем и парсим
        json_data = secure_channel.decrypt(encrypted_data)
        return json.loads(json_data)
    
    def _process_command(self, command: Command) -> Response:
        """
        Обработка полученной команды.
        
        Параметры:
        - command: Команда для обработки
        
        Возвращает:
        - Ответ на команду
        """
        handler = self.command_handlers.get(command.command_type.value)
        if handler:
            try:
                return handler(command)
            except Exception as e:
                logger.error(f"Error processing command {command.command_id}: {e}")
                return Response(
                    command_id=command.command_id,
                    status=ResponseStatus.ERROR,
                    data={},
                    error_message=str(e)
                )
        else:
            return Response(
                command_id=command.command_id,
                status=ResponseStatus.ERROR,
                data={},
                error_message=f"No handler for command type: {command.command_type.value}"
            )
    
    def _send_response(self, client_socket, secure_channel: EnhancedSecureChannel, response: Response):
        """
        Отправка ответа клиенту.
        
        Параметры:
        - client_socket: Сокет клиента
        - secure_channel: Защищенный канал
        - response: Ответ для отправки
        """
        # Сериализуем и шифруем ответ
        json_data = response.to_json()
        encrypted_data = secure_channel.encrypt(json_data)
        
        # Отправляем размер сообщения, затем само сообщение
        message_size = len(encrypted_data)
        client_socket.send(message_size.to_bytes(4, byteorder='big'))
        client_socket.send(encrypted_data)
    
    def register_command_handler(self, command_type: str, handler: Callable[[Command], Response]):
        """
        Регистрация обработчика для определенного типа команд.
        
        Параметры:
        - command_type: Тип команды
        - handler: Функция-обработчик
        """
        self.command_handlers[command_type] = handler

class EnhancedClient:
    """
    Расширенный клиент с поддержкой безопасного обмена ключами.
    """
    def __init__(
        self,
        host: str,
        port: int,
        handshake_type: str = HandshakeType.DIFFIE_HELLMAN,
        encryption_key: Optional[str] = None,
        use_ssl: bool = False,
        cert_file: Optional[str] = None
    ):
        """
        Инициализация клиента.
        
        Параметры:
        - host: Хост сервера
        - port: Порт сервера
        - handshake_type: Тип рукопожатия для обмена ключами
        - encryption_key: Предварительно согласованный ключ шифрования (опционально)
        - use_ssl: Использовать SSL для защиты соединения
        - cert_file: Путь к файлу сертификата SSL
        """
        self.host = host
        self.port = port
        self.handshake_type = handshake_type
        self.encryption_key = encryption_key
        self.use_ssl = use_ssl
        self.cert_file = cert_file
        
        # Создаем защищенный канал
        self.secure_channel = EnhancedSecureChannel(encryption_key, handshake_type)
        
        self.socket = None
        self.connected = False
    
    def connect(self) -> bool:
        """
        Подключение к серверу.
        
        Возвращает:
        - True, если подключение успешно
        """
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            
            if self.use_ssl:
                context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
                if self.cert_file:
                    context.load_verify_locations(cafile=self.cert_file)
                self.socket = context.wrap_socket(
                    self.socket,
                    server_hostname=self.host
                )
            
            self.socket.connect((self.host, self.port))
            
            # Если требуется рукопожатие, выполняем его
            if self.handshake_type != HandshakeType.NONE and not self.secure_channel.handshake_complete:
                self._perform_handshake()
            
            self.connected = True
            logger.info(f"Connected to server {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to server: {e}")
            return False
    
    def disconnect(self):
        """Отключение от сервера."""
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            finally:
                self.socket = None
                self.connected = False
                logger.info("Disconnected from server")
    
    def _perform_handshake(self):
        """Выполнение процедуры рукопожатия с сервером."""
        try:
            logger.info("Starting handshake with server")
            
            # Если используется DH
            if self.handshake_type == HandshakeType.DIFFIE_HELLMAN:
                # Получаем публичный ключ сервера
                server_handshake_data = self._receive_handshake_data()
                
                if server_handshake_data["type"] != HandshakeType.DIFFIE_HELLMAN:
                    raise ValueError("Server is using different handshake type")
                
                # Проверяем публичный ключ сервера на безопасность
                server_public_key = KeyExchange.deserialize_public_key(server_handshake_data["public_key"])
                if not KeyExchange.validate_dh_key(server_public_key):
                    raise ValueError("Server's DH key failed security validation")
                
                # Подготавливаем свои данные для рукопожатия
                handshake_data = self.secure_channel.prepare_handshake(is_server=False)
                
                # Отправляем свой публичный ключ
                self._send_handshake_data(handshake_data)
                
                # Завершаем рукопожатие
                self.secure_channel.complete_dh_handshake(server_handshake_data["public_key"])
                logger.info("Диффи-Хеллман рукопожатие успешно завершено")
                
            # Если используется RSA
            elif self.handshake_type == HandshakeType.RSA:
                # Получаем публичный ключ сервера
                server_handshake_data = self._receive_handshake_data()
                
                if server_handshake_data["type"] != HandshakeType.RSA:
                    raise ValueError("Server is using different handshake type")
                
                # Создаем и шифруем новый AES-ключ для сервера
                encrypted_key = self.secure_channel.complete_rsa_handshake({
                    "server_public_key": server_handshake_data["public_key"]
                })
                
                # Отправляем зашифрованный ключ серверу
                self._send_handshake_data({
                    "type": HandshakeType.RSA,
                    "encrypted_key": encrypted_key
                })
                
            logger.info("Handshake completed successfully")
            
            return True
            
        except Exception as e:
            logger.error(f"Handshake error: {str(e)}")
            return False
    
    def _send_handshake_data(self, data: Dict[str, Any]):
        """
        Отправка данных рукопожатия серверу.
        
        Параметры:
        - data: Данные для отправки
        """
        # Сериализуем и шифруем данные
        json_data = json.dumps(data)
        encrypted_data = self.secure_channel.encrypt(json_data)
        
        # Отправляем размер сообщения, затем само сообщение
        message_size = len(encrypted_data)
        self.socket.send(message_size.to_bytes(4, byteorder='big'))
        self.socket.send(encrypted_data)
    
    def _receive_handshake_data(self) -> Dict[str, Any]:
        """
        Получение данных рукопожатия от сервера.
        
        Возвращает:
        - Словарь с данными рукопожатия
        """
        # Получаем размер сообщения
        header = self.socket.recv(4)
        if not header:
            raise ConnectionError("Connection closed during handshake")
        
        message_size = int.from_bytes(header, byteorder='big')
        encrypted_data = b''
        
        # Получаем полное сообщение
        remaining = message_size
        while remaining > 0:
            chunk = self.socket.recv(min(remaining, 4096))
            if not chunk:
                raise ConnectionError("Connection closed during handshake")
            encrypted_data += chunk
            remaining -= len(chunk)
        
        # Расшифровываем и парсим
        json_data = self.secure_channel.decrypt(encrypted_data)
        return json.loads(json_data)
    
    def send_command(self, command: Command) -> Optional[Response]:
        """
        Отправка команды серверу и получение ответа.
        
        Параметры:
        - command: Команда для отправки
        
        Возвращает:
        - Ответ от сервера
        """
        if not self.connected:
            if not self.connect():
                return None
        
        try:
            # Шифруем и отправляем команду
            json_data = command.to_json()
            encrypted_data = self.secure_channel.encrypt(json_data)
            
            # Отправляем размер сообщения, затем само сообщение
            message_size = len(encrypted_data)
            self.socket.send(message_size.to_bytes(4, byteorder='big'))
            self.socket.send(encrypted_data)
            
            # Получаем ответ
            header = self.socket.recv(4)
            if not header:
                logger.error("Connection closed by server")
                self.disconnect()
                return None
            
            message_size = int.from_bytes(header, byteorder='big')
            encrypted_data = b''
            
            # Получаем полное сообщение
            remaining = message_size
            while remaining > 0:
                chunk = self.socket.recv(min(remaining, 4096))
                if not chunk:
                    break
                encrypted_data += chunk
                remaining -= len(chunk)
            
            if not encrypted_data:
                logger.error("Empty response from server")
                return None
            
            # Расшифровываем ответ
            json_data = self.secure_channel.decrypt(encrypted_data)
            return Response.from_json(json_data)
            
        except Exception as e:
            logger.error(f"Error sending command: {e}")
            self.disconnect()
            return None
    
    def ping(self) -> bool:
        """
        Проверка соединения с сервером.
        
        Возвращает:
        - True, если сервер отвечает
        """
        response = self.send_command(create_status_command())
        return response is not None and response.status.value == "success"

# Пример использования
if __name__ == "__main__":
    # Настраиваем логирование
    logging.basicConfig(level=logging.INFO)
    
    # Сервер
    server = EnhancedServer(
        host="localhost",
        port=8766,
        handshake_type=HandshakeType.DIFFIE_HELLMAN
    )
    
    # Регистрируем обработчик команды статуса
    def handle_status(command: Command) -> Response:
        return Response(
            command_id=command.command_id,
            status=ResponseStatus.SUCCESS,
            data={"status": "ok", "server_time": time.time()}
        )
    
    server.register_command_handler("status", handle_status)
    
    try:
        # Запускаем сервер
        server.start()
        
        # Клиент
        client = EnhancedClient(
            host="localhost",
            port=8766,
            handshake_type=HandshakeType.DIFFIE_HELLMAN
        )
        
        # Подключаемся и отправляем команду
        if client.connect():
            response = client.send_command(create_status_command())
            if response:
                logger.info(f"Response: {response.data}")
            client.disconnect()
        
        # Тест с другим типом рукопожатия
        time.sleep(1)
        logger.info("\nTesting RSA handshake:")
        
        # Останавливаем предыдущий сервер
        server.stop()
        
        # Создаем новый сервер с RSA
        server = EnhancedServer(
            host="localhost",
            port=8766,
            handshake_type=HandshakeType.RSA
        )
        server.register_command_handler("status", handle_status)
        server.start()
        
        # Клиент с RSA
        client = EnhancedClient(
            host="localhost",
            port=8766,
            handshake_type=HandshakeType.RSA
        )
        
        # Подключаемся и отправляем команду
        if client.connect():
            response = client.send_command(create_status_command())
            if response:
                logger.info(f"Response: {response.data}")
            client.disconnect()
        
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    finally:
        # Останавливаем сервер
        server.stop() 