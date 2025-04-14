#!/usr/bin/env python3
"""
Smoke-тест для phantom_builder.c
Проверяет сборку и базовый запуск билдера (Linux).
"""
import os
import subprocess
import unittest
import shutil

class TestPhantomBuilder(unittest.TestCase):
    BIN_PATH = "./bin/phantom_builder"
    SRC_PATH = "phantom_builder.c"

    @classmethod
    def setUpClass(cls):
        # Собираем phantom_builder.c
        os.makedirs("./bin", exist_ok=True)
        result = subprocess.run([
            "gcc", cls.SRC_PATH, "-o", cls.BIN_PATH, "-O2"
        ], capture_output=True, text=True)
        if result.returncode != 0:
            print("[phantom_builder] Build failed:\n", result.stderr)
        assert result.returncode == 0, f"phantom_builder.c не собрался: {result.stderr}"

    def test_help(self):
        # Запускаем phantom_builder с некорректными аргументами (ожидаем ошибку и usage)
        proc = subprocess.run([self.BIN_PATH, "--help"], capture_output=True, text=True)
        self.assertIn("Использование", proc.stdout + proc.stderr)
        self.assertEqual(proc.returncode, 0)  # help возвращает 0, если usage выведен

    @classmethod
    def tearDownClass(cls):
        # Удаляем бинарник после теста
        if os.path.exists(cls.BIN_PATH):
            os.remove(cls.BIN_PATH)

if __name__ == "__main__":
    unittest.main() 