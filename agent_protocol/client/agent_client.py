#!/usr/bin/env python3
"""
Клиент для работы с протоколом агентов.
Реализует функциональность для отправки команд серверу и обработки ответов.
"""

import json
import uuid
import time
import logging
import asyncio
import websockets
from typing import Dict, Any, Optional, Callable, List, Union, Tuple, Awaitable

from ..shared.protocol import Command, Response, create_status_command, create_heartbeat_command
from ..shared.encryption import Encryption, EncryptionMethod, KeyExchangeMethod

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AgentClient:
    """
    Клиент агента для взаимодействия с сервером.
    Поддерживает подключение к серверу, аутентификацию и асинхронную отправку команд.
    """
    
    def __init__(self, 
                 server_url: str, 
                 agent_id: str = None, 
                 auth_token: Optional[str] = None,
                 encryption_method: str = EncryptionMethod.AES,
                 key_exchange_method: str = KeyExchangeMethod.DIFFIE_HELLMAN):
        """
        Инициализация клиента агента.
        
        Параметры:
        - server_url: URL-адрес сервера
        - agent_id: Идентификатор агента (если не указан, будет сгенерирован случайный UUID)
        - auth_token: Токен аутентификации (опционально)
        - encryption_method: Метод шифрования (по умолчанию AES)
        - key_exchange_method: Метод обмена ключами (по умолчанию Диффи-Хеллман)
        """
        self.server_url = server_url
        self.agent_id = agent_id or str(uuid.uuid4())
        self.auth_token = auth_token
        self.websocket = None
        self.connected = False
        self.pending_commands = {}
        self.command_callbacks = {}
        self.connection_loop_task = None
        self.heartbeat_task = None
        
        # Инициализация шифрования
        self.encryption = Encryption(method=encryption_method)
        self.key_exchange_method = key_exchange_method
        self.encryption_established = False
    
    async def connect(self) -> bool:
        """
        Установка соединения с сервером.
        
        Возвращает:
        - True, если подключение успешно, False в противном случае
        """
        try:
            self.websocket = await websockets.connect(self.server_url)
            logger.info(f"Connected to server at {self.server_url}")
            
            # Выполняем обмен ключами для установки шифрованного канала
            success = await self._perform_key_exchange()
            if not success:
                logger.error("Failed to establish secure channel")
                await self.websocket.close()
                return False
            
            # Отправляем статусную команду для проверки соединения
            status_command = create_status_command(auth_token=self.auth_token)
            response = await self._send_command_internal(status_command)
            
            if response and response.status == "success":
                self.connected = True
                logger.info("Successfully authenticated with server")
                return True
            else:
                logger.error("Authentication failed")
                await self.websocket.close()
                return False
                
        except Exception as e:
            logger.error(f"Connection error: {str(e)}")
            return False
    
    async def _perform_key_exchange(self) -> bool:
        """
        Выполнение обмена ключами с сервером для установки шифрованного канала.
        
        Возвращает:
        - True, если обмен ключами успешен, False в противном случае
        """
        try:
            if self.key_exchange_method == KeyExchangeMethod.DIFFIE_HELLMAN:
                # Инициируем рукопожатие Диффи-Хеллмана
                handshake_data = self.encryption.prepare_dh_handshake()
                
                # Отправляем данные для рукопожатия
                await self.websocket.send(json.dumps({
                    "type": "key_exchange",
                    "agent_id": self.agent_id,
                    "data": handshake_data
                }))
                
                # Получаем ответ сервера
                response_str = await self.websocket.recv()
                response = json.loads(response_str)
                
                if response.get("type") != "key_exchange" or "data" not in response:
                    logger.error("Invalid key exchange response from server")
                    return False
                
                # Завершаем рукопожатие и вычисляем общий ключ
                self.encryption.complete_dh_handshake(response["data"])
                
            elif self.key_exchange_method == KeyExchangeMethod.RSA:
                # Инициируем рукопожатие RSA
                handshake_data = self.encryption.prepare_rsa_handshake()
                
                # Отправляем публичный ключ RSA
                await self.websocket.send(json.dumps({
                    "type": "key_exchange",
                    "agent_id": self.agent_id,
                    "data": handshake_data
                }))
                
                # Получаем ответ сервера с зашифрованным ключом AES
                response_str = await self.websocket.recv()
                response = json.loads(response_str)
                
                if response.get("type") != "key_exchange" or "data" not in response:
                    logger.error("Invalid key exchange response from server")
                    return False
                
                # Расшифровываем ключ AES
                self.encryption.process_rsa_handshake_response(response["data"])
            
            else:
                logger.warning(f"No key exchange performed with method: {self.key_exchange_method}")
            
            self.encryption_established = True
            logger.info(f"Secure channel established using {self.key_exchange_method}")
            return True
            
        except Exception as e:
            logger.error(f"Key exchange error: {str(e)}")
            return False
    
    async def disconnect(self):
        """
        Отключение от сервера.
        """
        if self.websocket:
            await self.websocket.close()
            self.connected = False
            logger.info("Disconnected from server")
    
    async def start_connection_loop(self, reconnect_interval: int = 30):
        """
        Запуск цикла поддержания соединения с сервером.
        
        Параметры:
        - reconnect_interval: Интервал переподключения в секундах
        """
        async def connection_loop():
            while True:
                if not self.connected:
                    await self.connect()
                await asyncio.sleep(reconnect_interval)
        
        self.connection_loop_task = asyncio.create_task(connection_loop())
        
        # Запуск задачи отправки heartbeat
        await self.start_heartbeat()
    
    async def stop_connection_loop(self):
        """
        Остановка цикла поддержания соединения с сервером.
        """
        if self.connection_loop_task:
            self.connection_loop_task.cancel()
            self.connection_loop_task = None
        
        # Остановка задачи отправки heartbeat
        await self.stop_heartbeat()
        
        # Отключение от сервера
        await self.disconnect()
    
    async def start_heartbeat(self, interval: int = 60):
        """
        Запуск отправки периодических сигналов heartbeat серверу.
        
        Параметры:
        - interval: Интервал отправки в секундах
        """
        async def heartbeat_loop():
            while self.connected:
                try:
                    heartbeat_command = create_heartbeat_command(self.agent_id, auth_token=self.auth_token)
                    await self._send_command_internal(heartbeat_command)
                    logger.debug("Heartbeat sent")
                except Exception as e:
                    logger.error(f"Error sending heartbeat: {str(e)}")
                await asyncio.sleep(interval)
        
        self.heartbeat_task = asyncio.create_task(heartbeat_loop())
    
    async def stop_heartbeat(self):
        """
        Остановка отправки сигналов heartbeat.
        """
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
            self.heartbeat_task = None
    
    async def send_command(self, command: Command, callback: Optional[Callable[[Response], Awaitable[None]]] = None) -> Optional[Response]:
        """
        Отправка команды серверу.
        
        Параметры:
        - command: Объект команды
        - callback: Асинхронный коллбэк, вызываемый при получении ответа (опционально)
        
        Возвращает:
        - Ответ сервера или None, если отправка не удалась
        """
        if not self.connected:
            connected = await self.connect()
            if not connected:
                logger.error("Failed to connect to server")
                return None
        
        if callback:
            self.command_callbacks[command.command_id] = callback
        
        return await self._send_command_internal(command)
    
    async def _send_command_internal(self, command: Command) -> Optional[Response]:
        """
        Внутренний метод для отправки команды серверу.
        
        Параметры:
        - command: Объект команды
        
        Возвращает:
        - Ответ сервера или None, если отправка не удалась
        """
        try:
            # Добавляем идентификатор агента и токен аутентификации к команде
            command.agent_id = self.agent_id
            if not command.auth_token and self.auth_token:
                command.auth_token = self.auth_token
            
            # Создаем объект с метаданными и зашифрованными данными
            command_dict = command.to_dict()
            
            if self.encryption_established:
                # Если канал шифрования установлен, шифруем данные
                encrypted_data = self.encryption.encrypt(json.dumps(command_dict))
                message = {
                    "type": "encrypted_command",
                    "agent_id": self.agent_id,
                    "encrypted": encrypted_data
                }
            else:
                # Если канал не шифрованный, отправляем данные открыто
                message = {
                    "type": "command",
                    "agent_id": self.agent_id,
                    "data": command_dict
                }
            
            # Отправляем команду
            await self.websocket.send(json.dumps(message))
            logger.debug(f"Command sent: {command.command_type} (ID: {command.command_id})")
            
            # Ожидаем ответа с установленным таймаутом
            timeout = command.timeout or 30  # Значение по умолчанию 30 секунд
            
            try:
                response_raw = await asyncio.wait_for(self.websocket.recv(), timeout)
                
                # Разбираем ответ
                response_json = json.loads(response_raw)
                
                if response_json.get("type") == "encrypted_response" and "encrypted" in response_json:
                    # Дешифруем данные ответа
                    decrypted_data = self.encryption.decrypt(response_json["encrypted"])
                    response_data = json.loads(decrypted_data)
                    response = Response.from_dict(response_data)
                elif response_json.get("type") == "response" and "data" in response_json:
                    response = Response.from_dict(response_json["data"])
                else:
                    logger.error(f"Invalid response format: {response_json}")
                    return None
                
                logger.debug(f"Received response for command {response.command_id}: {response.status}")
                
                # Проверяем, есть ли коллбэк для данной команды
                callback = self.command_callbacks.get(command.command_id)
                if callback:
                    asyncio.create_task(callback(response))
                    del self.command_callbacks[command.command_id]
                
                return response
                
            except asyncio.TimeoutError:
                logger.error(f"Timeout waiting for response to command {command.command_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error sending command: {str(e)}")
            self.connected = False
            return None
    
    async def start_listener(self):
        """
        Запуск слушателя входящих сообщений от сервера.
        """
        async def listener():
            while self.connected:
                try:
                    message_raw = await self.websocket.recv()
                    message = json.loads(message_raw)
                    
                    if message.get("type") == "encrypted_command" and "encrypted" in message:
                        # Дешифруем входящую команду
                        decrypted_data = self.encryption.decrypt(message["encrypted"])
                        command_data = json.loads(decrypted_data)
                        await self._handle_incoming_command(command_data)
                    elif message.get("type") == "command" and "data" in message:
                        await self._handle_incoming_command(message["data"])
                    else:
                        logger.warning(f"Unknown message type: {message.get('type')}")
                        
                except websockets.exceptions.ConnectionClosed:
                    logger.info("Connection closed by server")
                    self.connected = False
                    break
                except Exception as e:
                    logger.error(f"Error in listener: {str(e)}")
        
        asyncio.create_task(listener())
    
    async def _handle_incoming_command(self, command_data: Dict[str, Any]):
        """
        Обработка входящей команды от сервера.
        
        Параметры:
        - command_data: Данные команды
        """
        try:
            command = Command.from_dict(command_data)
            logger.info(f"Received command from server: {command.command_type}")
            
            # Здесь можно добавить обработку различных типов команд
            # Например, вызов соответствующих обработчиков
            
            # В данной реализации просто отправляем успешный ответ
            response = Response(
                command_id=command.command_id,
                status="success",
                data={"message": "Command processed"},
                agent_id=self.agent_id
            )
            
            # Отправляем ответ
            response_dict = response.to_dict()
            
            if self.encryption_established:
                # Если канал шифрования установлен, шифруем данные
                encrypted_data = self.encryption.encrypt(json.dumps(response_dict))
                message = {
                    "type": "encrypted_response",
                    "agent_id": self.agent_id,
                    "encrypted": encrypted_data
                }
            else:
                # Если канал не шифрованный, отправляем данные открыто
                message = {
                    "type": "response",
                    "agent_id": self.agent_id,
                    "data": response_dict
                }
            
            await self.websocket.send(json.dumps(message))
            
        except Exception as e:
            logger.error(f"Error handling incoming command: {str(e)}")


# Пример использования клиента
async def example_usage():
    # Создаем клиента
    client = AgentClient(
        server_url="ws://localhost:8080/agent",
        agent_id="example-agent",
        auth_token="test-token",
        encryption_method=EncryptionMethod.AES,
        key_exchange_method=KeyExchangeMethod.DIFFIE_HELLMAN
    )
    
    # Подключаемся к серверу
    connected = await client.connect()
    if not connected:
        print("Failed to connect to server")
        return
    
    # Запускаем слушателя входящих сообщений
    await client.start_listener()
    
    # Пример отправки команды с использованием коллбэка
    async def command_callback(response):
        print(f"Received response: {response.status}")
        print(f"Response data: {response.data}")
    
    # Создаем команду для выполнения shell-команды
    from ..shared.protocol import create_shell_command
    command = create_shell_command("ls -la", auth_token=client.auth_token)
    
    # Отправляем команду и регистрируем коллбэк
    response = await client.send_command(command, command_callback)
    
    # Дожидаемся завершения обработки
    await asyncio.sleep(5)
    
    # Отключаемся от сервера
    await client.disconnect()


if __name__ == "__main__":
    # Запускаем пример использования
    asyncio.run(example_usage()) 