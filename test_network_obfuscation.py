#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Тесты для модуля NetworkObfuscation
"""

import os
import unittest
import tempfile
import base64
from io import BytesIO
from PIL import Image
import numpy as np

from agent_modules.network_obfuscation import NetworkObfuscation

class TestNetworkObfuscation(unittest.TestCase):
    """Тесты для модуля сетевой обфускации"""
    
    def setUp(self):
        """Инициализация перед каждым тестом"""
        self.network = NetworkObfuscation(log_actions=True)
        
        # Создаем временное тестовое изображение для стеганографии
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_image_path = os.path.join(self.temp_dir.name, "test_image.png")
        self.output_image_path = os.path.join(self.temp_dir.name, "output_image.png")
        
        # Создаем тестовое изображение (100x100 RGB)
        img = Image.new('RGB', (100, 100), color=(73, 109, 137))
        img.save(self.test_image_path)
        
        # Тестовые данные
        self.test_data = b"This is a test message for network obfuscation testing"
    
    def tearDown(self):
        """Очистка после каждого теста"""
        self.temp_dir.cleanup()
    
    def test_initialization(self):
        """Тест инициализации и обнаружения возможностей"""
        # Проверяем, что объект создан
        self.assertIsNotNone(self.network)
        
        # Проверяем, что capabilities содержит все ожидаемые ключи
        capabilities = self.network.get_capabilities()
        expected_keys = ["dns_tunneling", "encryption", "steganography", "https", "http2"]
        for key in expected_keys:
            self.assertIn(key, capabilities)
    
    def test_action_logging(self):
        """Тест логирования действий"""
        # Выполняем какое-то действие, которое должно логироваться
        self.network._log_action("test", "This is a test action")
        
        # Получаем логи
        logs = self.network.get_action_log()
        
        # Проверяем, что действие залогировано
        self.assertGreaterEqual(len(logs), 1)
        found = False
        for log in logs:
            if log["type"] == "test" and log["details"] == "This is a test action":
                found = True
                break
        self.assertTrue(found)
    
    def test_encryption(self):
        """Тест шифрования и дешифрования данных"""
        # Пропускаем тест, если шифрование недоступно
        if not self.network.capabilities["encryption"]:
            self.skipTest("Encryption is not available")
        
        # Шифруем данные
        encrypted = self.network.encrypt_data(self.test_data)
        
        # Проверяем, что данные изменились
        self.assertNotEqual(encrypted, self.test_data)
        
        # Дешифруем данные
        decrypted = self.network.decrypt_data(encrypted)
        
        # Проверяем, что данные восстановлены
        self.assertEqual(decrypted, self.test_data)
    
    def test_dns_tunnel_encode(self):
        """Тест кодирования данных для DNS-туннеля"""
        # Пропускаем тест, если DNS-туннелирование недоступно
        if not self.network.capabilities["dns_tunneling"]:
            self.skipTest("DNS tunneling is not available")
        
        # Кодируем данные
        dns_queries = self.network.dns_tunnel_encode(self.test_data)
        
        # Проверяем, что есть результаты
        self.assertGreater(len(dns_queries), 0)
        
        # Проверяем формат запросов
        for query in dns_queries:
            # Запрос должен заканчиваться на tunnel.example.com
            self.assertTrue(query.endswith("tunnel.example.com"))
            
            # Запрос должен содержать данные и разделители
            parts = query.split('.')
            self.assertGreaterEqual(len(parts), 3)
            
            # Первая часть должна содержать идентификатор сессии и порядковый номер
            first_part = parts[0].split('-')
            self.assertGreaterEqual(len(first_part), 2)
    
    def test_steganography(self):
        """Тест стеганографии (встраивания и извлечения данных из изображения)"""
        # Пропускаем тест, если стеганография недоступна
        if not self.network.capabilities["steganography"]:
            self.skipTest("Steganography is not available")
        
        # Размер тестовых данных должен быть меньше, чем может вместить изображение
        test_data_small = b"Small test"
        
        # Встраиваем данные в изображение
        result = self.network.steganography_encode(test_data_small, self.test_image_path, self.output_image_path)
        
        # Проверяем результат операции
        self.assertTrue(result)
        
        # Проверяем, что выходной файл существует
        self.assertTrue(os.path.exists(self.output_image_path))
        
        # Извлекаем данные из изображения
        extracted_data = self.network.steganography_decode(self.output_image_path)
        
        # Проверяем, что данные извлечены корректно
        self.assertEqual(extracted_data, test_data_small)
    
    def test_https_send_mock(self):
        """Мок-тест отправки данных через HTTPS"""
        # Этот тест только проверяет, что метод не вызывает исключений при некорректном URL
        # В реальном сценарии нужно использовать mock для http-запросов
        
        # Отправляем данные на несуществующий URL (ожидаем ошибку)
        status, response = self.network.https_send("https://nonexistent.example.com/test", b"Test data")
        
        # Проверяем, что статус отрицательный (ошибка)
        self.assertEqual(status, -1)
        
        # Проверяем, что в ответе есть информация об ошибке
        self.assertIsInstance(response, bytes)
    
    def test_combined_encryption_steganography(self):
        """Тест комбинированного метода (шифрование + стеганография)"""
        # Пропускаем тест, если стеганография или шифрование недоступны
        if not self.network.capabilities["steganography"] or not self.network.capabilities["encryption"]:
            self.skipTest("Steganography or encryption is not available")
        
        # Размер тестовых данных должен быть меньше, чем может вместить изображение
        test_data_small = b"Small test for combined method"
        
        # Встраиваем зашифрованные данные в изображение
        result = self.network.steganography_with_encryption(
            test_data_small, self.test_image_path, self.output_image_path
        )
        
        # Проверяем результат операции
        self.assertTrue(result)
        
        # Проверяем, что выходной файл существует
        self.assertTrue(os.path.exists(self.output_image_path))
        
        # Извлекаем данные из изображения
        extracted_encrypted = self.network.steganography_decode(self.output_image_path)
        
        # Расшифровываем данные
        extracted_data = self.network.decrypt_data(extracted_encrypted)
        
        # Проверяем, что данные извлечены и расшифрованы корректно
        self.assertEqual(extracted_data, test_data_small)

if __name__ == "__main__":
    unittest.main() 