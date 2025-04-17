#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тесты для MCP Prompt API: persistence, антифорензика, self-delete, timestomp
"""
import unittest
import requests
import time

API_URL = "http://127.0.0.1:8088"

class TestMCPPersistenceAPI(unittest.TestCase):
    def test_persistence_autorun(self):
        payload = {
            "name": "offensive_tools.persistence_autorun",
            "arguments": {"method": "cron"}
        }
        resp = requests.post(f"{API_URL}/prompts/get", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("result", data)
        self.assertEqual(data["result"]["status"], "success")
        self.assertIn("action", data["result"])

    def test_clean_logs(self):
        payload = {
            "name": "offensive_tools.clean_logs",
            "arguments": {"method": "bash"}
        }
        resp = requests.post(f"{API_URL}/prompts/get", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("result", data)
        self.assertEqual(data["result"]["status"], "success")
        self.assertIn("actions", data["result"])

    def test_self_delete(self):
        payload = {"name": "offensive_tools.self_delete"}
        resp = requests.post(f"{API_URL}/prompts/get", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("result", data)
        self.assertEqual(data["result"]["status"], "success")
        self.assertIn("action", data["result"])

    def test_timestomp(self):
        # Создаём временный файл
        testfile = "testfile2.txt"
        with open(testfile, "w") as f:
            f.write("test")
        payload = {
            "name": "offensive_tools.timestomp",
            "arguments": {"target_file": testfile, "new_time": "2022-02-02 22:22:22"}
        }
        resp = requests.post(f"{API_URL}/prompts/get", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("result", data)
        self.assertEqual(data["result"]["status"], "success")
        self.assertIn("action", data["result"])

if __name__ == "__main__":
    time.sleep(2)
    unittest.main() 