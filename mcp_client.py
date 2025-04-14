#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Model Context Protocol (MCP) Client

Клиентская часть протокола для обмена контекстом с языковыми моделями.
Обеспечивает взаимодействие с MCP-сервером и управление локальным контекстом.
"""

import os
import sys
import json
import socket
import threading
import time
import logging
import base64
import hashlib
import ssl
import uuid
import random
from typing import Dict, List, Any, Optional, Union, Callable, Tuple
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('mcp_client.log')
    ]
)
logger = logging.getLogger('mcp_client')

class MCPClient:
    """
    Клиент для обмена контекстом и взаимодействия с языковыми моделями.
    Обеспечивает подключение к MCP-серверу и управление контекстом.
    """
    
    def __init__(self, server_url: str, api_key: Optional[str] = None,
                 default_model: str = "gemini-2.5-pro-preview-03-25"):
        """
        Инициализация клиента MCP.
        
        Args:
            server_url: URL MCP-сервера (например: http://localhost:8089)
            api_key: API ключ для авторизации на MCP сервере
            default_model: Модель по умолчанию
        """
        self.server_url = server_url
        self.api_key = api_key
        self.default_model = default_model
        
        # Локальный контекст для хранения истории сообщений
        self.conversations = {}
        
        # Логирование
        self.logger = logging.getLogger('mcp_client')
        
    def create_conversation(self, system_message: str = "") -> str:
        """
        Создание нового контекста разговора
        
        Args:
            system_message: Системное сообщение для настройки поведения модели
            
        Returns:
            Идентификатор созданного контекста
        """
        context_id = str(uuid.uuid4())
        
        # Сохраняем контекст локально
        self.conversations[context_id] = {
            "created": datetime.now().isoformat(),
            "messages": []
        }
        
        # Если есть системное сообщение, добавляем его
        if system_message:
            self.conversations[context_id]["messages"].append({
                "role": "system",
                "content": system_message
            })
            
        return context_id
    
    def chat(self, message: str, context_id: Optional[str] = None,
             model: Optional[str] = None, temperature: float = 0.7,
             max_tokens: int = 1000) -> Dict[str, Any]:
        """
        Отправка сообщения к LLM через MCP-сервер
        
        Args:
            message: Текст сообщения
            context_id: Идентификатор контекста (если None, создается новый)
            model: Модель для использования (если None, используется default_model)
            temperature: Температура генерации
            max_tokens: Максимальное количество токенов для генерации
            
        Returns:
            Ответ модели
        """
        # Если контекст не указан, создаем новый
        if not context_id:
            context_id = self.create_conversation()
            
        # Если контекст не существует, создаем его
        if context_id not in self.conversations:
            self.conversations[context_id] = {
                "created": datetime.now().isoformat(),
                "messages": []
            }
            
        # Добавляем сообщение пользователя в контекст
        self.conversations[context_id]["messages"].append({
            "role": "user",
            "content": message
        })
        
        # Формируем запрос к серверу
        url = f"{self.server_url}/api/v1/models/query"
        
        headers = {
            "Content-Type": "application/json"
        }
        
        # Добавляем авторизацию, если указан API ключ
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
            
        # Формируем данные запроса
        data = {
            "model": model or self.default_model,
            "messages": self.conversations[context_id]["messages"],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "context_id": context_id
        }
        
        try:
            import requests
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code != 200:
                self.logger.error(f"Error from MCP server: {response.status_code} - {response.text}")
                return {
                    "status": "error",
                    "error": f"Server returned status code {response.status_code}",
                    "content": "Ошибка при получении ответа от сервера"
                }
                
            result = response.json()
            
            # Добавляем ответ модели в контекст
            self.conversations[context_id]["messages"].append({
                "role": "assistant",
                "content": result["content"]
            })
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in chat request: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "content": "Ошибка при отправке запроса к серверу"
            }
    
    def clear_context(self, context_id: str) -> bool:
        """
        Очистка контекста разговора
        
        Args:
            context_id: Идентификатор контекста
            
        Returns:
            Успешность операции
        """
        if context_id in self.conversations:
            # Очищаем сообщения, сохраняя метаданные
            self.conversations[context_id]["messages"] = []
            return True
        return False


# Пример использования
if __name__ == "__main__":
    import argparse
    
    # Парсим аргументы командной строки
    parser = argparse.ArgumentParser(description='Model Context Protocol (MCP) Client')
    parser.add_argument('--host', required=True, help='MCP server host')
    parser.add_argument('--port', type=int, default=5500, help='MCP server port')
    parser.add_argument('--no-ssl', action='store_true', help='Disable SSL encryption')
    parser.add_argument('--no-verify', action='store_true', help='Disable SSL certificate verification')
    parser.add_argument('--token', help='Authentication token')
    parser.add_argument('--query', help='Query to send to the model')
    parser.add_argument('--system', help='System message for the query')
    parser.add_argument('--model', default='default', help='Model to use')
    parser.add_argument('--add-memory', help='Add content to memory')
    parser.add_argument('--category', default='general', help='Category for memory item')
    parser.add_argument('--importance', type=int, default=5, help='Importance for memory item (1-10)')
    parser.add_argument('--get-memory', action='store_true', help='Get memory items')
    parser.add_argument('--memory-query', help='Query to filter memory items')
    parser.add_argument('--limit', type=int, default=10, help='Limit for memory items')
    parser.add_argument('--sync', action='store_true', help='Sync context with server')
    parser.add_argument('--clear', action='store_true', help='Clear context')
    parser.add_argument('--list-models', action='store_true', help='List available models')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Настройка уровня логирования
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Создаем клиент
    client = MCPClient(
        server_url=args.host,
        api_key=args.token
    )
    
    # Подключаемся к серверу
    if not client.connect():
        print("Не удалось подключиться к серверу")
        sys.exit(1)
        
    try:
        # Обрабатываем команды
        if args.clear:
            result = client.clear_context(args.context_id)
            print(f"Очистка контекста: {'успешно' if result else 'ошибка'}")
            
        if args.sync:
            result = client.sync_context()
            print(f"Синхронизация контекста: {'успешно' if result else 'ошибка'}")
            
        if args.add_memory:
            response = client.add_to_memory(args.add_memory, args.category, args.importance)
            if response["status"] == "success":
                print(f"Добавлено в память, ID: {response.get('memory_id', 'unknown')}")
            else:
                print(f"Ошибка добавления в память: {response.get('error', 'Unknown error')}")
                
        if args.get_memory:
            memory_items = client.get_memory(args.category, args.memory_query, args.limit)
            print(f"Получено {len(memory_items)} элементов памяти:")
            for item in memory_items:
                print(f"[{item['id'][:8]}] [{item['category']}] (Важность: {item['importance']}): {item['content']}")
                
        if args.list_models:
            models = client.list_models()
            print(f"Доступные модели ({len(models)}):")
            for model in models:
                print(f"ID: {model['id']}, Тип: {model['type']}")
                
        if args.query:
            response = client.chat(args.query, args.context_id, args.model)
            if response["status"] == "success":
                print(f"\nМодель: {response.get('model', 'unknown')}")
                print(f"Ответ: {response['content']}")
            else:
                print(f"Ошибка запроса: {response.get('error', 'Unknown error')}")
                
    except KeyboardInterrupt:
        print("\nПрерывание пользователем")
    finally:
        client.disconnect() 