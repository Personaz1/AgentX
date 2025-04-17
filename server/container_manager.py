#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NeuroRAT Container Manager - утилита для управления Docker контейнерами
Позволяет выполнять основные операции с контейнерами: сборка, запуск, остановка, перезапуск,
просмотр логов и статуса, а также проверка состояния сети
"""

import os
import sys
import json
import time
import argparse
import subprocess
from datetime import datetime
import socket
import signal
import threading

COMPOSE_FILE = "docker-compose.yml"
DEFAULT_SERVICES = ["neurorat-server", "swarm-node-1"]

# Настройка логирования
LOGS_DIR = "logs"
os.makedirs(LOGS_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOGS_DIR, f"container_manager_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

def log(message, level="INFO"):
    """Запись сообщения в лог и вывод в консоль"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] [{level}] {message}"
    
    # Выводим в консоль
    if level == "ERROR":
        print(f"\033[91m{log_line}\033[0m")  # Красный цвет для ошибок
    elif level == "WARNING":
        print(f"\033[93m{log_line}\033[0m")  # Желтый цвет для предупреждений
    elif level == "SUCCESS":
        print(f"\033[92m{log_line}\033[0m")  # Зеленый цвет для успеха
    else:
        print(log_line)
    
    # Записываем в файл
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(log_line + "\n")

def check_docker_installed():
    """Проверка установки Docker и Docker Compose"""
    try:
        subprocess.run(["docker", "--version"], check=True, capture_output=True)
        docker_compose_result = subprocess.run(["docker-compose", "--version"], check=True, capture_output=True)
        log(f"Docker и Docker Compose установлены")
        return True
    except (subprocess.SubprocessError, FileNotFoundError) as e:
        log(f"Docker или Docker Compose не установлены: {str(e)}", "ERROR")
        return False

def find_compose_file():
    """Поиск docker-compose.yml файла"""
    if os.path.exists(COMPOSE_FILE):
        log(f"Найден {COMPOSE_FILE} в текущей директории")
        return os.path.abspath(COMPOSE_FILE)
    
    # Ищем файл в родительских директориях
    current_dir = os.getcwd()
    for _ in range(3):  # Проверяем 3 уровня вверх
        parent_dir = os.path.dirname(current_dir)
        if parent_dir == current_dir:  # Достигли корня файловой системы
            break
        current_dir = parent_dir
        compose_path = os.path.join(current_dir, COMPOSE_FILE)
        if os.path.exists(compose_path):
            log(f"Найден {COMPOSE_FILE} в директории {current_dir}")
            return compose_path
    
    log(f"Файл {COMPOSE_FILE} не найден", "ERROR")
    return None

def run_command(cmd, show_output=True):
    """Выполнение команды с выводом результата"""
    cmd_str = " ".join(cmd)
    log(f"Выполнение команды: {cmd_str}")
    
    try:
        process = subprocess.run(cmd, check=True, capture_output=True, text=True)
        if show_output and process.stdout:
            for line in process.stdout.splitlines():
                log(f"STDOUT: {line}")
        return {"status": "success", "output": process.stdout}
    except subprocess.CalledProcessError as e:
        log(f"Ошибка при выполнении команды: {str(e)}", "ERROR")
        if e.stderr:
            for line in e.stderr.splitlines():
                log(f"STDERR: {line}", "ERROR")
        return {"status": "error", "message": str(e), "stderr": e.stderr}

def get_services(compose_file):
    """Получение списка сервисов из docker-compose.yml"""
    try:
        cmd = ["docker-compose", "-f", compose_file, "config", "--services"]
        result = run_command(cmd, show_output=False)
        if result["status"] == "success":
            services = result["output"].strip().split('\n')
            log(f"Найдены сервисы: {', '.join(services)}")
            return services
        return DEFAULT_SERVICES
    except Exception as e:
        log(f"Ошибка при получении списка сервисов: {str(e)}", "ERROR")
        return DEFAULT_SERVICES

def build_containers(compose_file, service=None):
    """Сборка контейнеров"""
    log(f"Начинаем сборку {'всех контейнеров' if service is None else f'контейнера {service}'}")
    
    cmd = ["docker-compose", "-f", compose_file, "build"]
    if service:
        cmd.append(service)
    
    result = run_command(cmd)
    if result["status"] == "success":
        log(f"Сборка {'всех контейнеров' if service is None else f'контейнера {service}'} успешно завершена", "SUCCESS")
    else:
        log(f"Ошибка при сборке {'всех контейнеров' if service is None else f'контейнера {service}'}", "ERROR")
    
    return result

def start_containers(compose_file, service=None, detached=True):
    """Запуск контейнеров"""
    log(f"Запуск {'всех контейнеров' if service is None else f'контейнера {service}'}")
    
    cmd = ["docker-compose", "-f", compose_file, "up"]
    if detached:
        cmd.append("-d")
    if service:
        cmd.append(service)
    
    result = run_command(cmd)
    if result["status"] == "success":
        log(f"Запуск {'всех контейнеров' if service is None else f'контейнера {service}'} успешно выполнен", "SUCCESS")
    else:
        log(f"Ошибка при запуске {'всех контейнеров' if service is None else f'контейнера {service}'}", "ERROR")
    
    return result

def stop_containers(compose_file, service=None):
    """Остановка контейнеров"""
    log(f"Остановка {'всех контейнеров' if service is None else f'контейнера {service}'}")
    
    cmd = ["docker-compose", "-f", compose_file, "stop"]
    if service:
        cmd.append(service)
    
    result = run_command(cmd)
    if result["status"] == "success":
        log(f"Остановка {'всех контейнеров' if service is None else f'контейнера {service}'} успешно выполнена", "SUCCESS")
    else:
        log(f"Ошибка при остановке {'всех контейнеров' if service is None else f'контейнера {service}'}", "ERROR")
    
    return result

def restart_containers(compose_file, service=None):
    """Перезапуск контейнеров"""
    log(f"Перезапуск {'всех контейнеров' if service is None else f'контейнера {service}'}")
    
    cmd = ["docker-compose", "-f", compose_file, "restart"]
    if service:
        cmd.append(service)
    
    result = run_command(cmd)
    if result["status"] == "success":
        log(f"Перезапуск {'всех контейнеров' if service is None else f'контейнера {service}'} успешно выполнен", "SUCCESS")
    else:
        log(f"Ошибка при перезапуске {'всех контейнеров' if service is None else f'контейнера {service}'}", "ERROR")
    
    return result

def show_logs(compose_file, service=None, tail=100, follow=False):
    """Просмотр логов контейнеров"""
    log(f"Просмотр логов {'всех контейнеров' if service is None else f'контейнера {service}'}")
    
    cmd = ["docker-compose", "-f", compose_file, "logs"]
    if tail:
        cmd.extend(["--tail", str(tail)])
    if follow:
        cmd.append("-f")
    if service:
        cmd.append(service)
    
    if follow:
        try:
            # Запускаем процесс и перенаправляем вывод в реальном времени
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
            
            def signal_handler(sig, frame):
                log("Прерывание просмотра логов (Ctrl+C)")
                process.terminate()
                sys.exit(0)
            
            signal.signal(signal.SIGINT, signal_handler)
            
            for line in process.stdout:
                print(line.strip())
            
            process.wait()
            return {"status": "success"}
        except Exception as e:
            log(f"Ошибка при просмотре логов: {str(e)}", "ERROR")
            return {"status": "error", "message": str(e)}
    else:
        return run_command(cmd)

def show_status(compose_file):
    """Показать статус контейнеров"""
    log("Получение статуса контейнеров")
    
    cmd = ["docker-compose", "-f", compose_file, "ps"]
    result = run_command(cmd)
    
    # Дополнительно показываем сетевую информацию
    log("Получение информации о сети")
    network_cmd = ["docker", "network", "inspect", "neurorat-network"]
    try:
        network_result = subprocess.run(network_cmd, check=True, capture_output=True, text=True)
        network_data = json.loads(network_result.stdout)
        if network_data:
            log(f"Сеть: {network_data[0].get('Name')}, Driver: {network_data[0].get('Driver')}")
            containers = network_data[0].get('Containers', {})
            for container_id, container_info in containers.items():
                log(f"  Контейнер: {container_info.get('Name')}, IP: {container_info.get('IPv4Address')}")
    except (subprocess.CalledProcessError, json.JSONDecodeError, IndexError) as e:
        log(f"Ошибка при получении информации о сети: {str(e)}", "ERROR")
    
    return result

def check_ports(ports, host="localhost"):
    """Проверка доступности портов"""
    log(f"Проверка доступности портов на {host}")
    
    results = []
    for port in ports:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((host, port))
        sock.close()
        
        status = "открыт" if result == 0 else "закрыт"
        log(f"Порт {port}: {status}")
        results.append((port, status))
    
    return results

def main():
    """Основная функция"""
    parser = argparse.ArgumentParser(description="NeuroRAT Container Manager")
    parser.add_argument("action", choices=["build", "start", "stop", "restart", "logs", "status", "check-ports"], 
                        help="Действие для выполнения")
    parser.add_argument("--service", "-s", help="Имя сервиса (контейнера)")
    parser.add_argument("--detached", "-d", action="store_true", default=True, 
                        help="Запустить контейнеры в фоновом режиме (по умолчанию)")
    parser.add_argument("--follow", "-f", action="store_true", 
                        help="Отслеживать логи в реальном времени")
    parser.add_argument("--tail", "-t", type=int, default=100, 
                        help="Количество последних строк логов")
    parser.add_argument("--ports", "-p", type=int, nargs="+", default=[8080, 5001], 
                        help="Порты для проверки")
    parser.add_argument("--host", "-H", default="localhost", 
                        help="Хост для проверки портов")
    
    args = parser.parse_args()
    
    # Проверка установки Docker
    if not check_docker_installed():
        return 1
    
    # Поиск docker-compose.yml
    compose_file = find_compose_file()
    if not compose_file:
        return 1
    
    # Проверяем сервис, если указан
    if args.service:
        services = get_services(compose_file)
        if args.service not in services:
            log(f"Сервис '{args.service}' не найден. Доступные сервисы: {', '.join(services)}", "ERROR")
            return 1
    
    # Выполнение действия
    if args.action == "build":
        result = build_containers(compose_file, args.service)
    elif args.action == "start":
        result = start_containers(compose_file, args.service, args.detached)
    elif args.action == "stop":
        result = stop_containers(compose_file, args.service)
    elif args.action == "restart":
        result = restart_containers(compose_file, args.service)
    elif args.action == "logs":
        result = show_logs(compose_file, args.service, args.tail, args.follow)
    elif args.action == "status":
        result = show_status(compose_file)
    elif args.action == "check-ports":
        check_ports(args.ports, args.host)
        result = {"status": "success"}
    else:
        log(f"Неизвестное действие: {args.action}", "ERROR")
        return 1
    
    return 0 if result.get("status") == "success" else 1

if __name__ == "__main__":
    sys.exit(main()) 