#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SystemStealer Module - Находит и экстрактит системную информацию
"""

import os
import json
import logging
from typing import Dict, List, Any

logger = logging.getLogger("SystemStealer")

class SystemStealer:
    """
    Модуль для сбора системной информации (пользователи, сетевые подключения, и др.)
    """
    
    def __init__(self, output_dir=None):
        self.output_dir = output_dir or os.path.join(os.getcwd(), "extracted_data/system")
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Используем EnvironmentManager для получения системной информации
        try:
            from agent_modules.environment_manager import EnvironmentManager
            self.env_manager = EnvironmentManager()
            self.sys_info = self.env_manager.collect_system_info()
            self.has_env_manager = True
        except ImportError:
            self.env_manager = None
            self.sys_info = {"os": "unknown", "hostname": "unknown"}
            self.has_env_manager = False
        
    def run(self) -> Dict[str, Any]:
        """
        Выполняет сбор системной информации
        
        Returns:
            Словарь с результатами сканирования
        """
        logger.info("Начинаю сбор системной информации...")
        
        # Базовая информация
        system_info = {}
        network_info = {}
        user_accounts = []
        installed_software = []
        running_processes = []
        
        # Получаем информацию через EnvironmentManager если доступен
        if self.has_env_manager:
            logger.info("Используем EnvironmentManager для сбора системной информации")
            
            # Системная информация
            system_info = self.sys_info
            
            # Сетевая информация
            try:
                network_info = self.env_manager.collect_network_info()
            except:
                network_info = {"connections": [], "interfaces": []}
                
            # Информация о процессах
            try:
                running_processes = self.env_manager.collect_running_processes()
            except:
                running_processes = []
        else:
            # Демо-данные если нет EnvironmentManager
            system_info = {
                "os": "MacOS",
                "hostname": "demo-host",
                "username": "user",
                "os_version": "12.6",
                "cpu_info": "Apple M1",
                "ram_total": "16 GB"
            }
            
            network_info = {
                "interfaces": [
                    {"name": "en0", "ip": "192.168.1.100", "mac": "00:11:22:33:44:55"}
                ],
                "connections": [
                    {"local": "192.168.1.100:54321", "remote": "93.184.216.34:443", "state": "ESTABLISHED"}
                ]
            }
            
            running_processes = [
                {"pid": 1, "name": "systemd", "user": "root"},
                {"pid": 1000, "name": "chrome", "user": "user"}
            ]
        
        # Добавляем демо-данные для пользователей и ПО (в реальном модуле был бы сбор данных)
        user_accounts = [
            {"username": "admin", "uid": 0, "home": "/home/admin", "shell": "/bin/bash"},
            {"username": "user", "uid": 1000, "home": "/home/user", "shell": "/bin/bash"}
        ]
        
        installed_software = [
            {"name": "Chrome", "version": "100.0.4896.127"},
            {"name": "Firefox", "version": "98.0.2"},
            {"name": "Visual Studio Code", "version": "1.66.2"}
        ]
        
        # Сохраняем результаты
        collected_data = {
            "system_info": system_info,
            "network_info": network_info,
            "user_accounts": user_accounts,
            "installed_software": installed_software,
            "running_processes": running_processes
        }
        
        result_file = os.path.join(self.output_dir, "system_info.json")
        with open(result_file, 'w') as f:
            json.dump(collected_data, f, indent=2)
        
        return {
            "status": "success",
            "summary": {
                "system": system_info.get("os", "unknown"),
                "username": system_info.get("username", "unknown"),
                "user_accounts": len(user_accounts),
                "processes": len(running_processes),
                "connections": len(network_info.get("connections", [])),
                "using_environment_manager": self.has_env_manager
            },
            "system_info": system_info,
            "network_info": network_info,
            "user_accounts": user_accounts,
            "output_file": result_file
        }


def main():
    """Main function to run the system stealer module"""
    output_dir = os.path.join(os.getcwd(), "extracted_data")
    
    try:
        stealer = SystemStealer(output_dir)
        results = stealer.run()
        
        print(f"\nSystem Stealer Results:")
        print(f"System: {results['summary']['system']}")
        print(f"Username: {results['summary']['username']}")
        print(f"User accounts: {results['summary']['user_accounts']}")
        print(f"Processes: {results['summary']['processes']}")
        print(f"Connections: {results['summary']['connections']}")
        print(f"Using Environment Manager: {results['summary']['using_environment_manager']}")
        print(f"Output saved to: {results['summary']['output_file']}")
        
    except Exception as e:
        print(f"Error running system stealer: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    main() 