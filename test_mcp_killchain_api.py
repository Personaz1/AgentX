#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тесты для MCP Prompt API: killchain_attack (все сценарии)
"""
import unittest
import requests
import time

API_URL = "http://127.0.0.1:8088"

class TestMCPKillchainAPI(unittest.TestCase):
    def test_killchain_lateral_move(self):
        payload = {
            "name": "offensive_tools.killchain_attack",
            "arguments": {"target": "127.0.0.1", "scenario": "lateral_move", "userlist": "users.txt", "passlist": "pass.txt", "nmap_options": "-F"}
        }
        resp = requests.post(f"{API_URL}/prompts/get", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("result", data)
        self.assertIn("steps", data["result"])
        self.assertEqual(data["result"]["scenario"], "lateral_move")

    def test_killchain_persistence(self):
        payload = {
            "name": "offensive_tools.killchain_attack",
            "arguments": {"target": "127.0.0.1", "scenario": "persistence"}
        }
        resp = requests.post(f"{API_URL}/prompts/get", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("result", data)
        self.assertIn("steps", data["result"])
        self.assertEqual(data["result"]["scenario"], "persistence")

    def test_killchain_exfiltration(self):
        payload = {
            "name": "offensive_tools.killchain_attack",
            "arguments": {"target": "127.0.0.1", "scenario": "exfiltration"}
        }
        resp = requests.post(f"{API_URL}/prompts/get", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("result", data)
        self.assertIn("steps", data["result"])
        self.assertEqual(data["result"]["scenario"], "exfiltration")

    def test_killchain_stealth(self):
        payload = {
            "name": "offensive_tools.killchain_attack",
            "arguments": {"target": "127.0.0.1", "scenario": "stealth"}
        }
        resp = requests.post(f"{API_URL}/prompts/get", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("result", data)
        self.assertIn("steps", data["result"])
        self.assertEqual(data["result"]["scenario"], "stealth")

if __name__ == "__main__":
    time.sleep(2)
    unittest.main() 