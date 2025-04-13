#!/usr/bin/env python3
"""
Интеграция каркаса агента с нашим протоколом безопасной коммуникации.
Этот файл показывает, как можно улучшить предложенный агент, используя
наш разработанный протокол для безопасной связи с сервером.
"""

import importlib
import platform
import os
import time
import sys
import logging
import json
from typing import Dict, Any, Optional

# Добавляем путь к нашему протоколу
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Импортируем наш протокол
from shared.protocol import (
    Command, Response, ResponseStatus, CommandType,
    create_shell_command, create_file_command, create_status_command
)
from shared.communication import CommunicationClient, SecureChannel

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("agent.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('security_agent')

# Конфигурация агента
AGENT_ID = os.environ.get("AGENT_ID", "agent-" + platform.node())
SERVER_HOST = os.environ.get("SERVER_HOST", "localhost")
SERVER_PORT = int(os.environ.get("SERVER_PORT", "8765"))
ENCRYPTION_KEY = os.environ.get("ENCRYPTION_KEY", "")
HEARTBEAT_INTERVAL = int(os.environ.get("HEARTBEAT_INTERVAL", "60"))

class SecureAgent:
    def __init__(self, agent_id: str, server_host: str, server_port: int, encryption_key: Optional[str] = None):
        self.agent_id = agent_id
        self.server_host = server_host
        self.server_port = server_port
        
        # Создаем защищенный канал связи
        if encryption_key and encryption_key.startswith("base64:"):
            # Используем предоставленный ключ
            base64_key = encryption_key.split("base64:", 1)[1]
            secure_channel = SecureChannel.from_base64_key(base64_key)
        else:
            # Создаем новый ключ
            secure_channel = SecureChannel(encryption_key) if encryption_key else SecureChannel()
            
        # Сохраняем ключ шифрования
        self.encryption_key_base64 = secure_channel.get_key_base64()
        logger.info(f"Используется ключ шифрования (base64): {self.encryption_key_base64[:10]}...")
        
        # Создаем клиент для связи с сервером
        self.client = CommunicationClient(
            host=server_host,
            port=server_port,
            secure_channel=secure_channel
        )
        
        # Для хранения модулей
        self.modules = {}
        
    def connect(self) -> bool:
        """Подключение к серверу."""
        return self.client.connect()
    
    def disconnect(self):
        """Отключение от сервера."""
        self.client.disconnect()
    
    def collect_basic_info(self) -> Dict[str, Any]:
        """Сбор базовой информации о системе."""
        return {
            "agent_id": self.agent_id,
            "os": platform.system(),
            "os_release": platform.release(),
            "hostname": platform.node(),
            "username": os.getenv("USER") or os.getenv("USERNAME"),
            "cpu": platform.processor(),
            "python_version": platform.python_version(),
            "timestamp": time.time()
        }
    
    def report_to_server(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Отправка отчета на сервер с использованием нашего протокола."""
        # Создаем команду для отправки данных
        cmd = Command(
            command_type=CommandType.SYSTEM,
            payload={
                "action": "report",
                "agent_id": self.agent_id,
                "data": data
            }
        )
        
        # Отправляем команду и получаем ответ
        response = self.client.send_command(cmd)
        
        if not response:
            logger.error("Не удалось получить ответ от сервера")
            return {}
        
        # Проверяем статус ответа
        if response.status != ResponseStatus.SUCCESS:
            logger.error(f"Ошибка при отправке отчета: {response.error_message}")
            return {}
        
        return response.data
    
    def load_module(self, module_name: str) -> bool:
        """Загрузка модуля из указанного имени."""
        try:
            if module_name in self.modules:
                # Модуль уже загружен
                return True
                
            # Проверяем, есть ли модуль локально
            try:
                module = importlib.import_module(f"modules.{module_name}")
                self.modules[module_name] = module
                logger.info(f"Модуль {module_name} загружен локально")
                return True
            except ImportError:
                logger.info(f"Модуль {module_name} не найден локально, пробуем загрузить с сервера")
            
            # Пытаемся загрузить модуль с сервера
            cmd = Command(
                command_type=CommandType.SYSTEM,
                payload={
                    "action": "get_module",
                    "module_name": module_name
                }
            )
            
            response = self.client.send_command(cmd)
            
            if not response or response.status != ResponseStatus.SUCCESS:
                logger.error(f"Не удалось загрузить модуль {module_name}")
                return False
            
            # Получаем код модуля
            module_code = response.data.get("module_code", "")
            if not module_code:
                logger.error(f"Получен пустой код модуля {module_name}")
                return False
            
            # Сохраняем код модуля во временный файл
            os.makedirs("modules", exist_ok=True)
            with open(f"modules/{module_name}.py", "w") as f:
                f.write(module_code)
                
            # Загружаем модуль
            module = importlib.import_module(f"modules.{module_name}")
            self.modules[module_name] = module
            logger.info(f"Модуль {module_name} загружен с сервера")
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при загрузке модуля {module_name}: {e}")
            return False
    
    def run_module(self, module_name: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Запуск указанного модуля с параметрами."""
        if not self.load_module(module_name):
            return {"error": f"Не удалось загрузить модуль {module_name}"}
        
        try:
            module = self.modules[module_name]
            result = module.run(**(params or {}))
            return result
        except Exception as e:
            logger.error(f"Ошибка при выполнении модуля {module_name}: {e}")
            return {"error": str(e)}
    
    def execute_shell_command(self, command: str) -> Dict[str, Any]:
        """Выполнение shell-команды."""
        # Используем нашу функцию из протокола
        cmd = create_shell_command(command)
        response = self.client.send_command(cmd)
        
        if not response:
            logger.error("Не удалось получить ответ от сервера")
            return {"error": "Нет ответа от сервера"}
        
        if response.status != ResponseStatus.SUCCESS:
            logger.error(f"Ошибка при выполнении команды: {response.error_message}")
            return {"error": response.error_message or "Неизвестная ошибка"}
        
        return response.data
    
    def main_loop(self):
        """Основной цикл работы агента."""
        logger.info(f"Запуск агента {self.agent_id}...")
        
        while True:
            try:
                # Проверяем подключение к серверу
                if not self.client.connected:
                    if not self.connect():
                        logger.error("Не удалось подключиться к серверу. Повторная попытка через минуту...")
                        time.sleep(60)
                        continue
                
                # Собираем базовую информацию о системе
                info = self.collect_basic_info()
                
                # Отправляем отчет на сервер
                server_response = self.report_to_server(info)
                
                # Проверяем, есть ли задачи от сервера
                task = server_response.get("task")
                if task:
                    task_name = task.get("name")
                    task_params = task.get("params", {})
                    
                    logger.info(f"Получена задача: {task_name}")
                    
                    # Выполняем задачу
                    result = self.run_module(task_name, task_params)
                    
                    # Отправляем результат выполнения задачи
                    self.report_to_server({
                        "task_result": {
                            "task_name": task_name,
                            "result": result
                        }
                    })
                
                # Ждем перед следующим циклом
                time.sleep(HEARTBEAT_INTERVAL)
                
            except KeyboardInterrupt:
                logger.info("Получен сигнал прерывания. Завершение работы...")
                break
                
            except Exception as e:
                logger.error(f"Ошибка в основном цикле: {e}")
                time.sleep(60)  # Пауза перед повторной попыткой
        
        # Отключаемся от сервера перед выходом
        self.disconnect()
        logger.info("Агент остановлен")

def main():
    """Основная функция для запуска агента."""
    agent = SecureAgent(
        agent_id=AGENT_ID,
        server_host=SERVER_HOST,
        server_port=SERVER_PORT,
        encryption_key=ENCRYPTION_KEY
    )
    
    agent.main_loop()

if __name__ == "__main__":
    main() 