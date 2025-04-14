#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
NeuroRAT Agent State Module

Модуль для управления состоянием агента, включая его цели, память, контекст и режим работы.
"""

import os
import json
import time
import logging
import threading
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Tuple

# Константы режимов работы
OPERATIONAL_MODE_AUTO = "auto"       # Полностью автономный режим
OPERATIONAL_MODE_MANUAL = "manual"   # Ручной режим (только по командам)
OPERATIONAL_MODE_HYBRID = "hybrid"   # Гибридный режим (автономный с возможностью переопределения)

# Для обратной совместимости
MODE_AUTO = OPERATIONAL_MODE_AUTO
MODE_MANUAL = OPERATIONAL_MODE_MANUAL
MODE_HYBRID = OPERATIONAL_MODE_HYBRID

# Настройка логирования
logger = logging.getLogger("AgentState")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

class AgentState:
    """
    Класс для управления состоянием агента.
    Хранит информацию о целях, памяти, контексте и режиме работы.
    """
    
    def __init__(self, agent_id: str = None, state_file: str = "agent_state.json", 
                 auto_save: bool = True, save_interval: int = 60):
        """
        Инициализация состояния агента.
        
        Args:
            agent_id: Уникальный идентификатор агента (если None, будет сгенерирован)
            state_file: Путь к файлу для сохранения состояния
            auto_save: Автоматически сохранять состояние с указанным интервалом
            save_interval: Интервал автосохранения в секундах
        """
        # Основные атрибуты
        self.agent_id = agent_id or self._generate_agent_id()
        self.creation_time = datetime.now().isoformat()
        self.last_updated = self.creation_time
        self.state_file = state_file
        self.auto_save = auto_save
        self.save_interval = save_interval
        
        # Оперативные данные
        self.mode = OPERATIONAL_MODE_MANUAL  # По умолчанию ручной режим
        self.context = {}        # Контекст агента (текущие данные)
        self.goals = []          # Список целей агента
        self.memory = []         # Память агента (важные события)
        self.errors = []         # Журнал ошибок
        self.commands = []       # История выполненных команд
        
        # Блокировка для потокобезопасности
        self.lock = threading.RLock()
        
        # Попытка загрузить состояние из файла
        if os.path.exists(state_file):
            try:
                self.load()
                logger.info(f"Состояние загружено из {state_file}")
            except Exception as e:
                logger.error(f"Не удалось загрузить состояние: {str(e)}")
        
        # Запуск потока автосохранения
        if auto_save:
            self.stop_auto_save = threading.Event()
            self.auto_save_thread = threading.Thread(
                target=self._auto_save_loop, 
                daemon=True,
                name="AgentStateAutoSaveThread"
            )
            self.auto_save_thread.start()
            logger.info(f"Автосохранение запущено с интервалом {save_interval} сек")
    
    def _generate_agent_id(self) -> str:
        """Генерация уникального ID агента."""
        # Создаем уникальный идентификатор на основе времени, хоста и случайного числа
        # Короткая версия UUID для более компактного ID
        return str(uuid.uuid4())[:12]
    
    def _auto_save_loop(self):
        """Цикл автоматического сохранения состояния."""
        while not self.stop_auto_save.is_set():
            time.sleep(self.save_interval)
            try:
                self.save()
            except Exception as e:
                logger.error(f"Ошибка при автосохранении: {str(e)}")
    
    def load(self, file_path: str = None):
        """
        Загрузка состояния из файла.
        
        Args:
            file_path: Путь к файлу (если None, используется self.state_file)
        """
        file_path = file_path or self.state_file
        
        with self.lock:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # Загружаем основные атрибуты
                self.agent_id = data.get('agent_id', self.agent_id)
                self.creation_time = data.get('creation_time', self.creation_time)
                self.mode = data.get('mode', OPERATIONAL_MODE_MANUAL)
                
                # Загружаем оперативные данные
                self.context = data.get('context', {})
                self.goals = data.get('goals', [])
                self.memory = data.get('memory', [])
                self.errors = data.get('errors', [])
                self.commands = data.get('commands', [])
                
                # Обновляем timestamp
                self.last_updated = datetime.now().isoformat()
                logger.info(f"Состояние загружено из {file_path}")
                return True
            except Exception as e:
                error_msg = f"Не удалось загрузить состояние из {file_path}: {str(e)}"
                logger.error(error_msg)
                self.errors.append({
                    "time": datetime.now().isoformat(),
                    "type": "load_error",
                    "message": error_msg
                })
                return False
    
    def save(self, file_path: str = None):
        """
        Сохранение состояния в файл.
        
        Args:
            file_path: Путь к файлу (если None, используется self.state_file)
        """
        file_path = file_path or self.state_file
        
        with self.lock:
            try:
                # Обновляем время последнего обновления
                self.last_updated = datetime.now().isoformat()
                
                # Формируем данные для сохранения
                data = {
                    'agent_id': self.agent_id,
                    'creation_time': self.creation_time,
                    'last_updated': self.last_updated,
                    'mode': self.mode,
                    'context': self.context,
                    'goals': self.goals,
                    'memory': self.memory,
                    'errors': self.errors,
                    'commands': self.commands
                }
                
                # Создаем директорию, если не существует
                directory = os.path.dirname(file_path)
                if directory and not os.path.exists(directory):
                    os.makedirs(directory)
                
                # Сохраняем данные
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                
                logger.debug(f"Состояние сохранено в {file_path}")
                return True
            except Exception as e:
                error_msg = f"Не удалось сохранить состояние в {file_path}: {str(e)}"
                logger.error(error_msg)
                self.errors.append({
                    "time": datetime.now().isoformat(),
                    "type": "save_error",
                    "message": error_msg
                })
                return False
    
    # Методы для управления режимом работы
    
    def set_mode(self, mode: str):
        """
        Установка режима работы агента.
        
        Args:
            mode: Режим работы (OPERATIONAL_MODE_AUTO, OPERATIONAL_MODE_MANUAL, OPERATIONAL_MODE_HYBRID)
        """
        if mode not in [OPERATIONAL_MODE_AUTO, OPERATIONAL_MODE_MANUAL, OPERATIONAL_MODE_HYBRID]:
            logger.warning(f"Неизвестный режим: {mode}. Использую {OPERATIONAL_MODE_MANUAL}.")
            mode = OPERATIONAL_MODE_MANUAL
        
        with self.lock:
            old_mode = self.mode
            self.mode = mode
            logger.info(f"Режим изменен: {old_mode} -> {mode}")
            
            # Добавляем запись в память о смене режима
            if old_mode != mode:
                self.add_memory(
                    f"Смена режима: {old_mode} -> {mode}",
                    importance=7,
                    category="mode_change"
                )
    
    def get_mode(self) -> str:
        """Получение текущего режима работы."""
        with self.lock:
            return self.mode
    
    # Методы для управления контекстом
    
    def update_context(self, data: Dict[str, Any]):
        """
        Обновление контекста агента.
        
        Args:
            data: Словарь с данными для обновления
        """
        with self.lock:
            self.context.update(data)
            self.last_updated = datetime.now().isoformat()
    
    def get_context(self, key: str = None) -> Any:
        """
        Получение значения из контекста.
        
        Args:
            key: Ключ для получения (если None, возвращается весь контекст)
            
        Returns:
            Значение из контекста или весь контекст
        """
        with self.lock:
            if key is None:
                return self.context.copy()
            return self.context.get(key)
    
    def clear_context(self, keys: List[str] = None):
        """
        Очистка контекста.
        
        Args:
            keys: Список ключей для удаления (если None, очищается весь контекст)
        """
        with self.lock:
            if keys is None:
                self.context = {}
                logger.info("Контекст полностью очищен")
            else:
                for key in keys:
                    if key in self.context:
                        del self.context[key]
                logger.info(f"Из контекста удалены ключи: {', '.join(keys)}")
            
            self.last_updated = datetime.now().isoformat()
    
    # Методы для управления целями
    
    def add_goal(self, description: str, priority: int = 5, deadline: str = None,
                metadata: Dict[str, Any] = None) -> str:
        """
        Добавление новой цели.
        
        Args:
            description: Описание цели
            priority: Приоритет (1-10, где 10 - наивысший)
            deadline: Срок выполнения (ISO формат)
            metadata: Дополнительные метаданные
            
        Returns:
            ID добавленной цели
        """
        goal_id = str(uuid.uuid4())[:8]
        
        with self.lock:
            goal = {
                "id": goal_id,
                "description": description,
                "priority": min(max(1, priority), 10),  # Ограничиваем диапазон 1-10
                "status": "active",
                "created": datetime.now().isoformat(),
                "deadline": deadline,
                "metadata": metadata or {},
                "updates": []
            }
            
            self.goals.append(goal)
            self.last_updated = datetime.now().isoformat()
            
            # Добавляем запись в память о новой цели
            self.add_memory(
                f"Новая цель: {description} (приоритет: {priority})",
                importance=8 if priority > 7 else 6,
                category="goal_created",
                metadata={"goal_id": goal_id}
            )
            
            logger.info(f"Добавлена новая цель: {description} [ID: {goal_id}, приоритет: {priority}]")
            return goal_id
    
    def update_goal(self, goal_id: str, status: str = None, priority: int = None,
                   progress: float = None, notes: str = None):
        """
        Обновление статуса цели.
        
        Args:
            goal_id: ID цели
            status: Новый статус (active, completed, failed, suspended)
            priority: Новый приоритет
            progress: Прогресс выполнения (0-100%)
            notes: Заметки по обновлению
        """
        with self.lock:
            for goal in self.goals:
                if goal["id"] == goal_id:
                    update = {
                        "time": datetime.now().isoformat(),
                        "changes": {}
                    }
                    
                    if status is not None and status in ["active", "completed", "failed", "suspended"]:
                        old_status = goal["status"]
                        goal["status"] = status
                        update["changes"]["status"] = {"old": old_status, "new": status}
                    
                    if priority is not None:
                        old_priority = goal["priority"]
                        goal["priority"] = min(max(1, priority), 10)
                        update["changes"]["priority"] = {"old": old_priority, "new": goal["priority"]}
                    
                    if progress is not None:
                        old_progress = goal.get("progress", 0)
                        goal["progress"] = min(max(0, progress), 100)
                        update["changes"]["progress"] = {"old": old_progress, "new": goal["progress"]}
                    
                    if notes:
                        update["notes"] = notes
                    
                    if update["changes"]:
                        goal["updates"].append(update)
                        self.last_updated = datetime.now().isoformat()
                        
                        # Важные изменения добавляем в память
                        if "status" in update["changes"] and update["changes"]["status"]["new"] in ["completed", "failed"]:
                            self.add_memory(
                                f"Цель '{goal['description']}' изменила статус на {update['changes']['status']['new']}",
                                importance=7,
                                category="goal_status_changed",
                                metadata={"goal_id": goal_id, "update": update}
                            )
                        
                        logger.info(f"Цель обновлена [ID: {goal_id}]: {update['changes']}")
                        return True
                    return False
            
            logger.warning(f"Цель с ID {goal_id} не найдена")
            return False
    
    def get_goals(self, status: str = None, min_priority: int = None) -> List[Dict[str, Any]]:
        """
        Получение списка целей с фильтрацией.
        
        Args:
            status: Фильтр по статусу
            min_priority: Минимальный приоритет для включения
            
        Returns:
            Список целей
        """
        with self.lock:
            if status is None and min_priority is None:
                return self.goals.copy()
            
            filtered_goals = []
            for goal in self.goals:
                if status and goal["status"] != status:
                    continue
                if min_priority and goal["priority"] < min_priority:
                    continue
                filtered_goals.append(goal.copy())
            
            return filtered_goals
    
    def get_goal(self, goal_id: str) -> Optional[Dict[str, Any]]:
        """
        Получение информации о конкретной цели.
        
        Args:
            goal_id: ID цели
            
        Returns:
            Словарь с информацией о цели или None, если цель не найдена
        """
        with self.lock:
            for goal in self.goals:
                if goal["id"] == goal_id:
                    return goal.copy()
            return None
    
    # Методы для управления памятью
    
    def add_memory(self, content: str, importance: int = 5, category: str = "general",
                  metadata: Dict[str, Any] = None) -> str:
        """
        Добавление записи в память агента.
        
        Args:
            content: Содержание записи
            importance: Важность (1-10, где 10 - наиважнейшая)
            category: Категория записи
            metadata: Дополнительные метаданные
            
        Returns:
            ID добавленной записи
        """
        memory_id = str(uuid.uuid4())[:8]
        
        with self.lock:
            memory_entry = {
                "id": memory_id,
                "time": datetime.now().isoformat(),
                "content": content,
                "importance": min(max(1, importance), 10),
                "category": category,
                "metadata": metadata or {}
            }
            
            self.memory.append(memory_entry)
            self.last_updated = datetime.now().isoformat()
            
            # Лимитируем размер памяти (оставляем наиболее важные записи)
            if len(self.memory) > 1000:  # Пример: максимум 1000 записей
                # Сортируем по важности (по убыванию) и времени (по убыванию)
                self.memory.sort(key=lambda x: (-x["importance"], -datetime.fromisoformat(x["time"]).timestamp()))
                # Оставляем только первые 1000 записей
                self.memory = self.memory[:1000]
            
            logger.debug(f"Добавлена запись в память: {content[:50]}{'...' if len(content) > 50 else ''}")
            return memory_id
    
    def get_memories(self, category: str = None, min_importance: int = None,
                   limit: int = None, sort_by_time: bool = True) -> List[Dict[str, Any]]:
        """
        Получение записей из памяти с фильтрацией.
        
        Args:
            category: Фильтр по категории
            min_importance: Минимальная важность для включения
            limit: Максимальное количество записей
            sort_by_time: Сортировать по времени (от новых к старым)
            
        Returns:
            Список записей из памяти
        """
        with self.lock:
            # Фильтрация
            filtered_memories = self.memory.copy()
            
            if category:
                filtered_memories = [m for m in filtered_memories if m["category"] == category]
            
            if min_importance:
                filtered_memories = [m for m in filtered_memories if m["importance"] >= min_importance]
            
            # Сортировка
            if sort_by_time:
                filtered_memories.sort(key=lambda x: x["time"], reverse=True)
            else:
                filtered_memories.sort(key=lambda x: x["importance"], reverse=True)
            
            # Ограничение количества
            if limit and limit > 0:
                filtered_memories = filtered_memories[:limit]
            
            return filtered_memories
    
    # Методы для логирования ошибок и команд
    
    def log_error(self, message: str, metadata: Dict[str, Any] = None):
        """
        Логирование ошибки.
        
        Args:
            message: Сообщение об ошибке
            metadata: Дополнительные метаданные
        """
        with self.lock:
            error_entry = {
                "timestamp": datetime.now().isoformat(),  # Используем timestamp для соответствия с thinker
                "message": message,
                "metadata": metadata or {}
            }
            
            self.errors.append(error_entry)
            self.last_updated = datetime.now().isoformat()
            
            # Добавляем серьезные ошибки в память
            self.add_memory(
                f"Ошибка: {message}",
                importance=8,  # Высокая важность для ошибок
                category="error",
                metadata=metadata
            )
            
            logger.error(f"Ошибка: {message}")
    
    def log_command(self, command: str, source: str = "manual", metadata: Dict[str, Any] = None) -> str:
        """
        Логирование выполненной команды.
        
        Args:
            command: Выполненная команда
            source: Источник команды ("manual", "autonomous", "api")
            metadata: Дополнительные метаданные
            
        Returns:
            ID команды
        """
        command_id = str(uuid.uuid4())[:8]
        
        with self.lock:
            command_entry = {
                "id": command_id,
                "timestamp": datetime.now().isoformat(),  # Используем timestamp для соответствия с thinker
                "command": command,
                "source": source,
                "status": "pending",
                "metadata": metadata or {}
            }
            
            self.commands.append(command_entry)
            self.last_updated = datetime.now().isoformat()
            
            # Лимитируем историю команд
            if len(self.commands) > 100:  # Пример: максимум 100 команд
                self.commands = self.commands[-100:]
            
            logger.debug(f"Зарегистрирована команда: {command}")
            return command_id

    def update_command(self, command_id: str, status: str, result: Dict[str, Any] = None):
        """
        Обновление статуса и результата выполнения команды.
        
        Args:
            command_id: ID команды
            status: Новый статус ("pending", "running", "completed", "failed")
            result: Результат выполнения команды
        """
        with self.lock:
            for cmd in self.commands:
                if cmd.get("id") == command_id:
                    cmd["status"] = status
                    if result:
                        cmd["result"] = result
                    cmd["updated_at"] = datetime.now().isoformat()
                    logger.debug(f"Обновлен статус команды {command_id}: {status}")
                    return True
            
            logger.warning(f"Команда с ID {command_id} не найдена")
            return False
    
    def get_commands(self, limit: int = None, status: str = None) -> List[Dict[str, Any]]:
        """
        Получение истории команд с фильтрацией.
        
        Args:
            limit: Максимальное количество команд
            status: Фильтр по статусу
            
        Returns:
            Список команд
        """
        with self.lock:
            # Фильтрация
            if status:
                filtered_commands = [cmd for cmd in self.commands if cmd.get("status") == status]
            else:
                filtered_commands = self.commands.copy()
            
            # Сортировка по времени (от новых к старым)
            filtered_commands.sort(key=lambda x: x["timestamp"], reverse=True)
            
            # Ограничение количества
            if limit and limit > 0:
                filtered_commands = filtered_commands[:limit]
            
            return filtered_commands
    
    def get_errors(self, limit: int = None) -> List[Dict[str, Any]]:
        """
        Получение журнала ошибок.
        
        Args:
            limit: Максимальное количество ошибок
            
        Returns:
            Список ошибок
        """
        with self.lock:
            # Сортировка по времени (от новых к старым)
            sorted_errors = sorted(self.errors, key=lambda x: x["timestamp"], reverse=True)
            
            # Ограничение количества
            if limit and limit > 0:
                sorted_errors = sorted_errors[:limit]
            
            return sorted_errors
    
    def get_info(self) -> Dict[str, Any]:
        """
        Получение общей информации об агенте.
        
        Returns:
            Словарь с общей информацией
        """
        with self.lock:
            return {
                "agent_id": self.agent_id,
                "creation_time": self.creation_time,
                "last_updated": self.last_updated,
                "mode": self.mode,
                "goals_count": len(self.goals),
                "active_goals": len([g for g in self.goals if g["status"] == "active"]),
                "memory_entries": len(self.memory),
                "errors_count": len(self.errors),
                "commands_count": len(self.commands)
            }
    
    def __del__(self):
        """Деструктор для корректного завершения работы."""
        if hasattr(self, 'auto_save') and self.auto_save:
            if hasattr(self, 'stop_auto_save'):
                self.stop_auto_save.set()
                if hasattr(self, 'auto_save_thread') and self.auto_save_thread.is_alive():
                    self.auto_save_thread.join(timeout=2)
            # Последнее сохранение перед удалением
            try:
                self.save()
            except:
                pass


# Пример использования
if __name__ == "__main__":
    # Настройка логирования
    logging.basicConfig(level=logging.INFO)
    
    # Создаем объект состояния агента
    agent_state = AgentState(auto_save=True, save_interval=5)
    
    # Устанавливаем режим
    agent_state.set_mode(OPERATIONAL_MODE_AUTO)
    
    # Добавляем цель
    goal_id = agent_state.add_goal("Изучить систему и составить отчет", priority=8)
    
    # Обновляем контекст
    agent_state.update_context({"last_check": datetime.now().isoformat()})
    
    # Добавляем запись в память
    agent_state.add_memory("Инициализация агента завершена", importance=7, category="system")
    
    # Логируем команду
    agent_state.log_command("whoami", metadata={"purpose": "identification"})
    
    # Выводим информацию об агенте
    print(json.dumps(agent_state.get_info(), indent=2))
    
    # Обновляем статус цели
    agent_state.update_goal(goal_id, progress=10, notes="Начат сбор информации")
    
    # Ждем немного для демонстрации автосохранения
    print("Ожидание автосохранения...")
    time.sleep(6)
    
    # Получаем все активные цели
    active_goals = agent_state.get_goals(status="active")
    print(f"Активные цели: {len(active_goals)}")
    
    # Получаем последние записи из памяти
    memories = agent_state.get_memories(limit=5)
    print(f"Последние записи памяти: {len(memories)}")
    
    # Закрытие и сохранение
    print("Завершение работы...")
    del agent_state 