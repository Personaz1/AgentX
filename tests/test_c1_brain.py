import unittest
from unittest.mock import MagicMock, patch
import json
from datetime import datetime
import random

# Импортируем необходимые модули для тестирования
from src.intelligence.c1_brain import C1Brain, ThinkingMode

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
        
        # Обрабатываем результат
        self.brain.process_task_result("zond1", "task123", result)
        
        # Проверяем, что результат добавлен в историю
        self.assertEqual(len(self.brain.task_results_history), 1)
        self.assertEqual(self.brain.task_results_history[0]["zond_id"], "zond1")
        self.assertEqual(self.brain.task_results_history[0]["task_id"], "task123")
        self.assertEqual(self.brain.task_results_history[0]["result"], result)
        
        # Проверяем обновление статистики команд
        self.assertEqual(self.brain.command_statistics["scan_network"]["total"], 1)
        self.assertEqual(self.brain.command_statistics["scan_network"]["success"], 1)
        
        # Проверяем обновление статистики зондов
        self.assertEqual(self.brain.zond_statistics["zond1"]["total"], 1)
        self.assertEqual(self.brain.zond_statistics["zond1"]["success"], 1)
        
        # Проверяем обновление статуса зонда
        self.assertEqual(self.brain.zond_status["zond1"]["last_command"], "scan_network")
        self.assertEqual(self.brain.zond_status["zond1"]["last_result"], result)
    
    def test_process_task_result_failure(self):
        """Тест обработки неудачного результата задачи"""
        # Неудачный результат
        result = {
            "status": "failure",
            "command": "scan_network",
            "error": "Цель недоступна"
        }
        
        # Обрабатываем результат
        self.brain.process_task_result("zond2", "task456", result)
        
        # Проверяем, что результат добавлен в историю
        self.assertEqual(len(self.brain.task_results_history), 1)
        self.assertEqual(self.brain.task_results_history[0]["zond_id"], "zond2")
        self.assertEqual(self.brain.task_results_history[0]["task_id"], "task456")
        self.assertEqual(self.brain.task_results_history[0]["result"], result)
        
        # Проверяем обновление статистики команд
        self.assertEqual(self.brain.command_statistics["scan_network"]["total"], 1)
        self.assertEqual(self.brain.command_statistics["scan_network"]["success"], 0)
        
        # Проверяем обновление статистики зондов
        self.assertEqual(self.brain.zond_statistics["zond2"]["total"], 1)
        self.assertEqual(self.brain.zond_statistics["zond2"]["success"], 0)
        
        # Проверяем обновление статуса зонда
        self.assertEqual(self.brain.zond_status["zond2"]["last_command"], "scan_network")
        self.assertEqual(self.brain.zond_status["zond2"]["last_result"], result)
    
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
            
            result = {
                "status": "success" if success else "failure",
                "command": command,
                "output": "Успешно" if success else None,
                "error": None if success else "Ошибка соединения"
            }
            
            self.brain.process_task_result(zond_id, f"task{i}", result)
        
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

if __name__ == '__main__':
    unittest.main() 