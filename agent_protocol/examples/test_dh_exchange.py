#!/usr/bin/env python3
"""
Тестирование безопасного обмена ключами по алгоритму Диффи-Хеллмана.
"""

import os
import sys
import time
import logging
import threading
import multiprocessing
from typing import Dict, Any, Optional

# Добавляем папку проекта в PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from shared.key_exchange import KeyExchange, perform_key_exchange
from shared.enhanced_communication import EnhancedClient, EnhancedServer, HandshakeType
from shared.protocol import Command, Response, CommandType

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_dh_exchange')

# Параметры для тестирования
HOST = '127.0.0.1'  # localhost
PORT = 8765  # порт для тестирования

def start_server():
    """Запуск тестового сервера с поддержкой DH."""
    server = EnhancedServer(
        host=HOST,
        port=PORT,
        handshake_type=HandshakeType.DIFFIE_HELLMAN
    )
    
    # Зарегистрировать обработчик эхо-команды
    def echo_handler(command: Command) -> Response:
        logger.info(f"Received command: {command.command_type}")
        return Response(
            command_id=command.command_id,
            success=True,
            data={"echo": command.data}
        )
    
    server.register_command_handler("echo", echo_handler)
    
    # Запуск сервера
    try:
        server.start()
        logger.info("Server started. Press Ctrl+C to stop.")
        
        # Поддержание сервера активным
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Stopping server...")
    finally:
        server.stop()
        logger.info("Server stopped.")

def test_client():
    """Тестирование клиента с подключением через DH."""
    time.sleep(1)  # Задержка, чтобы сервер успел запуститься
    
    client = EnhancedClient(
        host=HOST,
        port=PORT,
        handshake_type=HandshakeType.DIFFIE_HELLMAN
    )
    
    try:
        # Подключение к серверу
        connected = client.connect()
        if not connected:
            logger.error("Failed to connect to server")
            return
        
        logger.info("Connected to server. Testing echo command...")
        
        # Отправка тестовой команды
        echo_command = Command("echo", {"message": "Hello, secure world!"})
        response = client.send_command(echo_command)
        
        if response and response.success:
            logger.info(f"Received response: {response.data}")
        else:
            logger.error("Echo command failed")
        
        # Отключение
        client.disconnect()
        logger.info("Client test completed.")
        
    except Exception as e:
        logger.error(f"Client error: {str(e)}")
    finally:
        client.disconnect()

def main():
    """Основная функция тестирования."""
    logger.info("Starting Diffie-Hellman key exchange test")
    
    # Запуск сервера в отдельном процессе
    server_process = multiprocessing.Process(target=start_server)
    server_process.start()
    
    try:
        # Запуск клиентского теста
        test_client()
    finally:
        # Завершение работы сервера
        server_process.terminate()
        server_process.join()
    
    logger.info("Test completed")

if __name__ == "__main__":
    main() 