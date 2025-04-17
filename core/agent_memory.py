#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
NeuroRAT Agent Memory Module

Модуль для работы с памятью агента и интеграцией с языковыми моделями.
"""

import os
import json
import time
import logging
import threading
import base64
import hashlib
import pickle
import sqlite3
import re
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime

# Настройка логирования
logger = logging.getLogger("AgentMemory")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

class AgentMemory:
    """
    Класс для работы с долговременной и кратковременной памятью агента.
    Обеспечивает хранение, поиск и извлечение информации.
    
    Поддерживает:
    - Долговременную память (persistent) - важная информация о системе, задачах
    - Кратковременную память (short-term) - текущий контекст работы
    - Рабочую память (workspace) - промежуточные результаты размышлений
    - Интеграцию с LLM для семантического поиска
    """
    
    def __init__(self, memory_db: str = "agent_memory.db", 
                 memory_file: str = "agent_memory.json",
                 max_long_term_entries: int = 1000,
                 max_short_term_entries: int = 100,
                 max_workspace_entries: int = 50):
        """
        Инициализация памяти агента.
        
        Args:
            memory_db: Путь к файлу SQLite базы данных для долговременной памяти
            memory_file: Путь к файлу для резервного хранения в JSON
            max_long_term_entries: Максимальное количество записей в долговременной памяти
            max_short_term_entries: Максимальное количество записей в кратковременной памяти
            max_workspace_entries: Максимальное количество записей в рабочей памяти
        """
        self.memory_db = memory_db
        self.memory_file = memory_file
        
        # Лимиты
        self.max_long_term_entries = max_long_term_entries
        self.max_short_term_entries = max_short_term_entries
        self.max_workspace_entries = max_workspace_entries
        
        # Структуры памяти
        self.long_term_memory = []  # Долговременная память
        self.short_term_memory = []  # Кратковременная память
        self.workspace_memory = []   # Рабочая память
        
        # Индексы для быстрого поиска
        self.category_index = {}  # Индекс по категориям
        self.tag_index = {}       # Индекс по тегам
        self.time_index = {}      # Индекс по времени создания
        
        # Блокировки для потокобезопасности
        self.memory_lock = threading.RLock()
        
        # Инициализация базы данных
        self._init_database()
        
        # Загрузка памяти
        self._load_memory()
        
        logger.info("AgentMemory инициализирован")
    
    def _init_database(self):
        """Инициализация SQLite базы данных для хранения памяти."""
        try:
            conn = sqlite3.connect(self.memory_db)
            cursor = conn.cursor()
            
            # Таблица долговременной памяти
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS long_term_memory (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                importance INTEGER NOT NULL,
                category TEXT NOT NULL,
                tags TEXT,
                metadata TEXT,
                embedding_id TEXT,
                accessed_count INTEGER DEFAULT 0,
                last_accessed TEXT
            )
            ''')
            
            # Таблица кратковременной памяти
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS short_term_memory (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                category TEXT NOT NULL,
                tags TEXT,
                metadata TEXT,
                expiry TEXT
            )
            ''')
            
            # Таблица для эмбеддингов (для семантического поиска)
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS memory_embeddings (
                id TEXT PRIMARY KEY,
                memory_id TEXT NOT NULL,
                embedding BLOB,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (memory_id) REFERENCES long_term_memory (id)
            )
            ''')
            
            # Индексы для ускорения поиска
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_ltm_category ON long_term_memory (category)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_ltm_importance ON long_term_memory (importance)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_ltm_timestamp ON long_term_memory (timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_stm_category ON short_term_memory (category)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_stm_timestamp ON short_term_memory (timestamp)')
            
            conn.commit()
            conn.close()
            logger.debug("База данных памяти инициализирована")
        except Exception as e:
            logger.error(f"Ошибка при инициализации базы данных: {str(e)}")
            # Если не получилось создать БД, будем работать только с JSON
    
    def _generate_id(self, content: str) -> str:
        """
        Генерация уникального ID для записи в памяти.
        
        Args:
            content: Содержимое записи
            
        Returns:
            Уникальный ID
        """
        # Создаем хеш на основе содержимого и времени
        content_hash = hashlib.md5((content + str(time.time())).encode()).hexdigest()
        return content_hash[:12]  # Используем первые 12 символов хеша
    
    def _load_memory(self):
        """Загрузка памяти из базы данных и/или JSON файла."""
        with self.memory_lock:
            self.long_term_memory = []
            self.short_term_memory = []
            self.workspace_memory = []
            
            # Сначала пытаемся загрузить из базы данных
            try:
                conn = sqlite3.connect(self.memory_db)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Загрузка долговременной памяти
                cursor.execute('SELECT * FROM long_term_memory ORDER BY importance DESC, timestamp DESC')
                rows = cursor.fetchall()
                for row in rows:
                    memory_item = dict(row)
                    # Преобразуем JSON строки в объекты Python
                    if memory_item['tags']:
                        memory_item['tags'] = json.loads(memory_item['tags'])
                    if memory_item['metadata']:
                        memory_item['metadata'] = json.loads(memory_item['metadata'])
                    self.long_term_memory.append(memory_item)
                
                # Загрузка кратковременной памяти
                cursor.execute('SELECT * FROM short_term_memory ORDER BY timestamp DESC')
                rows = cursor.fetchall()
                for row in rows:
                    memory_item = dict(row)
                    # Преобразуем JSON строки в объекты Python
                    if memory_item['tags']:
                        memory_item['tags'] = json.loads(memory_item['tags'])
                    if memory_item['metadata']:
                        memory_item['metadata'] = json.loads(memory_item['metadata'])
                    self.short_term_memory.append(memory_item)
                
                conn.close()
                logger.info(f"Загружено записей: {len(self.long_term_memory)} долговременных, {len(self.short_term_memory)} кратковременных")
            except Exception as e:
                logger.error(f"Ошибка при загрузке из базы данных: {str(e)}")
                
                # Если не удалось загрузить из БД, пробуем из JSON
                try:
                    if os.path.exists(self.memory_file):
                        with open(self.memory_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            self.long_term_memory = data.get('long_term_memory', [])
                            self.short_term_memory = data.get('short_term_memory', [])
                            self.workspace_memory = data.get('workspace_memory', [])
                        logger.info(f"Загружено из JSON: {len(self.long_term_memory)} долговременных, {len(self.short_term_memory)} кратковременных")
                except Exception as e2:
                    logger.error(f"Ошибка при загрузке из JSON: {str(e2)}")
            
            # Обновляем индексы
            self._rebuild_indices()
    
    def _save_memory(self):
        """Сохранение памяти в базу данных и JSON файл."""
        with self.memory_lock:
            # Сохранение в базу данных
            try:
                conn = sqlite3.connect(self.memory_db)
                cursor = conn.cursor()
                
                # Очищаем таблицы перед сохранением
                cursor.execute('DELETE FROM long_term_memory')
                cursor.execute('DELETE FROM short_term_memory')
                
                # Сохраняем долговременную память
                for item in self.long_term_memory:
                    cursor.execute(
                        'INSERT INTO long_term_memory VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                        (
                            item['id'],
                            item['content'],
                            item['timestamp'],
                            item['importance'],
                            item['category'],
                            json.dumps(item.get('tags', [])),
                            json.dumps(item.get('metadata', {})),
                            item.get('embedding_id'),
                            item.get('accessed_count', 0),
                            item.get('last_accessed')
                        )
                    )
                
                # Сохраняем кратковременную память
                for item in self.short_term_memory:
                    cursor.execute(
                        'INSERT INTO short_term_memory VALUES (?, ?, ?, ?, ?, ?, ?)',
                        (
                            item['id'],
                            item['content'],
                            item['timestamp'],
                            item['category'],
                            json.dumps(item.get('tags', [])),
                            json.dumps(item.get('metadata', {})),
                            item.get('expiry')
                        )
                    )
                
                conn.commit()
                conn.close()
                logger.debug("Память сохранена в базу данных")
            except Exception as e:
                logger.error(f"Ошибка при сохранении в базу данных: {str(e)}")
            
            # Сохранение в JSON файл для резервной копии
            try:
                data = {
                    'long_term_memory': self.long_term_memory,
                    'short_term_memory': self.short_term_memory,
                    'workspace_memory': self.workspace_memory,
                    'last_updated': datetime.now().isoformat()
                }
                
                # Создаем директорию, если не существует
                directory = os.path.dirname(self.memory_file)
                if directory and not os.path.exists(directory):
                    os.makedirs(directory)
                
                with open(self.memory_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                
                logger.debug("Память сохранена в JSON файл")
            except Exception as e:
                logger.error(f"Ошибка при сохранении в JSON: {str(e)}")
    
    def _rebuild_indices(self):
        """Перестроение индексов для быстрого поиска."""
        with self.memory_lock:
            # Очищаем индексы
            self.category_index = {}
            self.tag_index = {}
            self.time_index = {}
            
            # Индексируем долговременную память
            for i, item in enumerate(self.long_term_memory):
                # Индекс по категориям
                category = item['category']
                if category not in self.category_index:
                    self.category_index[category] = []
                self.category_index[category].append(i)
                
                # Индекс по тегам
                for tag in item.get('tags', []):
                    if tag not in self.tag_index:
                        self.tag_index[tag] = []
                    self.tag_index[tag].append(i)
                
                # Индекс по времени (по дням)
                try:
                    date = datetime.fromisoformat(item['timestamp']).strftime('%Y-%m-%d')
                    if date not in self.time_index:
                        self.time_index[date] = []
                    self.time_index[date].append(i)
                except Exception:
                    pass
    
    # Методы для работы с долговременной памятью
    
    def add_to_long_term(self, content: str, importance: int = 5, category: str = "general",
                         tags: List[str] = None, metadata: Dict[str, Any] = None) -> str:
        """
        Добавление записи в долговременную память.
        
        Args:
            content: Содержимое записи
            importance: Важность (1-10)
            category: Категория записи
            tags: Список тегов для категоризации
            metadata: Дополнительные метаданные
            
        Returns:
            ID добавленной записи
        """
        memory_id = self._generate_id(content)
        timestamp = datetime.now().isoformat()
        
        with self.memory_lock:
            # Проверяем, есть ли уже похожая запись
            for item in self.long_term_memory:
                if item['content'] == content and item['category'] == category:
                    # Обновляем существующую запись
                    item['importance'] = max(item['importance'], importance)  # Берем наибольшую важность
                    item['timestamp'] = timestamp  # Обновляем время
                    if tags:
                        item['tags'] = list(set(item.get('tags', []) + tags))  # Обновляем теги
                    if metadata:
                        if 'metadata' not in item:
                            item['metadata'] = {}
                        item['metadata'].update(metadata)  # Обновляем метаданные
                    
                    logger.debug(f"Обновлена существующая запись в долговременной памяти: {content[:30]}...")
                    self._save_memory()
                    return item['id']
            
            # Создаем новую запись
            memory_item = {
                'id': memory_id,
                'content': content,
                'timestamp': timestamp,
                'importance': max(1, min(10, importance)),  # Ограничиваем значением 1-10
                'category': category,
                'tags': tags or [],
                'metadata': metadata or {},
                'accessed_count': 0
            }
            
            # Добавляем в память
            self.long_term_memory.append(memory_item)
            
            # Сортируем по важности и времени
            self.long_term_memory.sort(key=lambda x: (-x['importance'], x['timestamp']), reverse=True)
            
            # Ограничиваем размер, удаляя наименее важные записи
            if len(self.long_term_memory) > self.max_long_term_entries:
                self.long_term_memory = self.long_term_memory[:self.max_long_term_entries]
            
            # Обновляем индексы
            self._rebuild_indices()
            
            # Сохраняем обновленную память
            self._save_memory()
            
            logger.debug(f"Добавлена новая запись в долговременную память: {content[:30]}...")
            return memory_id
    
    def get_from_long_term(self, memory_id: str = None, update_access: bool = True) -> Optional[Dict[str, Any]]:
        """
        Получение записи из долговременной памяти по ID.
        
        Args:
            memory_id: ID записи
            update_access: Обновлять счетчик доступа и время последнего доступа
            
        Returns:
            Запись из долговременной памяти или None, если не найдена
        """
        with self.memory_lock:
            for item in self.long_term_memory:
                if item['id'] == memory_id:
                    if update_access:
                        item['accessed_count'] = item.get('accessed_count', 0) + 1
                        item['last_accessed'] = datetime.now().isoformat()
                    return item.copy()
            return None
    
    def search_long_term(self, query: str = None, category: str = None, tags: List[str] = None,
                         min_importance: int = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Поиск в долговременной памяти.
        
        Args:
            query: Текстовый запрос (поиск по содержимому)
            category: Фильтр по категории
            tags: Фильтр по тегам (должны присутствовать все указанные теги)
            min_importance: Минимальная важность для включения
            limit: Максимальное количество результатов
            
        Returns:
            Список найденных записей
        """
        with self.memory_lock:
            # Начинаем с полного списка
            candidates = list(range(len(self.long_term_memory)))
            
            # Фильтрация по категории (используем индекс)
            if category:
                if category in self.category_index:
                    candidates = [i for i in candidates if i in self.category_index[category]]
                else:
                    return []  # Если категория не найдена, возвращаем пустой список
            
            # Фильтрация по тегам (используем индекс)
            if tags:
                for tag in tags:
                    if tag in self.tag_index:
                        candidates = [i for i in candidates if i in self.tag_index[tag]]
                    else:
                        return []  # Если хотя бы один тег не найден, возвращаем пустой список
            
            # Фильтрация по важности
            if min_importance:
                candidates = [i for i in candidates if self.long_term_memory[i]['importance'] >= min_importance]
            
            # Фильтрация по текстовому запросу
            if query:
                query_lower = query.lower()
                filtered_candidates = []
                for i in candidates:
                    if query_lower in self.long_term_memory[i]['content'].lower():
                        filtered_candidates.append(i)
                candidates = filtered_candidates
            
            # Получаем записи по индексам и обновляем счетчик доступа
            results = []
            for i in candidates[:limit]:
                item = self.long_term_memory[i].copy()
                self.long_term_memory[i]['accessed_count'] = self.long_term_memory[i].get('accessed_count', 0) + 1
                self.long_term_memory[i]['last_accessed'] = datetime.now().isoformat()
                results.append(item)
            
            return results
    
    def update_long_term(self, memory_id: str, updates: Dict[str, Any]) -> bool:
        """
        Обновление записи в долговременной памяти.
        
        Args:
            memory_id: ID записи
            updates: Словарь с обновлениями
            
        Returns:
            True если запись найдена и обновлена, иначе False
        """
        with self.memory_lock:
            for item in self.long_term_memory:
                if item['id'] == memory_id:
                    # Обновляем поля, кроме id
                    for key, value in updates.items():
                        if key != 'id':
                            item[key] = value
                    
                    # Обновляем время изменения
                    item['timestamp'] = datetime.now().isoformat()
                    
                    # Пересортируем, если изменилась важность
                    if 'importance' in updates:
                        self.long_term_memory.sort(key=lambda x: (-x['importance'], x['timestamp']), reverse=True)
                    
                    # Обновляем индексы, если изменились теги или категория
                    if 'tags' in updates or 'category' in updates:
                        self._rebuild_indices()
                    
                    # Сохраняем изменения
                    self._save_memory()
                    
                    logger.debug(f"Обновлена запись в долговременной памяти: {memory_id}")
                    return True
            
            logger.debug(f"Запись не найдена: {memory_id}")
            return False
    
    def delete_from_long_term(self, memory_id: str) -> bool:
        """
        Удаление записи из долговременной памяти.
        
        Args:
            memory_id: ID записи
            
        Returns:
            True если запись найдена и удалена, иначе False
        """
        with self.memory_lock:
            for i, item in enumerate(self.long_term_memory):
                if item['id'] == memory_id:
                    # Удаляем запись
                    del self.long_term_memory[i]
                    
                    # Обновляем индексы
                    self._rebuild_indices()
                    
                    # Сохраняем изменения
                    self._save_memory()
                    
                    logger.debug(f"Удалена запись из долговременной памяти: {memory_id}")
                    return True
            
            logger.debug(f"Запись для удаления не найдена: {memory_id}")
            return False
    
    # Методы для работы с кратковременной памятью
    
    def add_to_short_term(self, content: str, category: str = "temp", 
                          tags: List[str] = None, metadata: Dict[str, Any] = None,
                          ttl: int = 3600) -> str:
        """
        Добавление записи в кратковременную память.
        
        Args:
            content: Содержимое записи
            category: Категория записи
            tags: Список тегов для категоризации
            metadata: Дополнительные метаданные
            ttl: Время жизни записи в секундах (по умолчанию 1 час)
            
        Returns:
            ID добавленной записи
        """
        memory_id = self._generate_id(content)
        timestamp = datetime.now().isoformat()
        expiry = (datetime.now().timestamp() + ttl)
        
        with self.memory_lock:
            # Проверяем, есть ли уже похожая запись
            for item in self.short_term_memory:
                if item['content'] == content and item['category'] == category:
                    # Обновляем существующую запись
                    item['timestamp'] = timestamp
                    item['expiry'] = expiry
                    if tags:
                        item['tags'] = list(set(item.get('tags', []) + tags))
                    if metadata:
                        if 'metadata' not in item:
                            item['metadata'] = {}
                        item['metadata'].update(metadata)
                    
                    logger.debug(f"Обновлена существующая запись в кратковременной памяти: {content[:30]}...")
                    self._save_memory()
                    return item['id']
            
            # Создаем новую запись
            memory_item = {
                'id': memory_id,
                'content': content,
                'timestamp': timestamp,
                'category': category,
                'tags': tags or [],
                'metadata': metadata or {},
                'expiry': expiry
            }
            
            # Добавляем в память
            self.short_term_memory.append(memory_item)
            
            # Сортируем по времени (от новых к старым)
            self.short_term_memory.sort(key=lambda x: x['timestamp'], reverse=True)
            
            # Ограничиваем размер, удаляя самые старые записи
            if len(self.short_term_memory) > self.max_short_term_entries:
                self.short_term_memory = self.short_term_memory[:self.max_short_term_entries]
            
            # Сохраняем обновленную память
            self._save_memory()
            
            logger.debug(f"Добавлена новая запись в кратковременную память: {content[:30]}...")
            return memory_id
    
    def get_from_short_term(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """
        Получение записи из кратковременной памяти по ID.
        
        Args:
            memory_id: ID записи
            
        Returns:
            Запись из кратковременной памяти или None, если не найдена или истекла
        """
        current_time = datetime.now().timestamp()
        
        with self.memory_lock:
            for item in self.short_term_memory:
                if item['id'] == memory_id:
                    # Проверяем, не истекло ли время жизни
                    if item['expiry'] and float(item['expiry']) < current_time:
                        # Если истекло, удаляем запись
                        self.short_term_memory.remove(item)
                        self._save_memory()
                        return None
                    return item.copy()
            return None
    
    def search_short_term(self, query: str = None, category: str = None, 
                          tags: List[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Поиск в кратковременной памяти.
        
        Args:
            query: Текстовый запрос (поиск по содержимому)
            category: Фильтр по категории
            tags: Фильтр по тегам (должны присутствовать все указанные теги)
            limit: Максимальное количество результатов
            
        Returns:
            Список найденных записей
        """
        results = []
        current_time = datetime.now().timestamp()
        
        with self.memory_lock:
            # Очищаем истекшие записи
            self.short_term_memory = [item for item in self.short_term_memory 
                                      if not item.get('expiry') or float(item['expiry']) >= current_time]
            
            # Фильтруем записи
            for item in self.short_term_memory:
                # Фильтр по категории
                if category and item['category'] != category:
                    continue
                
                # Фильтр по тегам
                if tags:
                    item_tags = set(item.get('tags', []))
                    if not all(tag in item_tags for tag in tags):
                        continue
                
                # Фильтр по текстовому запросу
                if query and query.lower() not in item['content'].lower():
                    continue
                
                results.append(item.copy())
                
                if len(results) >= limit:
                    break
            
            return results
    
    def clear_expired_short_term(self) -> int:
        """
        Очистка истекших записей из кратковременной памяти.
        
        Returns:
            Количество удаленных записей
        """
        current_time = datetime.now().timestamp()
        
        with self.memory_lock:
            initial_count = len(self.short_term_memory)
            self.short_term_memory = [item for item in self.short_term_memory 
                                    if not item.get('expiry') or float(item['expiry']) >= current_time]
            
            if len(self.short_term_memory) < initial_count:
                self._save_memory()
            
            return initial_count - len(self.short_term_memory)
    
    # Методы для работы с рабочей памятью (workspace)
    
    def add_to_workspace(self, content: str, category: str = "workspace", 
                         metadata: Dict[str, Any] = None) -> str:
        """
        Добавление записи в рабочую память.
        
        Args:
            content: Содержимое записи
            category: Категория записи
            metadata: Дополнительные метаданные
            
        Returns:
            ID добавленной записи
        """
        memory_id = self._generate_id(content)
        timestamp = datetime.now().isoformat()
        
        with self.memory_lock:
            # Создаем новую запись
            memory_item = {
                'id': memory_id,
                'content': content,
                'timestamp': timestamp,
                'category': category,
                'metadata': metadata or {}
            }
            
            # Добавляем в память
            self.workspace_memory.append(memory_item)
            
            # Сортируем по времени (от новых к старым)
            self.workspace_memory.sort(key=lambda x: x['timestamp'], reverse=True)
            
            # Ограничиваем размер, удаляя самые старые записи
            if len(self.workspace_memory) > self.max_workspace_entries:
                self.workspace_memory = self.workspace_memory[:self.max_workspace_entries]
            
            # Сохраняем обновленную память
            self._save_memory()
            
            logger.debug(f"Добавлена новая запись в рабочую память: {content[:30]}...")
            return memory_id
    
    def get_workspace(self, category: str = None, limit: int = None) -> List[Dict[str, Any]]:
        """
        Получение записей из рабочей памяти.
        
        Args:
            category: Фильтр по категории
            limit: Максимальное количество записей
            
        Returns:
            Список записей из рабочей памяти
        """
        with self.memory_lock:
            if category:
                results = [item.copy() for item in self.workspace_memory if item['category'] == category]
            else:
                results = [item.copy() for item in self.workspace_memory]
            
            # Ограничиваем количество результатов
            if limit and limit > 0:
                results = results[:limit]
            
            return results
    
    def clear_workspace(self, category: str = None):
        """
        Очистка рабочей памяти.
        
        Args:
            category: Категория для очистки (если None, очищается вся рабочая память)
        """
        with self.memory_lock:
            if category:
                self.workspace_memory = [item for item in self.workspace_memory if item['category'] != category]
            else:
                self.workspace_memory = []
            
            # Сохраняем обновленную память
            self._save_memory()
            
            logger.debug(f"Рабочая память{'категории '+category if category else ''} очищена")
    
    # Методы для управления памятью в целом
    
    def promote_to_long_term(self, short_term_id: str, importance: int = 5) -> Optional[str]:
        """
        Перенос записи из кратковременной памяти в долговременную.
        
        Args:
            short_term_id: ID записи в кратковременной памяти
            importance: Важность для долговременной памяти
            
        Returns:
            ID записи в долговременной памяти или None, если запись не найдена
        """
        with self.memory_lock:
            # Ищем запись в кратковременной памяти
            short_term_item = None
            for item in self.short_term_memory:
                if item['id'] == short_term_id:
                    short_term_item = item
                    break
            
            if not short_term_item:
                logger.debug(f"Запись {short_term_id} не найдена в кратковременной памяти")
                return None
            
            # Добавляем в долговременную память
            long_term_id = self.add_to_long_term(
                content=short_term_item['content'],
                importance=importance,
                category=short_term_item['category'],
                tags=short_term_item.get('tags', []),
                metadata=short_term_item.get('metadata', {})
            )
            
            # Удаляем из кратковременной памяти
            self.short_term_memory = [item for item in self.short_term_memory if item['id'] != short_term_id]
            
            # Сохраняем обновленную память
            self._save_memory()
            
            logger.debug(f"Запись {short_term_id} перенесена в долговременную память как {long_term_id}")
            return long_term_id
    
    def summarize_memory(self, category: str = None, days: int = None, 
                         min_importance: int = None) -> str:
        """
        Создание текстового резюме памяти.
        
        Args:
            category: Фильтр по категории
            days: Количество дней для включения (от текущей даты)
            min_importance: Минимальная важность для включения
            
        Returns:
            Текстовое резюме
        """
        with self.memory_lock:
            # Фильтруем долговременную память
            filtered_memory = []
            
            if days:
                cutoff_date = (datetime.now() - datetime.timedelta(days=days)).isoformat()
                filtered_memory = [item for item in self.long_term_memory 
                                 if item['timestamp'] >= cutoff_date]
            else:
                filtered_memory = self.long_term_memory.copy()
            
            if category:
                filtered_memory = [item for item in filtered_memory 
                                 if item['category'] == category]
            
            if min_importance:
                filtered_memory = [item for item in filtered_memory 
                                 if item['importance'] >= min_importance]
            
            # Сортируем по важности и времени
            filtered_memory.sort(key=lambda x: (-x['importance'], x['timestamp']), reverse=True)
            
            # Формируем резюме
            summary = []
            
            # Добавляем заголовок
            if category:
                summary.append(f"Резюме памяти (категория: {category})")
            else:
                summary.append("Резюме памяти")
            
            if days:
                summary.append(f"За последние {days} дней")
            
            if min_importance:
                summary.append(f"Минимальная важность: {min_importance}")
            
            summary.append(f"Всего записей: {len(filtered_memory)}")
            summary.append("")
            
            # Группируем по категориям
            category_groups = {}
            for item in filtered_memory:
                cat = item['category']
                if cat not in category_groups:
                    category_groups[cat] = []
                category_groups[cat].append(item)
            
            # Добавляем записи по категориям
            for cat, items in category_groups.items():
                summary.append(f"== {cat.upper()} ({len(items)} записей) ==")
                for item in items[:5]:  # Ограничиваем до 5 записей на категорию
                    timestamp = datetime.fromisoformat(item['timestamp']).strftime('%Y-%m-%d %H:%M')
                    summary.append(f"[{timestamp}] [{item['importance']}] {item['content'][:100]}...")
                
                if len(items) > 5:
                    summary.append(f"... и еще {len(items) - 5} записей")
                
                summary.append("")
            
            return "\n".join(summary)
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """
        Получение статистики о памяти.
        
        Returns:
            Словарь со статистикой
        """
        with self.memory_lock:
            # Считаем количество записей по категориям
            long_term_categories = {}
            for item in self.long_term_memory:
                cat = item['category']
                if cat not in long_term_categories:
                    long_term_categories[cat] = 0
                long_term_categories[cat] += 1
            
            short_term_categories = {}
            for item in self.short_term_memory:
                cat = item['category']
                if cat not in short_term_categories:
                    short_term_categories[cat] = 0
                short_term_categories[cat] += 1
            
            # Считаем общее количество тегов
            all_tags = {}
            for item in self.long_term_memory:
                for tag in item.get('tags', []):
                    if tag not in all_tags:
                        all_tags[tag] = 0
                    all_tags[tag] += 1
            
            # Важные записи
            important_items = [item for item in self.long_term_memory if item['importance'] >= 8]
            
            # Возвращаем статистику
            return {
                'long_term_count': len(self.long_term_memory),
                'short_term_count': len(self.short_term_memory),
                'workspace_count': len(self.workspace_memory),
                'long_term_categories': long_term_categories,
                'short_term_categories': short_term_categories,
                'tags_count': len(all_tags),
                'most_common_tags': sorted(all_tags.items(), key=lambda x: x[1], reverse=True)[:10],
                'important_items_count': len(important_items)
            }
    
    def __del__(self):
        """Деструктор для корректного завершения работы."""
        try:
            self._save_memory()
        except:
            pass


# Пример использования
if __name__ == "__main__":
    # Настройка логирования
    logging.basicConfig(level=logging.INFO)
    
    # Создаем объект памяти агента
    memory = AgentMemory()
    
    # Добавляем записи в долговременную память
    memory.add_to_long_term(
        content="Обнаружен уязвимый сервис на порту 443",
        importance=9,
        category="security",
        tags=["vulnerability", "service", "https"],
        metadata={"port": 443, "service": "https", "cve": "CVE-2023-1234"}
    )
    
    memory.add_to_long_term(
        content="Имя пользователя системы: admin",
        importance=6,
        category="system_info",
        tags=["user", "credentials"],
        metadata={"username": "admin"}
    )
    
    # Добавляем запись в кратковременную память
    memory.add_to_short_term(
        content="Временный токен доступа: TOKEN123456",
        category="auth",
        tags=["token", "temporary"],
        metadata={"token": "TOKEN123456", "expires": "2023-05-01T12:00:00"},
        ttl=3600  # 1 час
    )
    
    # Добавляем запись в рабочую память
    memory.add_to_workspace(
        content="Анализ уязвимости CVE-2023-1234: HTTPS сервер уязвим к атаке типа...",
        category="analysis",
        metadata={"cve": "CVE-2023-1234"}
    )
    
    # Поиск в долговременной памяти
    results = memory.search_long_term(category="security", min_importance=8)
    print(f"Найдено {len(results)} записей в долговременной памяти:")
    for result in results:
        print(f"- {result['content']}")
    
    # Получение статистики
    stats = memory.get_memory_stats()
    print("\nСтатистика памяти:")
    print(f"Долговременная память: {stats['long_term_count']} записей")
    print(f"Кратковременная память: {stats['short_term_count']} записей")
    print(f"Рабочая память: {stats['workspace_count']} записей")
    
    # Получение резюме
    summary = memory.summarize_memory()
    print("\nРезюме памяти:")
    print(summary) 