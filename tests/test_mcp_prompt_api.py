#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тесты для MCP Prompt API (FastAPI)
"""
import unittest
import requests
import time

API_URL = "http://127.0.0.1:8088"

class TestMCPPromptAPI(unittest.TestCase):
    def test_list_prompts(self):
        resp = requests.get(f"{API_URL}/prompts/list")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("prompts", data)
        self.assertTrue(any(p["name"].startswith("offensive_tools.run_nmap") for p in data["prompts"]))

    def test_run_nmap(self):
        payload = {
            "name": "offensive_tools.run_nmap",
            "arguments": {"target": "127.0.0.1", "options": "-F"}
        }
        resp = requests.post(f"{API_URL}/prompts/get", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("result", data)
        self.assertIn("stdout", data["result"])
        self.assertIn("127.0.0.1", data["result"]["stdout"])

    def test_run_hydra(self):
        payload = {
            "name": "offensive_tools.run_hydra",
            "arguments": {"target": "127.0.0.1", "service": "ssh", "userlist": "users.txt", "passlist": "pass.txt"}
        }
        resp = requests.post(f"{API_URL}/prompts/get", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("result", data)
        self.assertIn("status", data["result"])
        self.assertIn(data["result"]["status"], ["success", "error", "timeout"])

if __name__ == "__main__":
    # Даем серверу время подняться
    time.sleep(2)
    unittest.main() 