#!/usr/bin/env python3
"""
Пример модуля для безопасного агента.
Этот модуль собирает расширенную информацию о системе.
"""

import platform
import psutil
import socket
import os
import json
from datetime import datetime

def get_network_info():
    """Получить информацию о сетевых интерфейсах."""
    interfaces = []
    
    try:
        # Получаем все сетевые интерфейсы
        addrs = psutil.net_if_addrs()
        stats = psutil.net_if_stats()
        
        for name, addr_list in addrs.items():
            if name in stats:
                # Создаем запись об интерфейсе
                interface = {
                    "name": name,
                    "addresses": [],
                    "is_up": stats[name].isup,
                    "speed": stats[name].speed
                }
                
                # Добавляем все адреса
                for addr in addr_list:
                    address_info = {
                        "family": str(addr.family),
                        "address": addr.address
                    }
                    
                    if hasattr(addr, "netmask") and addr.netmask:
                        address_info["netmask"] = addr.netmask
                        
                    if hasattr(addr, "broadcast") and addr.broadcast:
                        address_info["broadcast"] = addr.broadcast
                        
                    interface["addresses"].append(address_info)
                    
                interfaces.append(interface)
    except Exception as e:
        interfaces.append({"error": str(e)})
    
    return interfaces

def get_running_processes(limit=10):
    """Получить список запущенных процессов."""
    processes = []
    
    try:
        for proc in psutil.process_iter(['pid', 'name', 'username', 'memory_info', 'cpu_percent']):
            process_info = proc.info
            if process_info['cpu_percent'] > 0:  # Фильтруем только активные процессы
                processes.append({
                    "pid": process_info['pid'],
                    "name": process_info['name'],
                    "username": process_info['username'],
                    "memory_mb": round(process_info['memory_info'].rss / (1024 * 1024), 2),
                    "cpu_percent": process_info['cpu_percent']
                })
                
            # Ограничиваем количество возвращаемых процессов
            if len(processes) >= limit:
                break
    except Exception as e:
        processes.append({"error": str(e)})
    
    return processes

def get_disk_info():
    """Получить информацию о дисках."""
    disk_info = []
    
    try:
        # Получаем информацию о разделах
        for partition in psutil.disk_partitions():
            usage = psutil.disk_usage(partition.mountpoint)
            
            disk_info.append({
                "device": partition.device,
                "mountpoint": partition.mountpoint,
                "fstype": partition.fstype,
                "total_gb": round(usage.total / (1024**3), 2),
                "used_gb": round(usage.used / (1024**3), 2),
                "free_gb": round(usage.free / (1024**3), 2),
                "percent": usage.percent
            })
    except Exception as e:
        disk_info.append({"error": str(e)})
    
    return disk_info

def run(collect_network=True, collect_processes=True, collect_disks=True, process_limit=10):
    """
    Основная функция модуля для запуска сбора информации.
    
    Параметры:
    - collect_network: собирать ли информацию о сети
    - collect_processes: собирать ли информацию о процессах
    - collect_disks: собирать ли информацию о дисках
    - process_limit: максимальное количество собираемых процессов
    
    Возвращает словарь с собранными данными.
    """
    result = {
        "timestamp": datetime.now().isoformat(),
        "hostname": platform.node(),
        "system": {
            "platform": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor()
        },
        "python": platform.python_version(),
        "cpu": {
            "count_physical": psutil.cpu_count(logical=False),
            "count_logical": psutil.cpu_count(logical=True),
            "percent": psutil.cpu_percent(interval=1)
        },
        "memory": {
            "total_mb": round(psutil.virtual_memory().total / (1024**2), 2),
            "available_mb": round(psutil.virtual_memory().available / (1024**2), 2),
            "used_mb": round(psutil.virtual_memory().used / (1024**2), 2),
            "percent": psutil.virtual_memory().percent
        }
    }
    
    # Добавляем информацию о сети, если требуется
    if collect_network:
        result["network"] = {
            "hostname": socket.gethostname(),
            "interfaces": get_network_info()
        }
        
        # Добавляем информацию о возможных IP-адресах
        try:
            result["network"]["ip_addresses"] = socket.gethostbyname_ex(socket.gethostname())[2]
        except:
            result["network"]["ip_addresses"] = ["Unable to get IP"]
    
    # Добавляем информацию о процессах, если требуется
    if collect_processes:
        result["processes"] = get_running_processes(limit=process_limit)
    
    # Добавляем информацию о дисках, если требуется
    if collect_disks:
        result["disks"] = get_disk_info()
    
    return result

if __name__ == "__main__":
    # Если модуль запущен напрямую, выводим результат на экран
    result = run()
    print(json.dumps(result, indent=2)) 