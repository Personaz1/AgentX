#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Тесты для модуля EnvironmentManager
"""

import os
import unittest
from agent_modules.environment_manager import EnvironmentManager

class TestEnvironmentManager(unittest.TestCase):
    """Тесты для класса EnvironmentManager"""
    
    def setUp(self):
        """Инициализация перед каждым тестом"""
        self.env_manager = EnvironmentManager(log_actions=True)
    
    def test_collect_system_info(self):
        """Тест сбора системной информации"""
        sys_info = self.env_manager.collect_system_info()
        
        # Проверка, что есть основные поля
        self.assertIn('os', sys_info)
        self.assertIn('hostname', sys_info)
        self.assertIn('username', sys_info)
        self.assertIn('architecture', sys_info)
        self.assertIn('is_admin', sys_info)
        self.assertIn('timestamp', sys_info)
        
        # Проверка что все значения не пустые
        for key, value in sys_info.items():
            if isinstance(value, str):
                self.assertTrue(len(value) > 0, f"Значение '{key}' пустое")
    
    def test_collect_network_info(self):
        """Тест сбора сетевой информации"""
        network_info = self.env_manager.collect_network_info()
        
        # Проверка базовой структуры
        self.assertIn('interfaces', network_info)
        self.assertIn('connections', network_info)
        
        # Проверка что есть хотя бы один интерфейс
        self.assertTrue(len(network_info['interfaces']) > 0, "Не найдено ни одного сетевого интерфейса")
    
    def test_collect_running_processes(self):
        """Тест сбора информации о процессах"""
        processes = self.env_manager.collect_running_processes()
        
        # Должен вернуть список процессов
        self.assertIsInstance(processes, list)
        
        # В списке должен быть хотя бы один процесс
        self.assertTrue(len(processes) > 0, "Не найдено ни одного процесса")
    
    def test_security_products_detection(self):
        """Тест обнаружения продуктов безопасности"""
        security_products = self.env_manager.security_products
        
        # Проверка структуры
        self.assertIn('antivirus', security_products)
        self.assertIn('edr', security_products)
        self.assertIn('firewalls', security_products)
    
    def test_action_logging(self):
        """Тест журналирования действий"""
        # Выполним несколько действий
        self.env_manager.collect_system_info()
        self.env_manager.collect_network_info()
        
        # Проверим, что они записаны в журнал
        log = self.env_manager.get_action_log()
        self.assertTrue(len(log) >= 3)  # Минимум 3 записи: инициализация и два вызова collect_*
        
        # Проверим структуру записей журнала
        for entry in log:
            self.assertIn('timestamp', entry)
            self.assertIn('type', entry)
            self.assertIn('details', entry)
    
    def test_execute_command(self):
        """Тест выполнения команд"""
        # Выполним простую команду
        if os.name == 'nt':  # Windows
            cmd = "echo test"
        else:  # Unix
            cmd = "echo test"
            
        returncode, stdout, stderr = self.env_manager.execute_command(cmd, shell=True)
        
        # Проверим результат
        self.assertEqual(returncode, 0)
        self.assertEqual(stdout.strip(), "test")
        self.assertEqual(stderr.strip(), "")

if __name__ == '__main__':
    unittest.main() 