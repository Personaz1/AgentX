#!/usr/bin/env python3
"""
Серверная часть протокола агентов.
Обрабатывает подключения клиентов, аутентификацию и выполнение команд.
"""

import json
import asyncio
import logging
import uuid
import ssl
import signal
import time
import websockets
from typing import Dict, Any, Optional, List, Callable, Awaitable

from ..shared.protocol import Command, Response, CommandTypes, create_heartbeat_command
from ..shared.encryption import Encryption, EncryptionMethod, KeyExchangeMethod

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AgentServer:
    """
    Сервер агентского протокола.
    Обрабатывает подключения от клиентов и обеспечивает выполнение команд.
    """
    
    def __init__(self, 
                 host: str = "0.0.0.0", 
                 port: int = 8080, 
                 auth_enabled: bool = True,
                 ssl_context: Optional[ssl.SSLContext] = None,
                 encryption_enabled: bool = True):
        """
        Инициализация сервера.
        
        Параметры:
        - host: IP-адрес для прослушивания
        - port: Порт для прослушивания
        - auth_enabled: Флаг, указывающий, включена ли аутентификация
        - ssl_context: SSL контекст для защищенных соединений
        - encryption_enabled: Флаг, указывающий, включено ли шифрование данных
        """
        self.host = host
        self.port = port
        self.auth_enabled = auth_enabled
        self.ssl_context = ssl_context
        self.encryption_enabled = encryption_enabled
        
        # Хранилище активных соединений
        self.connections: Dict[str, Dict[str, Any]] = {}
        
        # Обработчики команд
        self.command_handlers: Dict[str, Callable[[Command, websockets.WebSocketServerProtocol], Awaitable[Response]]] = {}
        
        # Зарегистрированные агенты с их метаданными
        self.agents: Dict[str, Dict[str, Any]] = {}
        
        # Список разрешенных токенов аутентификации (в реальной системе хранится в БД)
        self.auth_tokens: List[str] = ["test-token"]  # Тестовый токен
        
        # Задачи для отслеживания активности агентов
        self.heartbeat_tasks = {}
        
        # Регистрация обработчиков по умолчанию
        self._register_default_handlers()
        
        # Флаг для контроля работы сервера
        self.running = False
        self.server = None
    
    def _register_default_handlers(self):
        """
        Регистрация стандартных обработчиков команд.
        """
        self.register_handler(CommandTypes.STATUS, self._handle_status_command)
        self.register_handler(CommandTypes.HEARTBEAT, self._handle_heartbeat_command)
        self.register_handler(CommandTypes.SHELL, self._handle_shell_command)
    
    def register_handler(self, command_type: str, handler: Callable[[Command, websockets.WebSocketServerProtocol], Awaitable[Response]]):
        """
        Регистрация обработчика для определенного типа команды.
        
        Параметры:
        - command_type: Тип команды
        - handler: Асинхронная функция-обработчик
        """
        self.command_handlers[command_type] = handler
        logger.info(f"Registered handler for command type: {command_type}")
    
    async def start(self):
        """
        Запуск сервера.
        """
        self.running = True
        
        # Настраиваем обработчик сигналов для корректного завершения работы
        loop = asyncio.get_running_loop()
        for s in [signal.SIGINT, signal.SIGTERM]:
            loop.add_signal_handler(s, lambda: asyncio.create_task(self.stop()))
        
        # Запускаем сервер
        self.server = await websockets.serve(
            self._handle_connection,
            self.host,
            self.port,
            ssl=self.ssl_context
        )
        
        logger.info(f"Agent server started on {self.host}:{self.port}")
        
        # Запускаем задачу для проверки активности агентов
        asyncio.create_task(self._monitor_agent_activity())
        
        # Ожидаем завершения работы сервера
        await self.server.wait_closed()
    
    async def stop(self):
        """
        Остановка сервера.
        """
        if not self.running:
            return
        
        logger.info("Stopping agent server...")
        self.running = False
        
        # Отключаем всех клиентов
        for agent_id, connection_info in list(self.connections.items()):
            websocket = connection_info.get("websocket")
            if websocket and not websocket.closed:
                await websocket.close(1001, "Server shutting down")
        
        # Очищаем список соединений
        self.connections.clear()
        self.agents.clear()
        
        # Останавливаем все задачи отслеживания активности
        for task in self.heartbeat_tasks.values():
            task.cancel()
        self.heartbeat_tasks.clear()
        
        # Останавливаем сервер
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        
        logger.info("Agent server stopped")
    
    async def _handle_connection(self, websocket: websockets.WebSocketServerProtocol, path: str):
        """
        Обработка входящего соединения.
        
        Параметры:
        - websocket: WebSocket соединение
        - path: Путь запроса
        """
        agent_id = None
        connection_info = {"websocket": websocket, "last_activity": time.time()}
        
        try:
            # Ожидаем первое сообщение для идентификации и настройки шифрования
            message_raw = await websocket.recv()
            message = json.loads(message_raw)
            
            # Получаем идентификатор агента
            agent_id = message.get("agent_id")
            if not agent_id:
                logger.warning("Connection attempt without agent_id")
                await websocket.close(1002, "Agent ID not provided")
                return
            
            # Сохраняем информацию о соединении
            self.connections[agent_id] = connection_info
            
            # Обрабатываем запрос на обмен ключами
            if message.get("type") == "key_exchange" and "data" in message:
                await self._handle_key_exchange(agent_id, message["data"], websocket)
            
            # Цикл обработки сообщений
            async for message_raw in websocket:
                try:
                    message = json.loads(message_raw)
                    connection_info["last_activity"] = time.time()
                    
                    # Обрабатываем зашифрованную команду
                    if message.get("type") == "encrypted_command" and "encrypted" in message:
                        encryption = self.connections[agent_id].get("encryption")
                        if not encryption:
                            await websocket.send(json.dumps({
                                "type": "response",
                                "status": "error",
                                "data": {"message": "Secure channel not established"}
                            }))
                            continue
                        
                        # Дешифруем данные
                        decrypted_data = encryption.decrypt(message["encrypted"])
                        command_data = json.loads(decrypted_data)
                        
                        # Обрабатываем команду
                        response = await self._process_command(command_data, websocket)
                        
                        # Шифруем ответ
                        response_dict = response.to_dict()
                        encrypted_data = encryption.encrypt(json.dumps(response_dict))
                        
                        # Отправляем зашифрованный ответ
                        await websocket.send(json.dumps({
                            "type": "encrypted_response",
                            "agent_id": agent_id,
                            "encrypted": encrypted_data
                        }))
                    
                    # Обрабатываем незашифрованную команду
                    elif message.get("type") == "command" and "data" in message:
                        command_data = message["data"]
                        response = await self._process_command(command_data, websocket)
                        
                        # Отправляем незашифрованный ответ
                        await websocket.send(json.dumps({
                            "type": "response",
                            "agent_id": agent_id,
                            "data": response.to_dict()
                        }))
                    
                    else:
                        logger.warning(f"Unknown message type: {message.get('type')}")
                        await websocket.send(json.dumps({
                            "type": "response",
                            "status": "error",
                            "data": {"message": "Unknown message type"}
                        }))
                
                except json.JSONDecodeError:
                    logger.error("Invalid JSON received")
                    await websocket.send(json.dumps({
                        "type": "response",
                        "status": "error",
                        "data": {"message": "Invalid JSON format"}
                    }))
                
                except Exception as e:
                    logger.error(f"Error processing message: {str(e)}")
                    await websocket.send(json.dumps({
                        "type": "response",
                        "status": "error",
                        "data": {"message": f"Server error: {str(e)}"}
                    }))
        
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Connection closed for agent {agent_id}")
        
        except Exception as e:
            logger.error(f"Unexpected error in connection handler: {str(e)}")
        
        finally:
            # Очистка ресурсов при отключении
            if agent_id and agent_id in self.connections:
                del self.connections[agent_id]
                logger.info(f"Removed connection for agent {agent_id}")
            
            # Отменяем задачу мониторинга активности, если она существует
            if agent_id and agent_id in self.heartbeat_tasks:
                self.heartbeat_tasks[agent_id].cancel()
                del self.heartbeat_tasks[agent_id]
    
    async def _handle_key_exchange(self, agent_id: str, handshake_data: Dict[str, Any], websocket: websockets.WebSocketServerProtocol):
        """
        Обработка запроса на обмен ключами.
        
        Параметры:
        - agent_id: Идентификатор агента
        - handshake_data: Данные для обмена ключами
        - websocket: WebSocket соединение
        """
        try:
            # Создаем объект шифрования для данного соединения
            encryption = Encryption()
            
            if "dh_public_key" in handshake_data:
                # Обмен ключами по алгоритму Диффи-Хеллмана
                server_handshake = encryption.prepare_dh_handshake()
                
                # Устанавливаем публичный ключ клиента
                encryption.complete_dh_handshake(handshake_data)
                
                # Отправляем свои данные клиенту
                await websocket.send(json.dumps({
                    "type": "key_exchange",
                    "status": "success",
                    "data": server_handshake
                }))
            
            elif "rsa_public_key" in handshake_data:
                # Обмен ключами по алгоритму RSA
                server_handshake = encryption.prepare_rsa_response_handshake(handshake_data)
                
                # Отправляем зашифрованный AES ключ клиенту
                await websocket.send(json.dumps({
                    "type": "key_exchange",
                    "status": "success",
                    "data": server_handshake
                }))
            
            else:
                logger.error(f"Unknown key exchange format for agent {agent_id}")
                await websocket.send(json.dumps({
                    "type": "key_exchange",
                    "status": "error",
                    "data": {"message": "Unknown key exchange format"}
                }))
                return
            
            # Сохраняем объект шифрования для данного соединения
            self.connections[agent_id]["encryption"] = encryption
            logger.info(f"Secure channel established with agent {agent_id}")
            
        except Exception as e:
            logger.error(f"Error during key exchange with agent {agent_id}: {str(e)}")
            await websocket.send(json.dumps({
                "type": "key_exchange",
                "status": "error",
                "data": {"message": f"Key exchange error: {str(e)}"}
            }))
    
    async def _process_command(self, command_data: Dict[str, Any], websocket: websockets.WebSocketServerProtocol) -> Response:
        """
        Обработка входящей команды.
        
        Параметры:
        - command_data: Данные команды
        - websocket: WebSocket соединение
        
        Возвращает:
        - Объект Response с результатом выполнения команды
        """
        try:
            # Преобразуем словарь в объект Command
            command = Command.from_dict(command_data)
            
            # Проверяем аутентификацию, если она включена
            if self.auth_enabled and command.command_type != CommandTypes.HEARTBEAT:
                if not command.auth_token or command.auth_token not in self.auth_tokens:
                    return Response(
                        command_id=command.command_id,
                        status="error",
                        data={"message": "Authentication failed: Invalid token"},
                        agent_id=command.agent_id
                    )
            
            # Получаем обработчик для данного типа команды
            handler = self.command_handlers.get(command.command_type)
            if not handler:
                return Response(
                    command_id=command.command_id,
                    status="error",
                    data={"message": f"Unknown command type: {command.command_type}"},
                    agent_id=command.agent_id
                )
            
            # Вызываем обработчик
            logger.info(f"Processing command {command.command_type} from agent {command.agent_id}")
            response = await handler(command, websocket)
            return response
            
        except Exception as e:
            logger.error(f"Error processing command: {str(e)}")
            return Response(
                command_id=command_data.get("command_id", str(uuid.uuid4())),
                status="error",
                data={"message": f"Command processing error: {str(e)}"},
                agent_id=command_data.get("agent_id", "unknown")
            )
    
    async def _handle_status_command(self, command: Command, websocket: websockets.WebSocketServerProtocol) -> Response:
        """
        Обработчик статусной команды.
        
        Параметры:
        - command: Объект команды
        - websocket: WebSocket соединение
        
        Возвращает:
        - Ответ с текущим статусом сервера
        """
        # Проверяем наличие агента в списке зарегистрированных
        if command.agent_id not in self.agents:
            # Регистрируем нового агента
            self.agents[command.agent_id] = {
                "registered_at": time.time(),
                "last_activity": time.time(),
                "metadata": command.data.get("metadata", {})
            }
            logger.info(f"New agent registered: {command.agent_id}")
        else:
            # Обновляем время последней активности
            self.agents[command.agent_id]["last_activity"] = time.time()
            
            # Обновляем метаданные, если они предоставлены
            if "metadata" in command.data:
                self.agents[command.agent_id]["metadata"] = command.data["metadata"]
        
        # Формируем ответ
        return Response(
            command_id=command.command_id,
            status="success",
            data={
                "server_status": "running",
                "agent_count": len(self.agents),
                "server_time": time.time()
            },
            agent_id=command.agent_id
        )
    
    async def _handle_heartbeat_command(self, command: Command, websocket: websockets.WebSocketServerProtocol) -> Response:
        """
        Обработчик команды heartbeat.
        
        Параметры:
        - command: Объект команды
        - websocket: WebSocket соединение
        
        Возвращает:
        - Подтверждение получения сигнала heartbeat
        """
        # Обновляем время последней активности агента
        if command.agent_id in self.agents:
            self.agents[command.agent_id]["last_activity"] = time.time()
        
        # Если агент не зарегистрирован, регистрируем его
        else:
            self.agents[command.agent_id] = {
                "registered_at": time.time(),
                "last_activity": time.time(),
                "metadata": command.data.get("metadata", {})
            }
            logger.info(f"Agent registered via heartbeat: {command.agent_id}")
        
        # Формируем ответ
        return Response(
            command_id=command.command_id,
            status="success",
            data={"message": "Heartbeat acknowledged"},
            agent_id=command.agent_id
        )
    
    async def _handle_shell_command(self, command: Command, websocket: websockets.WebSocketServerProtocol) -> Response:
        """
        Обработчик команды выполнения shell-команды.
        В реальной реализации здесь должна быть проверка разрешений на выполнение команд.
        
        Параметры:
        - command: Объект команды
        - websocket: WebSocket соединение
        
        Возвращает:
        - Результат выполнения shell-команды
        """
        # В демонстрационных целях просто возвращаем имитацию выполнения команды
        command_string = command.data.get("command", "")
        
        # Имитация выполнения команды (в реальной реализации здесь должно быть реальное выполнение)
        return Response(
            command_id=command.command_id,
            status="success",
            data={
                "command": command_string,
                "output": f"Simulated output for: {command_string}",
                "exit_code": 0
            },
            agent_id=command.agent_id
        )
    
    async def _monitor_agent_activity(self, check_interval: int = 30, max_inactivity: int = 120):
        """
        Мониторинг активности агентов и удаление неактивных соединений.
        
        Параметры:
        - check_interval: Интервал проверки в секундах
        - max_inactivity: Максимальное время неактивности в секундах
        """
        while self.running:
            try:
                current_time = time.time()
                
                # Проверяем активность каждого агента
                for agent_id in list(self.agents.keys()):
                    agent_info = self.agents[agent_id]
                    last_activity = agent_info.get("last_activity", 0)
                    
                    # Если агент неактивен слишком долго и есть активное соединение
                    if current_time - last_activity > max_inactivity and agent_id in self.connections:
                        websocket = self.connections[agent_id].get("websocket")
                        if websocket and not websocket.closed:
                            logger.info(f"Closing inactive connection for agent {agent_id}")
                            await websocket.close(1000, "Inactivity timeout")
                        
                        # Удаляем информацию о соединении
                        del self.connections[agent_id]
                
                # Ожидаем до следующей проверки
                await asyncio.sleep(check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in agent activity monitor: {str(e)}")
                await asyncio.sleep(check_interval)
    
    async def broadcast_command(self, command: Command, filter_func: Optional[Callable[[str, Dict[str, Any]], bool]] = None) -> Dict[str, Response]:
        """
        Широковещательная отправка команды всем подключенным агентам или подмножеству.
        
        Параметры:
        - command: Команда для отправки
        - filter_func: Функция фильтрации агентов (принимает agent_id и словарь с метаданными агента)
        
        Возвращает:
        - Словарь с ответами от агентов
        """
        responses = {}
        
        # Отбираем агентов для отправки команды
        target_agents = []
        for agent_id, connection_info in self.connections.items():
            if agent_id in self.agents:
                agent_info = self.agents[agent_id]
                
                # Применяем функцию фильтрации, если она предоставлена
                if filter_func is None or filter_func(agent_id, agent_info):
                    target_agents.append(agent_id)
        
        # Отправляем команду каждому агенту
        for agent_id in target_agents:
            connection_info = self.connections.get(agent_id)
            if not connection_info or "websocket" not in connection_info:
                continue
            
            websocket = connection_info["websocket"]
            if websocket.closed:
                continue
            
            # Создаем копию команды с идентификатором агента
            agent_command = command.copy()
            agent_command.agent_id = agent_id
            agent_command.command_id = str(uuid.uuid4())  # Генерируем новый ID для каждого агента
            
            try:
                # Подготавливаем данные команды
                command_dict = agent_command.to_dict()
                
                # Проверяем, установлено ли шифрование для данного соединения
                encryption = connection_info.get("encryption")
                
                if encryption and self.encryption_enabled:
                    # Шифруем данные команды
                    encrypted_data = encryption.encrypt(json.dumps(command_dict))
                    message = {
                        "type": "encrypted_command",
                        "agent_id": agent_id,
                        "encrypted": encrypted_data
                    }
                else:
                    # Отправляем команду без шифрования
                    message = {
                        "type": "command",
                        "agent_id": agent_id,
                        "data": command_dict
                    }
                
                # Отправляем команду
                await websocket.send(json.dumps(message))
                
                # Ожидаем ответа с таймаутом
                timeout = command.timeout or 30
                
                try:
                    response_raw = await asyncio.wait_for(websocket.recv(), timeout)
                    response_json = json.loads(response_raw)
                    
                    if response_json.get("type") == "encrypted_response" and "encrypted" in response_json:
                        # Дешифруем ответ
                        decrypted_data = encryption.decrypt(response_json["encrypted"])
                        response_data = json.loads(decrypted_data)
                        response = Response.from_dict(response_data)
                    elif response_json.get("type") == "response" and "data" in response_json:
                        response = Response.from_dict(response_json["data"])
                    else:
                        logger.error(f"Invalid response format from agent {agent_id}")
                        continue
                    
                    # Сохраняем ответ
                    responses[agent_id] = response
                    
                except asyncio.TimeoutError:
                    logger.error(f"Timeout waiting for response from agent {agent_id}")
                    responses[agent_id] = Response(
                        command_id=agent_command.command_id,
                        status="error",
                        data={"message": "Timeout waiting for response"},
                        agent_id=agent_id
                    )
            
            except Exception as e:
                logger.error(f"Error broadcasting command to agent {agent_id}: {str(e)}")
                responses[agent_id] = Response(
                    command_id=agent_command.command_id,
                    status="error",
                    data={"message": f"Error sending command: {str(e)}"},
                    agent_id=agent_id
                )
        
        return responses


# Пример запуска сервера
async def example_server():
    # Создаем и запускаем сервер
    server = AgentServer(host="0.0.0.0", port=8080, auth_enabled=True, encryption_enabled=True)
    
    # Регистрируем дополнительный обработчик команды
    async def handle_custom_command(command, websocket):
        return Response(
            command_id=command.command_id,
            status="success",
            data={"message": "Custom command processed successfully"},
            agent_id=command.agent_id
        )
    
    server.register_handler("custom", handle_custom_command)
    
    # Запускаем сервер
    await server.start()


if __name__ == "__main__":
    # Запускаем пример использования сервера
    try:
        asyncio.run(example_server())
    except KeyboardInterrupt:
        logger.info("Server stopped by user") 