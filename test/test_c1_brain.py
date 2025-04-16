import unittest
from unittest.mock import MagicMock, patch
import json
from datetime import datetime
import random
from src.intelligence.c1_brain import C1Brain, ThinkingMode

class TestC1Brain(unittest.TestCase):
    def setUp(self):
        self.controller = MagicMock()
        self.brain = C1Brain(self.controller, "gpt-4", temperature=0.7)
    
    def test_init(self):
        """Тест инициализации модуля C1Brain"""
        self.assertEqual(self.brain.model_name, "gpt-4")
        self.assertEqual(self.brain.temperature, 0.7)
        self.assertEqual(self.brain.task_results_history, [])
        self.assertEqual(self.brain.command_statistics, {})
        self.assertEqual(self.brain.zond_statistics, {})
        self.controller.set_brain.assert_called_once_with(self.brain)
    
    def test_process_task_result_success(self):
        """Тест обработки успешного результата выполнения задачи"""
        zond_id = "zond-123"
        task_id = "task-456"
        result = {
            "status": "success",
            "command": "scan_network",
            "output": "Найдено 5 хостов"
        }
        
        self.brain.process_task_result(zond_id, task_id, result)
        
        # Проверяем, что результат добавлен в историю
        self.assertEqual(len(self.brain.task_results_history), 1)
        entry = self.brain.task_results_history[0]
        self.assertEqual(entry["zond_id"], zond_id)
        self.assertEqual(entry["task_id"], task_id)
        self.assertEqual(entry["result"], result)
        
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
        """Тест обработки неудачного результата выполнения задачи"""
        zond_id = "zond-123"
        task_id = "task-456"
        result = {
            "status": "failure",
            "command": "exploit_vulnerability",
            "error": "Целевой хост недоступен"
        }
        
        self.brain.process_task_result(zond_id, task_id, result)
        
        # Проверяем обновление статистики команд для неудачного результата
        self.assertEqual(self.brain.command_statistics["exploit_vulnerability"]["total"], 1)
        self.assertEqual(self.brain.command_statistics["exploit_vulnerability"]["success"], 0)
        
        # Проверяем обновление статистики зондов для неудачного результата
        self.assertEqual(self.brain.zond_statistics[zond_id]["total"], 1)
        self.assertEqual(self.brain.zond_statistics[zond_id]["success"], 0)
    
    def test_get_task_results_analysis_empty(self):
        """Тест анализа результатов при пустой истории"""
        analysis = self.brain.get_task_results_analysis()
        
        self.assertEqual(analysis["total_tasks"], 0)
        self.assertEqual(analysis["success_rate"], 0)
        self.assertEqual(analysis["command_success_rates"], {})
        self.assertEqual(analysis["zond_success_rates"], {})
        self.assertEqual(analysis["patterns"], [])
        self.assertEqual(analysis["recommendations"], [])
    
    def test_get_task_results_analysis(self):
        """Тест анализа результатов выполнения задач"""
        # Добавляем результаты выполнения задач
        zond_id = "zond-123"
        commands = ["scan_network", "exploit_vulnerability", "gather_info"]
        
        # Создаем набор успешных и неудачных результатов
        for i in range(10):
            task_id = f"task-{i}"
            command = random.choice(commands)
            status = "success" if random.random() > 0.3 else "failure"
            result = {
                "status": status,
                "command": command,
                "output" if status == "success" else "error": f"Результат {i}"
            }
            self.brain.process_task_result(zond_id, task_id, result)
        
        # Добавляем паттерны ошибок для обнаружения закономерностей
        for i in range(3):
            task_id = f"task-pattern-{i}"
            result = {
                "status": "failure",
                "command": "exploit_vulnerability",
                "error": "Целевой хост недоступен"
            }
            self.brain.process_task_result(zond_id, task_id, result)
        
        # Получаем анализ
        analysis = self.brain.get_task_results_analysis()
        
        # Проверяем основные поля анализа
        self.assertEqual(analysis["total_tasks"], 13)
        self.assertIn("success_rate", analysis)
        self.assertIn("command_success_rates", analysis)
        self.assertIn("zond_success_rates", analysis)
        
        # Проверяем обнаружение закономерностей
        patterns = [p for p in analysis["patterns"] 
                   if p["command"] == "exploit_vulnerability" and "Целевой хост недоступен" in p["error_pattern"]]
        self.assertTrue(len(patterns) > 0)
        
        # Проверяем рекомендации
        recommendations = [r for r in analysis["recommendations"] 
                          if r["type"] == "avoid_command" and r["command"] == "exploit_vulnerability"]
        self.assertTrue(len(recommendations) > 0)
    
    def test_think_once(self):
        """Тест процесса размышления"""
        # Подготавливаем моки для вызова LLM и выполнения действий
        mock_response = {
            "thinking": "Анализирую доступные зонды и последние результаты команд.",
            "actions": [{
                "action_type": "COMMAND",
                "target": "zond-123",
                "params": {
                    "command": "scan_network",
                    "args": {"target": "192.168.1.0/24"}
                }
            }]
        }
        
        with patch.object(self.brain, '_call_llm', return_value=mock_response) as mock_call_llm:
            with patch.object(self.brain, '_execute_action', return_value={"task_id": "task-123"}) as mock_execute:
                # Обновляем статус зондов для теста
                self.brain.zond_status = {"zond-123": {"status": "active"}}
                
                # Вызываем метод размышления
                result = self.brain.think_once(ThinkingMode.AUTONOMOUS)
                
                # Проверяем вызов методов
                mock_call_llm.assert_called_once()
                self.assertEqual(mock_execute.call_count, 1)
                
                # Проверяем результат
                self.assertEqual(result["thinking"], mock_response["thinking"])
                self.assertEqual(result["actions"], mock_response["actions"])
                self.assertEqual(len(result["results"]), 1)
                self.assertEqual(result["results"][0]["result"]["task_id"], "task-123")
                
                # Проверяем сохранение лога размышления
                self.assertEqual(len(self.brain.thinking_logs), 1)
                self.assertEqual(self.brain.thinking_logs[0], result)
    
    def test_integration_with_controller(self):
        """Тест интеграции с контроллером"""
        # Настраиваем мок для контроллера
        self.controller.send_command_to_zond.return_value = "task-123"
        
        # Создаем действие для выполнения
        action = {
            "action_type": "COMMAND",
            "target": "zond-123",
            "params": {
                "command": "scan_network",
                "args": {"target": "192.168.1.0/24"}
            }
        }
        
        # Выполняем действие
        result = self.brain._execute_action(action)
        
        # Проверяем вызов метода контроллера
        self.controller.send_command_to_zond.assert_called_once_with(
            "zond-123", "scan_network", {"target": "192.168.1.0/24"}
        )
        
        # Проверяем результат
        self.assertEqual(result["task_id"], "task-123")
    
    def test_analyze_action(self):
        """Тест выполнения действия анализа данных"""
        action = {
            "action_type": "ANALYZE",
            "target": "zond-123",
            "data_type": "network_scan"
        }
        
        with patch.object(self.brain, '_analyze_network_scan', return_value={"hosts_count": 5}) as mock_analyze:
            result = self.brain._execute_action(action)
            
            mock_analyze.assert_called_once_with("zond-123")
            self.assertEqual(result["analysis_results"]["hosts_count"], 5)
    
    def test_results_history_limit(self):
        """Тест ограничения размера истории результатов"""
        # Патчим метод datetime.now() для стабильности тестов
        with patch('src.intelligence.c1_brain.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2023, 1, 1)
            
            # Добавляем больше результатов, чем разрешено хранить
            for i in range(1010):
                self.brain.process_task_result(
                    f"zond-{i % 10}", 
                    f"task-{i}", 
                    {"status": "success", "command": "test_command", "output": f"Result {i}"}
                )
            
            # Проверяем, что размер истории ограничен
            self.assertEqual(len(self.brain.task_results_history), 1000)
            
            # Проверяем, что старые записи удалены, а новые остались
            self.assertEqual(self.brain.task_results_history[0]["task_id"], "task-10")
            self.assertEqual(self.brain.task_results_history[-1]["task_id"], "task-1009")
    
    def test_thinking_logs_limit(self):
        """Тест ограничения размера логов размышления"""
        # Добавляем больше логов, чем разрешено хранить
        for i in range(110):
            self.brain.thinking_logs.append({
                "timestamp": datetime.now().isoformat(),
                "mode": "test",
                "thinking": f"Thinking {i}",
                "actions": [],
                "results": []
            })
        
        # Проверяем, что размер логов ограничен
        self.assertEqual(len(self.brain.thinking_logs), 100)
        
        # Проверяем, что старые записи удалены, а новые остались
        self.assertEqual(self.brain.thinking_logs[0]["thinking"], "Thinking 10")
        self.assertEqual(self.brain.thinking_logs[-1]["thinking"], "Thinking 109")

if __name__ == '__main__':
    unittest.main() 