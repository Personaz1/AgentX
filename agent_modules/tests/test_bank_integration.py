#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Тесты для модуля банковских инжектов
"""

import os
import sys
import json
import unittest
from unittest.mock import patch, MagicMock

# Добавляем путь к родительскому каталогу, чтобы импортировать модули
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Импортируем модуль для тестирования
from bank_integration import (
    BankInjectBase, SberbankInject, TinkoffInject,
    get_bank_inject, register_bank_inject, get_available_bank_injects
)

class TestBankInjectBase(unittest.TestCase):
    """
    Тесты для базового класса банковских инжектов
    """
    
    def setUp(self):
        """
        Настройка перед каждым тестом
        """
        self.bank_inject = BankInjectBase("test_bank")
        self.bank_inject.name = "Test Bank"
        self.bank_inject.description = "Test bank description"
        
    def test_init(self):
        """
        Тест инициализации базового класса
        """
        self.assertEqual(self.bank_inject.bank_type, "test_bank")
        self.assertEqual(self.bank_inject.name, "Test Bank")
        self.assertEqual(self.bank_inject.description, "Test bank description")
        self.assertEqual(self.bank_inject.version, "1.0.0")
        self.assertEqual(len(self.bank_inject.injects), 0)
    
    def test_add_inject(self):
        """
        Тест добавления инжекта
        """
        # Добавляем инжект
        result = self.bank_inject.add_inject(
            url_pattern="https://test.com/login",
            description="Login page inject",
            scripts=[{"id": "login_script", "content": "console.log('Hello');"}],
            styles=["body { background: red; }"],
            elements=[{"selector": "#login", "replacement": "<div>New login</div>"}]
        )
        
        self.assertTrue(result)
        self.assertEqual(len(self.bank_inject.injects), 1)
        
        inject = self.bank_inject.injects[0]
        self.assertEqual(inject["url_pattern"], "https://test.com/login")
        self.assertEqual(inject["description"], "Login page inject")
        self.assertEqual(len(inject["scripts"]), 1)
        self.assertEqual(len(inject["styles"]), 1)
        self.assertEqual(len(inject["elements"]), 1)
    
    def test_add_inject_duplicate(self):
        """
        Тест добавления дубликата инжекта
        """
        # Добавляем инжект
        self.bank_inject.add_inject(
            url_pattern="https://test.com/login",
            description="Login page inject"
        )
        
        # Пытаемся добавить инжект с таким же URL
        result = self.bank_inject.add_inject(
            url_pattern="https://test.com/login",
            description="Another login page inject"
        )
        
        self.assertFalse(result)
        self.assertEqual(len(self.bank_inject.injects), 1)
        self.assertEqual(self.bank_inject.injects[0]["description"], "Login page inject")
    
    def test_remove_inject(self):
        """
        Тест удаления инжекта
        """
        # Добавляем инжект
        self.bank_inject.add_inject(
            url_pattern="https://test.com/login",
            description="Login page inject"
        )
        
        # Удаляем инжект
        result = self.bank_inject.remove_inject("https://test.com/login")
        
        self.assertTrue(result)
        self.assertEqual(len(self.bank_inject.injects), 0)
    
    def test_remove_inject_nonexistent(self):
        """
        Тест удаления несуществующего инжекта
        """
        result = self.bank_inject.remove_inject("https://test.com/nonexistent")
        
        self.assertFalse(result)
    
    def test_get_inject(self):
        """
        Тест получения инжекта по URL
        """
        # Добавляем инжект
        self.bank_inject.add_inject(
            url_pattern="https://test.com/login",
            description="Login page inject"
        )
        
        # Получаем инжект
        inject = self.bank_inject.get_inject("https://test.com/login")
        
        self.assertIsNotNone(inject)
        self.assertEqual(inject["url_pattern"], "https://test.com/login")
        self.assertEqual(inject["description"], "Login page inject")
    
    def test_get_inject_nonexistent(self):
        """
        Тест получения несуществующего инжекта
        """
        inject = self.bank_inject.get_inject("https://test.com/nonexistent")
        
        self.assertIsNone(inject)
    
    def test_to_dict(self):
        """
        Тест преобразования объекта в словарь
        """
        # Добавляем инжект
        self.bank_inject.add_inject(
            url_pattern="https://test.com/login",
            description="Login page inject"
        )
        
        # Преобразуем в словарь
        data = self.bank_inject.to_dict()
        
        self.assertEqual(data["bank_type"], "test_bank")
        self.assertEqual(data["name"], "Test Bank")
        self.assertEqual(data["description"], "Test bank description")
        self.assertEqual(data["version"], "1.0.0")
        self.assertEqual(len(data["injects"]), 1)
    
    def test_from_dict(self):
        """
        Тест создания объекта из словаря
        """
        # Создаем словарь
        data = {
            "bank_type": "test_bank",
            "name": "Test Bank",
            "description": "Test bank description",
            "version": "1.0.0",
            "injects": [
                {
                    "url_pattern": "https://test.com/login",
                    "description": "Login page inject",
                    "scripts": [],
                    "styles": [],
                    "elements": []
                }
            ]
        }
        
        # Создаем объект из словаря
        inject = BankInjectBase.from_dict(data)
        
        self.assertEqual(inject.bank_type, "test_bank")
        self.assertEqual(inject.name, "Test Bank")
        self.assertEqual(inject.description, "Test bank description")
        self.assertEqual(inject.version, "1.0.0")
        self.assertEqual(len(inject.injects), 1)

    @patch("builtins.open", new_callable=unittest.mock.mock_open)
    @patch("json.dump")
    def test_save_to_file(self, mock_json_dump, mock_open):
        """
        Тест сохранения в файл
        """
        # Добавляем инжект
        self.bank_inject.add_inject(
            url_pattern="https://test.com/login",
            description="Login page inject"
        )
        
        # Сохраняем в файл
        self.bank_inject.save_to_file("test_bank.json")
        
        mock_open.assert_called_once_with("test_bank.json", "w", encoding="utf-8")
        mock_json_dump.assert_called_once()

    @patch("builtins.open", new_callable=unittest.mock.mock_open, read_data='{"bank_type": "test_bank", "name": "Test Bank", "description": "Test bank description", "version": "1.0.0", "injects": []}')
    @patch("json.load", return_value={"bank_type": "test_bank", "name": "Test Bank", "description": "Test bank description", "version": "1.0.0", "injects": []})
    def test_load_from_file(self, mock_json_load, mock_open):
        """
        Тест загрузки из файла
        """
        # Загружаем из файла
        result = self.bank_inject.load_from_file("test_bank.json")
        
        self.assertTrue(result)
        mock_open.assert_called_once_with("test_bank.json", "r", encoding="utf-8")
        mock_json_load.assert_called_once()

class TestSberbankInject(unittest.TestCase):
    """
    Тесты для инжекта Сбербанка
    """
    
    def setUp(self):
        """
        Настройка перед каждым тестом
        """
        self.sberbank_inject = SberbankInject()
    
    def test_init(self):
        """
        Тест инициализации инжекта Сбербанка
        """
        self.assertEqual(self.sberbank_inject.bank_type, "sberbank")
        self.assertEqual(self.sberbank_inject.name, "Сбербанк")
        self.assertTrue(len(self.sberbank_inject.injects) > 0)
    
    def test_login_inject(self):
        """
        Тест наличия инжекта для страницы входа
        """
        inject = self.sberbank_inject.get_inject("https://online.sberbank.ru/CSAFront/login.do")
        
        self.assertIsNotNone(inject)
        self.assertTrue(any("login" in script.get("id", "") for script in inject["scripts"]))

class TestTinkoffInject(unittest.TestCase):
    """
    Тесты для инжекта Тинькофф
    """
    
    def setUp(self):
        """
        Настройка перед каждым тестом
        """
        self.tinkoff_inject = TinkoffInject()
    
    def test_init(self):
        """
        Тест инициализации инжекта Тинькофф
        """
        self.assertEqual(self.tinkoff_inject.bank_type, "tinkoff")
        self.assertEqual(self.tinkoff_inject.name, "Тинькофф")
        self.assertTrue(len(self.tinkoff_inject.injects) > 0)
    
    def test_login_inject(self):
        """
        Тест наличия инжекта для страницы входа
        """
        inject = self.tinkoff_inject.get_inject("https://www.tinkoff.ru/login/")
        
        self.assertIsNotNone(inject)
        self.assertTrue(any("login" in script.get("id", "") for script in inject["scripts"]))

class TestRegistryFunctions(unittest.TestCase):
    """
    Тесты для функций реестра инжектов
    """
    
    def test_get_bank_inject(self):
        """
        Тест получения инжекта из реестра
        """
        # Получаем инжект Сбербанка
        sberbank_inject = get_bank_inject("sberbank")
        
        self.assertIsNotNone(sberbank_inject)
        self.assertEqual(sberbank_inject.bank_type, "sberbank")
        self.assertEqual(sberbank_inject.name, "Сбербанк")
    
    def test_get_bank_inject_nonexistent(self):
        """
        Тест получения несуществующего инжекта
        """
        inject = get_bank_inject("nonexistent_bank")
        
        self.assertIsNone(inject)
    
    def test_register_bank_inject(self):
        """
        Тест регистрации нового инжекта
        """
        # Создаем новый класс инжекта
        class TestBankInject(BankInjectBase):
            def __init__(self):
                super().__init__("test_bank")
                self.name = "Test Bank"
                self.description = "Test bank description"
        
        # Регистрируем новый инжект
        register_bank_inject("test_bank", TestBankInject)
        
        # Получаем инжект
        inject = get_bank_inject("test_bank")
        
        self.assertIsNotNone(inject)
        self.assertEqual(inject.bank_type, "test_bank")
        self.assertEqual(inject.name, "Test Bank")
    
    def test_get_available_bank_injects(self):
        """
        Тест получения списка доступных инжектов
        """
        # Получаем список инжектов
        injects = get_available_bank_injects()
        
        self.assertIsInstance(injects, list)
        self.assertTrue(len(injects) >= 2)  # должны быть как минимум Сбербанк и Тинькофф
        self.assertIn("sberbank", injects)
        self.assertIn("tinkoff", injects)

if __name__ == "__main__":
    unittest.main() 