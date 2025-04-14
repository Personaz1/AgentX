#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Скрипт запуска MCP сервера с Docker контейнерами для NeuroRAT

Скрипт выполняет:
1. Остановку существующих Docker контейнеров
2. Запуск Docker контейнеров
3. Запуск MCP сервера для поддержки языковых моделей

Автор: Neuro Agent System
"""

import os
import sys
import time
import argparse
import subprocess
import logging
import signal
import threading
from pathlib import Path
from dotenv import load_dotenv

# Загрузка переменных из .env файла
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('start_mcp.log')
    ]
)
logger = logging.getLogger('start_mcp')

def run_command(command, shell=True, cwd=None):
    """
    Выполнение команды с выводом в реальном времени
    
    Args:
        command: Команда для выполнения
        shell: Использовать оболочку
        cwd: Рабочая директория
        
    Returns:
        Код возврата команды
    """
    logger.info(f"Выполняем команду: {command}")
    
    process = subprocess.Popen(
        command,
        shell=shell,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        cwd=cwd
    )
    
    # Вывод в реальном времени
    for line in process.stdout:
        print(line.strip())
        logger.debug(line.strip())
    
    # Ожидаем завершения процесса
    process.wait()
    
    if process.returncode != 0:
        logger.warning(f"Команда завершилась с кодом {process.returncode}")
    else:
        logger.info(f"Команда успешно выполнена (код: {process.returncode})")
        
    return process.returncode

def stop_docker_containers():
    """Остановка Docker контейнеров"""
    logger.info("Останавливаем Docker контейнеры...")
    return run_command("docker-compose down")

def start_docker_containers():
    """Запуск Docker контейнеров"""
    logger.info("Запускаем Docker контейнеры...")
    return run_command("docker-compose up --build -d")

def start_mcp_server(host="0.0.0.0", port=8089, gemini_api_key=None):
    """
    Запуск MCP сервера
    
    Args:
        host: Хост для привязки
        port: Порт для привязки
        gemini_api_key: API ключ для Google Gemini
    """
    logger.info(f"Запускаем MCP сервер на {host}:{port}...")
    
    # Устанавливаем API ключ, если он указан в параметре или в .env
    if gemini_api_key:
        os.environ["GEMINI_API_KEY"] = gemini_api_key
        logger.info("API ключ Gemini установлен из параметра командной строки")
    elif "GEMINI_API_KEY" in os.environ:
        logger.info("Используем API ключ Gemini из .env файла")
    else:
        logger.warning("API ключ Gemini не найден")
    
    # Проверяем наличие необходимых библиотек
    try:
        import uvicorn
        from fastapi import FastAPI
    except ImportError:
        logger.error("Не удалось импортировать uvicorn или fastapi. Устанавливаем зависимости...")
        run_command("pip install uvicorn fastapi google-generativeai python-dotenv")
    
    # Проверяем наличие файла mcp_server.py
    if not os.path.exists("mcp_server.py"):
        logger.error("Файл mcp_server.py не найден")
        return 1
    
    # Запускаем MCP сервер
    cmd = f"python mcp_server.py --host {host} --port {port}"
    return run_command(cmd)

def main():
    """Основная функция запуска"""
    
    # Парсинг аргументов командной строки
    parser = argparse.ArgumentParser(description="Запуск MCP сервера с Docker контейнерами")
    parser.add_argument("--skip-docker", action="store_true", help="Пропустить управление Docker")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Хост для MCP сервера")
    parser.add_argument("--port", type=int, default=8089, help="Порт для MCP сервера")
    parser.add_argument("--gemini-key", type=str, help="API ключ для Google Gemini (переопределяет ключ из .env)")
    parser.add_argument("--verbose", action="store_true", help="Подробный вывод")
    
    args = parser.parse_args()
    
    # Настройка уровня логирования
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Обработка Docker контейнеров
        if not args.skip_docker:
            stop_docker_containers()
            start_docker_containers()
        else:
            logger.info("Пропускаем управление Docker контейнерами")
        
        # Запуск MCP сервера
        result = start_mcp_server(args.host, args.port, args.gemini_key)
        
        return result
    
    except KeyboardInterrupt:
        logger.info("Прервано пользователем")
        return 0
    except Exception as e:
        logger.error(f"Ошибка при выполнении: {str(e)}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main()) 