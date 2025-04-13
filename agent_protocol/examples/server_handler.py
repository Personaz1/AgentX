#!/usr/bin/env python3
"""
Пример обработчика на серверной стороне для работы с безопасными агентами.
Интегрируется с нашим протоколом агентской коммуникации.
"""

import os
import sys
import json
import time
import logging
import threading
from typing import Dict, Any, List, Optional
from datetime import datetime

# Добавляем путь к нашему протоколу
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Импортируем наш протокол
from shared.protocol import (
    Command, Response, ResponseStatus, CommandType
)
from shared.communication import CommunicationServer, SecureChannel

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("server.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('agent_server')

class AgentServer:
    def __init__(
        self,
        host: str = '0.0.0.0',
        port: int = 8765,
        encryption_key: Optional[str] = None,
        use_ssl: bool = False,
        cert_file: Optional[str] = None,
        key_file: Optional[str] = None
    ):
        self.host = host
        self.port = port
        
        # Создаем защищенный канал связи
        if encryption_key and encryption_key.startswith("base64:"):
            # Используем предоставленный ключ
            base64_key = encryption_key.split("base64:", 1)[1]
            secure_channel = SecureChannel.from_base64_key(base64_key)
        else:
            # Создаем новый ключ
            secure_channel = SecureChannel(encryption_key) if encryption_key else SecureChannel()
            
        self.encryption_key_base64 = secure_channel.get_key_base64()
        logger.info(f"Используется ключ шифрования (base64): {self.encryption_key_base64}")
        
        # Создаем сервер
        self.server = CommunicationServer(
            host=host,
            port=port,
            secure_channel=secure_channel,
            use_ssl=use_ssl,
            cert_file=cert_file,
            key_file=key_file
        )
        
        # Регистрируем обработчики команд
        self.register_command_handlers()
        
        # Хранение данных об агентах
        self.agents = {}
        
        # Очередь задач для агентов
        self.task_queue = {}
        
        # Результаты выполнения задач
        self.task_results = {}
        
        # Доступные модули
        self.available_modules = self._load_available_modules()
    
    def _load_available_modules(self) -> Dict[str, str]:
        """Загрузка доступных модулей для отправки агентам."""
        modules = {}
        
        try:
            modules_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "modules")
            if os.path.exists(modules_dir):
                for filename in os.listdir(modules_dir):
                    if filename.endswith(".py") and not filename.startswith("__"):
                        module_name = filename[:-3]
                        module_path = os.path.join(modules_dir, filename)
                        
                        with open(module_path, "r") as f:
                            module_content = f.read()
                            
                        modules[module_name] = module_content
                        logger.info(f"Загружен модуль: {module_name}")
        except Exception as e:
            logger.error(f"Ошибка при загрузке модулей: {e}")
        
        return modules
    
    def register_command_handlers(self):
        """Регистрация обработчиков команд."""
        self.server.register_command_handler(CommandType.SYSTEM.value, self.handle_system_command)
        self.server.register_command_handler(CommandType.SHELL.value, self.handle_shell_command)
        self.server.register_command_handler(CommandType.FILE.value, self.handle_file_command)
        self.server.register_command_handler(CommandType.STATUS.value, self.handle_status_command)
    
    def start(self):
        """Запуск сервера."""
        logger.info(f"Запуск сервера агентов на {self.host}:{self.port}")
        self.server.start()
    
    def stop(self):
        """Остановка сервера."""
        logger.info("Остановка сервера агентов")
        self.server.stop()
    
    def handle_system_command(self, command: Command) -> Response:
        """Обработка системных команд от агентов."""
        action = command.payload.get("action", "")
        
        if action == "report":
            # Обработка отчета от агента
            agent_id = command.payload.get("agent_id")
            data = command.payload.get("data", {})
            
            if not agent_id:
                return Response(
                    command_id=command.command_id,
                    status=ResponseStatus.ERROR,
                    data={},
                    error_message="ID агента не указан"
                )
            
            # Обновляем информацию об агенте
            self.update_agent_info(agent_id, data)
            
            # Проверяем, есть ли задачи для этого агента
            task = self.get_task_for_agent(agent_id)
            
            return Response(
                command_id=command.command_id,
                status=ResponseStatus.SUCCESS,
                data={"task": task} if task else {}
            )
            
        elif action == "get_module":
            # Запрос на получение модуля
            module_name = command.payload.get("module_name")
            
            if not module_name or module_name not in self.available_modules:
                return Response(
                    command_id=command.command_id,
                    status=ResponseStatus.ERROR,
                    data={},
                    error_message=f"Модуль не найден: {module_name}"
                )
            
            # Возвращаем код модуля
            return Response(
                command_id=command.command_id,
                status=ResponseStatus.SUCCESS,
                data={"module_code": self.available_modules[module_name]}
            )
            
        else:
            return Response(
                command_id=command.command_id,
                status=ResponseStatus.ERROR,
                data={},
                error_message=f"Неизвестное действие: {action}"
            )
    
    def handle_shell_command(self, command: Command) -> Response:
        """Обработка команд оболочки от агентов (логирование и проксирование)."""
        # Просто логируем команду и прозрачно проксируем ее
        logger.info(f"Получена команда оболочки: {command.payload.get('command', '')}")
        
        # В данном примере мы просто перенаправляем команду обратно агенту,
        # но в реальном случае здесь может быть проверка на допустимость команды,
        # ее модификация или другая логика
        
        # Возвращаем ошибку, так как сервер не может выполнять команды напрямую
        return Response(
            command_id=command.command_id,
            status=ResponseStatus.ERROR,
            data={},
            error_message="Прямое выполнение команд на сервере запрещено"
        )
    
    def handle_file_command(self, command: Command) -> Response:
        """Обработка файловых операций от агентов."""
        action = command.payload.get("action", "")
        path = command.payload.get("path", "")
        
        # Логируем действие
        logger.info(f"Получена файловая операция: {action} для {path}")
        
        # В данном примере мы просто запрещаем файловые операции на сервере
        return Response(
            command_id=command.command_id,
            status=ResponseStatus.ERROR,
            data={},
            error_message="Файловые операции на сервере запрещены"
        )
    
    def handle_status_command(self, command: Command) -> Response:
        """Обработка команд статуса от агентов."""
        # Возвращаем базовую информацию о сервере
        return Response(
            command_id=command.command_id,
            status=ResponseStatus.SUCCESS,
            data={
                "server_time": datetime.now().isoformat(),
                "connected_agents": len(self.agents),
                "agent_ids": list(self.agents.keys())
            }
        )
    
    def update_agent_info(self, agent_id: str, data: Dict[str, Any]):
        """Обновление информации об агенте."""
        # Если это новый агент - логируем подключение
        if agent_id not in self.agents:
            logger.info(f"Новый агент подключен: {agent_id}")
        
        # Обновляем данные об агенте
        if "task_result" in data:
            # Обрабатываем результат выполнения задачи
            task_name = data["task_result"].get("task_name")
            result = data["task_result"].get("result", {})
            
            logger.info(f"Получен результат задачи от агента {agent_id}: {task_name}")
            
            # Сохраняем результат
            if agent_id not in self.task_results:
                self.task_results[agent_id] = {}
                
            self.task_results[agent_id][task_name] = {
                "timestamp": datetime.now().isoformat(),
                "result": result
            }
        else:
            # Обновляем базовую информацию
            self.agents[agent_id] = {
                "last_seen": datetime.now().isoformat(),
                "info": data
            }
    
    def get_task_for_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Получение задачи для агента."""
        # Проверяем, есть ли задачи в очереди для этого агента
        if agent_id in self.task_queue and self.task_queue[agent_id]:
            task = self.task_queue[agent_id].pop(0)
            logger.info(f"Отправка задачи агенту {agent_id}: {task['name']}")
            return task
        
        return None
    
    def add_task_for_agent(self, agent_id: str, task_name: str, params: Dict[str, Any] = None):
        """Добавление задачи для агента."""
        if agent_id not in self.task_queue:
            self.task_queue[agent_id] = []
        
        task = {
            "name": task_name,
            "params": params or {}
        }
        
        self.task_queue[agent_id].append(task)
        logger.info(f"Добавлена задача для агента {agent_id}: {task_name}")
    
    def get_agent_info(self, agent_id: str) -> Dict[str, Any]:
        """Получение информации об агенте."""
        return self.agents.get(agent_id, {})
    
    def get_all_agents(self) -> Dict[str, Dict[str, Any]]:
        """Получение информации обо всех агентах."""
        return self.agents
    
    def get_task_result(self, agent_id: str, task_name: str) -> Dict[str, Any]:
        """Получение результата выполнения задачи."""
        if agent_id in self.task_results and task_name in self.task_results[agent_id]:
            return self.task_results[agent_id][task_name]
        
        return {}
    
    def get_all_task_results(self, agent_id: str = None) -> Dict[str, Dict[str, Any]]:
        """Получение всех результатов выполнения задач."""
        if agent_id:
            return self.task_results.get(agent_id, {})
        
        return self.task_results

def main():
    """Основная функция для запуска сервера."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Сервер агентской коммуникации")
    
    parser.add_argument("--host", default="0.0.0.0", help="Хост для привязки")
    parser.add_argument("--port", type=int, default=8765, help="Порт для прослушивания")
    parser.add_argument("--encryption-key", help="Ключ шифрования (текстовый или base64:...)")
    parser.add_argument("--use-ssl", action="store_true", help="Использовать SSL")
    parser.add_argument("--cert-file", help="Файл сертификата SSL")
    parser.add_argument("--key-file", help="Файл ключа SSL")
    
    args = parser.parse_args()
    
    # Создаем и запускаем сервер
    server = AgentServer(
        host=args.host,
        port=args.port,
        encryption_key=args.encryption_key,
        use_ssl=args.use_ssl,
        cert_file=args.cert_file,
        key_file=args.key_file
    )
    
    try:
        server.start()
        
        # Демонстрационная функция добавления задач
        def demo_task_adder():
            """Демо-функция для добавления тестовых задач."""
            time.sleep(10)  # Даем время на подключение агентов
            
            while True:
                try:
                    # Получаем ID всех подключенных агентов
                    agents = server.get_all_agents()
                    
                    for agent_id in agents.keys():
                        # Добавляем задачу по сбору системной информации
                        server.add_task_for_agent(
                            agent_id=agent_id,
                            task_name="example_module",
                            params={
                                "collect_network": True,
                                "collect_processes": True,
                                "collect_disks": True,
                                "process_limit": 5
                            }
                        )
                        
                        # Проверяем результаты предыдущих задач
                        results = server.get_all_task_results(agent_id)
                        if results:
                            logger.info(f"Агент {agent_id} имеет {len(results)} результатов задач")
                    
                    # Ждем перед следующим циклом
                    time.sleep(300)  # 5 минут
                    
                except Exception as e:
                    logger.error(f"Ошибка в демо-функции добавления задач: {e}")
                    time.sleep(60)
        
        # Запускаем демо-функцию в отдельном потоке
        threading.Thread(target=demo_task_adder, daemon=True).start()
        
        # Ожидаем сигнала прерывания
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Получен сигнал прерывания. Останавливаем сервер...")
    except Exception as e:
        logger.error(f"Ошибка при работе сервера: {e}")
    finally:
        server.stop()

if __name__ == "__main__":
    main() 