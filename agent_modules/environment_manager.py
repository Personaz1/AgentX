#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
EnvironmentManager - Модуль для анализа и управления окружением агента
Предоставляет абстракции для доступа к системным ресурсам и выполнения команд
"""

import os
import sys
import time
import json
import socket
import platform
import logging
import subprocess
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("EnvironmentManager")

class EnvironmentManager:
    """
    Менеджер окружения для анализа системы и управления ресурсами.
    Предоставляет унифицированный интерфейс к системным ресурсам,
    независимый от операционной системы.
    """
    
    def __init__(self, log_actions: bool = True):
        """
        Инициализация менеджера окружения
        
        Args:
            log_actions: Включить журналирование действий
        """
        self.os_type = platform.system().lower()
        self.log_actions = log_actions
        self.action_log = []
        self.hostname = socket.gethostname()
        
        # Проверяем наличие прав администратора/root
        self.is_admin = self._check_admin_rights()
        
        # Идентифицируем версию и тип системы
        self.os_info = self._identify_os()
        
        # Проверяем наличие EDR/AV
        self.security_products = self._detect_security_products()
        
        logger.info(f"EnvironmentManager инициализирован: OS={self.os_type}, Admin={self.is_admin}")
        self._log_action("init", f"EnvironmentManager initialized on {self.os_type}")
    
    def _log_action(self, action_type: str, details: str) -> None:
        """
        Записывает действие в журнал
        
        Args:
            action_type: Тип действия (init, exec, scan, etc)
            details: Детали действия
        """
        if self.log_actions:
            timestamp = datetime.now().isoformat()
            log_entry = {
                "timestamp": timestamp,
                "type": action_type,
                "details": details
            }
            self.action_log.append(log_entry)
            logger.debug(f"Action logged: {action_type} - {details}")
    
    def _check_admin_rights(self) -> bool:
        """
        Проверяет наличие прав администратора/root
        
        Returns:
            bool: True если есть права администратора/root
        """
        try:
            if self.os_type == "windows":
                # Проверка на Windows
                import ctypes
                return ctypes.windll.shell32.IsUserAnAdmin() != 0
            else:
                # Проверка на Unix-системах (Linux/macOS)
                return os.geteuid() == 0
        except Exception as e:
            logger.warning(f"Не удалось проверить права администратора: {e}")
            return False
    
    def _identify_os(self) -> Dict[str, str]:
        """
        Определяет детальную информацию об ОС
        
        Returns:
            Dict[str, str]: Информация об ОС
        """
        os_info = {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "architecture": platform.machine(),
            "processor": platform.processor()
        }
        
        # Дополнительная информация в зависимости от ОС
        if self.os_type == "windows":
            os_info["edition"] = os.environ.get("OS", "Unknown")
            os_info["build"] = platform.version().split('.')[-1] if '.' in platform.version() else "Unknown"
        elif self.os_type == "darwin":  # macOS
            try:
                os_info["mac_version"] = subprocess.check_output(["sw_vers", "-productVersion"]).decode().strip()
                os_info["build_version"] = subprocess.check_output(["sw_vers", "-buildVersion"]).decode().strip()
            except Exception:
                pass
        elif self.os_type == "linux":
            try:
                # Попытка определить дистрибутив Linux
                if os.path.exists("/etc/os-release"):
                    with open("/etc/os-release", "r") as f:
                        lines = f.readlines()
                        for line in lines:
                            if line.startswith("ID="):
                                os_info["distro"] = line.split("=")[1].strip().strip('"')
                            elif line.startswith("VERSION_ID="):
                                os_info["distro_version"] = line.split("=")[1].strip().strip('"')
            except Exception:
                pass
        
        return os_info
    
    def _detect_security_products(self) -> Dict[str, List[str]]:
        """
        Обнаруживает установленные EDR и антивирусы
        
        Returns:
            Dict[str, List[str]]: Обнаруженные продукты безопасности по категориям
        """
        security_products = {
            "antivirus": [],
            "edr": [],
            "firewalls": [],
            "other": []
        }
        
        # Проверки зависят от ОС
        if self.os_type == "windows":
            # Проверка Windows Defender
            try:
                defender_status = subprocess.check_output(["powershell", "Get-MpComputerStatus"], 
                                                         stderr=subprocess.PIPE).decode()
                if "RealTimeProtectionEnabled : True" in defender_status:
                    security_products["antivirus"].append("Windows Defender (enabled)")
                elif "RealTimeProtectionEnabled" in defender_status:
                    security_products["antivirus"].append("Windows Defender (disabled)")
            except Exception:
                pass
            
            # Проверка других продуктов через WMI
            try:
                av_query = subprocess.check_output(["wmic", "/Namespace:\\\\root\\SecurityCenter2", 
                                                  "Path", "AntiVirusProduct", "Get", 
                                                  "displayName,productState"], 
                                                 stderr=subprocess.PIPE).decode()
                for line in av_query.splitlines()[1:]:
                    if line.strip():
                        parts = line.strip().split()
                        if parts:
                            security_products["antivirus"].append(" ".join(parts[:-1]))
            except Exception:
                pass
            
            # Проверка известных EDR-процессов
            edr_processes = [
                "CrowdStrike", "cb", "Cybereason", "SentinelOne", "Cortex", "Symantec",
                "McAfee", "Trend Micro", "Sophos", "Elastic", "Wazuh", "Lacework"
            ]
            
            try:
                processes = subprocess.check_output(["tasklist", "/FO", "CSV"], 
                                                 stderr=subprocess.PIPE).decode()
                for edr in edr_processes:
                    if edr.lower() in processes.lower():
                        security_products["edr"].append(edr)
            except Exception:
                pass
            
        elif self.os_type == "darwin":  # macOS
            # Проверка macOS Security
            try:
                security_status = subprocess.check_output(["launchctl", "list"], 
                                                       stderr=subprocess.PIPE).decode()
                if "com.apple.security" in security_status:
                    security_products["antivirus"].append("macOS Security")
                
                # Проверка распространенных macOS EDR
                edr_processes = [
                    "CrowdStrike", "Falcon", "SentinelOne", "Cortex", "Symantec",
                    "McAfee", "Sophos", "Elastic", "Jamf", "KnowBe4"
                ]
                
                processes = subprocess.check_output(["ps", "aux"], 
                                                 stderr=subprocess.PIPE).decode()
                for edr in edr_processes:
                    if edr.lower() in processes.lower():
                        security_products["edr"].append(edr)
            except Exception:
                pass
            
        elif self.os_type == "linux":
            # Проверка распространенных Linux AV/EDR
            av_processes = [
                "clamav", "avast", "avg", "comodo", "eset", "sophos"
            ]
            
            edr_processes = [
                "crowdstrike", "falcon", "sentinelone", "cortex", "symantec", 
                "mcafee", "osquery", "wazuh", "elastic"
            ]
            
            try:
                processes = subprocess.check_output(["ps", "aux"], 
                                                 stderr=subprocess.PIPE).decode()
                for av in av_processes:
                    if av.lower() in processes.lower():
                        security_products["antivirus"].append(av)
                
                for edr in edr_processes:
                    if edr.lower() in processes.lower():
                        security_products["edr"].append(edr)
            except Exception:
                pass
        
        return security_products
    
    def collect_system_info(self) -> Dict[str, Any]:
        """
        Собирает базовую информацию о системе
        
        Returns:
            Dict[str, Any]: Системная информация
        """
        self._log_action("collect", "Collecting system information")
        
        system_info = {
            "os": self.os_info["system"],
            "hostname": self.hostname,
            "username": os.environ.get("USER") or os.environ.get("USERNAME", "unknown"),
            "architecture": self.os_info["architecture"],
            "os_version": self.os_info.get("version", "unknown"),
            "cpu_info": self.os_info.get("processor", "unknown"),
            "is_admin": self.is_admin,
            "security_products": self.security_products,
            "timestamp": datetime.now().isoformat()
        }
        
        # Дополнительная информация по ОС
        try:
            if self.os_type == "windows":
                system_info["windows_domain"] = os.environ.get("USERDOMAIN", "unknown")
                system_info["windows_edition"] = os.environ.get("OS", "unknown")
            elif self.os_type == "linux":
                system_info["kernel_version"] = platform.release()
                system_info["distro"] = self.os_info.get("distro", "unknown")
                system_info["distro_version"] = self.os_info.get("distro_version", "unknown")
            elif self.os_type == "darwin":
                system_info["mac_version"] = self.os_info.get("mac_version", "unknown")
                system_info["build_version"] = self.os_info.get("build_version", "unknown")
            
            # Сбор информации о памяти
            if self.os_type == "windows":
                memory_cmd = subprocess.check_output(["wmic", "OS", "get", "TotalVisibleMemorySize"], 
                                                   stderr=subprocess.PIPE).decode().strip()
                for line in memory_cmd.splitlines():
                    if line.strip() and line.strip().isdigit():
                        system_info["ram_total"] = f"{int(line.strip()) // 1024} MB"
                        break
            elif self.os_type == "darwin":
                memory_cmd = subprocess.check_output(["sysctl", "hw.memsize"], 
                                                   stderr=subprocess.PIPE).decode().strip()
                memory_bytes = int(memory_cmd.split()[1])
                system_info["ram_total"] = f"{memory_bytes // (1024 * 1024 * 1024)} GB"
            elif self.os_type == "linux":
                with open("/proc/meminfo", "r") as f:
                    for line in f:
                        if "MemTotal" in line:
                            memory_kb = int(line.split()[1])
                            system_info["ram_total"] = f"{memory_kb // 1024} MB"
                            break
        except Exception as e:
            logger.warning(f"Ошибка при сборе дополнительной системной информации: {e}")
        
        return system_info
    
    def collect_network_info(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Собирает информацию о сетевых интерфейсах и соединениях
        
        Returns:
            Dict[str, List[Dict[str, Any]]]: Сетевая информация
        """
        self._log_action("collect", "Collecting network information")
        
        network_info = {
            "interfaces": [],
            "connections": []
        }
        
        # Сбор информации о сетевых интерфейсах
        try:
            if self.os_type == "windows":
                # Windows: использование ipconfig
                ipconfig = subprocess.check_output(["ipconfig", "/all"], 
                                                 stderr=subprocess.PIPE).decode()
                # Парсинг ipconfig - базовая реализация
                current_if = {}
                for line in ipconfig.splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    
                    if "adapter" in line.lower() and ":" in line:
                        if current_if and "name" in current_if:
                            network_info["interfaces"].append(current_if)
                        current_if = {"name": line.split(":")[0].strip()}
                    elif "IPv4 Address" in line and ":" in line:
                        current_if["ip"] = line.split(":")[-1].strip()
                    elif "Physical Address" in line and ":" in line:
                        current_if["mac"] = line.split(":")[-1].strip()
                
                if current_if and "name" in current_if:
                    network_info["interfaces"].append(current_if)
                
            elif self.os_type in ["darwin", "linux"]:
                # Unix: использование ifconfig
                try:
                    ifconfig = subprocess.check_output(["ifconfig"], 
                                                     stderr=subprocess.PIPE).decode()
                except FileNotFoundError:
                    # В некоторых Linux-системах ifconfig может отсутствовать
                    ifconfig = subprocess.check_output(["ip", "addr"], 
                                                     stderr=subprocess.PIPE).decode()
                
                # Базовый парсинг ifconfig/ip addr
                current_if = {}
                for line in ifconfig.splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    
                    if line[0].isalnum() and ":" in line:
                        if current_if and "name" in current_if:
                            network_info["interfaces"].append(current_if)
                        current_if = {"name": line.split(":")[0].strip()}
                    elif "inet " in line:
                        addr_part = line.split("inet ")[1].split()[0]
                        current_if["ip"] = addr_part
                    elif "ether" in line:
                        mac_part = line.split("ether ")[1].split()[0]
                        current_if["mac"] = mac_part
                
                if current_if and "name" in current_if:
                    network_info["interfaces"].append(current_if)
        except Exception as e:
            logger.warning(f"Ошибка при сборе информации о сетевых интерфейсах: {e}")
        
        # Сбор информации о сетевых соединениях
        try:
            if self.os_type == "windows":
                # Windows: использование netstat
                netstat = subprocess.check_output(["netstat", "-ano"], 
                                               stderr=subprocess.PIPE).decode()
                
                for line in netstat.splitlines()[4:]:  # Пропускаем заголовки
                    parts = line.strip().split()
                    if len(parts) >= 5 and "ESTABLISHED" in line:
                        connection = {
                            "protocol": parts[0],
                            "local": parts[1],
                            "remote": parts[2],
                            "state": parts[3],
                            "pid": parts[4]
                        }
                        network_info["connections"].append(connection)
            
            elif self.os_type in ["darwin", "linux"]:
                # Unix: использование netstat
                try:
                    netstat = subprocess.check_output(["netstat", "-tupn"],
                                                   stderr=subprocess.PIPE).decode()
                except Exception:
                    # Альтернатива в случае ошибки или отсутствия прав
                    netstat = subprocess.check_output(["netstat", "-tn"],
                                                   stderr=subprocess.PIPE).decode()
                
                for line in netstat.splitlines():
                    if "ESTABLISHED" in line:
                        parts = line.strip().split()
                        if len(parts) >= 7:
                            connection = {
                                "protocol": parts[0],
                                "local": parts[3],
                                "remote": parts[4],
                                "state": parts[5]
                            }
                            if len(parts) > 6:
                                connection["pid"] = parts[6].split("/")[0]
                            network_info["connections"].append(connection)
        except Exception as e:
            logger.warning(f"Ошибка при сборе информации о сетевых соединениях: {e}")
        
        return network_info
    
    def collect_running_processes(self) -> List[Dict[str, Any]]:
        """
        Собирает информацию о запущенных процессах
        
        Returns:
            List[Dict[str, Any]]: Список запущенных процессов
        """
        self._log_action("collect", "Collecting process information")
        
        processes = []
        
        try:
            if self.os_type == "windows":
                # Windows: использование tasklist
                tasklist = subprocess.check_output(["tasklist", "/FO", "CSV", "/NH"], 
                                                stderr=subprocess.PIPE).decode()
                
                for line in tasklist.splitlines():
                    if not line.strip():
                        continue
                    
                    # Парсинг CSV формата
                    parts = line.strip().strip('"').split('","')
                    if len(parts) >= 5:
                        process = {
                            "name": parts[0],
                            "pid": parts[1],
                            "session_name": parts[2],
                            "session_num": parts[3],
                            "memory": parts[4]
                        }
                        processes.append(process)
            
            elif self.os_type in ["darwin", "linux"]:
                # Unix: использование ps
                ps_cmd = subprocess.check_output(["ps", "aux"], 
                                              stderr=subprocess.PIPE).decode()
                
                for line in ps_cmd.splitlines()[1:]:  # Пропускаем заголовок
                    parts = line.strip().split(None, 10)
                    if len(parts) >= 11:
                        process = {
                            "user": parts[0],
                            "pid": parts[1],
                            "cpu": parts[2],
                            "memory": parts[3],
                            "start": parts[8],
                            "time": parts[9],
                            "name": parts[10]
                        }
                        processes.append(process)
        except Exception as e:
            logger.warning(f"Ошибка при сборе информации о процессах: {e}")
        
        return processes
    
    def execute_command(self, command: str, shell: bool = False) -> Tuple[int, str, str]:
        """
        Безопасно выполняет команду и возвращает результат
        
        Args:
            command: Команда для выполнения (строка или список аргументов)
            shell: Использовать shell для выполнения команды
            
        Returns:
            Tuple[int, str, str]: Код возврата, stdout, stderr
        """
        self._log_action("execute", f"Executing command: {command}")
        
        try:
            if not shell and isinstance(command, str):
                # Разбиваем строку на аргументы, если shell=False
                command = command.split()
            
            # Выполняем команду
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=shell,
                universal_newlines=True
            )
            
            stdout, stderr = process.communicate()
            returncode = process.returncode
            
            return returncode, stdout, stderr
        
        except Exception as e:
            logger.error(f"Ошибка при выполнении команды {command}: {e}")
            return -1, "", str(e)
    
    def get_action_log(self) -> List[Dict[str, Any]]:
        """
        Возвращает журнал действий
        
        Returns:
            List[Dict[str, Any]]: Журнал действий
        """
        return self.action_log
    
    def get_status(self) -> Dict[str, Any]:
        """
        Возвращает текущий статус окружения
        
        Returns:
            Dict[str, Any]: Текущий статус окружения
        """
        return {
            "os": self.os_type,
            "hostname": self.hostname,
            "is_admin": self.is_admin,
            "security_products": self.security_products,
            "action_count": len(self.action_log),
            "last_action": self.action_log[-1] if self.action_log else None
        }
    
    def adapt_behavior(self, detection_level: float = 0.0) -> Dict[str, Any]:
        """
        Адаптирует поведение в зависимости от обнаруженной защиты
        
        Args:
            detection_level: Уровень обнаружения (0.0-1.0), где 1.0 - максимальная осторожность
            
        Returns:
            Dict[str, Any]: Рекомендации по адаптации поведения
        """
        self._log_action("adapt", f"Adapting behavior, detection level: {detection_level}")
        
        # Базовый уровень риска - зависит от наличия EDR/AV
        edr_count = len(self.security_products["edr"])
        av_count = len(self.security_products["antivirus"])
        base_risk = min(1.0, (edr_count * 0.2) + (av_count * 0.1) + detection_level)
        
        # Рекомендации в зависимости от уровня риска
        recommendations = {
            "risk_level": base_risk,
            "edr_detected": self.security_products["edr"],
            "av_detected": self.security_products["antivirus"],
            "execution_mode": "stealth" if base_risk > 0.5 else "normal",
            "sleep_between_actions": int(base_risk * 5000),  # от 0 до 5000 мс
            "use_obfuscation": base_risk > 0.3,
            "random_sleep": base_risk > 0.2,
            "minimize_commands": base_risk > 0.4,
            "disable_logging": base_risk > 0.8,
            "self_delete_traces": base_risk > 0.4,
            "terminate_recommended": base_risk > 0.9
        }
        
        return recommendations

# Пример использования (для автотеста):
if __name__ == "__main__":
    em = EnvironmentManager()
    em.collect_system_info()
    em.collect_processes()
    em.collect_network_info()
    em.detect_edr_av()
    print(em.summary()) 